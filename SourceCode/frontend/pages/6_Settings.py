import streamlit as st
import os
import sys
import pandas as pd
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../"))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.styles import apply_common_styles, render_header

# =========================
# CONFIG PAGE
# =========================
st.set_page_config(
    page_title="Cài đặt - Smart Finance",
    layout="wide"
)

apply_common_styles()

# =========================
# AUTH CHECK
# =========================
if not st.session_state.get("logged_in", False):
    st.warning("Vui lòng đăng nhập để tiếp tục!")
    st.stop()

current_user = st.session_state.get("user_name", "User")

# =========================
# HEADER
# =========================
render_header("⚙️ Cài đặt hệ thống", current_user)

st.write("---")

# =========================
# LOAD SETTINGS
# =========================
SETTINGS_FILE = os.path.join(PROJECT_ROOT, "data", "user_settings.json")

default_settings = {
    "email_notification": True,
    "monthly_report": True
}

# Tạo folder nếu chưa có
os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)

# Đọc settings
if os.path.exists(SETTINGS_FILE):
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except:
        settings = default_settings
else:
    settings = default_settings

# =========================
# LAYOUT
# =========================
col1, col2 = st.columns([1, 1], gap="large")

# ==================================================
# LEFT SIDE
# ==================================================
with col1:

    # -------------------------
    # NOTIFICATION SETTINGS
    # -------------------------
    st.subheader("🔔 Thông báo")

    email_notification = st.toggle(
        "Nhận email cảnh báo vượt ngân sách",
        value=settings.get("email_notification", True)
    )

    monthly_report = st.toggle(
        "Nhận báo cáo tài chính cuối tháng",
        value=settings.get("monthly_report", True)
    )

    st.write("")

    # -------------------------
    # SAVE SETTINGS
    # -------------------------
    if st.button("💾 Lưu cài đặt", use_container_width=True):

        updated_settings = {
            "email_notification": email_notification,
            "monthly_report": monthly_report
        }

        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_settings, f, ensure_ascii=False, indent=4)

        st.success("Đã lưu cài đặt thành công!")
        st.rerun()

# ==================================================
# RIGHT SIDE
# ==================================================
with col2:


    # -------------------------
    # ACCOUNT INFORMATION
    # -------------------------
    st.subheader("👤 Thông tin tài khoản")

    st.text_input("Tên người dùng", value=current_user, disabled=True)

    st.text_input(
        "Vai trò",
        value=st.session_state.get("role", "Người dùng"),
        disabled=True
    )

