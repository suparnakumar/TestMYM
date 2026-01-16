import streamlit as st
from lib.ui import require_login, set_active_session_id
from lib.coach import pick_prescription, compute_brain_score
from lib.db import get_default_video, create_session, insert_survey

st.set_page_config(page_title="Brain Check-in", page_icon="🧠", layout="centered")
require_login()

st.title("🧠 Brain Check-in")
st.caption("Tell your Brain Coach where you are right now.")

# ---------- Form ----------
with st.form("pre_survey"):
    c1, c2 = st.columns(2)
    with c1:
        energy = st.slider("Energy", 1, 5, 3)
        stress = st.slider("Stress", 1, 5, 3)
    with c2:
        focus = st.slider("Focus / Clarity", 1, 5, 3)
        mood = st.slider("Mood", 1, 5, 3)

    goal = st.selectbox(
        "Primary goal today",
        ["Calm", "Focus", "Creativity", "Confidence", "Sleep"],
        index=1,
    )
    notes = st.text_area("Optional: what’s on your mind?", placeholder="One sentence is enough…")

    submitted = st.form_submit_button("Get my prescription")

# ---------- Only compute/create session ON submit ----------
if submitted:
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
    pre_score = compute_brain_score(pre)

    u = st.session_state["user"]
    session = create_session(
        user_id=u["id"],
        video_id=video["id"],
        coach_prescription=prescription,
    )
    insert_survey(session_id=session["id"], kind="pre", payload=pre)

    # Persist for reruns + Session page
    st.session_state["active_session_id"] = session["id"]
    st.session_state["active_video"] = video
    st.session_state["active_prescription"] = prescription
    st.session_state["pre_score"] = pre_score

# ---------- Render prescription if we have it (even on reruns) ----------
prescription = st.session_state.get("active_prescription")
video = st.session_state.get("active_video")
pre_score = st.session_state.get("pre_score")

if not prescription or not video or pre_score is None:
    st.info("Fill the check-in above to get your prescription.")
    st.stop()

st.success("Prescription ready.")
st.markdown(prescription["insight"])
st.metric("Brain Score (pre)", pre_score)

st.divider()
st.write(f"**Today’s session:** {video['title']}")

# ---------- Robust navigation ----------
if st.button("Start Session ▶", key="start_session_btn"):
    # (Optional) if you use this helper elsewhere
    if "active_session_id" in st.session_state:
        try:
            set_active_session_id(st.session_state["active_session_id"])
        except Exception:
            pass

    st.switch_page("pages/Sessions.py")
