import streamlit as st
from dialogs import show_profile_dialog, show_change_password_dialog

def apply_common_styles():
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] h1 {
            display: none !important;
        }

        /* Ẩn trang "App" trong navigation */
        [data-testid="stSidebarNavItems"] li:first-child {
            display: none !important;
        }
        [data-testid="stSidebarNav"]::before {
            content: "Smart Finance";
            display: block;
            text-align: center;
            color: #A093F2;
            font-size: 26px;
            font-weight: bold;
            padding-top: 20px;
            padding-bottom: 10px;
        }
        /* Sidebar màu */
        [data-testid="stSidebar"] {
            background-color: #F5E6DA !important;
        }

        /* Background */
        .stApp {
            background-color: #F8F9FE;
        }

        /* Container rộng */
        .block-container {
            padding-top: 1.5rem !important;
            max-width: 95% !important;
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
        div[data-testid="stHorizontalBlock"]:has(.header-anchor) {
            background-color: #A093F2;
            padding: 15px 25px;
            border-radius: 20px;
            align-items: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        /* Chữ bên trong dải header màu trắng */
        div[data-testid="stHorizontalBlock"]:has(.header-anchor) * {
            color: white !important;
        }
        
        div[data-testid="stHorizontalBlock"]:has(.header-anchor) button {
            border: 1px solid rgba(255, 255, 255, 0.5);
            background-color: rgba(255, 255, 255, 0.2);
            font-weight: bold;
        }
        div[data-testid="stHorizontalBlock"]:has(.header-anchor) button:hover {
            background-color: rgba(255, 255, 255, 0.4);
            border-color: white;
        }
        /* Chọn màu đen cho chữ trong popover*/
        div[data-testid="stPopoverBody"] * {
            color: #333 !important;
        }
        div[data-testid="stPopoverBody"] button {
            background-color: #f0f0f0 !important;
            border: none !important;
            margin-top: 5px;
        }
        div[data-testid="stPopoverBody"] button:hover {
            background-color: #e0e0e0 !important;
            color: black !important;
        }
        </style>
        """, unsafe_allow_html=True
    )

    col1, col2 = st.columns([5, 2])

    with col1:
        st.markdown(f"<div class='header-anchor' style='font-size: 24px; font-weight: bold;'>{title}</div>", unsafe_allow_html=True)

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