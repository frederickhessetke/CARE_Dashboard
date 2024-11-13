import streamlit as st
from scripts.db_utils import get_rvp_emails


def main():
    # Capture URL parameters if they exist
    query_params = st.query_params
    unit_id = query_params.get("unit_id", [None])[0]
    rvp_approval = query_params.get("rvp_approval", ["False"])[0] == "True"

    # Store URL parameters in session state for later use, only if not already set
    if unit_id and "unit_id_for_review" not in st.session_state:
        st.session_state["unit_id_for_review"] = unit_id
    if "is_rvp_approval" not in st.session_state:
        st.session_state["is_rvp_approval"] = rvp_approval

    # Display the title and email input form
    st.title("Welcome to C.A.R.E Dashboard")
    st.write("Please enter your email to start.")

    # Input for the user's email
    user_email = st.text_input("Email Address")
    rvp_emails = st.session_state.get("rvp_emails", get_rvp_emails())

    if st.button("Submit"):
        # Store email in session state and determine if the user is an RVP
        st.session_state["user_email"] = user_email
        is_rvp = user_email in rvp_emails

        # Set 'is_rvp_approval' based on URL parameter or if the user is an RVP
        st.session_state["is_rvp_approval"] = st.session_state["is_rvp_approval"] or is_rvp

        # Display success or error message based on email role
        if is_rvp or not st.session_state["is_rvp_approval"]:
            st.success("Email verified! You can now access the dashboard.")
        else:
            st.error("Unauthorized access: You must be an RVP to access this page.")

