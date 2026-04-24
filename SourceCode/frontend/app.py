import streamlit as st
import requests
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../"))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from styles import apply_common_styles

st.set_page_config(page_title="Smart Finance - Login/Register", layout="centered")

# Gọi hàm style chung (Hàm này sẽ lo việc ẩn chữ 'app' ở sidebar)
apply_common_styles()

# 1. Khởi tạo trạng thái đăng nhập
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

BASE_URL = "http://127.0.0.1:8000"

# --- GIAO DIỆN CHÍNH ---
if not st.session_state.logged_in:
    st.title("🔐 Hệ Thống Smart Finance")

    # Ẩn hoàn toàn menu sidebar khi chưa đăng nhập
    st.markdown("<style>section[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

    # TẠO TAB ĐỂ CHỌN ĐĂNG NHẬP HOẶC ĐĂNG KÝ
    tab_login, tab_register = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký mới"])

    # --- TAB ĐĂNG NHẬP ---
    with tab_login:
        username = st.text_input("Tên đăng nhập", key="login_user")
        password = st.text_input("Mật khẩu", type="password", key="login_pass")

        if st.button("Đăng nhập", use_container_width=True, type="primary"):
            if username and password:
                try:
                    payload = {"username": username, "password": password}
                    response = requests.post(f"{BASE_URL}/users/login", json=payload)

                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.logged_in = True
                        st.session_state.user_name = data.get("full_name", username)

                        # ✨ DÒNG LỆNH THẦN THÁNH: Đăng nhập xong là nhảy thẳng vào Dashboard
                        st.switch_page("pages/1_Dashboard.py")
                    else:
                        error_msg = response.json().get("detail", "Sai tài khoản hoặc mật khẩu!")
                        st.error(f"Lỗi: {error_msg}")
                except Exception as e:
                    st.error(f"Lỗi kết nối: {e}")

    # --- TAB ĐĂNG KÝ ---
    with tab_register:
        st.subheader("Tạo tài khoản mới")
        new_user = st.text_input("Tên đăng nhập mới", key="reg_user")
        new_email = st.text_input("Email", key="reg_email")
        new_pass = st.text_input("Mật khẩu mới", type="password", key="reg_pass")

        if st.button("Đăng ký tài khoản", use_container_width=True):
            if new_user and new_pass:
                payload = {
                    "username": new_user,
                    "email": new_email,
                    "password": new_pass,
                    "full_name": new_user
                }
                try:
                    response = requests.post(f"{BASE_URL}/users/", json=payload)
                    if response.status_code == 200:
                        st.success("🎉 Đăng ký thành công! Hãy chuyển sang tab Đăng nhập.")
                    else:
                        err_msg = response.json().get("detail", "Lỗi đăng ký!")
                        st.error(f"Lỗi: {err_msg}")
                except Exception as e:
                    st.error(f"Lỗi kết nối: {e}")
            else:
                st.warning("Vui lòng điền đủ thông tin!")

else:
    # Nếu người dùng quay lại trang app.py sau khi đã đăng nhập
    st.switch_page("pages/1_Dashboard.py")