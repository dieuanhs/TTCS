import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from styles import apply_common_styles, render_header

# 1. Cấu hình trang và Styles
st.set_page_config(layout="wide")
apply_common_styles()
user_name = st.session_state.get("user_name", "User")
render_header("Dashboard Overview", user_name=user_name)

BASE_URL = "http://127.0.0.1:8000"

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vui lòng đăng nhập trước!")
    st.stop()

try:
    # 2. Lấy dữ liệu từ Backend
    response = requests.get(f"{BASE_URL}/dashboard/")
    data = response.json() if response.status_code == 200 else {}

    # --- PHẦN 1: 3 THẺ METRIC MÀU SẮC (Top Row) ---
    col1, col2, col3 = st.columns(3)

    def styled_metric(label, value, bg_color):
        st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid rgba(0,0,0,0.05);">
                <p style="color: #555; margin-bottom: 5px; font-size: 14px;">{label}</p>
                <h3 style="margin: 0; color: #000; font-size: 22px;">{value:,} VND</h3>
            </div>
        """, unsafe_allow_html=True)

    with col1:
        styled_metric("Balance", data.get('total_balance', 0), "#D6EAF8") # Xanh dương nhạt
    with col2:
        styled_metric("Income this month", data.get('total_income', 0), "#D5F5E3") # Xanh lá nhạt
    with col3:
        styled_metric("Expense this month", data.get('total_expense', 0), "#FADBD8") # Đỏ nhạt

    st.write("") # Tạo khoảng cách

    # --- PHẦN 2: BIỂU ĐỒ (Middle Row) ---
    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown("<h4 style='text-align: center;'>Expense by Category</h4>", unsafe_allow_html=True)
        # Giả sử Backend trả về data['expense_by_category'] = {"Food": 40, "Transport": 20, ...}
        cat_data = data.get('expense_by_category', {"Food": 30, "Shopping": 25, "Transport": 15, "Entertainment": 10, "Accommodation": 20})
        fig_pie = px.pie(
            names=list(cat_data.keys()),
            values=list(cat_data.values()),
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig_pie, use_container_width=True)

    with c_right:
        st.markdown("<h4 style='text-align: center;'>Emotion vs Spending</h4>", unsafe_allow_html=True)
        # Biểu đồ cột màu tím giống hình mẫu
        emo_data = data.get('emotion_spending', {"Vui": 10, "Buồn": 30, "Stress": 25, "Tiếc": 12, "Bình thường": 8})
        df_emo = pd.DataFrame(list(emo_data.items()), columns=['Emotion', 'Count'])
        fig_bar = px.bar(df_emo, x='Emotion', y='Count', color_discrete_sequence=['#A093F2'])
        fig_bar.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300, xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- PHẦN 3: AI ALERT (Bottom Row) ---
    st.markdown(f"""
        <div style="background-color: #FFF9C4; padding: 25px; border-radius: 15px; margin-top: 20px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="margin: 0; color: #333; font-size: 20px;">AI Alert</h3>
                <p style="margin: 10px 0 0 0; color: #555; font-size: 16px; font-weight: 500;">
                    {data.get('ai_insight', "You tend to spend more money when you're feeling bad, stress.")}
                </p>
            </div>
            <button style="background-color: #FFB74D; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer;">
                View insight
            </button>
        </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Lỗi kết nối Backend: {e}")
    st.info("Hãy đảm bảo Uvicorn đang chạy và trả về đúng định dạng JSON!")