import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# Updated database path with new Routes table
DB_PATH = r'C:\Users\HESSEFREDERICK\PycharmProjects\CARE_Dashboard\data\CARE_Database.db'

# Connect to database
def connect_db():
    return sqlite3.connect(DB_PATH)


# Fetch unique regions from Canada_Hierarchy table
def get_regions():
    with connect_db() as conn:
        query = "SELECT DISTINCT Region FROM Canada_Hierarchy ORDER BY Region ASC;"
        regions = [row[0] for row in conn.execute(query).fetchall()]
    return regions


# Fetch branches based on selected region
def get_branches(selected_region):
    with connect_db() as conn:
        query = f"SELECT DISTINCT `Parent Branch` FROM Canada_Hierarchy WHERE Region = ? ORDER BY `Parent Branch` ASC;"
        branches = [row[0] for row in conn.execute(query, (selected_region,)).fetchall()]
    return branches


# Function to calculate top 20 customers for the selected branch
def get_top20_customers(selected_branch):
    with connect_db() as conn:
        # Query for all contracts for the selected branch, along with customer and contract values
        query = """
            SELECT 
                CC.Customer,
                CC.`Current Monthly Amount`,
                CC.`Billing Frequency`
            FROM Canada_Contracts AS CC
            WHERE CC.Branch = ?
        """
        contracts_df = pd.read_sql_query(query, conn, params=(selected_branch,))

    # Define billing frequency multipliers
    frequency_multipliers = {
        "Monthly": 12,
        "Bi-Monthly": 6,
        "Quarterly": 4,
        "Semi-Annually": 2,
        "Annually": 1,
        "Non-Billable": 0
    }

    # Convert Current Monthly Amount to numeric and calculate Annual Value for each contract
    contracts_df['Current Monthly Amount'] = pd.to_numeric(
        contracts_df['Current Monthly Amount'].replace(r'[\$,]', '', regex=True), errors='coerce').fillna(0)
    contracts_df['Annual Value'] = contracts_df.apply(
        lambda x: x['Current Monthly Amount'] * frequency_multipliers.get(x['Billing Frequency'], 0), axis=1)

    # Aggregate the annual value by customer
    top_customers = contracts_df.groupby('Customer')['Annual Value'].sum().reset_index()

    # Rank customers by aggregated annual value and get the top 20
    top_customers = top_customers.sort_values(by='Annual Value', ascending=False).head(20)

    # Print top 20 customers and their aggregated values
    print("Top 20 customers for branch:", selected_branch)
    print(top_customers)

    # Return a set of the top 20 customers for quick lookup
    return set(top_customers['Customer'])


