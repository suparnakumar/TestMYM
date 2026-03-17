import streamlit as st
from lib.ui import require_login
from lib.email import get_weekly_stats, send_weekly_summary

st.set_page_config(page_title="Weekly Summary", page_icon="📧", layout="centered")
require_login()

st.title("📧 Weekly Summary")
st.caption("Preview your progress and send it to your email.")

u = st.session_state["user"]
stats = get_weekly_stats(u["id"])

st.divider()

if stats["total_sessions"] == 0:
    st.info("No sessions in the past 7 days. Complete a session to see your weekly stats!")
    if st.button("Start Brain Check-in"):
        st.switch_page("pages/Brain_Checkin.py")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Sessions Completed", stats["completed_sessions"])

delta_sign = "+" if stats["avg_brain_score_delta"] >= 0 else ""
c2.metric("Avg Brain Score Change", f"{delta_sign}{stats['avg_brain_score_delta']}")

if stats["streak_days"] > 0:
    c3.metric("Current Streak", f"{stats['streak_days']} days")
else:
    c3.metric("Current Streak", "—")

if stats["best_metric"]:
    metric_labels = {
        "focus": "Focus improvement",
        "mood": "Mood improvement",
        "energy": "Energy boost",
        "stress": "Stress reduction"
    }
    st.success(f"**Biggest win this week:** {metric_labels.get(stats['best_metric'], stats['best_metric'])}")

if stats["session_dates"]:
    st.write(f"**Sessions on:** {', '.join(stats['session_dates'])}")

st.divider()

st.subheader("Send to Email")
st.write(f"Send this summary to **{u['email']}**")

if st.button("Send Weekly Summary", type="primary"):
    with st.spinner("Sending..."):
        result = send_weekly_summary(u)

    if result["success"]:
        st.success(result["message"])
    else:
        st.error(result["message"])

st.divider()
if st.button("Back to Dashboard"):
    st.switch_page("pages/Dashboard.py")
