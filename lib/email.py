import streamlit as st
import resend
from datetime import datetime, timedelta, timezone
from lib.db import supabase
from lib.coach import compute_brain_score


def get_weekly_stats(user_id: str) -> dict:
    """Get session statistics for the past 7 days."""
    sb = supabase()

    start_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    sessions = (
        sb.table("sessions")
        .select("*")
        .eq("user_id", user_id)
        .gte("created_at", start_date)
        .order("created_at", desc=True)
        .execute()
        .data
    )

    if not sessions:
        return {
            "total_sessions": 0,
            "completed_sessions": 0,
            "avg_brain_score_delta": 0,
            "best_metric": None,
            "streak_days": 0,
            "session_dates": [],
        }

    session_ids = [s["id"] for s in sessions]
    surveys = (
        sb.table("surveys")
        .select("*")
        .in_("session_id", session_ids)
        .execute()
        .data
    )

    surveys_by_session = {}
    for s in sessions:
        surveys_by_session[s["id"]] = {"pre": None, "post": None}
    for r in surveys:
        sid = r["session_id"]
        if sid in surveys_by_session:
            surveys_by_session[sid][r["kind"]] = r

    deltas = {"focus": [], "mood": [], "energy": [], "stress": []}
    brain_score_deltas = []
    completed = 0
    session_dates = set()

    for s in sessions:
        pre = surveys_by_session[s["id"]]["pre"]
        post = surveys_by_session[s["id"]]["post"]

        if pre and post:
            completed += 1
            pre_score = compute_brain_score(pre)
            post_score = compute_brain_score(post)
            brain_score_deltas.append(post_score - pre_score)

            for metric in ["focus", "mood", "energy", "stress"]:
                deltas[metric].append(int(post[metric]) - int(pre[metric]))

        date_str = (s.get("created_at") or "")[:10]
        if date_str:
            session_dates.add(date_str)

    avg_brain_delta = round(sum(brain_score_deltas) / len(brain_score_deltas), 1) if brain_score_deltas else 0

    best_metric = None
    best_value = 0
    for metric, vals in deltas.items():
        if not vals:
            continue
        avg = sum(vals) / len(vals)
        effective = -avg if metric == "stress" else avg
        if effective > best_value:
            best_value = effective
            best_metric = metric

    streak = calculate_streak(session_dates)

    return {
        "total_sessions": len(sessions),
        "completed_sessions": completed,
        "avg_brain_score_delta": avg_brain_delta,
        "best_metric": best_metric,
        "best_metric_value": round(best_value, 1) if best_metric else 0,
        "streak_days": streak,
        "session_dates": sorted(session_dates),
    }


def calculate_streak(session_dates: set) -> int:
    """Calculate consecutive days with sessions ending at today or yesterday."""
    if not session_dates:
        return 0

    today = datetime.now(timezone.utc).date()
    dates = sorted([datetime.strptime(d, "%Y-%m-%d").date() for d in session_dates], reverse=True)

    if dates[0] < today - timedelta(days=1):
        return 0

    streak = 1
    for i in range(1, len(dates)):
        if dates[i - 1] - dates[i] == timedelta(days=1):
            streak += 1
        else:
            break

    return streak


def generate_email_html(user: dict, stats: dict) -> str:
    """Generate HTML email content for weekly summary."""
    name = user.get("full_name") or "there"

    if stats["total_sessions"] == 0:
        return f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #1a1a1a;">Your Weekly Brain Summary</h1>
            <p>Hi {name},</p>
            <p>You didn't complete any sessions this week. That's okay - every week is a fresh start!</p>
            <p>When you're ready, your Brain Coach is here to help you find calm, focus, or energy.</p>
            <p style="margin-top: 30px;">- The MoveYourMatter Team</p>
        </body>
        </html>
        """

    best_metric_text = ""
    if stats["best_metric"]:
        metric_labels = {
            "focus": "Focus",
            "mood": "Mood",
            "energy": "Energy",
            "stress": "Stress reduction"
        }
        best_metric_text = f"<li><strong>Biggest win:</strong> {metric_labels.get(stats['best_metric'], stats['best_metric'])}</li>"

    streak_text = ""
    if stats["streak_days"] > 1:
        streak_text = f"<li><strong>Current streak:</strong> {stats['streak_days']} days in a row!</li>"

    delta_sign = "+" if stats["avg_brain_score_delta"] >= 0 else ""

    motivation = _get_motivation(stats)

    return f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #1a1a1a;">Your Weekly Brain Summary</h1>
        <p>Hi {name},</p>
        <p>Here's how your brain wellness journey went this week:</p>

        <ul style="line-height: 1.8;">
            <li><strong>Sessions completed:</strong> {stats['completed_sessions']}</li>
            <li><strong>Avg Brain Score change:</strong> {delta_sign}{stats['avg_brain_score_delta']} points</li>
            {best_metric_text}
            {streak_text}
        </ul>

        <p style="background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
            {motivation}
        </p>

        <p>Keep showing up for your brain!</p>
        <p style="margin-top: 30px; color: #666;">- The MoveYourMatter Team</p>
    </body>
    </html>
    """


def _get_motivation(stats: dict) -> str:
    """Return a motivational message based on stats."""
    if stats["avg_brain_score_delta"] >= 10:
        return "You're making significant progress. Your brain is thanking you for the consistent care."
    elif stats["avg_brain_score_delta"] >= 5:
        return "Solid week! Small improvements compound over time. You're building lasting brain health."
    elif stats["avg_brain_score_delta"] > 0:
        return "Every session moves the needle. You're on the right track."
    elif stats["streak_days"] >= 3:
        return "Your consistency is impressive! Showing up regularly is the key to lasting change."
    elif stats["completed_sessions"] >= 3:
        return "Three or more sessions this week - you're building a real habit. Keep it going!"
    else:
        return "You showed up for yourself this week. That's what matters most."


def send_weekly_summary(user: dict) -> dict:
    """Send weekly summary email to user. Returns {'success': bool, 'message': str}."""
    api_key = st.secrets.get("resend_api_key")
    if not api_key:
        return {"success": False, "message": "Email not configured. Add resend_api_key to secrets."}

    resend.api_key = api_key

    stats = get_weekly_stats(user["id"])
    html = generate_email_html(user, stats)

    try:
        resend.Emails.send({
            "from": "MoveYourMatter <noreply@resend.dev>",
            "to": [user["email"]],
            "subject": "Your MoveYourMatter Weekly Summary",
            "html": html,
        })
        return {"success": True, "message": f"Summary sent to {user['email']}"}
    except Exception as e:
        return {"success": False, "message": f"Failed to send email: {str(e)}"}
