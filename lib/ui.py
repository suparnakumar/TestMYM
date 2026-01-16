import streamlit as st

def require_login():
    if not st.session_state.get("user"):
        st.warning("Please sign in first.")
        st.switch_page("app.py")

def get_active_session_id() -> str | None:
    return st.session_state.get("active_session_id")

def set_active_session_id(session_id: str):
    st.session_state["active_session_id"] = session_id

def clear_active_session():
    st.session_state.pop("active_session_id", None)

def pill(text: str):
    st.markdown(
        f"""
        <div style="
          display:inline-block;
          padding:6px 10px;
          border-radius:999px;
          border:1px solid rgba(255,255,255,0.15);
          background: rgba(255,255,255,0.04);
          font-size: 0.9rem;
        ">{text}</div>
        """,
        unsafe_allow_html=True,
    )
