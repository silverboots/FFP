import streamlit as st

if not st.session_state.auth["is_authed"]:
    st.switch_page("Main_Menu.py")
    
st.set_page_config(page_title="FPL DashBoard ", page_icon="📈")

st.write('Alerts')