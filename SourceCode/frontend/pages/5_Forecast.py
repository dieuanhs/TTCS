import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import sys
import os
CURRENT_DIR= os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from frontend.styles import apply_common_styles, render_header

st.set_page_config(layout="wide")
apply_common_styles()
user_name = st.session_state.get("user_name", "User")
render_header("Forecast", user_name=user_name)

BASE_URL = "http://127.0.0.1:8000"

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vui lòng đăng nhập trước!")
    st.stop()

try:
    # 2. Lấy dữ liệu từ Backend

    response = requests.get(f"{BASE_URL}/forecast/")
    data = response.json() if response.status_code == 200 else {}

    # --- PHẦN 1: 3 THẺ DỰ BÁO TỔNG QUAN ---
    m1, m2, m3 = st.columns(3)


    def forecast_card(label, value, change, color_bg, text_color, sub_text=""):
        st.markdown(f"""
            <div style="background-color: {color_bg}; padding: 20px; border-radius: 15px; border: 1px solid rgba(0,0,0,0.05);">
                <p style="margin:0; font-size: 14px; color: #666;">{label}</p>
                <h3 style="margin:5px 0; color: #2E3A59; font-size: 24px;">{value:,} VND</h3>
                <p style="margin:0; font-size: 13px; color: {text_color}; font-weight: bold;">
                    {"+" if change > 0 else ""}{change}% {sub_text}
                </p>
            </div>
        """, unsafe_allow_html=True)


    with m1:
        forecast_card("Predicted Income", data.get('predicted_income', 8500000), 12.5, "#E8EAF6", "#5C6BC0", "↑")
    with m2:
        forecast_card("Predicted Expense", data.get('predicted_expense', 27800000), 8.3, "#FCE4EC", "#EC407A", "↑")
    with m3:
        forecast_card("Projected Balance", data.get('projected_balance', 11200000), 0, "#E8F5E9", "#43A047", "Safe ✅")

    st.write("")

    # --- PHẦN 2: BIỂU ĐỒ XU HƯỚNG & DANH MỤC ---
    c_left, c_right = st.columns([2, 1])

    with c_left:
        st.subheader("Spending Forecast (Next 6 Months)")
        # Dữ liệu mẫu mô phỏng biểu đồ Area trong hình
        months = ["May", "Jun", "Jul", "Aug", "Sep", "Oct"]
        values = [2.5, 4.0, 5.8, 7.2, 9.5, 11.2]  # Đơn vị M (triệu)
        df_trend = pd.DataFrame({"Month": months, "Balance (M)": values})

        fig_trend = px.area(df_trend, x="Month", y="Balance (M)", markers=True)
        fig_trend.update_traces(line_color='#A093F2', fillcolor='rgba(160, 147, 242, 0.2)')
        fig_trend.update_layout(height=350, margin=dict(t=10, b=10, l=10, r=10), yaxis_title="Millions (VND)")
        st.plotly_chart(fig_trend, use_container_width=True)

    with c_right:
        st.subheader("Predicted Expenses")
        # Biểu đồ cột ngang/đứng theo danh mục
        cat_preds = data.get('category_forecast',
                             {"Food": 9700, "Transport": 5600, "Shopping": 6500, "Entertainment": 3200})
        df_cat = pd.DataFrame(list(cat_preds.items()), columns=['Category', 'Value'])
        fig_cat = px.bar(df_cat, x='Category', y='Value', color='Category',
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_cat.update_layout(height=350, showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_cat, use_container_width=True)

    # --- PHẦN 3: BẢNG DỰ BÁO & AI PREDICTION ---
    st.write("")
    b_left, b_right = st.columns([2, 1])

    with b_left:
        st.subheader("Monthly Forecast Table")
        # Tạo bảng thủ công để có màu sắc chữ xanh/đỏ giống mẫu
        t_col = st.columns([1, 1.5, 1.5, 1.5])
        headers = ["Month", "Income", "Expense", "Balance"]
        for col, h in zip(t_col, headers): col.write(f"**{h}**")

        forecast_list = [
            {"m": "May", "i": 1400000, "e": -4300000, "b": 9700000},
            {"m": "Jun", "i": 1400000, "e": -4600000, "b": 8550000},
            {"m": "Jul", "i": 1550000, "e": -4500000, "b": 4250000}
        ]
        for row in forecast_list:
            r = st.columns([1, 1.5, 1.5, 1.5])
            r[0].write(row['m'])
            r[1].write(f"<span style='color:green;'>{row['i']:,}</span>", unsafe_allow_html=True)
            r[2].write(f"<span style='color:red;'>{row['e']:,}</span>", unsafe_allow_html=True)
            r[3].write(f"<span style='color:blue;'>{row['b']:,}</span>", unsafe_allow_html=True)

    with b_right:
        st.subheader("AI Prediction")
        st.markdown(f"""
            <div style="background-color: #FFF9C4; padding: 20px; border-radius: 15px; border-left: 5px solid #FBC02D;">
                <p style="font-size: 24px; margin: 0;">💡</p>
                <p style="color: #444; font-size: 15px; line-height: 1.6;">
                    {data.get('ai_prediction_text', "Your balance is expected to grow steadily if expenses remain under control. Consider saving 10% more in Shopping.")}
                </p>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Lỗi: {e}")