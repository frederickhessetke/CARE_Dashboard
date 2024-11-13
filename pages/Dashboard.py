import streamlit as st
from scripts.db_utils import get_regions, get_branches, retrieve_units_data

def main():
    # Check if the user has provided their email
    if "user_email" not in st.session_state:
        st.warning("To gain access to the app, you need to first provide your email.")
        st.stop()  # Stop further execution until the email is provided

    st.markdown("<h1 style='text-align: center;'>C.A.R.E Dashboard</h1>", unsafe_allow_html=True)

    # Sidebar settings menu
    st.sidebar.header("Settings")
    region = st.sidebar.selectbox("Select Region", get_regions())
    if region:
        branch = st.sidebar.selectbox("Select Branch", get_branches(region))

    # Retrieve data button
    if st.sidebar.button("Retrieve Units Data"):
        if branch:
            units_data = retrieve_units_data(branch)
            st.session_state["units_data"] = units_data  # Store units_data in session state

    # Retrieve units_data from session state if available
    units_data = st.session_state.get("units_data", None)

    if units_data is not None:
        st.write("Units Out of Service:")
        if not units_data.empty:
            html_table = units_data.to_html(index=False, classes='wide-table')
            st.markdown(
                """
                <style>
                .wide-table {
                    width: 100%;
                    max-width: 1200px;
                    margin-left: auto;
                    margin-right: auto;
                }
                .wide-table th, .wide-table td {
                    padding: 8px;
                    text-align: center;
                }
                .wide-table td:nth-child(2) {
                    white-space: normal;
                    word-wrap: break-word;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            st.markdown(html_table, unsafe_allow_html=True)

        # Input field to enter Unit ID
        entered_unit_id = st.text_input("Enter the Unit ID to submit for review:", key="unit_id_input").strip()

        # Submit button to store unit_id and region in session state, and display a success message
        if st.button("Submit selected unit for review"):
            if entered_unit_id and entered_unit_id in units_data['Unit ID'].astype(str).values:
                st.session_state["unit_id_for_review"] = entered_unit_id
                st.session_state["selected_region"] = region  # Store the selected region

                # Flashy success message
                st.markdown(
                    """
                    <div style="
                        background-color: #4CAF50;
                        padding: 15px;
                        border-radius: 5px;
                        border: 2px solid #388E3C;
                        color: white;
                        font-size: 18px;
                        font-weight: bold;
                        text-align: center;
                        margin-top: 15px;
                        ">
                        ✅ Unit has been identified for review. Please click the 'CARE Form' page on the left side menu.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            else:
                st.error("Invalid Unit ID. Please enter a valid Unit ID from the table above.")


# Run main() if this file is executed
if __name__ == "__main__":
    main()
