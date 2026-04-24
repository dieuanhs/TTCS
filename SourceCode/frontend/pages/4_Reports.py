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
render_header("Reports", user_name=user_name)

BASE_URL = "http://127.0.0.1:8000"

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vui lòng đăng nhập trước!")
    st.stop()

try:
    # 2. Lấy dữ liệu từ Backend
    response = requests.get(f"{BASE_URL}/reports/")
    data = response.json() if response.status_code == 200 else {}

    # --- PHẦN 1: REPORT OVERVIEW ---
    st.subheader("Report Overview")
    c1, c2, c3 = st.columns(3)


    def report_card(label, value, bg_color):
        st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 20px; border-radius: 15px; text-align: center; border: 1px solid rgba(0,0,0,0.05);">
                <p style="margin:0; font-size: 14px; color: #666;">{label}</p>
                <h3 style="margin:5px 0; color: #2E3A59; font-size: 22px;">{value:,} VND</h3>
            </div>
        """, unsafe_allow_html=True)


    with c1:
        report_card("Total Income", data.get('total_income', 8500000), "#E3F2FD")
    with c2:
        report_card("Total Expense", -data.get('total_expense', 4300000), "#FCE4EC")
    with c3:
        report_card("Net Balance", data.get('net_balance', 4200000), "#E8F5E9")

    st.write("")

    # --- PHẦN 2: XU HƯỚNG & HẠNG MỤC (Biểu đồ) ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Spending Trend")
        # Dữ liệu mẫu
        trend_data = data.get('monthly_trend', {
            "Jan": 2000000, "Feb": 3500000, "Mar": 4500000, "Apr": 7000000, "May": 8500000
        })
        df_trend = pd.DataFrame(list(trend_data.items()), columns=['Month', 'Income'])
        fig_trend = px.bar(df_trend, x='Month', y='Income', color_discrete_sequence=['#A093F2'])
        fig_trend.update_layout(height=300, margin=dict(t=10, b=10, l=0, r=0), xaxis_title=None)
        st.plotly_chart(fig_trend, width="stretch")

    with col_right:
        st.subheader("Expense by Category")
        cat_data = data.get('categories', {"Food": 45, "Shopping": 25, "Entertainment": 15, "Other": 15})
        fig_pie = px.pie(names=list(cat_data.keys()), values=list(cat_data.values()), hole=0.5,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_layout(height=300, margin=dict(t=10, b=10, l=0, r=0), showlegend=False)
        st.plotly_chart(fig_pie, width="stretch")

    # --- PHẦN 3: TOP SPENDING (Bảng chi tiết) ---
    st.subheader("Top Spending")

    # Header bảng
    t_col = st.columns([2, 2, 2, 2, 2, 2])
    headers = ["Category", "Transactions", "Amount", "Limit", "Status", "Diff"]
    for col, h in zip(t_col, headers): col.write(f"**{h}**")

    # Dữ liệu bảng
    spending_list = data.get('spending_details', [
        {"cat": "Food", "count": 12, "amt": 2300000, "lim": 2300000, "status": "Overspent", "diff": -4300000},
        {"cat": "Shopping", "count": 8, "amt": 1200000, "lim": 1000000, "status": "Lack of 250", "diff": -500000},
        {"cat": "Entertainment", "count": 4, "amt": 300000, "lim": 900000, "status": "On Track", "diff": -300000},
        {"cat": "Other", "count": 3, "amt": 300000, "lim": 300000, "status": "On Track", "diff": 700000}
    ])

    icons = {"Food": "🍕", "Shopping": "🛍️", "Entertainment": "🎬", "Other": "🔹"}

    for item in spending_list:
        row = st.columns([2, 2, 2, 2, 2, 2])
        row[0].write(f"{icons.get(item['cat'], '💰')} {item['cat']}")
        row[1].write(f"{item['count']}")
        row[2].write(f"{item['amt']:,}")
        row[3].write(f"{item['lim']:,}")

        # Định dạng màu cho Status
        s = item['status']
        s_color = "#FF9800" if "Over" in s or "Lack" in s else "#4CAF50"
        row[4].markdown(
            f"<span style='background-color:{s_color}22; color:{s_color}; padding:2px 8px; border-radius:10px; font-size:12px; font-weight:bold;'>{s}</span>",
            unsafe_allow_html=True)

        diff_color = "red" if item['diff'] < 0 else "green"
        row[5].markdown(f"<span style='color:{diff_color}; font-weight:bold;'>{item['diff']:,}</span>",
                        unsafe_allow_html=True)

    # --- PHẦN 4: AI INSIGHT  ---
    st.write("")
    st.markdown(f"""
        <div style="background-color: #FFF3E0; padding: 20px; border-radius: 15px; display: flex; justify-content: space-between; align-items: center; border-left: 5px solid #FFB74D;">
            <div>
                <p style="margin:0; font-weight: bold; color: #E65100;">💡 AI Insight</p>
                <p style="margin:5px 0 0 0; color: #5D4037;">{data.get('ai_insight', "You spend the most money on Food this month. Consider reducing dining-out expenses.")}</p>
            </div>
            <button style="background-color: #FFB74D; border: none; padding: 10px 20px; border-radius: 8px; color: white; font-weight: bold; cursor: pointer;">View suggestion</button>
        </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Lỗi kết nối Backend: {e}")