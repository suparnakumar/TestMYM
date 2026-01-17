import streamlit as st
from openai import OpenAI


def generate_insight(pre: dict, post: dict) -> str:
    """Generate AI-powered insight based on pre/post survey deltas."""
    # Calculate deltas
    deltas = {
        "energy": int(post["energy"]) - int(pre["energy"]),
        "stress": int(post["stress"]) - int(pre["stress"]),
        "focus": int(post["focus"]) - int(pre["focus"]),
        "mood": int(post["mood"]) - int(pre["mood"]),
    }

    goal = pre.get("goal", "wellness")

    # Build context for the prompt
    changes = []
    for metric, delta in deltas.items():
        if delta > 0:
            changes.append(f"{metric} increased by {delta}")
        elif delta < 0:
            # Stress decrease is good, others decrease is neutral/less good
            if metric == "stress":
                changes.append(f"{metric} decreased by {abs(delta)} (improvement)")
            else:
                changes.append(f"{metric} decreased by {abs(delta)}")
        else:
            changes.append(f"{metric} stayed the same")

    changes_text = ", ".join(changes)

    prompt = f"""You are a supportive brain wellness coach. Based on the user's session data, provide a brief, personalized insight (2-3 sentences max).

User's goal: {goal}
Session changes: {changes_text}

Before session: Energy {pre['energy']}/5, Stress {pre['stress']}/5, Focus {pre['focus']}/5, Mood {pre['mood']}/5
After session: Energy {post['energy']}/5, Stress {post['stress']}/5, Focus {post['focus']}/5, Mood {post['mood']}/5

Guidelines:
- Be warm and encouraging
- Highlight the most significant positive change
- If stress decreased, that's a win
- Keep it concise and actionable
- Don't use generic phrases like "Great job!"
"""

    try:
        api_key = st.secrets.get("openai_api_key")
        if not api_key:
            return _fallback_insight(deltas)

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return _fallback_insight(deltas)


def _fallback_insight(deltas: dict) -> str:
    """Generate a simple fallback insight when API is unavailable."""
    best_metric = None
    best_delta = 0

    for metric, delta in deltas.items():
        # For stress, a decrease is positive
        effective_delta = -delta if metric == "stress" else delta
        if effective_delta > best_delta:
            best_delta = effective_delta
            best_metric = metric

    if best_metric == "stress":
        return "Your stress levels dropped after this session. Taking time for yourself is paying off."
    elif best_metric == "focus":
        return "Your focus sharpened during this session. You're building mental clarity."
    elif best_metric == "energy":
        return "Your energy got a boost. Movement is a powerful reset for your brain."
    elif best_metric == "mood":
        return "Your mood lifted after this session. Keep honoring what your brain needs."
    else:
        return "Every session is a step toward better brain health. Notice the small shifts."


def pick_prescription(pre: dict) -> dict:
    stress = int(pre["stress"])
    focus = int(pre["focus"])
    energy = int(pre["energy"])
    goal = pre.get("goal") or "Focus"

    if stress >= 4:
        session_type = "Calm Reset"
        target = "downshift stress and calm the nervous system"
    elif focus <= 2:
        session_type = "Focus Primer"
        target = "stabilize attention and improve clarity"
    elif energy <= 2:
        session_type = "Energize"
        target = "increase energy and motivation"
    else:
        session_type = "Balanced Boost"
        target = "support steady focus and mood"

    insight = (
        f"Your Brain Coach recommends **{session_type}** to {target}. "
        f"Goal: **{goal}**."
    )

    return {
        "session_type": session_type,
        "target": target,
        "insight": insight,
        "goal": goal,
    }

def compute_brain_score(m: dict) -> int:
    # 1–5 metrics -> 0–100 score; stress is inverted
    focus = int(m["focus"])
    mood = int(m["mood"])
    energy = int(m["energy"])
    stress = int(m["stress"])
    raw = (focus + mood + energy + (6 - stress)) / 4.0  # 1..5
    score = round((raw - 1) / 4 * 100)
    return max(0, min(100, int(score)))
