import streamlit as st
import requests
from styles import apply_common_styles, render_header

# 1. Khởi tạo giao diện
apply_common_styles()
user_name = st.session_state.get("user_name", "User")
render_header("Transactions", user_name=user_name)

BASE_URL = "http://127.0.0.1:8000"

# Kiểm tra đăng nhập
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vui lòng đăng nhập trước!")
    st.stop()

# --- PHẦN 1: THÊM GIAO DỊCH MỚI ---
st.button("➕ Add Transaction", type="primary")

# Ô nhập liệu AI
input_text = st.text_input("Nhập chi tiêu (VD: Ăn bún bò 45k thấy hơi mệt)", placeholder="AI đang lắng nghe...")

if st.button("Analyze ✨"):
    if input_text:
        # Gửi sang Backend để AI phân tích (Giả sử bạn có endpoint /transactions/analyze)
        # Ở đây tớ mô phỏng logic nhận diện từ text
        with st.spinner("Đang phân tích..."):
            # Gọi API phân tích (đây là nơi lấy "số liệu tạo mới" từ Backend)
            # response = requests.post(f"{BASE_URL}/transactions/analyze", json={"text": input_text})

            # Giả lập dữ liệu trả về từ Backend
            detected = {"amount": "45,000", "category": "Food", "emotion": "Tired"}

            st.write("### Detected:")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Amount", f"{detected['amount']} VND")
            col_b.write(f"**Category:** 🟢 {detected['category']}")
            col_c.write(f"**Emotion:** 😴 {detected['emotion']}")

            if st.button("Save to Database"):
                # Gửi lệnh lưu vào DB
                st.success("Đã lưu vào lịch sử!")
    else:
        st.error("Vui lòng nhập nội dung!")

st.divider()

# --- PHẦN 2: LỊCH SỬ GIAO DỊCH (Lấy từ Backend) ---
st.subheader("Lịch sử giao dịch")

try:
    # Lấy dữ liệu thực tế từ Database thông qua Backend
    response = requests.get(f"{BASE_URL}/transactions/")
    if response.status_code == 200:
        transactions = response.json()

        # Tạo Header cho bảng
        h_col = st.columns([1.5, 3, 2, 2, 2, 1.5])
        headers = ["Date", "Description", "Category", "Emotion", "Amount", "Action"]
        for col, h in zip(h_col, headers):
            col.write(f"**{h}**")

        # Hiển thị từng dòng dữ liệu từ Backend
        for tx in transactions:
            cols = st.columns([1.5, 3, 2, 2, 2, 1.5])
            cols[0].write(tx.get("date", "Today"))
            cols[1].write(f"**{tx.get('description')}**")

            # Hiển thị tag màu cho Category
            cat = tx.get("category", "Other")
            cols[2].markdown(
                f"<span style='background:#E1F5FE; padding:2px 8px; border-radius:10px; font-size:12px;'>🏷️ {cat}</span>",
                unsafe_allow_html=True)

            cols[3].write(tx.get("emotion", "Normal"))

            # Amount màu đỏ nếu là chi tiêu (-)
            amt = tx.get("amount", 0)
            cols[4].write(f"<span style='color:red;'>-{amt:,}</span>", unsafe_allow_html=True)

            if cols[5].button("Edit", key=f"edit_{tx.get('id')}"):
                st.info(f"Sửa giao dịch {tx.get('id')}")
    else:
        st.info("Chưa có giao dịch nào trong hệ thống.")

except Exception as e:
    st.error(f"Lỗi kết nối Backend: {e}")