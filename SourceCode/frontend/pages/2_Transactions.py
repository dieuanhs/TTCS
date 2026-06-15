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
    "Ăn uống": 1, "Di chuyển": 2, "Giao lưu": 3, "Giải trí": 4,
    "Hóa đơn": 5, "Học tập": 6, "Mua sắm": 7, "Phát sinh": 8,
    "Sức khỏe": 9, "Thu nhập": 10,
}
REVERSE_CAT_MAP = {v: k for k, v in CATEGORY_MAP.items()}

# ==========================================
# 1. KHỞI TẠO GIAO DIỆN
# ==========================================
apply_common_styles()
user_name = st.session_state.get("user_name", "User")
render_header("Transactions", user_name=user_name)

BASE_URL = "http://127.0.0.1:8000"

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vui lòng đăng nhập trước!")
    st.stop()

if "ai_result" not in st.session_state:
    st.session_state.ai_result = None
user_id = st.session_state.get("user_id")

# ==========================================
# PHẦN 1: THÊM GIAO DỊCH BẰNG AI (SMART INPUT)
# ==========================================
with st.container():
    st.markdown("<h3 style='font-family: \"Syne\", sans-serif;'>✨ Thêm giao dịch nhanh</h3>", unsafe_allow_html=True)
    input_text = st.text_input("Nhập chi tiêu (VD: Đi ăn bún bò hết 45k thấy hơi mệt)",
                               placeholder="AI đang lắng nghe...", label_visibility="collapsed")

    col_btn1, col_btn2, _ = st.columns([0.15, 0.2, 0.65])
    with col_btn1:
        btn_analyze = st.button("Phân tích AI", use_container_width=True)

    if btn_analyze:
        if input_text:
            with st.spinner("Đang phân tích..."):
                try:
                    res = requests.post(f"{BASE_URL}/transactions/smart-input", json={"text": input_text})
                    if res.status_code == 200:
                        st.session_state.ai_result = res.json()
                    else:
                        st.error(f"Lỗi phân tích: {res.json().get('detail')}")
                except Exception as e:
                    st.error("Không thể kết nối đến Backend. Đảm bảo uvicorn đang chạy!")
        else:
            st.error("Vui lòng nhập nội dung!")

    # Hiển thị kết quả AI
    if st.session_state.ai_result:
        detected = st.session_state.ai_result
        st.markdown("""
            <div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #7B61FF; margin-top: 10px;'>
                <h4 style='margin-top:0;'>🤖 Trợ lý AI nhận diện:</h4>
            </div>
        """, unsafe_allow_html=True)

        col_a, col_b, col_c, col_d = st.columns(4)

        # Sửa lại hiển thị số tiền AI với class riêng để đảm bảo font vuông vức
        col_a.markdown("<p style='margin:0; color:#555;'>Số tiền</p>", unsafe_allow_html=True)
        col_a.markdown(f"<div class='ai-amount-text'>{detected['amount']:,} đ</div>", unsafe_allow_html=True)

        col_b.write(f"**Danh mục:** 🏷️ {detected['category']}")
        col_c.write(f"**Cảm xúc:** 🎭 {detected['emotion']}")

        type_color = "🟢" if detected['type'] == "Thu nhập" else "🔴"
        col_d.write(f"**Loại:** {type_color} {detected['type']}")

        if st.button("✅ Xác nhận lưu"):
            try:
                cat_id_number = CATEGORY_MAP.get(detected["category"], 8)
                payload = {
                    "user_id": user_id,
                    "description": detected["text"],
                    "category_id": cat_id_number,
                    "amount": detected["amount"],
                    "type": detected["type"],
                    "emotion": detected["emotion"]
                }
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

# ==========================================
# PHẦN 2: BỘ LỌC TÌM KIẾM (DEEP FILTERS)
# ==========================================
st.markdown("<h3 style='font-family: \"Syne\", sans-serif;'>🔍 Tra cứu & Quản lý</h3>", unsafe_allow_html=True)

# Hàng 1: Nút Lọc thời gian nhanh (Gọi API)
time_option = st.radio(
    "Khoảng thời gian:",
    ["Tất cả", "Tháng này", "7 ngày gần nhất"],
    horizontal=True,
    label_visibility="collapsed"
)
time_map = {"Tất cả": "all", "Tháng này": "month", "7 ngày gần nhất": "week"}
time_param = time_map[time_option]

