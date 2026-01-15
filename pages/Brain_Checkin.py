import streamlit as st
from lib.ui import require_login, set_active_session_id
from lib.coach import pick_prescription, compute_brain_score
from lib.db import get_default_video, create_session, insert_survey

st.set_page_config(page_title="Brain Check-in", page_icon="🧠", layout="centered")
require_login()

st.title("🧠 Brain Check-in")
st.caption("Tell your Brain Coach where you are right now.")

with st.form("pre_survey"):
    c1, c2 = st.columns(2)
    with c1:
        energy = st.slider("Energy", 1, 5, 3)
        stress = st.slider("Stress", 1, 5, 3)
    with c2:
        focus = st.slider("Focus / Clarity", 1, 5, 3)
        mood = st.slider("Mood", 1, 5, 3)

    goal = st.selectbox("Primary goal today", ["Calm", "Focus", "Creativity", "Confidence", "Sleep"], index=1)
    notes = st.text_area("Optional: what’s on your mind?", placeholder="One sentence is enough…")

    submitted = st.form_submit_button("Get my prescription")

if not submitted:
    st.stop()

pre = {
    "energy": energy,
    "stress": stress,
    "focus": focus,
    "mood": mood,
    "goal": goal,
    "notes": notes.strip() if notes else None,
}

prescription = pick_prescription(pre)
video = get_default_video()

st.success("Prescription ready.")
st.markdown(prescription["insight"])

pre_score = compute_brain_score(pre)
st.metric("Brain Score (pre)", pre_score)

u = st.session_state["user"]
session = create_session(user_id=u["id"], video_id=video["id"], coach_prescription=prescription)
insert_survey(session_id=session["id"], kind="pre", payload=pre)

set_active_session_id(session["id"])

st.divider()
st.write(f"**Today’s session:** {video['title']}")
if st.button("Start Session ▶"):
    st.switch_page("pages/Session.py")
