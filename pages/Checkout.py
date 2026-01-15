import streamlit as st
from lib.ui import require_login, get_active_session_id, clear_active_session
from lib.db import insert_survey, end_session, get_surveys_for_session
from lib.coach import compute_brain_score

st.set_page_config(page_title="Brain Check-out", page_icon="✅", layout="centered")
require_login()

session_id = get_active_session_id()
if not session_id:
    st.warning("No active session found.")
    st.switch_page("pages/Brain_Checkin.py")

pre, post_existing = get_surveys_for_session(session_id)
if not pre:
    st.error("Missing pre-survey for this session.")
    st.switch_page("pages/Brain_Checkin.py")

if post_existing:
    st.info("You already completed the check-out for this session.")
    clear_active_session()
    st.switch_page("pages/Dashboard.py")

st.title("✅ Brain Check-out")
st.caption("How did the session shift you?")

with st.form("post_survey"):
    c1, c2 = st.columns(2)
    with c1:
        energy = st.slider("Energy (now)", 1, 5, 3)
        stress = st.slider("Stress (now)", 1, 5, 3)
    with c2:
        focus = st.slider("Focus / Clarity (now)", 1, 5, 3)
        mood = st.slider("Mood (now)", 1, 5, 3)

    changed = st.selectbox("What changed most?", ["Stress", "Focus", "Mood", "Energy"])
    notes = st.text_area("Optional: any notes?", placeholder="What did you notice in your body/mind?")

    submitted = st.form_submit_button("Save & view stats")

if not submitted:
    st.stop()

post = {
    "energy": energy,
    "stress": stress,
    "focus": focus,
    "mood": mood,
    "goal": pre.get("goal"),
    "notes": (f"Changed most: {changed}. " + (notes.strip() if notes else "")).strip(),
}

insert_survey(session_id=session_id, kind="post", payload=post)
end_session(session_id)

pre_score = compute_brain_score(pre)
post_score = compute_brain_score(post)

st.success("Session saved.")
st.metric("Brain Score", post_score, delta=(post_score - pre_score))

# Clear active session so user doesn’t resubmit accidentally
clear_active_session()

if st.button("Go to Dashboard 📊"):
    st.switch_page("pages/Dashboard.py")
