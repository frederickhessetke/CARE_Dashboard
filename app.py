import streamlit as st
import pages.Dashboard as Dashboard
import pages.CARE_Form as CARE_Form
import pages.Landing as Landing

st.set_page_config(page_title="C.A.R.E Dashboard", layout="wide")

# If the user email is not yet in session state, go to the landing page
if "user_email" not in st.session_state:
    Landing.main()
else:
    # Sidebar navigation with Dashboard listed first
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "CARE Form"])

    # Load the selected page
    if page == "Dashboard":
        Dashboard.main()
    elif page == "CARE Form":
        CARE_Form.main()
