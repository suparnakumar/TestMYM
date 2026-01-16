import streamlit as st
from supabase import create_client
from datetime import datetime, timezone

@st.cache_resource
def supabase():
    return create_client(st.secrets["supabase_url"], st.secrets["supabase_service_role_key"])

def now_utc_iso():
    return datetime.now(timezone.utc).isoformat()

def upsert_user(google_sub: str, email: str, full_name: str | None, avatar_url: str | None):
    sb = supabase()
    data = {
        "google_sub": google_sub,
        "email": email,
        "full_name": full_name,
        "avatar_url": avatar_url,
    }
    res = sb.table("users").upsert(data, on_conflict="google_sub").execute()
    return res.data[0]

def get_default_video():
    sb = supabase()
    res = sb.table("videos").select("*").order("created_at", desc=True).limit(1).execute()
    if not res.data:
        raise RuntimeError("No video found in table 'videos'. Seed one video row first.")
    return res.data[0]

def create_session(user_id: str, video_id: str, coach_prescription: dict):
    sb = supabase()
    res = sb.table("sessions").insert({
        "user_id": user_id,
        "video_id": video_id,
        "coach_prescription": coach_prescription,
        "started_at": now_utc_iso(),
    }).execute()
    return res.data[0]

def end_session(session_id: str):
    sb = supabase()
    sb.table("sessions").update({"ended_at": now_utc_iso()}).eq("id", session_id).execute()

def insert_survey(session_id: str, kind: str, payload: dict):
    sb = supabase()
    row = {"session_id": session_id, "kind": kind, **payload}
    res = sb.table("surveys").insert(row).execute()
    return res.data[0]

def get_session(session_id: str):
    sb = supabase()
    res = sb.table("sessions").select("*").eq("id", session_id).limit(1).execute()
    return res.data[0] if res.data else None

def get_surveys_for_session(session_id: str):
    sb = supabase()
    res = sb.table("surveys").select("*").eq("session_id", session_id).execute()
    pre = next((r for r in res.data if r["kind"] == "pre"), None)
    post = next((r for r in res.data if r["kind"] == "post"), None)
    return pre, post

def get_sessions_with_surveys(user_id: str, limit: int = 100):
    sb = supabase()
    sessions = sb.table("sessions").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute().data
    if not sessions:
        return []

    # Fetch surveys for all sessions (simple approach for MVP)
    session_ids = [s["id"] for s in sessions]
    surveys = sb.table("surveys").select("*").in_("session_id", session_ids).execute().data

    by_session = {}
    for s in sessions:
        by_session[s["id"]] = {"session": s, "pre": None, "post": None}

    for r in surveys:
        sid = r["session_id"]
        if sid in by_session:
            by_session[sid][r["kind"]] = r

    # Return list in session order
    return [by_session[s["id"]] for s in sessions]
