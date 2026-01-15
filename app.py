import streamlit as st
from lib.auth_google import get_login_url, handle_auth_callback
from lib.db import upsert_user
from lib.ui import pill

st.set_page_config(page_title="MoveYourMatter — Brain Coach", page_icon="🧠", layout="centered")

handle_auth_callback()

# If Google userinfo exists, upsert to DB, then set app user
if st.session_state.get("google_userinfo") and not st.session_state.get("user"):
    ui = st.session_state["google_userinfo"]
    user = upsert_user(
        google_sub=ui["sub"],
        email=ui.get("email"),
        full_name=ui.get("name"),
        avatar_url=ui.get("picture"),
    )
    st.session_state["user"] = user

st.title("🧠 MoveYourMatter")
st.caption("AI-powered Brain Coach (MVP)")

if not st.session_state.get("user"):
    st.write("Sign in to start a session and track your brain stats over time.")
    st.link_button("Continue with Google", get_login_url())
    st.stop()

u = st.session_state["user"]
col1, col2 = st.columns([1, 4])
with col1:
    if u.get("avatar_url"):
        st.image(u["avatar_url"], width=64)
with col2:
    st.subheader(u.get("full_name") or "Welcome")
    st.write(u["email"])

pill("Flow: Check-in → Session → Check-out → Dashboard")

st.divider()
st.write("Use the sidebar to begin.")
if st.button("Start Brain Check-in"):
    st.switch_page("pages/Brain_Checkin.py")

st.button("Log out", on_click=lambda: st.session_state.clear())
