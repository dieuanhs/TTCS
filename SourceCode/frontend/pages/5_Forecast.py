import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.styles import apply_common_styles, render_header

st.set_page_config(layout="wide")
apply_common_styles()
user_name = st.session_state.get("user_name", "User")
render_header("AI Forecast", user_name=user_name)

BASE_URL = "http://127.0.0.1:8000"

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vui lòng đăng nhập trước!")
    st.stop()

try:
    # Lấy dữ liệu Dự báo từ Backend
    response = requests.get(f"{BASE_URL}/forecast/")
    if response.status_code == 200:
        data = response.json()
    else:
        data = {
            "predicted_income": 0, "predicted_expense": 0, "projected_balance": 0,
            "category_forecast": {"Không có dữ liệu": 0},
            "ai_prediction_text": "Không thể kết nối đến AI phân tích."
        }

    # --- PHẦN 1: 3 THẺ DỰ BÁO TỔNG QUAN ---
    m1, m2, m3 = st.columns(3)


    def forecast_card(label, value, color_bg, text_color, icon=""):
        st.markdown(f"""
            <div style="background-color: {color_bg}; padding: 20px; border-radius: 15px; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <p style="margin:0; font-size: 15px; color: #666; font-weight: 500;">{label}</p>
                <h3 style="margin:8px 0; color: {text_color}; font-size: 26px;">{value:,.0f} VND</h3>
                <p style="margin:0; font-size: 13px; color: #888;">{icon} Tính toán dựa trên tốc độ tiêu hiện tại</p>
            </div>
        """, unsafe_allow_html=True)


    with m1:
        forecast_card("Ngân sách / Thu nhập", data.get('predicted_income', 0), "#E8EAF6", "#3F51B5", "🎯")
    with m2:
        forecast_card("Dự báo Tổng Chi Tháng", data.get('predicted_expense', 0), "#FCE4EC", "#E91E63", "💸")
    with m3:
        bal = data.get('projected_balance', 0)
        bal_color = "#43A047" if bal >= 0 else "#D32F2F"
        bal_bg = "#E8F5E9" if bal >= 0 else "#FFEBEE"
        forecast_card("Dự báo Số Dư Cuối Tháng", bal, bal_bg, bal_color, "🏦")

    st.write("")

    # --- PHẦN 2: BIỂU ĐỒ & AI ALERT ---
    c_left, c_right = st.columns([2, 1.5])

    with c_left:
        st.subheader("📊 Dự báo chi tiêu theo Danh Mục")
        cat_preds = data.get('category_forecast', {})

        df_cat = pd.DataFrame(list(cat_preds.items()), columns=['Danh mục', 'Dự báo (VND)'])

        if df_cat['Dự báo (VND)'].sum() > 0:
            fig_cat = px.bar(df_cat, x='Danh mục', y='Dự báo (VND)', color='Danh mục',
                             color_discrete_sequence=px.colors.qualitative.Pastel,
                             text_auto='.2s')  # Hiển thị số rút gọn trên cột
            fig_cat.update_layout(height=400, showlegend=False, margin=dict(t=20, b=10, l=10, r=10))
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Chưa có đủ dữ liệu giao dịch trong tháng để vẽ biểu đồ dự báo.")

    with c_right:
        st.subheader("🤖 Trợ lý AI Phân Tích")

        # Đổi màu khung AI Alert tùy theo trạng thái
        bal = data.get('projected_balance', 0)
        ai_bg = "#FFF9C4" if bal >= 0 else "#FFEBEE"
        ai_border = "#FBC02D" if bal >= 0 else "#F44336"

        st.markdown(f"""
            <div style="background-color: {ai_bg}; padding: 25px; border-radius: 15px; border-left: 6px solid {ai_border}; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="font-size: 30px; margin-bottom: 10px;">{'💡' if bal >= 0 else '🚨'}</div>
                <p style="color: #333; font-size: 16px; line-height: 1.6; font-weight: 500;">
                    {data.get('ai_prediction_text', '')}
                </p>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Lỗi: {e}")