import streamlit as st
import streamlit_authenticator as stauth


def auth():
    authenticator = stauth.Authenticate(
        dict(st.secrets['credentials']),
        st.secrets['cookie']['name'],
        st.secrets['cookie']['key'],
        st.secrets['cookie']['expiry_days'],
        dict(st.secrets['preauthorized'])
    )
    return authenticator
