import streamlit as st
from lib.ui import require_login, get_active_session_id
from lib.db import get_session, get_default_video

st.set_page_config(page_title="Session", page_icon="🎬", layout="centered")
require_login()

session_id = get_active_session_id()
if not session_id:
    st.warning("No active session found. Start with Brain Check-in.")
    st.switch_page("pages/1_Brain_Checkin.py")

session = get_session(session_id)
if not session:
    st.error("Session not found in DB.")
    st.switch_page("pages/1_Brain_Checkin.py")

video = get_default_video()  # MVP: always the latest seeded video

st.title("🎬 Your prescribed session")
prescription = session.get("coach_prescription") or {}

st.markdown(f"**Session type:** {prescription.get('session_type','Session')}")
st.markdown(f"**Brain target:** {prescription.get('target','')}")
st.info(prescription.get("insight", "Move with intention."))

st.video(video["url"])

st.divider()
st.caption("When you’re done, complete your Brain Check-out.")
if st.button("Complete session ✅"):
    st.switch_page("pages/Checkout.py")
