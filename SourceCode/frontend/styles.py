import streamlit as st

def apply_common_styles():
    st.markdown("""
<style>
    /* 1. Xóa khoảng trắng và ép trang rộng ra */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
        max-width: 95% !important;
    }

    /* 2. Ẩn thanh công cụ mặc định của Streamlit */
    /* Chỉ ẩn các nút bên phải (Deploy, Settings), giữ lại nút Sidebar bên trái */
    [data-testid="stHeaderActionElements"] {
        display: none;
    }

    /* 3. Màu nền Sidebar (Cam đào) */
    [data-testid="stSidebar"] {
        background-color: #F5E6DA !important;
    }

    /* 4. Chỉnh màu nền toàn trang */
    .stApp {
        background-color: #F8F9FE;
    }
</style>
    """, unsafe_allow_html=True)

def render_header(title, user_name="User"):
    display_name = user_name if user_name else "User"
    initial = display_name[0].upper()


    header_html = f"""
<div style="background-color: #A093F2; padding: 15px 30px; border-radius: 20px; display: flex; justify-content: space-between; align-items: center; width: 100%; box-sizing: border-box; margin-bottom: 30px; box-shadow: 0 4px 12px rgba(160, 147, 242, 0.2);">
    <div style="flex-shrink: 0;">
        <h2 style="color: white; margin: 0; font-size: 24px; white-space: nowrap; font-family: sans-serif;">{title}</h2>
    </div>
    <div style="display: flex; align-items: center; gap: 20px;">
        <div style="background: rgba(255, 255, 255, 0.2); padding: 8px 15px; border-radius: 12px; display: flex; align-items: center; min-width: 150px;">
            <span style="margin-right: 10px;">🔍</span>
            <span style="color: rgba(255,255,255,0.8); font-size: 14px;">Search...</span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px; color: white; font-family: sans-serif;">
            <span style="font-weight: 500; white-space: nowrap;">{display_name}</span>
            <div style="width: 40px; height: 40px; background-color: white; color: #A093F2; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px;">
                {initial}
            </div>
        </div>
    </div>
</div>
"""
    st.markdown(header_html, unsafe_allow_html=True)