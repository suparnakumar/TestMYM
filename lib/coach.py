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