# Hàng 2: Bộ lọc chi tiết (Xử lý Frontend)
f_col1, f_col2, f_col3 = st.columns(3)
search_query = f_col1.text_input("🔍 Tìm theo nội dung...", placeholder="Nhập từ khóa...")
cat_filter = f_col2.selectbox("🏷️ Theo danh mục", ["Tất cả"] + list(CATEGORY_MAP.keys()))
emo_filter = f_col3.selectbox("🎭 Theo cảm xúc", ["Tất cả", "Tích cực", "Bình thường", "Tiêu cực"])

st.write("")  # Tạo khoảng trắng nhỏ

# ==========================================
# PHẦN 3: BẢNG LỊCH SỬ GIAO DỊCH
# ==========================================
try:
    # 1. Lấy dữ liệu từ Backend kèm bộ lọc thời gian
    response = requests.get(f"{BASE_URL}/transactions/?user_id={user_id}&time_range={time_param}")

    if response.status_code == 200:
        raw_transactions = response.json()

        # 2. Xử lý bộ lọc chi tiết (Deep Filters) bằng Python
        filtered_tx = []
        for tx in raw_transactions:
            db_cat_name = REVERSE_CAT_MAP.get(tx.get("category_id", 8), "Khác")

            # Logic kiểm tra khớp điều kiện
            match_search = (search_query.lower() in tx.get('description', '').lower()) if search_query else True
            match_cat = (cat_filter == "Tất cả") or (db_cat_name == cat_filter)
            match_emo = (emo_filter == "Tất cả") or (tx.get('emotion') == emo_filter)

            if match_search and match_cat and match_emo:
                filtered_tx.append(tx)

        # 3. Hiển thị dữ liệu
        if not filtered_tx:
            st.info("Không tìm thấy giao dịch nào phù hợp với bộ lọc hiện tại.")
        else:
            st.caption(f"Đang hiển thị {len(filtered_tx)} giao dịch.")

            # Tạo Header cho bảng
            h_col = st.columns([2, 3, 2, 2, 2, 1.5])
            headers = ["Thời gian", "Nội dung", "Danh mục", "Cảm xúc", "Số tiền", "Hành động"]
            for col, h in zip(h_col, headers):
                col.write(f"**{h}**")

            # Hiển thị từng dòng dữ liệu
            for tx in filtered_tx:
                cols = st.columns([2, 3, 2, 2, 2, 1.5])

                # Thời gian
                time_str = tx.get("transaction_time", "N/A")[:16].replace("T", " ")
                cols[0].markdown(f"<span style='color:#555; font-size:14px;'>{time_str}</span>", unsafe_allow_html=True)

                # Nội dung
                cols[1].write(f"**{tx.get('description', '')}**")

                # Danh mục
                db_cat_id = tx.get("category_id", 8)
                display_cat_name = REVERSE_CAT_MAP.get(db_cat_id, "Khác")
                cols[2].markdown(
                    f"<span style='background:#E1F5FE; color:#0277BD; padding:4px 8px; border-radius:10px; font-size:12px; font-weight:600;'>{display_cat_name}</span>",
                    unsafe_allow_html=True
                )

                # Cảm xúc (Kèm Emoji)
                emo = tx.get("emotion", "Normal")
                emo_icon = "😊" if emo == "Tích cực" else "😐" if emo == "Bình thường" else "😢"
                cols[3].write(f"{emo_icon} {emo}")

                # Số tiền (Căn font DM Sans vuông vức)
                amt = tx.get("amount", 0)
                if tx.get("type") == "Thu nhập":
                    cols[4].markdown(
                        f"<span style='color:#2ECC71; font-weight:700; font-family:\"DM Sans\";'>+{amt:,} đ</span>",
                        unsafe_allow_html=True)
                else:
                    cols[4].markdown(
                        f"<span style='color:#E74C3C; font-weight:700; font-family:\"DM Sans\";'>-{amt:,} đ</span>",
                        unsafe_allow_html=True)

                # Nút Xóa
                if cols[5].button("🗑️ Xóa", key=f"del_{tx.get('transaction_id')}"):
                    requests.delete(f"{BASE_URL}/transactions/{tx.get('transaction_id')}")
                    st.rerun()
    else:
        st.error("Không thể lấy dữ liệu lịch sử.")

except Exception as e:
    st.error(f"Lỗi kết nối Backend: Đảm bảo uvicorn đang chạy ở port 8000. Chi tiết: {e}")