import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from frontend.styles import apply_common_styles, render_header
import os
import sys
from datetime import datetime

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
    user_id = st.session_state.get("user_id")

    # 2. Lấy dữ liệu Tổng quan (Dashboard)
    response = requests.get(f"{BASE_URL}/dashboard/?user_id={user_id}")
    data = response.json() if response.status_code == 200 else {}

    # Lấy dữ liệu Giao dịch để lấy 5 giao dịch gần nhất
    tx_response = requests.get(f"{BASE_URL}/transactions/?user_id={user_id}&time_range=all")
    all_transactions = tx_response.json() if tx_response.status_code == 200 else []
    recent_transactions = all_transactions[:5]

    # --- PHẦN 1: 3 THẺ METRIC MÀU SẮC ---
    col1, col2, col3 = st.columns(3)


    def styled_metric(label, value, bg_color):
        st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <p style="color: #555; margin-bottom: 5px; font-size: 14px; font-weight: 500; font-family: 'DM Sans', sans-serif;">{label}</p>
                <h3 style="margin: 0; color: #000; font-size: 24px; font-family: 'Syne', sans-serif;">{value:,.0f} VND</h3>
            </div>
        """, unsafe_allow_html=True)


    with col1:
        styled_metric("Net Balance", data.get('net_balance', 0), "#D6EAF8")
    with col2:
        styled_metric("Income this month", data.get('total_income', 0), "#D5F5E3")
    with col3:
        styled_metric("Expense this month", data.get('total_expense', 0), "#FADBD8")

    st.write("")

    # --- PHẦN 2: BIỂU ĐỒ (Middle Row) ---
    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown(
            "<h4 style='text-align: center; color: #333; font-family: \"Syne\", sans-serif;'>Expense by Category</h4>",
            unsafe_allow_html=True)
        cat_data = data.get('expense_by_category', {"Chưa có dữ liệu": 1})

        fig_pie = px.pie(
            names=list(cat_data.keys()),
            values=list(cat_data.values()),
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        if "Chưa có dữ liệu" in cat_data:
            fig_pie.update_traces(textinfo='none')

        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=20, l=0, r=0),
            height=320
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with c_right:
        st.markdown(
            "<h4 style='text-align: center; color: #333; font-family: \"Syne\", sans-serif;'>Emotion vs Spending (VND)</h4>",
            unsafe_allow_html=True)
        emo_data = data.get('emotion_spending', {"Chưa có": 0})
        df_emo = pd.DataFrame(list(emo_data.items()), columns=['Cảm xúc', 'Tổng tiền (VND)'])

        fig_bar = px.bar(
            df_emo,
            x='Cảm xúc',
            y='Tổng tiền (VND)',
            color='Cảm xúc',
            color_discrete_map={
                "Tích cực": "#2ECC71",
                "Bình thường": "#95A5A6",
                "Tiêu cực": "#E74C3C"
            },
            text_auto='.2s'
        )
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=20, l=0, r=0),
            height=320,
            xaxis_title=None,
            yaxis_title=None,
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- PHẦN 3: AI INSIGHT & GIAO DỊCH GẦN ĐÂY ---
    st.write("---")
    bot_left, bot_right = st.columns([6, 4])  # Chia tỷ lệ 6:4

    # 1. AI Insight (Bên trái)
    with bot_left:
        st.markdown(f"""
            <div style="background-color: #FFF9C4; padding: 25px; border-radius: 15px; border-left: 6px solid #FBC02D; box-shadow: 0 4px 6px rgba(0,0,0,0.05); height: 100%;">
                <h3 style="margin: 0 0 15px 0; color: #333; font-size: 20px; font-family: 'Syne', sans-serif;">🤖 AI Insight</h3>
                <p style="margin: 0; color: #444; font-size: 16px; font-family: 'DM Sans', sans-serif; line-height: 1.6;">
                    {data.get('ai_insight', "Đang tải dữ liệu phân tích hành vi...")}
                </p>
            </div>
        """, unsafe_allow_html=True)

    # 2. Giao dịch gần đây (Bên phải)
    with bot_right:
        st.markdown(
            "<h3 style='margin: 0 0 10px 0; color: #333; font-size: 20px; font-family: \"Syne\", sans-serif;'>📋 Giao dịch gần đây</h3>",
            unsafe_allow_html=True)

        if not recent_transactions:
            st.info("Chưa có giao dịch nào.")
        else:
            # Tạo HTML List cho danh sách giao dịch
            tx_html = "<div style='background-color: white; border-radius: 10px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 15px;'>"
            for tx in recent_transactions:
                # Xử lý ngày tháng an toàn
                try:
                    dt_obj = datetime.fromisoformat(tx['transaction_time'])
                    date_str = dt_obj.strftime("%d/%m")
                except:
                    date_str = "N/A"

                is_income = (tx['type'] == 'Thu nhập')
                color = "#2ECC71" if is_income else "#E74C3C"
                sign = "+" if is_income else "-"

                desc = tx['description']
                if len(desc) > 20:
                    desc = desc[:17] + "..."

                # hiển thị
                tx_html += f"<div style='display: flex; justify-content: space-between; padding: 10px 5px; border-bottom: 1px solid #eee; font-family: \"DM Sans\", sans-serif;'>"
                tx_html += f"<div style='color: #888; font-size: 14px; width: 50px;'>{date_str}</div>"
                tx_html += f"<div style='flex-grow: 1; color: #333; font-weight: 500; font-size: 15px;'>{desc}</div>"
                tx_html += f"<div style='color: {color}; font-weight: bold; font-size: 15px;'>{sign}{tx['amount']:,.0f} đ</div>"
                tx_html += "</div>"

            tx_html += "</div>"
            st.markdown(tx_html, unsafe_allow_html=True)
            # Nút Xem tất cả (Điều hướng sang file transactions.py)
            if st.button("Xem tất cả giao dịch ➔", use_container_width=True):
                st.switch_page("pages/2_Transactions.py")

except Exception as e:
    st.error(f"Lỗi kết nối Backend: {e}")
    st.info("Hãy đảm bảo Uvicorn đang chạy và không bị lỗi!")