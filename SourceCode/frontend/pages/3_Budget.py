import streamlit as st
import requests
import sys
import os
CURRENT_DIR= os.path.dirname(os.path.abspath(__file__)) # Đang ở frontend/pages
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)



from frontend.styles import apply_common_styles, render_header

# 1. Cấu hình trang và Styles
st.set_page_config(layout="wide") # Nên thêm dòng này để giao diện rộng đẹp như hình mẫu
apply_common_styles()
user_name = st.session_state.get("user_name", "User")
render_header("Budget", user_name=user_name)
BASE_URL = "http://127.0.0.1:8000"

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vui lòng đăng nhập trước!")
    st.stop()

try:
    response = requests.get(f"{BASE_URL}/budgets/progress")
    data_json = response.json()

    # 1. XỬ LÝ AN TOÀN: Kiểm tra data_json là List hay Dict
    if isinstance(data_json, list):
        budgets = data_json
        total_limit = sum(b.get('limit', b.get('limit_amount', 0)) for b in budgets)
    else:
        # Nếu là Dict thì lấy trong key 'categories'
        budgets = data_json.get('categories', [])
        total_limit = data_json.get('total_budget', sum(b.get('limit', 0) for b in budgets))

    # Mapping dữ liệu để hiển thị
    cat_map = {1: "Food", 2: "Transport", 3: "Shopping", 4: "Entertainment"}
    icons = {"Food": "🍕", "Transport": "🚗", "Shopping": "🛍️", "Entertainment": "🎬"}
    colors = {"Food": "#E8F5E9", "Transport": "#E3F2FD", "Shopping": "#FCE4EC", "Entertainment": "#F3E5F5"}

    if budgets:
        total_spent = sum(b.get('spent', 0) for b in budgets)
        remaining_all = total_limit - total_spent
        total_progress = min(total_spent / total_limit, 1.0) if total_limit > 0 else 0

        # --- PHẦN 1: 3 THẺ TỔNG QUAN ---
        st.subheader("Monthly Budget Overview")
        m1, m2, m3 = st.columns(3)


        def card(label, value, color_bg, text_color):
            st.markdown(f"""
                <div style="background-color: {color_bg}; padding: 15px; border-radius: 12px; text-align: center;">
                    <p style="margin:0; font-size: 14px; color: #666;">{label}</p>
                    <h3 style="margin:0; color: {text_color}; font-size: 20px;">{value:,} VND</h3>
                </div>
            """, unsafe_allow_html=True)


        with m1:
            card("Total Budget", total_limit, "#E3F2FD", "#1976D2")
        with m2:
            card("Total Spent", -total_spent, "#FCE4EC", "#C2185B")
        with m3:
            card("Remaining", remaining_all, "#E8F5E9", "#388E3C")

        # --- PHẦN 2: THANH TIẾN ĐỘ TỔNG ---
        st.write("")
        st.markdown(f"""
            <div style="margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: bold; color: #C2185B; margin-bottom: 5px;">
                    <span>📍 {total_spent:,} VND</span>
                    <span style="color: #999;">{total_limit:,} VND</span>
                </div>
                <div style="background-color: #eee; border-radius: 10px; height: 12px; width: 100%;">
                    <div style="background: linear-gradient(90deg, #F06292 {total_progress * 100}%, #64B5F6 {total_progress * 100}%); 
                                width: 100%; height: 100%; border-radius: 10px;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # --- PHẦN 3: CÁC THẺ DANH MỤC (Grid 4 cột) ---
        st.write("")
        cols = st.columns(4)
        for i, b in enumerate(budgets[:4]):
            # Lấy tên Category (Ưu tiên tên từ Backend, không có thì dùng map)
            c_name = b.get('category') or cat_map.get(b.get('category_id'), "Other")

            spent = b.get('spent', 0)
            limit = b.get('limit') or b.get('limit_amount', 0)
            rem = limit - spent
            prog = min(spent / limit, 1.0) if limit > 0 else 0

            with cols[i]:
                st.markdown(f"""
                    <div style="background-color: {colors.get(c_name, '#f9f9f9')}; padding: 15px; border-radius: 15px; border: 1px solid rgba(0,0,0,0.05); min-height: 150px;">
                        <p style="margin:0; font-size: 14px; font-weight: bold;">{icons.get(c_name, '💰')} {c_name}</p>
                        <h4 style="margin: 5px 0; color: #2E7D32;">{rem:,} <small style="font-size:10px; color:#999;">left</small></h4>
                        <div style="background-color: rgba(0,0,0,0.05); border-radius: 5px; height: 6px; width: 100%; margin-top: 10px;">
                            <div style="background-color: #A093F2; width: {prog * 100}%; height: 100%; border-radius: 5px;"></div>
                        </div>
                        <p style="margin: 5px 0 0 0; font-size: 10px; color: #888; text-align: center;">{spent:,} / {limit:,}</p>
                    </div>
                """, unsafe_allow_html=True)

        # --- PHẦN 4: BẢNG CHI TIẾT ---
        st.write("")
        st.markdown("### Detailed Budget Status")
        t_col = st.columns([2, 2, 2, 2, 1.5])
        headers = ["Category", "Limit", "Spent", "Remaining", "Status"]
        for col, h in zip(t_col, headers):
            col.write(f"**{h}**")

        for b in budgets:
            c_name = b.get('category') or cat_map.get(b.get('category_id'), "Other")
            limit = b.get('limit') or b.get('limit_amount', 1)  # Tránh chia cho 0
            spent = b.get('spent', 0)
            rem = limit - spent

            status_val = int(abs(rem / limit * 100))
            status = "On Track" if rem >= 0 else f"{status_val}% Over"
            status_color = "#4CAF50" if rem >= 0 else "#FF9800"

            row = st.columns([2, 2, 2, 2, 1.5])
            row[0].write(f"{icons.get(c_name, '🔹')} {c_name}")
            row[1].write(f"{limit:,} VND")
            row[2].write(f"{spent:,}")
            row[3].write(f"<span style='color: {status_color}; font-weight:bold;'>{rem:,} VND</span>",
                         unsafe_allow_html=True)
            row[4].markdown(
                f"<span style='background-color: {status_color}22; color: {status_color}; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: bold;'>{status}</span>",
                unsafe_allow_html=True)

    else:
        st.info("Chưa có dữ liệu ngân sách.")

except Exception as e:
    st.error(f"Lỗi: {e}")