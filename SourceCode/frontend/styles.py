import streamlit as st


def apply_common_styles():
    st.markdown(
        """
        <style>
        /* Ẩn chữ "app" sidebar */
        section[data-testid="stSidebar"] h1 {
            display: none !important;
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
        avatar = display_name[0].upper()

    col1, col2, col3 = st.columns([5, 3, 1])

    with col1:
        st.markdown(
            f"""
            <div style="
                background-color: #A093F2;
                padding: 18px;
                border-radius: 20px;
                color: white;
                font-size: 24px;
                font-weight: bold;
                height: 60px;
                display: flex;
                align-items: center;
            ">
                {title}
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div style="
                background-color: #A093F2;
                padding: 18px;
                border-radius: 20px;
                height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
            ">
                🔍 Search...
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        if st.button(avatar):
            if is_logged_in:
                st.session_state.clear()
                st.rerun()
            else:
                st.switch_page("app.py")