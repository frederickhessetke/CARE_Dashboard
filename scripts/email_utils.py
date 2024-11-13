import win32com.client as win32
import pythoncom
import streamlit as st


def send_rvp_email(recipient_email, form_link):
    try:
        # Initialize COM
        pythoncom.CoInitialize()

        # Use EnsureDispatch instead of Dispatch
        outlook = win32.gencache.EnsureDispatch('outlook.application')
        mail = outlook.CreateItem(0)
        mail.To = recipient_email
        mail.Subject = "CARE Submission Form Approval Required"
        mail.Body = f"Please review and approve the CARE submission form at the following link:\n\n{form_link}"
        mail.Send()

        st.success("Approval request email sent to the RVP.")
    except Exception as e:
        st.error("Failed to send email through Outlook. Please ensure Outlook is open and try again.")
        print("Error details:", e)
    finally:
        # Uninitialize COM to clean up
        pythoncom.CoUninitialize()
