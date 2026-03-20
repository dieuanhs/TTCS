import streamlit as st
import requests


st.set_page_config(page_title="Login - Smart Finance", layout="centered")
st.markdown("""
   <style>
       [data-testid="stSidebar"] {
           background-color: #E8E3FF; /* Màu tím nhạt cho sidebar */
       }
   </style>
""", unsafe_allow_html=True)
# 1. Khởi tạo trạng thái đăng nhập nếu chưa có
if "logged_in" not in st.session_state:
   st.session_state.logged_in = False




# --- HÀM XỬ LÝ ĐĂNG NHẬP ---
def login():
   st.title("🔐 Đăng nhập hệ thống")


   with st.container():
       username = st.text_input("Tên đăng nhập")
       password = st.text_input("Mật khẩu", type="password")

       if st.button("Đăng nhập", use_container_width=True):
           # Dữ liệu gửi đi
           payload = {
               "username": username,  # Khớp với payload.get("username") ở backend
               "password": password
           }

           try:
               # GỌI ĐẾN BACKEND (Lưu ý: có thêm /users/ vì prefix của router là /users)
               response = requests.post("http://127.0.0.1:8000/users/login", json=payload)

               if response.status_code == 200:
                   data = response.json()
                   st.session_state.logged_in = True
                   st.session_state.user_name = data["full_name"]
                   st.success(f"Chào mừng {data['full_name']} đã quay trở lại!")
                   st.rerun()
               else:
                   # Lấy thông tin lỗi từ backend trả về
                   error_msg = response.json().get("detail", "Sai tài khoản hoặc mật khẩu!")
                   st.error(error_msg)

           except requests.exceptions.ConnectionError:
               st.error("Không thể kết nối tới Backend. Bạn đã chạy uvicorn chưa?")




# --- KIỂM TRA TRẠNG THÁI ---
if not st.session_state.logged_in:
   login()
   # Ẩn menu sidebar khi chưa đăng nhập (Dùng CSS)
   st.markdown("<style>ul {display: none;} .stSidebar {display: none;}</style>", unsafe_allow_html=True)
else:
   # Nếu đã đăng nhập thành công
   st.title(f"💸 Chào mừng {st.session_state.user_name}!")
   st.success("Bạn đã đăng nhập thành công. Hãy chọn chức năng ở menu bên trái.")


   if st.sidebar.button("Đăng xuất"):
       st.session_state.logged_in = False
       st.rerun()
