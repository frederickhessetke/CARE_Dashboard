import streamlit as st
from scripts.db_utils import retrieve_units_data, get_branch_code, save_to_care_submissions, update_unit_status
import urllib.parse

def main():
    # Ensure 'unit_id_for_review' and 'is_rvp_approval' are set in session state
    query_params = st.query_params
    unit_id_from_url = query_params.get("unit_id", [None])[0]
    rvp_approval_from_url = query_params.get("rvp_approval", ["False"])[0] == "True"

    # Store URL parameters in session state only if they don't already exist
    if unit_id_from_url and "unit_id_for_review" not in st.session_state:
        st.session_state["unit_id_for_review"] = unit_id_from_url
    if "is_rvp_approval" not in st.session_state:
        st.session_state["is_rvp_approval"] = rvp_approval_from_url

    # Ensure email is provided before proceeding
    if "user_email" not in st.session_state:
        st.warning("To gain access to the app, you need to first provide your email.")
        st.stop()

    # Retrieve values from session state
    unit_id = st.session_state.get("unit_id_for_review")
    is_rvp_approval = st.session_state.get("is_rvp_approval", False)

    # Verify that we have a unit_id to review
    if not unit_id:
        st.error("No Unit ID found for review. Please ensure you're accessing the correct link.")
        st.stop()

    # Retrieve unit data based on the unit_id
    unit_data = retrieve_units_data(selected_branch=None, unit_id=unit_id)
    if unit_data.empty:
        st.error("No details found for the selected Unit ID.")
        st.stop()

    # Extract relevant details from the retrieved unit data
    unit_details = unit_data.iloc[0]
    branch = unit_details['Branch']
    customer = unit_details['Customer']
    contract_expiry_date = unit_details['Contract Expiry Date']
    controller_manufacturer = unit_details['Controller Name']
    branch_code = get_branch_code(branch) or "N/A"

    st.title("CARE Submission Form")

    with st.form("care_submission_form"):
        # Populate form fields, with some fields disabled for review
        st.text_input("**Region**", st.session_state.get("selected_region"), disabled=True)
        area = st.text_input("**Area**")
        st.text_input("**Branch Code**", branch_code, disabled=True)
        wo_number = st.text_input("**WO #**")
        st.text_input("**Customer**", customer, disabled=True)
        wo_type = st.selectbox("**WO Type**", ["", "Rope Replacement", "Machine/Bear Repair", "Hydro Packing Change",
                                               "Sheave Replacement", "Other"])
        description = st.text_area("**Description**")
        st.text_input("**Unit #**", unit_id, disabled=True)
        order_date = st.date_input("**Order Date (YYYY-MM-DD)**")
        estimated_completion = st.date_input("**Estimated Completion (YYYY-MM-DD)**")
        pre_calc_labour_hours = st.number_input("**Pre Calc Labour Hours**", min_value=0.0)
        st.text_input("**Branch Name**", branch, disabled=True)
        unit_on_list = st.selectbox("**Unit on Original CARE Unit List?**", options=["Yes", "No"], index=0)
        st.text_input("**Contract Expiry Date**", contract_expiry_date, disabled=True)
        temperament = st.text_area("**Current Temperament of Customer? How will This prevent a Cancellation?**")
        poc_name = st.text_input("**POC Name**")
        customer_email = st.text_input("**Customer Email Address**")
        st.text_input("**Controller Manufacturer**", controller_manufacturer, disabled=True)
        max_connected = st.selectbox("**MAX Connected**", options=["", "Yes", "No"])
        tk_extend_status = st.text_input("**TK Extend Status (Enter Proposal #)**")
        number_of_stops = st.number_input("**Number of Stops**", min_value=0)
        customer_visit_date = st.text_input("**Date Customer Visited and by Who**")
        dm_approval_date = st.date_input("**District Manager Approval Date (YYYY-MM-DD)**")
        approval_by_dm = st.text_input("**Approval By**")
        dm_notes = st.text_area("**District Manager Notes**")

        # Conditional RVP fields, visible only in RVP approval mode
        if is_rvp_approval:
            rvp_approval_date = st.date_input("**RVP Approval Date (YYYY-MM-DD)**")
            approval_by_rvp = st.text_input("**Approval by**")
        else:
            rvp_approval_date = None
            approval_by_rvp = None

        # Repair hours fields with mutually exclusive inputs
        repair_team_hours = st.number_input("**Repair Team Hours Approved**", min_value=0.0, step=0.1)
        repair_labour_hours = st.number_input("**Repair Labour Hours Approved**", min_value=0.0, step=0.1)

        # Ensure only one repair hours field can have a positive value
        if repair_team_hours > 0:
            repair_labour_hours = 0.0
        elif repair_labour_hours > 0:
            repair_team_hours = 0.0

        # Additional notes and calculated approval value
        notes = st.text_area("**Notes**")
        value_approved = (190.70 * repair_team_hours) if repair_team_hours > 0 else (101.50 * repair_labour_hours)
        st.text_input("**Value Approved**", value=f"{value_approved:.2f}", disabled=True)

        submit_button = st.form_submit_button("Submit for RVP Approval" if not is_rvp_approval else "Approve and Submit")

    # Handle form submission based on RVP approval status
    if submit_button:
        if is_rvp_approval:
            # Collect form data for saving in RVP approval mode
            form_data = {
                "unit_id": unit_id,
                "region": st.session_state.get("selected_region"),
                "area": area,
                "branch_code": branch_code,
                "wo_number": wo_number,
                "customer": customer,
                "wo_type": wo_type,
                "description": description,
                "order_date": order_date.strftime('%Y-%m-%d') if order_date else None,
                "estimated_completion": estimated_completion.strftime('%Y-%m-%d') if estimated_completion else None,
                "pre_calc_labour_hours": pre_calc_labour_hours,
                "branch_name": branch,
                "unit_on_list": unit_on_list,
                "contract_expiry_date": contract_expiry_date,
                "temperament": temperament,
                "poc_name": poc_name,
                "customer_email": customer_email,
                "controller_manufacturer": controller_manufacturer,
                "max_connected": max_connected,
                "tk_extend_status": tk_extend_status,
                "number_of_stops": number_of_stops,
                "customer_visit_date": customer_visit_date,
                "dm_approval_date": dm_approval_date.strftime('%Y-%m-%d') if dm_approval_date else None,
                "approval_by_dm": approval_by_dm,
                "dm_notes": dm_notes,
                "rvp_approval_date": rvp_approval_date.strftime('%Y-%m-%d') if rvp_approval_date else None,
                "approval_by_rvp": approval_by_rvp,
                "repair_team_hours": repair_team_hours,
                "repair_labour_hours": repair_labour_hours,
                "notes": notes,
                "value_approved": value_approved
            }

            # Save the form data to the CARE_Submissions table
            save_to_care_submissions(form_data)
            update_unit_status(unit_id, "Yes")
            st.success("Form has been approved and submitted by the RVP.")
        else:
            # Generate the email content for manual copy-paste
            form_link = f"http://localhost:8501/CARE_Form?unit_id={unit_id}&rvp_approval=True"
            email_subject = "CARE Submission Form Approval Required"
            email_body = (
                f"Dear RVP,\n\n"
                f"Please review and approve the CARE submission form at the following link:\n\n"
                f"{form_link}\n\n"
                "Thank you for your attention to this matter.\n\n"
                "Best regards,\n"
                "Your Name"
            )

            # Display the email content in a text area for easy copying
            st.markdown("### Send Approval Request Email")
            st.write("To request approval, copy the following email content and paste it into an email to the RVP.")
            st.text_area("Email Content", f"Subject: {email_subject}\n\n{email_body}", height=200)

            st.success("The email content has been generated. Copy and send it through your Outlook client.")

# Call main() to execute the CARE form
if __name__ == "__main__":
    main()