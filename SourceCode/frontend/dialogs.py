import streamlit as st
import requests
import time

BASE_URL = "http://127.0.0.1:8000"


@st.dialog("👤 Thông tin cá nhân")
def show_profile_dialog(user_name):
    st.write("Cập nhật thông tin tài khoản của bạn:")

    raw_email = st.session_state.get("email")
    current_email = raw_email if raw_email else "b23dccn062@stu.ptit.edu.vn"

    new_name = st.text_input("Họ và tên", value=user_name)
    new_email = st.text_input("Email", value=current_email)

    if st.button("💾 Lưu thay đổi", type="primary", use_container_width=True):
        payload = {"full_name": new_name, "email": new_email}
        res = requests.put(f"{BASE_URL}/users/{st.session_state.user_id}/update-profile", json=payload)
        if res.status_code == 200:
            st.session_state.user_name = new_name
            st.session_state.email = new_email
            st.success("Cập nhật thành công!")
            st.rerun()


@st.dialog("🔒 Đổi mật khẩu")
def show_change_password_dialog():
    old_pw = st.text_input("Mật khẩu hiện tại", type="password")
    new_pw = st.text_input("Mật khẩu mới", type="password")
    confirm_pw = st.text_input("Xác nhận mật khẩu mới", type="password")

    if st.button("Cập nhật mật khẩu", type="primary", use_container_width=True):
        if new_pw != confirm_pw:
            st.error("Mật khẩu xác nhận không khớp!")
        elif len(new_pw) < 8:
            st.error("Mật khẩu phải từ 6 ký tự trở lên!")
        else:
            payload = {"old_password": old_pw, "new_password": new_pw}
            res = requests.put(f"{BASE_URL}/users/{st.session_state.user_id}/change-password", json=payload)
            if res.status_code == 200:
                st.success("Đổi mật khẩu thành công!")
                st.session_state.clear()
                st.switch_page("app.py")
            else:
                st.error(res.json().get("detail", "Lỗi đổi mật khẩu"))