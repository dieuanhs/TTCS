import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from frontend.styles import apply_common_styles, render_header
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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

    # --- PHẦN 1: 3 THẺ METRIC MÀU SẮC ---
    col1, col2, col3 = st.columns(3)


    def styled_metric(label, value, bg_color):
        st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <p style="color: #555; margin-bottom: 5px; font-size: 14px; font-weight: 500;">{label}</p>
                <h3 style="margin: 0; color: #000; font-size: 24px;">{value:,.0f} VND</h3>
            </div>
        """, unsafe_allow_html=True)


    with col1:
        styled_metric("Net Balance", data.get('net_balance', 0), "#D6EAF8")  # Đã fix key net_balance
    with col2:
        styled_metric("Income this month", data.get('total_income', 0), "#D5F5E3")
    with col3:
        styled_metric("Expense this month", data.get('total_expense', 0), "#FADBD8")

    st.write("")

    # --- PHẦN 2: BIỂU ĐỒ (Middle Row) ---
    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown("<h4 style='text-align: center; color: #333;'>Expense by Category</h4>", unsafe_allow_html=True)
        # Lấy dữ liệu thật từ DB
        cat_data = data.get('expense_by_category', {"Chưa có dữ liệu": 1})

        fig_pie = px.pie(
            names=list(cat_data.keys()),
            values=list(cat_data.values()),
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        # Ẩn chú thích nếu là mảng rỗng để giao diện sạch sẽ
        if "Chưa có dữ liệu" in cat_data:
            fig_pie.update_traces(textinfo='none')

        fig_pie.update_layout(margin=dict(t=20, b=20, l=0, r=0), height=320)
        st.plotly_chart(fig_pie, use_container_width=True)

    with c_right:
        st.markdown("<h4 style='text-align: center; color: #333;'>Emotion vs Spending (VND)</h4>",
                    unsafe_allow_html=True)
        # Lấy dữ liệu thật từ DB
        emo_data = data.get('emotion_spending', {"Chưa có": 0})
        df_emo = pd.DataFrame(list(emo_data.items()), columns=['Cảm xúc', 'Tổng tiền (VND)'])

        fig_bar = px.bar(
            df_emo,
            x='Cảm xúc',
            y='Tổng tiền (VND)',
            color_discrete_sequence=['#A093F2'],
            text_auto='.2s'
        )
        fig_bar.update_layout(margin=dict(t=20, b=20, l=0, r=0), height=320, xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- PHẦN 3: AI ALERT ---
    st.markdown(f"""
        <div style="background-color: #FFF9C4; padding: 25px; border-radius: 15px; margin-top: 10px; display: flex; justify-content: space-between; align-items: center; border-left: 6px solid #FBC02D; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <div>
                <h3 style="margin: 0; color: #333; font-size: 20px;">🤖 AI Insight</h3>
                <p style="margin: 10px 0 0 0; color: #444; font-size: 16px; font-weight: 500; line-height: 1.5;">
                    {data.get('ai_insight', "Đang tải dữ liệu phân tích...")}
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Lỗi kết nối Backend: {e}")
    st.info("Hãy đảm bảo Uvicorn đang chạy và không bị lỗi!")