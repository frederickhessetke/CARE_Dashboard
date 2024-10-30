import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# Database path
DB_PATH = DB_PATH = 'data/CARE_Database.db'


# Custom CSS to expand table width
st.markdown("""
    <style>
    .streamlit-container {
        max-width: 100% !important;
    }
    .dataframe-container {
        overflow-x: auto;  /* Enable horizontal scrolling */
        max-width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

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
                CU.`Contract Number` AS `Contract #`,
                CC.Customer,
                CC.`Expiration Date` AS `Contract Expiry Date`
            FROM Units_Out_Of_Service AS UOS
            LEFT JOIN Canada_Units AS CU ON UOS.`Serial Number` = CU.`Serial Number`
            LEFT JOIN Canada_Contracts AS CC ON CU.`Contract Number` = CC.`Contract #`
            WHERE UOS.Branch = ?
        """
        # Fetch data into DataFrame
        df = pd.read_sql_query(query, conn, params=(selected_branch,))

        # Convert Contract Expiry Date to datetime and filter contracts expiring in 18 months or less
        df['Contract Expiry Date'] = pd.to_datetime(df['Contract Expiry Date'], errors='coerce')
        cutoff_date = datetime.today() + timedelta(days=18 * 30)  # approx. 18 months
        df = df[df['Contract Expiry Date'] <= cutoff_date]

        # Print out the number of units for verification
        print(f"Number of units retrieved for branch {selected_branch}: {len(df)}")

        return df


# Streamlit App
st.title("C.A.R.E Dashboard")

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

        # Display results in Streamlit with customized width
        st.write("Units Out of Service:")
        if not units_data.empty:
            st.dataframe(units_data.style.set_table_styles([{
                'selector': 'table',
                'props': [('width', '100%')]
            }]), use_container_width=True)
        else:
            st.write("No units found with contracts expiring in 18 months or less.")
    else:
        st.write("Please select a Branch.")
