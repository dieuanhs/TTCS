import streamlit as st
import requests
import datetime
import os
import sys

# --- CẤU TRÌNH ĐƯỜNG DẪN ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.styles import apply_common_styles, render_header

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="Smart Finance - Budget", layout="wide")
apply_common_styles()

# Lấy thông tin user
user_name = st.session_state.get("user_name", "User")
render_header("Budget Management", user_name=user_name)

BASE_URL = "http://127.0.0.1:8000"

# Kiểm tra đăng nhập
if not st.session_state.get("logged_in", False):
    st.warning("⚠️ Vui lòng đăng nhập để sử dụng chức năng này!")
    st.stop()

# --- 2. PHẦN THIẾT LẬP NGÂN SÁCH (FORM NHẬP) ---
st.markdown("### ⚙️ Thiết lập ngân sách mới")
with st.expander("➕ Bấm vào đây để Thêm hoặc Cập nhật hạn mức chi tiêu", expanded=False):
    with st.form("budget_form"):
        col1, col2 = st.columns(2)

        with col1:
            # Mapping tên hiển thị và ID (Khớp với Database của Ánh)
            cat_options = {"Ăn uống": 1, "Di chuyển": 2, "Mua sắm": 3, "Giải trí": 4, "Hóa đơn": 5}
            selected_cat = st.selectbox("Chọn danh mục chi tiêu", list(cat_options.keys()))
            limit_amount = st.number_input("Hạn mức tối đa (VND)", min_value=0, value=3000000, step=100000)

        with col2:
            now = datetime.datetime.now()
            month = st.number_input("Tháng", min_value=1, max_value=12, value=now.month)
            year = st.number_input("Năm", min_value=2000, max_value=2100, value=now.year)

        submit_btn = st.form_submit_button("💾 Lưu Ngân Sách", type="primary", use_container_width=True)

        if submit_btn:
            payload = {
                "category_id": cat_options[selected_cat],
                "limit": limit_amount,
                "month": month,
                "year": year
            }
            try:
                # Gọi API
                post_res = requests.post(f"{BASE_URL}/budgets/", json=payload)
                if post_res.status_code == 200:
                    st.success(f"🎉 Đã thiết lập {limit_amount:,} VND cho mục {selected_cat} thành công!")
                    st.rerun()
                else:
                    st.error(f"Lỗi: {post_res.text}")
            except Exception as e:
                st.error(f"Không thể kết nối đến máy chủ: {e}")

st.divider()

# --- 3. PHẦN HIỂN THỊ TRẠNG THÁI NGÂN SÁCH ---
try:
    # Gọi API lấy tiến độ ngân sách tháng hiện tại
    response = requests.get(f"{BASE_URL}/budgets/progress")

    if response.status_code == 200:
        budgets = response.json()

        if budgets and len(budgets) > 0:
            # Tính toán tổng quan
            total_limit = sum(b.get('limit', 0) for b in budgets)
            total_spent = sum(b.get('spent', 0) for b in budgets)
            remaining_total = total_limit - total_spent

            # --- Layout 3 thẻ Metric ---
            m1, m2, m3 = st.columns(3)


            def draw_metric_card(label, value, color_bg, text_color):
                st.markdown(f"""
                    <div style="background-color: {color_bg}; padding: 20px; border-radius: 15px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                        <p style="margin:0; font-size: 14px; color: #666; font-weight: 500;">{label}</p>
                        <h2 style="margin:5px 0; color: {text_color};">{value:,} VND</h2>
                    </div>
                """, unsafe_allow_html=True)


            with m1:
                draw_metric_card("Tổng hạn mức", total_limit, "#E3F2FD", "#1976D2")
            with m2:
                draw_metric_card("Tổng đã tiêu", total_spent, "#FCE4EC", "#C2185B")
            with m3:
                # Màu xanh nếu còn tiền, màu cam nếu tiêu quá
                rem_color = "#388E3C" if remaining_total >= 0 else "#D32F2F"
                draw_metric_card("Còn lại", remaining_total, "#E8F5E9", rem_color)

            # --- Danh sách tiến độ từng mục ---
            st.write("")
            st.markdown("### 📊 Tiến độ chi tiêu theo danh mục")

            # Chia grid 3 cột cho các thẻ danh mục
            cat_cols = st.columns(3)
            cat_names = {1: "Food", 2: "Transport", 3: "Shopping", 4: "Entertainment", 5: "Bills"}
            cat_icons = {"Food": "🍕", "Transport": "🚗", "Shopping": "🛍️", "Entertainment": "🎬", "Bills": "💵"}

            for idx, b in enumerate(budgets):
                col_idx = idx % 3
                c_id = b.get('category_id')
                c_name = cat_names.get(c_id, "Khác")
                limit = b.get('limit', 1)
                spent = b.get('spent', 0)
                rem = b.get('remaining', 0)
                # Tính % tiến độ
                progress_pct = min((spent / limit) * 100, 100)
                bar_color = "#A093F2" if spent <= limit else "#FF5252"

                with cat_cols[col_idx]:
                    st.markdown(f"""
                        <div style="background: white; padding: 15px; border-radius: 15px; border: 1px solid #eee; margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-weight: bold; color: #333;">{cat_icons.get(c_name, '💰')} {c_name}</span>
                                <span style="font-size: 12px; color: {'#388E3C' if rem >= 0 else '#D32F2F'}; font-weight: bold;">
                                    {rem:,} VND left
                                </span>
                            </div>
                            <div style="background-color: #f0f0f0; border-radius: 10px; height: 10px; width: 100%; margin: 10px 0;">
                                <div style="background-color: {bar_color}; width: {progress_pct}%; height: 100%; border-radius: 10px;"></div>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 11px; color: #888;">
                                <span>Tiêu: {spent:,}</span>
                                <span>Hạn mức: {limit:,}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("💡 Bạn chưa thiết lập ngân sách cho tháng này. Hãy sử dụng form phía trên để bắt đầu nhé!")
    else:
        st.error(f"❌ Không thể tải dữ liệu từ máy chủ (Mã lỗi: {response.status_code})")

except Exception as e:
    st.error(f"🚑 Lỗi kết nối hệ thống: {e}")