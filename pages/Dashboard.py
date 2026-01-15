import streamlit as st
import pandas as pd
from lib.ui import require_login
from lib.db import get_sessions_with_surveys
from lib.coach import compute_brain_score

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
require_login()

st.title("📊 Brain Dashboard")
st.caption("Your progress over time — before/after each MoveYourMatter session.")

u = st.session_state["user"]
rows = get_sessions_with_surveys(user_id=u["id"], limit=200)

if not rows:
    st.info("No sessions yet. Start your first Brain Check-in.")
    if st.button("Start Brain Check-in"):
        st.switch_page("pages/Brain_Checkin.py")
    st.stop()

# Build dataframe
data = []
for r in rows:
    s = r["session"]
    pre = r["pre"]
    post = r["post"]
    if not pre:
        continue
    pre_score = compute_brain_score(pre)
    post_score = compute_brain_score(post) if post else None

    data.append({
        "date": (s.get("created_at") or "")[:10],
        "session_id": s["id"],
        "session_type": (s.get("coach_prescription") or {}).get("session_type", "Session"),
        "pre_score": pre_score,
        "post_score": post_score,
        "delta_score": (post_score - pre_score) if post_score is not None else None,
        "pre_stress": pre["stress"],
        "post_stress": post["stress"] if post else None,
        "delta_stress": (post["stress"] - pre["stress"]) if post else None,
        "pre_focus": pre["focus"],
        "post_focus": post["focus"] if post else None,
        "delta_focus": (post["focus"] - pre["focus"]) if post else None,
        "pre_mood": pre["mood"],
        "post_mood": post["mood"] if post else None,
        "delta_mood": (post["mood"] - pre["mood"]) if post else None,
        "pre_energy": pre["energy"],
        "post_energy": post["energy"] if post else None,
        "delta_energy": (post["energy"] - pre["energy"]) if post else None,
    })

df = pd.DataFrame(data)
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.sort_values("date")

# Summary metrics (use completed sessions only)
completed = df.dropna(subset=["post_score"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Sessions (total)", len(df))
c2.metric("Sessions (completed)", len(completed))
if len(completed) > 0:
    c3.metric("Avg Brain Score Δ", round(completed["delta_score"].mean(), 1))
    c4.metric("Avg Stress Δ", round(completed["delta_stress"].mean(), 2))
else:
    c3.metric("Avg Brain Score Δ", "—")
    c4.metric("Avg Stress Δ", "—")

st.divider()

# Trend charts (Streamlit auto color)
left, right = st.columns(2)

with left:
    st.subheader("Brain Score trend")
    chart_df = df.set_index("date")[["pre_score", "post_score"]]
    st.line_chart(chart_df)

with right:
    st.subheader("Deltas per session (post - pre)")
    delta_df = df.set_index("date")[["delta_focus", "delta_mood", "delta_energy", "delta_stress"]]
    st.line_chart(delta_df)

st.divider()
st.subheader("Session history")
display_cols = ["date", "session_type", "pre_score", "post_score", "delta_score",
                "delta_stress", "delta_focus", "delta_mood", "delta_energy"]
st.dataframe(df[display_cols], use_container_width=True)

st.divider()
if st.button("Start a new session"):
    st.switch_page("pages/Brain_Checkin.py")
