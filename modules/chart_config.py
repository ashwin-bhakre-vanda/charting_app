import streamlit as st

def ensure_state():
    if "chart_items" not in st.session_state:
        st.session_state["chart_items"] = []

def add_item(item: dict):
    ensure_state()
    st.session_state["chart_items"].append(item)

def remove_item(idx: int):
    ensure_state()
    if 0 <= idx < len(st.session_state["chart_items"]):
        st.session_state["chart_items"].pop(idx)

def clear_items():
    st.session_state["chart_items"] = []

def get_items():
    ensure_state()
    return st.session_state["chart_items"]