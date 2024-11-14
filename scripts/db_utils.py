import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta


# Adjust path to move up one directory and then access the database file
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'CARE_Database.db')


def connect_db():
    try:
        return sqlite3.connect(DB_PATH)
    except sqlite3.OperationalError as e:
        print(f"Error connecting to database at {DB_PATH}: {e}")
        raise  # Reraise to identify the issue if it still occurs


def get_regions():
    """Fetches a list of unique regions from the Canada_Hierarchy table."""
    with connect_db() as conn:
        query = "SELECT DISTINCT Region FROM Canada_Hierarchy ORDER BY Region ASC;"
        regions = [row[0] for row in conn.execute(query).fetchall()]
    return regions


def get_branches(selected_region):
    """Fetches a list of branches for a specified region from the Canada_Hierarchy table."""
    with connect_db() as conn:
        query = """
            SELECT DISTINCT `Parent Branch`
            FROM Canada_Hierarchy
            WHERE Region = ?
            ORDER BY `Parent Branch` ASC;
        """
        branches = [row[0] for row in conn.execute(query, (selected_region,)).fetchall()]
    return branches


def get_branch_code(branch_name):
    # Connect to the database using the existing function
    conn = connect_db()
    cursor = conn.cursor()

    # Query the Branch Code from Canada_Hierarchy table
    cursor.execute("SELECT [Branch Code] FROM Canada_Hierarchy WHERE Branch = ?", (branch_name,))
    result = cursor.fetchone()

    # Close the database connection
    conn.close()

    # Return the Branch Code if found, otherwise None
    return result[0] if result else None

def get_rvp_emails():
    """Fetch the list of RVP emails from the Canada_RVPs table."""
    conn = connect_db()  # Use the already defined connection function
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM Canada_RVPs")
    rvps = cursor.fetchall()
    conn.close()
    # Print retrieved emails for debugging
    print("Retrieved RVP emails:", rvps)
    # Return a set of emails for faster lookup
    return {row[0] for row in rvps}

