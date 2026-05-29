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
    user_id = st.session_state.get("user_id")
    response = requests.get(f"{BASE_URL}/reports/?user_id={user_id}")
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
        fig_trend.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=350,
            margin=dict(t=10, b=10, l=0, r=0),
            xaxis_title=None
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_right:
        st.subheader("🥧 Tỷ trọng Danh mục")
        cat_data = data.get('categories', {"Chưa có dữ liệu": 1})
        fig_pie = px.pie(names=list(cat_data.keys()), values=list(cat_data.values()), hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        if "Chưa có dữ liệu" in cat_data:
            fig_pie.update_traces(textinfo='none')
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=350,
            margin=dict(t=10, b=10, l=0, r=0),
            showlegend=True
        )
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

        # --- PHẦN 4: PHÂN TÍCH HÀNH VI TÂM LÝ ---
        st.write("---")
        st.subheader("🧠 Phân tích Hành vi & Tâm lý (Behavioral Analytics)")

        try:
            res = requests.get(f"{BASE_URL}/analytics/emotion-spending?user_id={user_id}")
            if res.status_code == 200:
                analytics_data = res.json()
                is_sufficient = analytics_data.get("is_sufficient", True)

                if not is_sufficient:
                    st.info(f"📊 **Phân tích Hành vi & Cảm xúc**: {analytics_data.get('insight')}")
                else:
                    # 1. Các chỉ số phân tích và Risk Meter
                    c1, c2 = st.columns([1, 1])

                    corr_val = analytics_data.get('correlation', 0.0)
                    if corr_val <= -0.4:
                        corr_class = "Trung bình - Cao"
                        corr_desc = "Khi tâm trạng tiêu cực, chi tiêu của bạn thường tăng."
                    elif corr_val <= -0.2:
                        corr_class = "Trung bình"
                        corr_desc = "Bạn có xu hướng chi tiêu nhẹ khi tâm trạng đi xuống."
                    elif corr_val >= 0.4:
                        corr_class = "Trung bình - Cao"
                        corr_desc = "Khi tâm trạng tích cực, chi tiêu của bạn thường tăng."
                    elif corr_val >= 0.2:
                        corr_class = "Trung bình"
                        corr_desc = "Bạn có xu hướng chi tiêu nhẹ khi tâm trạng đi lên."
                    else:
                        corr_class = "Thấp"
                        corr_desc = "Tâm trạng hầu như không ảnh hưởng đến số tiền chi tiêu của bạn."

                    risk_score = analytics_data.get('risk_score', 10)
                    if risk_score >= 70:
                        risk_status = "Emotional spending risk (Rủi ro chi tiêu theo cảm xúc)"
                        risk_color = "#F44336"  # Red
                        card_border = "#F44336"
                    elif risk_score >= 40:
                        risk_status = "Moderate (Trung bình)"
                        risk_color = "#FF9800"  # Orange
                        card_border = "#FF9800"
                    else:
                        risk_status = "Stable (Cân bằng)"
                        risk_color = "#4CAF50"  # Green
                        card_border = "#4CAF50"

                    with c1:
                        st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #f5f7fa 0%, #e4ecf7 100%); padding: 20px; border-radius: 15px; border-left: 5px solid #A093F2; box-shadow: 0 4px 6px rgba(0,0,0,0.05); height: 160px; display: flex; flex-direction: column; justify-content: space-between;">
                                <div>
                                    <span style="font-size: 12px; color: #555; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Mức ảnh hưởng cảm xúc</span>
                                    <h3 style="margin: 4px 0 0 0; color: #2E3A59; font-size: 20px;">{corr_class}</h3>
                                    <p style="margin: 2px 0 0 0; font-size: 13px; color: #666; line-height: 1.2;">{corr_desc}</p>
                                </div>
                                <p style="margin: 0; font-size: 11px; color: #888;">Hệ số tương quan: <b>r = {corr_val}</b></p>
                            </div>
                        """, unsafe_allow_html=True)

                    with c2:
                        st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #FFF8F0 0%, #FFEEDD 100%); padding: 20px; border-radius: 15px; border-left: 5px solid {card_border}; box-shadow: 0 4px 6px rgba(0,0,0,0.05); height: 160px; display: flex; flex-direction: column; justify-content: space-between;">
                                <div>
                                    <span style="font-size: 12px; color: #757575; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Chỉ số rủi ro cảm xúc</span>
                                    <h3 style="margin: 4px 0 0 0; color: {risk_color}; font-size: 20px;">{risk_score}/100</h3>
                                    <div style="background-color: #E0E0E0; border-radius: 10px; height: 8px; width: 100%; margin-top: 8px; overflow: hidden;">
                                        <div style="background-color: {risk_color}; width: {risk_score}%; height: 100%; border-radius: 10px;"></div>
                                    </div>
                                </div>
                                <p style="margin: 0; font-size: 13px; color: #555;">Đánh giá: <b>{risk_status}</b></p>
                            </div>
                        """, unsafe_allow_html=True)

                    st.write("")

                    # 2. AI Insight Alert
                    pattern = analytics_data.get('behavior_pattern', 'stable')
                    insight = analytics_data.get("insight", "")

                    if pattern == "stress":
                        st.error(insight)
                    elif pattern == "euphoric":
                        st.warning(insight)
                    else:
                        st.success(insight)

                    # 3. Anomaly Detection Alert (Phát hiện bất thường)
                    anomalies = analytics_data.get("anomalies", [])
                    if anomalies:
                        st.write("")

                        # Mapping tag -> (label, color)
                        tag_styles = {
                            "amount": ("💰 Số tiền", "#E65100", "#FFF3E0"),
                            "time": ("🕐 Giờ giấc", "#1565C0", "#E3F2FD"),
                            "category": ("📂 Danh mục", "#6A1B9A", "#F3E5F5"),
                            "combined": ("🔍 Tổng hợp", "#455A64", "#ECEFF1"),
                        }

                        # Build anomaly cards
                        cards_html = ""
                        for ano in anomalies:
                            # Render tag badges
                            tags_html = ""
                            for tag in ano.get("anomaly_tags", []):
                                label, color, bg = tag_styles.get(tag, ("🔍 Khác", "#757575", "#F5F5F5"))
                                tags_html += f"""<span style="display:inline-block; background:{bg}; color:{color}; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; margin-right:6px; border:1px solid {color}33;">{label}</span>"""

                            # Render detail reasons
                            reasons_html = ""
                            for reason in ano.get("reasons", []):
                                reasons_html += f"""<li style="margin-bottom:4px; color:#424242; font-size:13px; line-height:1.5;">{reason}</li>"""

                            hour_str = f"{ano.get('hour', 0):02d}:00" if 'hour' in ano else ""
                            cat_str = ano.get("category", "")
                            meta_parts = [f"{ano['date']}"]
                            if hour_str:
                                meta_parts.append(hour_str)
                            if cat_str:
                                meta_parts.append(cat_str)
                            meta_str = " · ".join(meta_parts)

                            cards_html += f"""
<div style="background:#FFFFFF; border:1px solid #FFCDD2; border-radius:10px; padding:14px 18px; margin-bottom:10px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <div>
            <span style="font-weight:700; color:#C62828; font-size:15px;">{ano['amount']:,.0f}đ</span>
            <span style="color:#888; font-size:13px; margin-left:8px;">— {ano['description']}</span>
        </div>
        <span style="color:#999; font-size:12px; white-space:nowrap;">{meta_str}</span>
    </div>
    <div style="margin-bottom:8px;">{tags_html}</div>
    <ul style="margin:0; padding-left:20px;">{reasons_html}</ul>
</div>
"""

                        html_content = f"""
<div style="background-color: #FFEBEE; padding: 20px; border-radius: 12px; border-left: 5px solid #F44336; margin-bottom: 15px;">
    <h4 style="margin-top: 0; color: #D32F2F; font-size:18px;">🚨 Cảnh báo Giao dịch Bất thường (Anomaly Detection)</h4>
    <p style="font-size: 14px; color: #333; margin-bottom: 12px;">AI Isolation Forest đã phát hiện <b>{len(anomalies)}</b> giao dịch lệch khỏi thói quen chi tiêu thường ngày:</p>
    {cards_html}
</div>
"""
                        st.markdown(html_content, unsafe_allow_html=True)

                    # 4. Biểu đồ chi tiết
                    st.write("")
                    c_chart1, c_chart2 = st.columns([1.2, 1])

                    trend_list = analytics_data.get("trend_data", [])
                    heatmap_list = analytics_data.get("heatmap_data", [])

                    with c_chart1:
                        if trend_list:
                            df_trend = pd.DataFrame(trend_list)
                            fig_trend = px.line(
                                df_trend, x="date", y="amount", color="emotion",
                                title="📈 Xu hướng Chi tiêu & Cảm xúc theo Ngày",
                                color_discrete_map={"Tích cực": "#4CAF50", "Bình thường": "#9E9E9E",
                                                    "Tiêu cực": "#F44336"},
                                markers=True
                            )
                            fig_trend.update_layout(
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)",
                                xaxis_title="Ngày",
                                yaxis_title="VND",
                                height=320,
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )
                            st.plotly_chart(fig_trend, use_container_width=True)
                        else:
                            st.info("Chưa có dữ liệu xu hướng theo ngày.")

                    with c_chart2:
                        if heatmap_list:
                            df_heat = pd.DataFrame(heatmap_list)
                            category_order = df_heat.groupby("category_name")["amount"].sum().sort_values(
                                ascending=False).index.tolist()
                            fig_heat = px.bar(
                                df_heat, x="category_name", y="amount", color="emotion",
                                barmode="group",
                                title="🛍️ Chi tiêu Danh mục phân bổ theo Cảm xúc",
                                color_discrete_map={"Tích cực": "#4CAF50", "Bình thường": "#9E9E9E",
                                                    "Tiêu cực": "#F44336"},
                                category_orders={"category_name": category_order}
                            )
                            fig_heat.update_layout(
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)",
                                xaxis_title=None,
                                yaxis_title="VND",
                                height=320,
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )
                            st.plotly_chart(fig_heat, use_container_width=True)
                        else:
                            st.info("Chưa có dữ liệu phân bổ danh mục.")
            else:
                st.warning("Không thể lấy dữ liệu phân tích cảm xúc từ máy chủ.")
        except Exception as e:
            st.error(f"Lỗi khi hiển thị phân tích cảm xúc: {e}")
    # --- PHẦN 5: AI INSIGHT ---
    st.write("")
    # Lấy danh mục chi tiêu nhiều nhất để đưa ra gợi ý phù hợp
    top_cat = "Khác"
    top_cat_desc = []
    if spending_list:
        top_cat = spending_list[0].get("cat", "Khác")
        top_cat_desc = spending_list[0].get("descriptions", [])

    SAVINGS_TIPS = {
        "Ăn uống": [
            "🍳 **Tự nấu ăn tại nhà**: Chuẩn bị bữa trưa mang đi làm có thể tiết kiệm tới 50% chi phí ăn uống.",
            "📱 **Sử dụng ứng dụng giảm giá**: Săn các voucher/deal ăn uống hoặc mua thực phẩm vào khung giờ vàng.",
            "☕ **Hạn chế cafe ngoài tiệm**: Tự pha cafe tại văn phòng hoặc nhà giúp tiết kiệm một khoản đáng kể hàng tháng."
        ],
        "Di chuyển": [
            "🛵 **Sử dụng phương tiện công cộng**: Hoặc đi chung xe (carpool) khi đi làm hàng ngày để giảm chi phí nhiên liệu.",
            "🚲 **Di chuyển xanh**: Đi xe đạp hoặc đi bộ đối với các quãng đường ngắn dưới 2km vừa tiết kiệm vừa nâng cao sức khỏe.",
            "🚗 **Bảo dưỡng xe định kỳ**: Giúp tối ưu hóa mức tiêu thụ nhiên liệu và tránh các khoản chi sửa chữa lớn đột xuất."
        ],
        "Giao lưu": [
            "🏡 **Tổ chức tụ tập tại nhà**: Thay vì ra nhà hàng đắt đỏ, hãy tự nấu hoặc yêu cầu mỗi người mang một món (potluck).",
            "🍺 **Đặt giới hạn chi tiêu**: Xác định trước số tiền tối đa sẽ chi trước khi ra ngoài và thanh toán bằng tiền mặt để tự kiểm soát.",
            "🎯 **Tìm hoạt động miễn phí**: Săn tìm các sự kiện, triển lãm hoặc hoạt động vui chơi miễn phí/giá rẻ trong thành phố."
        ],
        "Giải trí": [
            "📺 **Chia sẻ tài khoản Premium**: Đăng ký các gói gia đình cho Netflix, Spotify, Youtube Premium để chia sẻ chi phí.",
            "📚 **Sử dụng thư viện**: Đọc sách điện tử hoặc mượn sách từ thư viện thay vì mua sách mới liên tục.",
            "🎬 **Săn khuyến mãi**: Xem phim vào các ngày giảm giá trong tuần hoặc tận dụng ưu đãi thẻ ngân hàng tại rạp."
        ],
        "Hóa đơn": [
            "💡 **Tiết kiệm điện**: Tắt thiết bị khi không sử dụng, cài đặt hẹn giờ điều hòa và đổi sang dùng bóng đèn LED tiết kiệm điện.",
            "🚿 **Tiết kiệm nước**: Kiểm tra rò rỉ đường ống nước định kỳ và sử dụng vòi sen tăng áp giảm thất thoát nước.",
            "📶 **Tối ưu cước viễn thông**: Định kỳ xem lại và hạ gói cước Internet/4G nếu nhu cầu thực tế thấp hơn dung lượng gói."
        ],
        "Học tập": [
            "🌐 **Tận dụng khóa học miễn phí**: Tự học qua Coursera, edX, hoặc Youtube trước khi quyết định mua các khóa học đắt tiền.",
            "📖 **Mua sách giáo trình cũ**: Mua lại hoặc trao đổi tài liệu học tập với các sinh viên khóa trước.",
            "💻 **Ưu đãi sinh viên/học sinh**: Luôn đăng ký các phần mềm bản quyền bằng email giáo dục để hưởng ưu đãi từ 50-80%."
        ],
        "Mua sắm": [
            "⏳ **Quy tắc 72 giờ**: Trì hoãn việc mua sắm các món đồ không thiết yếu trong 3 ngày để kiểm tra xem bạn thực sự cần nó hay chỉ là cảm xúc nhất thời.",
            "📝 **Lên danh sách trước**: Cam kết chỉ mua đúng những thứ được ghi trong danh sách khi đi siêu thị/mua sắm.",
            "🏷️ **Săn sale thông minh**: Chỉ mua đồ giảm giá nếu đó là thứ bạn thực sự cần dùng và đã lên kế hoạch chi tiêu từ trước."
        ],
        "Sức khỏe": [
            "🏃‍♂️ **Tự tập thể dục**: Tận dụng công viên hoặc các bài tập tại nhà thay vì đăng ký gói gym đắt đỏ nhưng ít đi.",
            "🍎 **Ăn uống khoa học**: Phòng bệnh hơn chữa bệnh, duy trì lối sống lành mạnh giúp giảm chi phí thuốc men dài hạn.",
            "🏥 **Mua bảo hiểm y tế**: Chuẩn bị bảo hiểm y tế đầy đủ để tránh gánh nặng tài chính lớn khi có rủi ro sức khỏe."
        ],
        "Khác": [
            "💰 **Tự động tiết kiệm**: Trích lập tự động 10-20% thu nhập ngay khi nhận lương vào tài khoản tiết kiệm.",
            "📊 **Ghi chép chi tiêu**: Theo dõi chi tiêu mỗi ngày một cách nghiêm túc để kịp thời điều chỉnh dòng tiền.",
            "❌ **Hủy dịch vụ không dùng**: Rà soát và hủy toàn bộ các dịch vụ đăng ký hàng tháng (Netflix, Spotify...) nếu 2 tháng qua không dùng tới."
        ]
    }

    tips = SAVINGS_TIPS.get(top_cat, SAVINGS_TIPS["Khác"])
    if top_cat == "Hóa đơn":
        # phân biệt tiền trọ với các loại hóa đơn khác
        rent_keywords = ["trọ", "nhà", "phòng", "rent", "thuê", "chung cư", "apartment", "mặt bằng"]
        is_rent = any(any(k in desc.lower() for k in rent_keywords) for desc in top_cat_desc)
        if is_rent:
            tips = [
                "🏠 **Cân đối chi phí thuê**: Đảm bảo tiền thuê phòng/nhà không vượt quá 30% thu nhập. Cân nhắc tìm phòng trọ phù hợp hơn nếu vượt hạn mức.",
                "👥 **Tìm bạn ở ghép**: Tìm bạn ở ghép hoặc chia sẻ phòng trọ để giảm bớt gánh nặng tài chính (tiền phòng, điện, nước, mạng).",
                "⚡ **Kiểm tra đơn giá dịch vụ**: Thỏa thuận rõ với chủ nhà về giá điện, nước và dịch vụ đi kèm. Hãy tự theo dõi số điện nước để tránh bị tính sai."
            ]

    st.markdown(f"""
        <div style="background-color: #FFF3E0; padding: 25px; border-radius: 15px; border-left: 6px solid #FFB74D; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px;">
            <h3 style="margin:0 0 8px 0; color: #E65100; font-size: 20px;">🤖 AI Insight</h3>
            <p style="margin:0; color: #5D4037; font-size: 16px; font-weight: 500; line-height: 1.5;">
                {data.get('ai_insight', 'Đang tải phân tích...')}
            </p>
        </div>
    """, unsafe_allow_html=True)

    # GỢI Ý
    with st.popover(f"💡 Xem gợi ý tiết kiệm cho mục '{top_cat}'", use_container_width=True):
        st.markdown(f"#### 💡 Gợi ý tiết kiệm tốt nhất cho danh mục **{top_cat}**:")
        for tip in tips:
            st.markdown(f"- {tip}")


except Exception as e:
    st.error(f"Lỗi kết nối Backend: {e}")