# Function to retrieve units data for selected branch and region
def retrieve_units_data(selected_branch):
    # Identify top 20 customers for the selected branch
    top20_customers = get_top20_customers(selected_branch)

    with connect_db() as conn:
        # Define the query with joins to gather all required data, including the Supervisor from Routes table
        query = """
            SELECT 
                UOS.Branch,
                UOS.`Serial Number` AS `Unit ID`,
                UOS.`Building Address` AS Address,
                UOS.`Building Salesperson` AS Salesperson,
                UOS.`Out of Service Date` AS `Out of Service Date`,
                UOS.`Route`,
                CU.`Contract Number` AS `Contract #`,
                CU.`Controller Name` AS `Controller Name`,
                CC.Customer,
                CC.`Expiration Date` AS `Contract Expiry Date`,
                CC.`Current Monthly Amount`,
                CC.`Billing Frequency`,
                R.Supervisor AS `Supervisor`
            FROM Units_Out_Of_Service AS UOS
            LEFT JOIN Canada_Units AS CU ON UOS.`Serial Number` = CU.`Serial Number`
            LEFT JOIN Canada_Contracts AS CC ON CU.`Contract Number` = CC.`Contract #`
            LEFT JOIN Routes AS R ON UOS.`Route` = R.`Route`
            WHERE UOS.Branch = ?
        """
        # Fetch data into DataFrame
        df = pd.read_sql_query(query, conn, params=(selected_branch,))

        # Convert Contract Expiry Date to datetime and apply 13-month cutoff
        df['Contract Expiry Date'] = pd.to_datetime(df['Contract Expiry Date'], errors='coerce')
        comparison_date = datetime(2024, 10, 1)
        cutoff_date = comparison_date + timedelta(days=13 * 30)  # approx. 13 months
        df = df[df['Contract Expiry Date'] <= cutoff_date]

        # Parse Out of Service Date and calculate days out of service
        df['Out of Service Date'] = pd.to_datetime(df['Out of Service Date'], errors='coerce')
        today = datetime.today()
        df['Days Out of Service'] = (today - df['Out of Service Date']).dt.days

        # Filter out units that have been out of service for 60 days or more
        df = df[df['Days Out of Service'] < 60]

        # Ensure Contract # is an integer
        df['Contract #'] = pd.to_numeric(df['Contract #'], errors='coerce').fillna(0).astype(int)

        # Add TAC Controller column based on "Controller Name" containing "TAC"
        df['TAC Controller'] = df['Controller Name'].apply(lambda x: "✅" if "TAC" in str(x) else "")

        # Calculate Annual Value based on Current Monthly Amount and Billing Frequency
        frequency_multipliers = {
            "Monthly": 12,
            "Bi-Monthly": 6,
            "Quarterly": 4,
            "Semi-Annually": 2,
            "Annually": 1,
            "Non-Billable": 0
        }
        df['Current Monthly Amount'] = pd.to_numeric(df['Current Monthly Amount'].replace(r'[\$,]', '', regex=True),
                                                     errors='coerce').fillna(0)
        df['Annual Value'] = df.apply(
            lambda x: x['Current Monthly Amount'] * frequency_multipliers.get(x['Billing Frequency'], 0), axis=1)

        # Add Top 20 Customer column based on top 20 customer list
        df['Top 20 Customer'] = df['Customer'].apply(lambda x: "✅" if x in top20_customers else "")

        # Format Annual Value as currency
        df['Annual Value'] = df['Annual Value'].apply(lambda x: "${:,.2f}".format(x))

        # Reorder columns to the specified order
        df = df[['Branch', 'Address', 'Customer', 'Top 20 Customer', 'Contract Expiry Date', 'Annual Value',
                 'Contract #', 'Unit ID', 'Salesperson', 'Supervisor', 'TAC Controller', 'Days Out of Service']]

        # Drop unnecessary columns
        df = df.drop(
            columns=["Controller Name", "Out of Service Date", "Current Monthly Amount", "Billing Frequency", "Route"],
            errors='ignore')

        # Print out the number of units for verification
        print(f"Number of units retrieved for branch {selected_branch}: {len(df)}")

        return df


# Streamlit App
st.markdown("<h1 style='text-align: center;'>C.A.R.E Dashboard</h1>", unsafe_allow_html=True)  # Centered title

# Sidebar for settings menu
st.sidebar.header("Settings")

# Dropdown for selecting Region
region = st.sidebar.selectbox("Select Region", get_regions())

# Dropdown for selecting Branch, filtered by selected Region
if region:
    branch = st.sidebar.selectbox("Select Branch", get_branches(region))

# Retrieve data button
if st.sidebar.button("Retrieve Units Data"):
    if branch:
        # Retrieve and display the data in a table format
        units_data = retrieve_units_data(branch)

        # Display results as a custom HTML table for full-width view
        st.write("Units Out of Service:")
        if not units_data.empty:
            # Convert DataFrame to HTML with custom CSS styling
            html_table = units_data.to_html(index=False, classes='wide-table')
            # Inject CSS to center the table and align columns
            st.markdown(
                """
                <style>
                .wide-table {
                    width: 80%; /* Center the table horizontally */
                    margin: auto;
                }
                .wide-table th, .wide-table td {
                    padding: 8px;
                    text-align: center;  /* Center align all columns */
                }
                .wide-table td:nth-child(2) { /* Wrap text for Address column */
                    white-space: normal;
                    word-wrap: break-word;
                }
                .wide-table td:nth-child(5) { /* Set minimum width for Contract Expiry Date */
                    min-width: 120px;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            st.markdown(html_table, unsafe_allow_html=True)
        else:
            st.write("No units found with contracts expiring in 13 months or less and active for under 60 days.")
    else:
        st.write("Please select a Branch.")