def save_to_care_submissions(form_data):
    # Define SQL to create the CARE_Submissions table if it doesn’t exist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS CARE_Submissions (
        unit_id TEXT,
        region TEXT,
        area TEXT,
        branch_code TEXT,
        wo_number TEXT,
        customer TEXT,
        wo_type TEXT,
        description TEXT,
        order_date TEXT,
        estimated_completion TEXT,
        pre_calc_labour_hours REAL,
        branch_name TEXT,
        unit_on_list TEXT,
        contract_expiry_date TEXT,
        temperament TEXT,
        poc_name TEXT,
        customer_email TEXT,
        controller_manufacturer TEXT,
        max_connected TEXT,
        tk_extend_status TEXT,
        number_of_stops INTEGER,
        customer_visit_date TEXT,
        dm_approval_date TEXT,
        approval_by_dm TEXT,
        dm_notes TEXT,
        rvp_approval_date TEXT,
        approval_by_rvp TEXT,
        repair_team_hours REAL,
        repair_labour_hours REAL,
        notes TEXT,
        value_approved REAL
    )
    """

    # Insert data into CARE_Submissions table
    insert_data_query = """
    INSERT INTO CARE_Submissions (
        unit_id, region, area, branch_code, wo_number, customer, wo_type, description,
        order_date, estimated_completion, pre_calc_labour_hours, branch_name,
        unit_on_list, contract_expiry_date, temperament, poc_name, customer_email,
        controller_manufacturer, max_connected, tk_extend_status, number_of_stops,
        customer_visit_date, dm_approval_date, approval_by_dm, dm_notes, 
        rvp_approval_date, approval_by_rvp, repair_team_hours, repair_labour_hours,
        notes, value_approved
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    # Connect to the database and execute the queries
    conn = connect_db()
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute(create_table_query)

    # Insert form data into the table
    cursor.execute(insert_data_query, (
        form_data["unit_id"],
        form_data["region"],
        form_data["area"],
        form_data["branch_code"],
        form_data["wo_number"],
        form_data["customer"],
        form_data["wo_type"],
        form_data["description"],
        form_data["order_date"],
        form_data["estimated_completion"],
        form_data["pre_calc_labour_hours"],
        form_data["branch_name"],
        form_data["unit_on_list"],
        form_data["contract_expiry_date"],
        form_data["temperament"],
        form_data["poc_name"],
        form_data["customer_email"],
        form_data["controller_manufacturer"],
        form_data["max_connected"],
        form_data["tk_extend_status"],
        form_data["number_of_stops"],
        form_data["customer_visit_date"],
        form_data["dm_approval_date"],
        form_data["approval_by_dm"],
        form_data["dm_notes"],
        form_data["rvp_approval_date"],
        form_data["approval_by_rvp"],
        form_data["repair_team_hours"],
        form_data["repair_labour_hours"],
        form_data["notes"],
        form_data["value_approved"]
    ))

    # Commit and close the connection
    conn.commit()
    conn.close()


def update_unit_status(unit_id, status):
    # Update the Care Submission status in the Units_Out_Of_Service table
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE Units_Out_Of_Service SET [CARE Submission] = ? WHERE [Serial Number] = ?", (status, unit_id))
    conn.commit()
    conn.close()


def create_pending_submissions_table():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS CARE_Pending_Submissions (
        unit_id TEXT PRIMARY KEY,
        region TEXT,
        area TEXT,
        branch_code TEXT,
        wo_number TEXT,
        customer TEXT,
        wo_type TEXT,
        description TEXT,
        order_date TEXT,
        estimated_completion TEXT,
        pre_calc_labour_hours REAL,
        branch_name TEXT,
        unit_on_list TEXT,
        contract_expiry_date TEXT,
        temperament TEXT,
        poc_name TEXT,
        customer_email TEXT,
        controller_manufacturer TEXT,
        max_connected TEXT,
        tk_extend_status TEXT,
        number_of_stops INTEGER,
        customer_visit_date TEXT,
        dm_approval_date TEXT,
        approval_by_dm TEXT,
        dm_notes TEXT,
        repair_team_hours REAL,
        repair_labour_hours REAL,
        notes TEXT,
        value_approved REAL,
        status TEXT DEFAULT 'Pending'
    )
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating CARE_Pending_Submissions table: {e}")
    finally:
        conn.close()


def save_to_pending_submissions(form_data):
    create_pending_submissions_table()

    # Ensure "status" field is included with a default value
    form_data["status"] = "Pending"

    # Connect to the database and fetch column names from CARE_Pending_Submissions
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Get the column names from the table
        cursor.execute("PRAGMA table_info(CARE_Pending_Submissions)")
        table_columns = [column[1] for column in cursor.fetchall()]

    except sqlite3.Error as e:
        print(f"Error retrieving table columns: {e}")
        conn.close()
        return

    # Debugging: Check each field for valid value and corresponding column
    print("Debugging form_data contents with status indicators:")
    for key, value in form_data.items():
        # Check if the field has a corresponding column in the table
        has_column = key in table_columns
        has_value = bool(value)

        # Display ✔ if both value and column are valid, ✘ if either is missing
        status_icon = "✔" if has_column and has_value else "✘"
        status_message = f"{key}: {status_icon} (Value: {'Valid' if has_value else 'Missing'}, Column: {'Exists' if has_column else 'Missing'})"
        print(status_message)

    # Prepare values for insertion
    values = (
        form_data["unit_id"],
        form_data["region"],
        form_data["area"],
        form_data["branch_code"],
        form_data["wo_number"],
        form_data["customer"],
        form_data["wo_type"],
        form_data["description"],
        form_data["order_date"],
        form_data["estimated_completion"],
        form_data["pre_calc_labour_hours"],
        form_data["branch_name"],
        form_data["unit_on_list"],
        form_data["contract_expiry_date"],
        form_data["temperament"],
        form_data["poc_name"],
        form_data["customer_email"],
        form_data["controller_manufacturer"],
        form_data["max_connected"],
        form_data["tk_extend_status"],
        form_data["number_of_stops"],
        form_data["customer_visit_date"],
        form_data["dm_approval_date"],
        form_data["approval_by_dm"],
        form_data["dm_notes"],
        form_data["repair_team_hours"],
        form_data["repair_labour_hours"],
        form_data["notes"],
        form_data["value_approved"],
        form_data["status"]
    )

    # Insert data into the database
    insert_data_query = """
    INSERT OR REPLACE INTO CARE_Pending_Submissions (
        unit_id, region, area, branch_code, wo_number, customer, wo_type, description,
        order_date, estimated_completion, pre_calc_labour_hours, branch_name,
        unit_on_list, contract_expiry_date, temperament, poc_name, customer_email,
        controller_manufacturer, max_connected, tk_extend_status, number_of_stops,
        customer_visit_date, dm_approval_date, approval_by_dm, dm_notes,
        repair_team_hours, repair_labour_hours, notes, value_approved, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    try:
        cursor.execute(insert_data_query, values)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving data to CARE_Pending_Submissions: {e}")
    finally:
        conn.close()


def retrieve_pending_submission(unit_id):
    query = """
    SELECT * FROM CARE_Pending_Submissions
    WHERE unit_id = ?
    """
    try:
        conn = connect_db()
        df = pd.read_sql_query(query, conn, params=(unit_id,))
    except sqlite3.Error as e:
        print(f"Error retrieving data from CARE_Pending_Submissions: {e}")
        df = pd.DataFrame()  # Return empty DataFrame on error
    finally:
        conn.close()

    return df


def get_top20_customers(selected_branch):
    """Calculates and returns a set of the top 20 customers by annual revenue for a specific branch."""
    with connect_db() as conn:
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

    # Calculate Annual Value for each contract
    contracts_df['Current Monthly Amount'] = pd.to_numeric(
        contracts_df['Current Monthly Amount'].replace(r'[\$,]', '', regex=True), errors='coerce').fillna(0)
    contracts_df['Annual Value'] = contracts_df.apply(
        lambda x: x['Current Monthly Amount'] * frequency_multipliers.get(x['Billing Frequency'], 0), axis=1)

    # Aggregate the annual value by customer
    top_customers = contracts_df.groupby('Customer')['Annual Value'].sum().reset_index()
    top_customers = top_customers.sort_values(by='Annual Value', ascending=False).head(20)

    return set(top_customers['Customer'])


def retrieve_units_data(selected_branch=None, unit_id=None):
    """
    Retrieves and filters units data based on the selected branch or specific unit ID.
    If a unit_id is provided, retrieves details for that specific unit only.
    """
    with connect_db() as conn:
        # Modify query to filter by branch and optionally by a specific unit ID
        query = """
            SELECT 
                UOS.Branch,
                UOS.`Serial Number` AS `Unit ID`,
                UOS.`Building Address` AS Address,
                UOS.`Building Salesperson` AS Salesperson,
                UOS.`Out of Service Date` AS `Out of Service Date`,
                UOS.`Route`,
                UOS.`CARE Submission`,
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
            WHERE UOS.`CARE Submission` = 'No'
        """

        # Set up parameters based on whether branch or unit_id is provided
        params = []
        if selected_branch:
            query += " AND UOS.Branch = ?"
            params.append(selected_branch)
        if unit_id:
            query += " AND UOS.`Serial Number` = ?"
            params.append(unit_id)

        df = pd.read_sql_query(query, conn, params=params)

    # Perform additional transformations if we're getting all units for a branch
    if selected_branch and not unit_id:
        # Convert Contract Expiry Date to datetime and apply a 13-month cutoff
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

        # Get top 20 customers for the branch
        top20_customers = get_top20_customers(selected_branch)
        df['Top 20 Customer'] = df['Customer'].apply(lambda x: "✅" if x in top20_customers else "")

        # Format Annual Value as currency
        df['Annual Value'] = df['Annual Value'].apply(lambda x: "${:,.2f}".format(x))

        # Reorder columns to the specified order
        df = df[['Branch', 'Address', 'Customer', 'Top 20 Customer', 'Contract Expiry Date', 'Annual Value',
                 'Contract #', 'Unit ID', 'Salesperson', 'Supervisor', 'TAC Controller', 'Days Out of Service']]

    return df
