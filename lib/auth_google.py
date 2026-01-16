import streamlit as st
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from urllib.parse import urlencode

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

def get_login_url():
    params = {
        "client_id": st.secrets["client_id"],
        "redirect_uri": st.secrets["app_base_url"],
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

def exchange_code_for_tokens(code: str):
    data = {
        "code": code,
        "client_id": st.secrets["client_id"],
        "client_secret": st.secrets["client_secret"],
        "redirect_uri": st.secrets["app_base_url"],
        "grant_type": "authorization_code",
    }
    resp = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=15)
    resp.raise_for_status()
    return resp.json()

def verify_google_id_token(id_token_str: str):
    info = id_token.verify_oauth2_token(
        id_token_str,
        grequests.Request(),
        st.secrets["client_id"],
    )
    return info

def handle_auth_callback():
    if st.session_state.get("user"):
        return

    qp = st.query_params
    code = qp.get("code")
    if not code:
        return

    tokens = exchange_code_for_tokens(code)
    userinfo = verify_google_id_token(tokens["id_token"])

    st.session_state["google_tokens"] = tokens
    st.session_state["google_userinfo"] = userinfo

    # clean URL
    st.query_params.clear()
