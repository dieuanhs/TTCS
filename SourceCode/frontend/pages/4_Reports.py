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
render_header("Reports", user_name=user_name)

BASE_URL = "http://127.0.0.1:8000"

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vui lòng đăng nhập trước!")
    st.stop()

try:
    # Lấy dữ liệu
    response = requests.get(f"{BASE_URL}/reports/")
    data = response.json() if response.status_code == 200 else {}

    # --- PHẦN 1: REPORT OVERVIEW ---
    st.subheader("Tổng quan báo cáo tháng này")
    c1, c2, c3 = st.columns(3)


    def report_card(label, value, bg_color):
        st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 20px; border-radius: 15px; text-align: center; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <p style="margin:0; font-size: 15px; color: #666; font-weight: 500;">{label}</p>
                <h3 style="margin:8px 0; color: #2E3A59; font-size: 24px;">{value:,.0f} VND</h3>
            </div>
        """, unsafe_allow_html=True)


    with c1:
        report_card("Tổng Thu Nhập", data.get('total_income', 0), "#E3F2FD")
    with c2:
        report_card("Tổng Chi Tiêu", data.get('total_expense', 0), "#FCE4EC")
    with c3:
        report_card("Số Dư (Net Balance)", data.get('net_balance', 0), "#E8F5E9")

    st.write("")

    # --- PHẦN 2: XU HƯỚNG & HẠNG MỤC ---
    col_left, col_right = st.columns([2, 1.5])

    with col_left:
        st.subheader("📈 Xu hướng chi tiêu (5 tháng gần nhất)")
        trend_data = data.get('monthly_trend', {"Tháng này": 0})
        df_trend = pd.DataFrame(list(trend_data.items()), columns=['Tháng', 'Tổng chi (VND)'])
        fig_trend = px.bar(df_trend, x='Tháng', y='Tổng chi (VND)', color_discrete_sequence=['#A093F2'],
                           text_auto='.2s')
        fig_trend.update_layout(height=350, margin=dict(t=10, b=10, l=0, r=0), xaxis_title=None)
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_right:
        st.subheader("🥧 Tỷ trọng Danh mục")
        cat_data = data.get('categories', {"Chưa có dữ liệu": 1})
        fig_pie = px.pie(names=list(cat_data.keys()), values=list(cat_data.values()), hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        if "Chưa có dữ liệu" in cat_data:
            fig_pie.update_traces(textinfo='none')
        fig_pie.update_layout(height=350, margin=dict(t=10, b=10, l=0, r=0), showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- PHẦN 3: TOP SPENDING (Bảng chi tiết) ---
    st.write("---")
    st.subheader("🏆 Phân tích chi tiết theo Ngân sách")

    # Header bảng
    t_col = st.columns([2, 1.5, 2, 2, 2, 2])
    headers = ["Danh mục", "Số giao dịch", "Đã tiêu", "Ngân sách (Limit)", "Trạng thái", "Chênh lệch"]
    for col, h in zip(t_col, headers): col.write(f"**{h}**")

    # Từ điển Icon
    icons = {
        "Ăn uống": "🍕", "Di chuyển": "🚗", "Giao lưu": "🍻",
        "Giải trí": "🎬", "Hóa đơn": "💵", "Học tập": "📚",
        "Mua sắm": "🛍️", "Phát sinh": "⚠️", "Sức khỏe": "💊", "Thu nhập": "💰"
    }

    spending_list = data.get('spending_details', [])

    if not spending_list:
        st.info("Chưa có giao dịch chi tiêu nào trong tháng này.")
    else:
        for item in spending_list:
            row = st.columns([2, 1.5, 2, 2, 2, 2])
            row[0].write(f"{icons.get(item['cat'], '🔹')} {item['cat']}")
            row[1].write(f"{item['count']} lần")
            row[2].write(f"{item['amt']:,.0f}")

            # Nếu limit = 0 thì in "--"
            lim_str = f"{item['lim']:,.0f}" if item['lim'] > 0 else "--"
            row[3].write(lim_str)

            # Định dạng màu cho Status
            s = item['status']
            if s == "Vượt hạn mức":
                s_color = "#F44336"  # Đỏ
            elif s == "An toàn":
                s_color = "#4CAF50"  # Xanh
            else:
                s_color = "#9E9E9E"  # Xám cho chưa đặt ngân sách

            row[4].markdown(
                f"<span style='background-color:{s_color}22; color:{s_color}; padding:4px 10px; border-radius:12px; font-size:13px; font-weight:bold;'>{s}</span>",
                unsafe_allow_html=True)

            # Định dạng cột chênh lệch
            diff_color = "red" if item['diff'] < 0 else "green"
            diff_str = f"{item['diff']:,.0f}" if item['lim'] > 0 else "--"
            row[5].markdown(f"<span style='color:{diff_color}; font-weight:bold;'>{diff_str}</span>",
                            unsafe_allow_html=True)
        # --- PHẦN 4: PHÂN TÍCH HÀNH VI TÂM LÝ (ANALYTICS) ---
        st.write("---")
        st.subheader("🧠 Phân tích Hành vi & Tâm lý (Behavioral Analytics)")

        try:
            res = requests.get(f"{BASE_URL}/analytics/emotion-spending")
            if res.status_code == 200:
                analytics_data = res.json()
                emo_list = analytics_data.get("emotion_data", [])

                if emo_list:
                    c1, c2 = st.columns([1.5, 1])

                    with c1:
                        # Biểu đồ Bar Chart
                        df_emo = pd.DataFrame(emo_list)
                        fig_emo = px.bar(
                            df_emo, x="emotion", y="amount",
                            color="emotion", text_auto=".2s",
                            title="Tổng chi tiêu theo từng Cảm xúc",
                            color_discrete_map={"Tích cực": "#4CAF50", "Bình thường": "#9E9E9E", "Tiêu cực": "#F44336"}
                        )
                        fig_emo.update_layout(xaxis_title=None, yaxis_title="VND", height=300)
                        st.plotly_chart(fig_emo, use_container_width=True)

                    with c2:
                        # Hiển thị chỉ số tương quan
                        corr_val = analytics_data.get('correlation', 0)
                        st.markdown(f"""
                            <div style="background-color: #F8F9FA; padding: 20px; border-radius: 10px; border-left: 5px solid #6C63FF;">
                                <h4 style="margin-top:0;">Hệ số Tương quan (Correlation)</h4>
                                <h2 style="color: #6C63FF; margin: 10px 0;">{corr_val}</h2>
                                <p style="font-size: 13px; color: #666;">(Gần -1 nghĩa là càng buồn càng tiêu nhiều)</p>
                            </div>
                        """, unsafe_allow_html=True)

                        st.info(analytics_data.get("insight", ""))
        except Exception as e:
            st.error("Đang cập nhật dữ liệu Analytics...")
    # --- PHẦN 5: AI INSIGHT ---
    st.write("")
    st.markdown(f"""
        <div style="background-color: #FFF3E0; padding: 25px; border-radius: 15px; display: flex; justify-content: space-between; align-items: center; border-left: 6px solid #FFB74D; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <div>
                <h3 style="margin:0 0 8px 0; color: #E65100; font-size: 20px;">🤖 AI Insight</h3>
                <p style="margin:0; color: #5D4037; font-size: 16px; font-weight: 500; line-height: 1.5;">
                    {data.get('ai_insight', 'Đang tải phân tích...')}
                </p>
            </div>
            <button style="background-color: #FFB74D; border: none; padding: 12px 24px; border-radius: 8px; color: white; font-weight: bold; cursor: pointer; transition: 0.3s;">
                Xem gợi ý tiết kiệm
            </button>
        </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Lỗi kết nối Backend: {e}")
