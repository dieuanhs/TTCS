import streamlit as st
from dialogs import show_profile_dialog, show_change_password_dialog

import json
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../"))
SETTINGS_FILE = os.path.join(PROJECT_ROOT, "data", "user_settings.json")


def apply_common_styles():
    st.session_state.dark_mode = False

    st.markdown(
        """
        <style>
        /* --- 1. FONTS & IMPORTS --- */
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Syne:wght@600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

        /* --- 2. TYPOGRAPHY (TEXT & NUMBERS) --- */
        html, body, p, a, li, td, input, label, h5, h6,
        .stMarkdown p, .stMarkdown span,
        [data-testid="stMetricLabel"], [data-testid="stMetricDelta"] {
            font-family: 'DM Sans', sans-serif !important;
        }

        h1, h2, h3, h4, 
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
            font-family: 'Syne', sans-serif !important;
            color: #1a202c !important;
            font-weight: 700 !important;
        }

        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] *,
        [data-testid="stMetricValue"] div,
        [data-testid="stMetricValue"] p,
        div[data-testid="metric-container"] [data-testid="stMetricValue"],
        div[data-testid="metric-container"] [data-testid="stMetricValue"] > div,
        [class*="metric"] [class*="value"],
        [class*="MetricValue"],
        /* AI phan tich */
        .ai-amount-text, .ai-amount-text * {
            font-family: 'DM Sans', sans-serif !important; /* Dùng DM Sans để số tròn đều */
            font-size: 34px !important; /* Cỡ chữ to rõ */
            font-weight: 700 !important;
            color: #1a202c !important;
            letter-spacing: 0px !important;
        }

        /* --- 3. METRIC CARDS ALIGNMENT --- */
        div[data-testid="stHorizontalBlock"]:has(div[data-testid="metric-container"]) {
            align-items: stretch !important;
        }

        div[data-testid="stHorizontalBlock"]:has(div[data-testid="metric-container"]) > div[data-testid="stColumn"] {
            display: flex !important;
            flex-direction: column !important;
            height: auto !important;
        }

        div[data-testid="stHorizontalBlock"]:has(div[data-testid="metric-container"]) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
        div[data-testid="stHorizontalBlock"]:has(div[data-testid="metric-container"]) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > div {
            flex: 1 !important;
            display: flex !important;
            flex-direction: column !important;
            height: 100% !important;
        }

        div[data-testid="metric-container"] {
            font-family: 'DM Sans', sans-serif !important;
            flex: 1 !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            height: 100% !important;
        }

        /* --- 4. ICONS FIX --- */
        button[data-testid="stSidebarCollapseButton"] {
            display: flex !important;
            color: #7B61FF !important; 
        }

        button[data-testid="stSidebarCollapseButton"] * {
            font-family: 'Material Symbols Outlined', sans-serif !important;
            font-size: 24px !important;
        }

        span[data-testid="stExpanderIcon"], 
        .stPopover button svg,
        .stPopover button span[class*="material"] {
            font-family: 'Material Symbols Outlined' !important;
            display: inline-block !important;
            visibility: visible !important;
        }

        .stPopover button {
            font-family: 'DM Sans', sans-serif !important;
        }

        /* --- 5. SIDEBAR --- */
        section[data-testid="stSidebar"] h1 { display: none !important; }
        [data-testid="stSidebarNavItems"] li:nth-child(1) { display: none !important; }

        [data-testid="stSidebarNav"]::before {
            content: "Smart Finance";
            display: block;
            text-align: center;
            color: #7B61FF !important;
            font-size: 24px;
            font-weight: 800;
            padding: 30px 0 20px 0;
            font-family: 'Syne', sans-serif !important;
        }

        [data-testid="stSidebar"] { background-color: #F5E6DA !important; }
        [data-testid="stSidebarNav"] span { color: #4a5568 !important; font-weight: 600 !important; }

        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background-color: rgba(123, 97, 255, 0.15) !important;
            border-radius: 8px !important;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] span { color: #7B61FF !important; }

        /* --- 6. GENERAL LAYOUT & COMPONENTS --- */
        .stApp { background-color: #F8F9FE !important; }
        .block-container { max-width: 100% !important; padding: 0 !important; }

        div.block-container > div[data-testid="stVerticalBlock"] > div:not(:has(.header-anchor)) {
            padding-left: 3rem !important;
            padding-right: 3rem !important;
        }

        .stButton>button {
            background: linear-gradient(135deg, #7B61FF, #56cfe1) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 6px rgba(123, 97, 255, 0.2) !important;
        }

        .stTextInput>div>div>input {
            border: 1px solid #cbd5e0 !important;
            border-radius: 10px !important;
            background-color: #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def render_header(title, user_name=None):
    is_logged_in = st.session_state.get("logged_in", False)

    if not is_logged_in:
        avatar = "Login"
        display_name = ""
    else:
        name = user_name if user_name else "User"
        display_name = name.split()[-1]
        avatar = f"👤 {display_name}"

    st.markdown(
        """
        <style>
        /* --- HEADER NAVBAR --- */
        div[data-testid="stHorizontalBlock"]:has(.header-anchor) {
            background: linear-gradient(135deg, #6C63FF 0%, #9B8DF2 100%);
            padding: 15px 30px;
            border-radius: 0px;
            align-items: center;
            box-shadow: 0 8px 20px rgba(108, 99, 255, 0.2);
            margin-top: 0px !important;
            margin-bottom: 25px;
            width: 100% !important;
        }

        div[data-testid="stHorizontalBlock"]:has(.header-anchor) * {
            color: white !important;
        }

        /* --- HEADER BUTTONS --- */
        div[data-testid="stHorizontalBlock"]:has(.header-anchor) button {
            border: 1px solid rgba(255, 255, 255, 0.3);
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 25px;
            padding: 5px 15px;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        div[data-testid="stHorizontalBlock"]:has(.header-anchor) button:hover {
            background: rgba(255, 255, 255, 0.3);
            border-color: white;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        /* --- POPOVER MENU --- */
        div[data-testid="stPopoverBody"] * {
            color: #333 !important;
        }

        div[data-testid="stPopoverBody"] button {
            background-color: #f8f9fa !important;
            border: 1px solid #eee !important;
            border-radius: 8px !important;
            margin-top: 8px;
            transition: all 0.2s ease;
        }

        div[data-testid="stPopoverBody"] button:hover {
            background-color: #A093F2 !important;
            color: white !important;
        }
        /* --- CĂN LỀ CHO NÚT AVATAR --- */
        div[data-testid="stHorizontalBlock"]:has(.header-anchor) > div[data-testid="stColumn"]:nth-child(2) {
            display: flex;
            justify-content: flex-end;
            align-items: center;
        }
        
        div[data-testid="stHorizontalBlock"]:has(.header-anchor) div[data-testid="stPopover"] {
            display: flex;
            justify-content: flex-end;
        }
        </style>
        """, unsafe_allow_html=True
    )

    col1, col2 = st.columns([8.5, 1.5])

    with col1:
        st.markdown(f"<div class='header-anchor' style='font-size: 24px; font-weight: bold;'>{title}</div>",
                    unsafe_allow_html=True)

    with col2:
        if is_logged_in:
            with st.popover(avatar):
                st.write(f"**Xin chào, {user_name}**")
                if st.button("Xem Profile", use_container_width=True):
                    show_profile_dialog(user_name)
                if st.button("Đổi mật khẩu", use_container_width=True):
                    show_change_password_dialog()
                if st.button("Đăng xuất", use_container_width=True):
                    st.session_state.clear()
                    st.switch_page("app.py")
        else:
            if st.button("Login"):
                st.switch_page("app.py")