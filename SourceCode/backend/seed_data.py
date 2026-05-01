import sqlite3
import random
from datetime import datetime
import calendar


def generate_mock_data():
    # 1. KẾT NỐI DATABASE
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()

    USER_ID = 1

    # 2. CHUẨN BỊ TỪ ĐIỂN DỮ LIỆU (Đã update theo AI model của Ánh)
    categories = [
        (1, "Ăn uống"), (2, "Di chuyển"),
        (3, "Mua sắm"), (4, "Giải trí"), (5, "Hóa đơn")
    ]
    # Cập nhật đúng 3 nhãn cảm xúc từ AI
    emotions = ["tích cực", "tiêu cực", "bình thường"]

    expense_templates = {
        "Ăn uống": ["Ăn bún bò", "Uống trà sữa", "Đi siêu thị mua đồ ăn", "Ăn lẩu cuối tuần", "Cà phê bạn bè",
                    "Mua trái cây"],
        "Di chuyển": ["Đổ xăng", "Đi Grab", "Bảo dưỡng xe", "Vé xe bus", "Gửi xe tháng"],
        "Mua sắm": ["Mua áo mới", "Mua sách", "Sắm đồ skincare", "Mua giày", "Mua quà sinh nhật"],
        "Giải trí": ["Xem phim chiếu rạp", "Mua vé concert", "Đăng ký Netflix", "Đi boardgame", "Đi Pub"],
        "Hóa đơn": ["Tiền điện", "Tiền nước", "Tiền mạng", "Tiền trọ"]
    }

    current_date = datetime.now()
    print("🚀 Bắt đầu tạo dữ liệu cho 6 tháng...")

    # 3. VÒNG LẶP TẠO DỮ LIỆU
    for i in range(1, 7):
        target_month = current_date.month - i
        target_year = current_date.year
        if target_month <= 0:
            target_month += 12
            target_year -= 1

        _, num_days = calendar.monthrange(target_year, target_month)

        monthly_budget = random.randint(4000000, 6000000)
        current_spent = 0

        while current_spent < monthly_budget:
            cat_id, cat_name = random.choice(categories)
            desc = random.choice(expense_templates[cat_name])
            emotion = random.choice(emotions)

            amount = random.randint(2, 30) * 10000

            # CẬP NHẬT LOGIC TÂM LÝ: Dựa trên nhãn "tiêu cực"
            if emotion == "tiêu cực" and cat_name in ["Mua sắm", "Giải trí"]:
                amount = amount * random.randint(2, 4)

            if current_spent + amount > monthly_budget:
                amount = monthly_budget - current_spent
                if amount < 15000:
                    break

            current_spent += amount

            day = random.randint(1, num_days)
            hour = random.randint(7, 22)
            minute = random.randint(0, 59)
            tx_date = datetime(target_year, target_month, day, hour, minute)
            formatted_date = tx_date.strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute('''
                           INSERT INTO transactions (user_id, category_id, description, amount, type, emotion,
                                                     transaction_time, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                           ''', (
                               USER_ID,
                               cat_id,
                               desc,
                               amount,
                               'expense',
                               emotion,
                               formatted_date,
                               formatted_date
                           ))

        print(f"✅ Tháng {target_month}/{target_year}: Đã tạo {current_spent:,} VND")

    conn.commit()
    conn.close()
    print("🎉 Bơm dữ liệu chuẩn AI thành công! Ánh kiểm tra Database nhé!")


if __name__ == "__main__":
    generate_mock_data()