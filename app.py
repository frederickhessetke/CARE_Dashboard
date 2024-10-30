import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# Database path
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


# Function to retrieve units data for selected branch and region
def retrieve_units_data(selected_branch):
    with connect_db() as conn:
        # Define the query with joins to gather all required data
        query = """
            SELECT 
                UOS.Branch,
                UOS.`Serial Number` AS `Unit ID`,
                UOS.`Building Address` AS Address,
                UOS.`Building Salesperson` AS Salesperson,
                UOS.`Out of Service Date` AS `Out of Service Date`,  -- Used for filtering by 60 days
                CU.`Contract Number` AS `Contract #`,
                CU.`Controller Name` AS `Controller Name`,  -- Check for TAC Controller
                CC.Customer,
                CC.`Expiration Date` AS `Contract Expiry Date`
            FROM Units_Out_Of_Service AS UOS
            LEFT JOIN Canada_Units AS CU ON UOS.`Serial Number` = CU.`Serial Number`
            LEFT JOIN Canada_Contracts AS CC ON CU.`Contract Number` = CC.`Contract #`
            WHERE UOS.Branch = ?
        """
        # Fetch data into DataFrame
        df = pd.read_sql_query(query, conn, params=(selected_branch,))

        # Convert Contract Expiry Date to datetime and apply 13-month cutoff
        df['Contract Expiry Date'] = pd.to_datetime(df['Contract Expiry Date'], errors='coerce')
        comparison_date = datetime(2024, 10, 1)
        cutoff_date = comparison_date + timedelta(days=13 * 30)  # approx. 13 months
        df = df[df['Contract Expiry Date'] <= cutoff_date]

        # Parse Out of Service Date and filter out units that have been out of service for 60 days or more
        df['Out of Service Date'] = pd.to_datetime(df['Out of Service Date'], errors='coerce')
        today = datetime.today()
        df = df[(today - df['Out of Service Date']).dt.days < 60]

        # Ensure Contract # is an integer
        df['Contract #'] = pd.to_numeric(df['Contract #'], errors='coerce').fillna(0).astype(int)

        # Add TAC Controller column based on "Controller Name" containing "TAC"
        df['TAC Controller'] = df['Controller Name'].apply(lambda x: "✅" if "TAC" in str(x) else "")

        # Drop the "Controller Name" and "Out of Service Date" columns from the final display
        df = df.drop(columns=["Controller Name", "Out of Service Date"])

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
            # Inject CSS to center align all columns, wrap text in Address column, and widen Expiry Date
            st.markdown(
                """
                <style>
                .wide-table {
                    width: 100%;
                    margin-left: auto;
                    margin-right: auto;
                }
                .wide-table th, .wide-table td {
                    padding: 8px;
                    text-align: center;  /* Center align all columns */
                }
                .wide-table td:nth-child(3) { /* Wrap text for Address column */
                    white-space: normal;
                    word-wrap: break-word;
                }
                .wide-table td:nth-child(7) { /* Set minimum width for Contract Expiry Date */
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
