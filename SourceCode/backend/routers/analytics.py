from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from sklearn.ensemble import IsolationForest
import pandas as pd
import math

from ..database import SessionLocal
from .. import models

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/emotion-spending")
def emotion_spending(user_id: int, db: Session = Depends(get_db)):
    now = datetime.now()
    current_ym = now.strftime("%Y-%m")

    # 1. LỌC DỮ LIỆU: Lấy thêm transaction_id và description để báo cáo Bất thường
    transactions = db.query(
        models.Transaction.transaction_id,
        models.Transaction.description,
        models.Transaction.emotion,
        models.Transaction.amount,
        models.Transaction.category_id,
        models.Transaction.transaction_time
    ).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
        models.Transaction.category_id != 5,  # Bỏ Hóa đơn cố định
        func.strftime("%Y-%m", models.Transaction.transaction_time) == current_ym
    ).all()

    # Trả về rỗng nếu không có dữ liệu
    if not transactions:
        return {
            "emotion_data": [],
            "correlation": 0.0,
            "behavior_pattern": "stable",
            "insight": "Chưa có đủ dữ liệu trong tháng này để phân tích.",
            "is_sufficient": False,
            "confidence_score": 0.0,
            "risk_score": 10,
            "trend_data": [],
            "heatmap_data": [],
            "anomalies": []
        }

    # 2. CHUYỂN ĐỔI PANDAS VÀ TẠO FEATURE THỜI GIAN
    df = pd.DataFrame(transactions,
                      columns=["transaction_id", "description", "emotion", "amount", "category_id", "transaction_time"])
    df["amount"] = df["amount"].abs()

    df_time = pd.to_datetime(df["transaction_time"])
    df["date"] = df_time.dt.strftime("%Y-%m-%d")
    df["hour"] = df_time.dt.hour
    df["day_of_week"] = df_time.dt.dayofweek  # 0: Thứ 2, 6: Chủ nhật

    # 3. CHUẨN HÓA DỮ LIỆU CẢM XÚC
    df["emotion"] = df["emotion"].apply(lambda x: str(x).strip().capitalize() if pd.notnull(x) else "Bình thường")
    score_map = {"Tích cực": 1, "Bình thường": 0.0, "Tiêu cực": -1}
    df["sentiment_score"] = df["emotion"].map(score_map).fillna(0.0)

    # 4. KIỂM TRA ĐIỀU KIỆN DỮ LIỆU (DATA SUFFICIENCY CHECK)
    total_txs = len(df)
    negative_txs = len(df[df["sentiment_score"] < 0])
    unique_days = df["date"].nunique()

    MIN_TRANSACTIONS = 10
    MIN_NEGATIVE_RECORDS = 3
    MIN_HISTORY_DAYS = 1

    is_sufficient = (total_txs >= MIN_TRANSACTIONS) and (negative_txs >= MIN_NEGATIVE_RECORDS) and (
                unique_days >= MIN_HISTORY_DAYS)

    # 5. TÍNH CORRELATION & MULTI-FEATURE RULE-BASED (ĐIỂM PHẠT THỜI GIAN)
    if df["sentiment_score"].nunique() <= 1 or df["amount"].nunique() <= 1:
        correlation = 0.0
    else:
        correlation = df["sentiment_score"].corr(df["amount"])
    if math.isnan(correlation): correlation = 0.0

    # Hàm đánh giá rủi ro thời gian và danh mục
    def calculate_time_risk(row):
        penalty = 0
        h = row["hour"]
        d = row["day_of_week"]
        c_id = row["category_id"]
        amt = row["amount"]

        # Rule 1: Săn sale đêm khuya (23:00 - 04:00) -> Cộng 15 điểm rủi ro
        if (h >= 23 or h <= 4) and c_id in [4, 7]:
            penalty += 15
        # Rule 2: Ăn uống xả stress muộn (22:00 - 02:00) -> Cộng 10 điểm
        if (h >= 22 or h <= 2) and c_id == 1:
            penalty += 10
        # Rule 3: Bốc đồng cuối tuần (T7, CN) với số tiền lớn -> Cộng 10 điểm
        if d in [5, 6] and amt > 500000 and c_id in [3, 7]:
            penalty += 10

        return penalty

    df["time_penalty"] = df.apply(calculate_time_risk, axis=1)
    avg_time_penalty = df["time_penalty"].mean() if not df.empty else 0

    # 6. PHÁT HIỆN BẤT THƯỜNG (ANOMALY DETECTION) — Chi tiết từng chiều
    anomalies_list = []
    if total_txs >= 10:  # Chỉ chạy AI khi có đủ 10 giao dịch
        features = df[["amount", "category_id", "hour", "day_of_week"]].fillna(0)
        # Isolation Forest tìm ra 5% giao dịch dị thường nhất
        clf = IsolationForest(contamination=0.05, random_state=42)
        df["is_anomaly"] = clf.fit_predict(features)

        # --- Tính baseline thống kê từ giao dịch BÌNH THƯỜNG ---
        normal_df = df[df["is_anomaly"] == 1]

        # Baseline số tiền
        amt_mean = normal_df["amount"].mean() if not normal_df.empty else df["amount"].mean()
        amt_std = normal_df["amount"].std() if not normal_df.empty else df["amount"].std()
        if pd.isna(amt_std) or amt_std == 0:
            amt_std = amt_mean * 0.5 if amt_mean > 0 else 1

        # Baseline giờ giao dịch
        hour_mean = normal_df["hour"].mean() if not normal_df.empty else df["hour"].mean()
        hour_std = normal_df["hour"].std() if not normal_df.empty else df["hour"].std()
        if pd.isna(hour_std) or hour_std == 0:
            hour_std = 3.0
        hour_q1 = int(normal_df["hour"].quantile(0.1)) if not normal_df.empty else 7
        hour_q3 = int(normal_df["hour"].quantile(0.9)) if not normal_df.empty else 22

        # Baseline tần suất danh mục
        cat_freq = (normal_df["category_id"].value_counts(normalize=True)
                    if not normal_df.empty
                    else df["category_id"].value_counts(normalize=True))

        cat_names = {
            1: "Ăn uống", 2: "Di chuyển", 3: "Giao lưu", 4: "Giải trí", 5: "Hóa đơn",
            6: "Học tập", 7: "Mua sắm", 8: "Phát sinh", 9: "Sức khỏe", 10: "Thu nhập"
        }

        # Baseline số tiền THEO TỪNG DANH MỤC
        cat_amt_stats = normal_df.groupby("category_id")["amount"].agg(["mean", "std"]) if not normal_df.empty \
            else df.groupby("category_id")["amount"].agg(["mean", "std"])

        # Baseline tần suất DANH MỤC theo KHUNG GIỜ (sáng/chiều/tối)
        def hour_slot(h):
            if h < 12:
                return "sáng"
            elif h < 18:
                return "chiều"
            else:
                return "tối"

        ref_df = normal_df if not normal_df.empty else df
        ref_df = ref_df.copy()
        ref_df["slot"] = ref_df["hour"].apply(hour_slot)
        cat_slot_counts = ref_df.groupby(["category_id", "slot"]).size()
        cat_total_counts = ref_df.groupby("category_id").size()

        anomaly_df = df[df["is_anomaly"] == -1]
        for _, row in anomaly_df.iterrows():
            reasons = []
            anomaly_tags = []

            cat_id = row["category_id"]
            c_name = cat_names.get(cat_id, "Khác")

            # === Kiểm tra SỐ TIỀN bất thường (toàn cục) ===
            amt_z = (row["amount"] - amt_mean) / amt_std if amt_std > 0 else 0
            if abs(amt_z) >= 2.0:
                ratio = row["amount"] / amt_mean if amt_mean > 0 else 0
                if row["amount"] > amt_mean:
                    reasons.append(
                        f"💰 Số tiền {row['amount']:,.0f}đ cao gấp {ratio:.1f}x mức trung bình chung ({amt_mean:,.0f}đ)")
                else:
                    reasons.append(
                        f"💰 Số tiền {row['amount']:,.0f}đ thấp bất thường so với trung bình chung ({amt_mean:,.0f}đ)")
                anomaly_tags.append("amount")

            # === Kiểm tra số tiền bất thường theo danh mục ===
            if "amount" not in anomaly_tags and cat_id in cat_amt_stats.index:
                cat_mean = cat_amt_stats.loc[cat_id, "mean"]
                cat_std = cat_amt_stats.loc[cat_id, "std"]
                if pd.isna(cat_std) or cat_std == 0:
                    cat_std = cat_mean * 0.5 if cat_mean > 0 else 1
                cat_z = (row["amount"] - cat_mean) / cat_std if cat_std > 0 else 0
                if abs(cat_z) >= 1.5 and cat_mean > 0:
                    ratio_cat = row["amount"] / cat_mean
                    if row["amount"] > cat_mean:
                        reasons.append(
                            f"💰 Số tiền {row['amount']:,.0f}đ cao gấp {ratio_cat:.1f}x mức chi trung bình cho '{c_name}' ({cat_mean:,.0f}đ)")
                    else:
                        reasons.append(
                            f"💰 Số tiền {row['amount']:,.0f}đ thấp hơn nhiều so với mức chi trung bình cho '{c_name}' ({cat_mean:,.0f}đ)")
                    anomaly_tags.append("amount")

            # === Kiểm tra giờ giấc bất thường ===
            # Chỉ cảnh báo giờ giấc khi giao dịch rơi vào khung đêm khuya/rạng sáng (23:00 – 05:00)
            is_late_night = (row["hour"] >= 23 or row["hour"] <= 5)
            if is_late_night:
                h_display = f"{int(row['hour']):02d}:00"
                reasons.append(
                    f"🕐 Giao dịch lúc {h_display} (khung giờ đêm khuya) — chi tiêu vào giờ này thường thiếu cân nhắc")
                anomaly_tags.append("time")

            # === Kiểm tra danh mục bất thường ===
            cat_pct = cat_freq.get(cat_id, 0.0) * 100
            if cat_pct < 5.0:
                reasons.append(
                    f"📂 Danh mục '{c_name}' hiếm khi xuất hiện (chỉ {cat_pct:.0f}% giao dịch thông thường)")
                anomaly_tags.append("category")

            # === Kiểm tra TỔ HỢP danh mục + khung giờ ===
            if "time" not in anomaly_tags and "category" not in anomaly_tags:
                row_slot = hour_slot(row["hour"])
                combo_count = cat_slot_counts.get((cat_id, row_slot), 0)
                cat_total = cat_total_counts.get(cat_id, 0)
                if cat_total > 0:
                    combo_pct = combo_count / cat_total * 100
                    if combo_pct < 15.0:  # Ít hơn 15% giao dịch cùng danh mục rơi vào khung giờ này
                        reasons.append(
                            f"🕐📂 '{c_name}' vào buổi {row_slot} là bất thường — chỉ {combo_pct:.0f}% giao dịch '{c_name}' diễn ra buổi {row_slot}")
                        anomaly_tags.append("time")
                        anomaly_tags.append("category")

            # === Fallback: phân tích chi tiết ===
            if not reasons:
                # So sánh với trung bình theo ngày trong tuần
                dow_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
                dow = int(row["day_of_week"])
                dow_name = dow_names[dow] if 0 <= dow <= 6 else "N/A"
                dow_avg = ref_df[ref_df["day_of_week"] == dow]["amount"].mean() if not ref_df.empty else amt_mean
                if pd.isna(dow_avg) or dow_avg == 0:
                    dow_avg = amt_mean

                # Tìm điểm khác biệt rõ nhất
                detail_parts = []
                if amt_mean > 0:
                    overall_ratio = row["amount"] / amt_mean
                    if overall_ratio > 1.3:
                        detail_parts.append(f"số tiền cao hơn {(overall_ratio - 1) * 100:.0f}% so với trung bình chung")
                    elif overall_ratio < 0.7:
                        detail_parts.append(f"số tiền thấp hơn {(1 - overall_ratio) * 100:.0f}% so với trung bình chung")

                if cat_id in cat_amt_stats.index:
                    cat_m = cat_amt_stats.loc[cat_id, "mean"]
                    if cat_m > 0:
                        cat_ratio = row["amount"] / cat_m
                        if cat_ratio > 1.3:
                            detail_parts.append(f"cao hơn {(cat_ratio - 1) * 100:.0f}% mức chi trung bình cho '{c_name}' ({cat_m:,.0f}đ)")
                        elif cat_ratio < 0.7:
                            detail_parts.append(f"thấp hơn {(1 - cat_ratio) * 100:.0f}% mức chi trung bình cho '{c_name}' ({cat_m:,.0f}đ)")

                if dow_avg > 0 and not pd.isna(dow_avg):
                    dow_ratio = row["amount"] / dow_avg
                    if dow_ratio > 1.3:
                        detail_parts.append(f"cao hơn {(dow_ratio - 1) * 100:.0f}% mức chi trung bình vào {dow_name}")

                if detail_parts:
                    combined_detail = "; ".join(detail_parts)
                    reasons.append(f"🔍 Giao dịch {row['amount']:,.0f}đ cho '{c_name}': {combined_detail}")
                else:
                    reasons.append(f"🔍 Tổ hợp yếu tố của giao dịch này ({row['amount']:,.0f}đ · '{c_name}' · {int(row['hour']):02d}:00 · {dow_name}) khác biệt so với mô hình chi tiêu thông thường của bạn")
                anomaly_tags.append("combined")

            anomalies_list.append({
                "description": row["description"] if row["description"] else "Giao dịch không tên",
                "amount": row["amount"],
                "date": row["date"],
                "hour": int(row["hour"]),
                "category": c_name,
                "anomaly_tags": list(set(anomaly_tags)),  # Loại bỏ tag trùng
                "reasons": reasons
            })

    # 7. PHÂN TÍCH HÀNH VI (BEHAVIOR PATTERN) & CHỈ SỐ RỦI RO (RISK SCORE)
    pos_spend = df[df["sentiment_score"] > 0]["amount"].sum()
    neg_spend = df[df["sentiment_score"] < 0]["amount"].sum()
    total_spend = df["amount"].sum()

    behavior_pattern = "stable"
    top_cat_id = None

    if correlation < -0.3 or (neg_spend > pos_spend * 1.5 and neg_spend > 0):
        behavior_pattern = "stress"
        stress_df = df[df["sentiment_score"] < 0]
        if not stress_df.empty: top_cat_id = stress_df.groupby("category_id")["amount"].sum().idxmax()
    elif correlation > 0.3 or (pos_spend > neg_spend * 1.5 and pos_spend > 0):
        behavior_pattern = "euphoric"
        euphoric_df = df[df["sentiment_score"] > 0]
        if not euphoric_df.empty: top_cat_id = euphoric_df.groupby("category_id")["amount"].sum().idxmax()

    cat_names = {
        1: "Ăn uống", 2: "Di chuyển", 3: "Giao lưu", 4: "Giải trí", 5: "Hóa đơn",
        6: "Học tập", 7: "Mua sắm", 8: "Phát sinh", 9: "Sức khỏe", 10: "Thu nhập"
    }
    top_cat_name = cat_names.get(top_cat_id, "Khác") if top_cat_id else "Chưa rõ"

    # Tính Confidence Score
    confidence_score = min(total_txs / 20.0, 1.0) * 0.6 + min(negative_txs / 6.0, 1.0) * 0.4
    if not is_sufficient: confidence_score = confidence_score * 0.5
    confidence_score = round(confidence_score, 2)

    # Tính Risk score có cộng dồn điểm phạt thời gian
    neg_ratio = neg_spend / total_spend if total_spend > 0 else 0
    pos_ratio = pos_spend / total_spend if total_spend > 0 else 0

    if behavior_pattern == "stress":
        base_risk = 50 + (neg_ratio * 30) + (abs(min(correlation, 0.0)) * 20)
    elif behavior_pattern == "euphoric":
        base_risk = 30 + (pos_ratio * 30) + (max(correlation, 0.0) * 20)
    else:
        base_risk = (neg_ratio + pos_ratio) * 15 + abs(correlation) * 10

    risk_score = int(base_risk + avg_time_penalty)
    risk_score = min(max(risk_score, 10), 99)

    # 8. XỬ LÝ DỮ LIỆU BIỂU ĐỒ (VISUALIZATION PREP)
    emo_summary = df.groupby("emotion")["amount"].sum().reset_index()
    emotion_data = emo_summary.to_dict(orient="records")

    trend_df = df.groupby(["date", "emotion"])["amount"].sum().reset_index().sort_values("date")
    trend_data = trend_df.to_dict(orient="records")

    df["category_name"] = df["category_id"].map(cat_names).fillna("Khác")
    heatmap_df = df.groupby(["category_name", "emotion"])["amount"].sum().reset_index()
    heatmap_data = heatmap_df.to_dict(orient="records")

    # 9. SINH INSIGHT (BEHAVIORAL ECONOMICS)
    if not is_sufficient:
        insight = "Hệ thống cần tích lũy thêm dữ liệu giao dịch của bạn trong tháng này để phân tích hành vi tài chính một cách chính xác."
    elif behavior_pattern == "stress":
        insight = f"🚨 Nhận diện **Stress-relief (Chi tiêu giải tỏa)**: Bạn đang có xu hướng dùng tiền để xoa dịu cảm xúc tiêu cực (Chi {neg_spend:,.0f}đ lúc buồn). Đặc biệt, danh mục '{top_cat_name}' đang là lỗ hổng tài chính. AI cũng phát hiện dấu hiệu **Hyperbolic Discounting** khi bạn ưu tiên cảm giác thoải mái tức thời hơn là bảo vệ ngân sách dài hạn."
    elif behavior_pattern == "euphoric":
        insight = f"⚠️ Nhận diện **Loss Aversion (Sợ bỏ lỡ)** & **Bốc đồng**: Có dấu hiệu bạn vung tay quá trán khi tâm trạng hưng phấn (Chi {pos_spend:,.0f}đ). Bạn đặc biệt hào phóng đối với mục '{top_cat_name}'. Hãy cẩn thận vì hệ thống **Mental Accounting (Kế toán tâm lý)** của bạn đang hoạt động khá lỏng lẻo trong những thời điểm này."
    else:
        insight = "✅ **Kỷ luật tâm lý**: Thói quen chi tiêu của bạn rất cân bằng. Trạng thái cảm xúc vui/buồn hầu như không làm sai lệch hệ thống **Mental Accounting** của bạn. Hãy tiếp tục duy trì!"

    return {
        "emotion_data": emotion_data,
        "correlation": round(correlation, 2),
        "behavior_pattern": behavior_pattern,
        "top_impulsive_category": top_cat_name if top_cat_id else None,
        "insight": insight,
        "is_sufficient": is_sufficient,
        "confidence_score": confidence_score,
        "risk_score": risk_score,
        "trend_data": trend_data,
        "heatmap_data": heatmap_data,
        "anomalies": anomalies_list
    }