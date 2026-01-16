import streamlit as st
from lib.ui import require_login, get_active_session_id, clear_active_session
from lib.db import insert_survey, end_session, get_surveys_for_session
from lib.coach import compute_brain_score

st.set_page_config(page_title="Brain Check-out", page_icon="✅", layout="centered")
require_login()

# Keep a stable session_id across reruns (button clicks rerun the whole script)
session_id = get_active_session_id() or st.session_state.get("last_session_id")
if not session_id:
    st.warning("No active session found.")
    st.switch_page("pages/Brain_Checkin.py")
    st.stop()

pre, post_existing = get_surveys_for_session(session_id)
if not pre:
    st.error("Missing pre-survey for this session.")
    st.switch_page("pages/Brain_Checkin.py")
    st.stop()

# If a post survey already exists, route to Dashboard (and avoid redirect loops on rerun)
if post_existing:
    st.info("You already completed the check-out for this session.")
    st.session_state["last_session_id"] = session_id
    clear_active_session()
    st.switch_page("pages/Dashboard.py")
    st.stop()

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

# IMPORTANT: don't clear active session yet — the Dashboard button click reruns this page.
# Keep a stable reference so reruns don't bounce the user back to Check-in.
st.session_state["last_session_id"] = session_id

if st.button("Go to Dashboard 📊"):
    clear_active_session()
    st.session_state.pop("last_session_id", None)
    st.switch_page("pages/Dashboard.py")
    st.stop()
