import streamlit as st
import requests
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.styles import apply_common_styles, render_header


CATEGORY_MAP = {
    "Ăn uống": 1,
    "Di chuyển": 2,
    "Hóa đơn": 3,
    "Học tập": 4,
    "Mua sắm": 5,
    "Sức khỏe": 6,
    "Giao lưu": 7,
    "Thu nhập": 8,
    "Khác": 9
}

REVERSE_CAT_MAP = {v: k for k, v in CATEGORY_MAP.items()}

# ==========================================

# 1. Khởi tạo giao diện
apply_common_styles()
user_name = st.session_state.get("user_name", "User")
render_header("Transactions", user_name=user_name)

BASE_URL = "http://127.0.0.1:8000"

# Kiểm tra đăng nhập
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vui lòng đăng nhập trước!")
    st.stop()

# Khởi tạo bộ nhớ tạm để giữ kết quả AI không bị mất khi load lại trang
if "ai_result" not in st.session_state:
    st.session_state.ai_result = None

# --- PHẦN 1: NHẬP LIỆU ---
input_text = st.text_input("Nhập chi tiêu (VD: Đi ăn bún bò hết 45k thấy hơi mệt)", placeholder="AI đang lắng nghe...")

# Tạo 2 cột nhỏ cho nút bấm
col_btn1, col_btn2, _ = st.columns([0.15, 0.2, 0.65])

with col_btn1:
    btn_analyze = st.button("Analyze ✨", use_container_width=True)

# with col_btn2:
#     # Nút Add Transaction nằm bên phải Analyze
#     btn_add = st.button("➕ Add Transaction", type="primary", use_container_width=True)

if btn_analyze:
    if input_text:
        with st.spinner("🧠 AI đang phân tích..."):
            try:
                #GỌI API
                res = requests.post(f"{BASE_URL}/transactions/smart-input", json={"text": input_text})

                if res.status_code == 200:
                    # Lưu kết quả vào session_state
                    st.session_state.ai_result = res.json()
                else:
                    st.error(f"Lỗi phân tích: {res.json().get('detail')}")
            except Exception as e:
                st.error("Không thể kết nối đến Backend. Đảm bảo uvicorn đang chạy!")
    else:
        st.error("Vui lòng nhập nội dung!")

# Hiển thị kết quả để người dùng Review
if st.session_state.ai_result:
    detected = st.session_state.ai_result

    st.write("### 🤖 Trợ lý AI nhận diện:")
    col_a, col_b, col_c, col_d = st.columns(4)

    # Hiển thị số tiền định dạng có dấu phẩy (VD: 45,000)
    col_a.metric("Số tiền", f"{detected['amount']:,} đ")
    col_b.write(f"**Danh mục:** 🏷️ {detected['category']}")
    col_c.write(f"**Cảm xúc:** 🎭 {detected['emotion']}")

    # Hiển thị Loại (Thu nhập/Chi tiêu) với màu sắc
    type_color = "🟢" if detected['type'] == "Thu nhập" else "🔴"
    col_d.write(f"**Loại:** {type_color} {detected['type']}")

    # Nút Xác nhận lưu vào Database
    if st.button("✅ Xác nhận"):
        try:
            # Chuyển danh mục về số
            cat_name = detected["category"]
            cat_id_number = CATEGORY_MAP.get(cat_name, 9)

            payload = {
                "user_id": 1,
                "description": detected["text"],
                "category_id": cat_id_number,
                "amount": detected["amount"],
                "type": detected["type"],
                "emotion": detected["emotion"]
            }

            # LƯU DATABASE
            save_res = requests.post(f"{BASE_URL}/transactions/", json=payload)

            if save_res.status_code == 200:
                st.success("🎉 Đã lưu giao dịch thành công!")
                st.session_state.ai_result = None
                st.rerun()
            else:
                st.error(f"Lỗi khi lưu: {save_res.text}")
        except Exception as e:
            st.error(f"Lỗi hệ thống: {e}")

st.divider()

# --- PHẦN 2: LỊCH SỬ GIAO DỊCH  ---
st.subheader("Lịch sử giao dịch")

try:
    # GỌI API
    response = requests.get(f"{BASE_URL}/transactions/")
    if response.status_code == 200:
        transactions = response.json()

        if not transactions:
            st.info("Chưa có giao dịch nào trong hệ thống.")
        else:
            # Tạo Header cho bảng
            h_col = st.columns([2, 3, 2, 2, 2, 1.5])
            headers = ["Thời gian", "Nội dung", "Danh mục", "Cảm xúc", "Số tiền", "Hành động"]
            for col, h in zip(h_col, headers):
                col.write(f"**{h}**")

            # Hiển thị từng dòng dữ liệu
            for tx in transactions:
                cols = st.columns([2, 3, 2, 2, 2, 1.5])

                # Cắt chuỗi thời gian
                time_str = tx.get("transaction_time", "N/A")[:16].replace("T", " ")
                cols[0].write(time_str)

                cols[1].write(f"**{tx.get('description', '')}**")

                # DỊCH NGƯỢC TỪ SỐ SANG CHỮ CHO BẢNG LỊCH SỬ
                db_cat_id = tx.get("category_id", 9)
                display_cat_name = REVERSE_CAT_MAP.get(db_cat_id, "Khác")

                cols[2].markdown(
                    f"<span style='background:#E1F5FE; color:#0277BD; padding:4px 8px; border-radius:10px; font-size:12px;'>🏷️ {display_cat_name}</span>",
                    unsafe_allow_html=True
                )

                cols[3].write(tx.get("emotion", "Normal"))

                # Phân loại màu cho số tiền (Xanh cho thu nhập, Đỏ cho chi tiêu)
                amt = tx.get("amount", 0)
                if tx.get("type") == "Thu nhập":
                    cols[4].write(f"<span style='color:green;'>+{amt:,} đ</span>", unsafe_allow_html=True)
                else:
                    cols[4].write(f"<span style='color:red;'>-{amt:,} đ</span>", unsafe_allow_html=True)

                if cols[5].button("Xóa", key=f"del_{tx.get('transaction_id')}"):
                    # GỌI API XÓA GIAO DỊCH
                    requests.delete(f"{BASE_URL}/transactions/{tx.get('transaction_id')}")
                    st.rerun()
    else:
        st.error("Không thể lấy dữ liệu lịch sử.")

except Exception as e:
    st.error(f"Lỗi kết nối Backend: Đảm bảo uvicorn đang chạy ở port 8000. Chi tiết: {e}")