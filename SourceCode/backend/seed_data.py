import pymysql
import random
from datetime import datetime
import calendar


def generate_mock_data():
    # 1. KẾT NỐI DATABASE MYSQL
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='finance_db',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Không thể kết nối MySQL. Hãy đảm bảo MySQL đang chạy! Lỗi: {e}")
        return

    USER_ID = 1  # Đảm bảo bạn đã đăng ký tài khoản đầu tiên để có user_id = 1

    # 2. CHUẨN BỊ TỪ ĐIỂN DỮ LIỆU SẠCH
    # Tách riêng các danh mục chi tiêu để tránh bốc nhầm vào danh mục "Thu nhập"
    expense_categories = [
        (1, "Ăn uống"), (2, "Di chuyển"), (3, "Giao lưu"), (4, "Giải trí"),
        (5, "Hóa đơn"), (6, "Học tập"), (7, "Mua sắm"), (8, "Phát sinh"), (9, "Sức khỏe")
    ]

    # Chuẩn hóa chữ viết hoa để đồng bộ với AI PhoBERT (.str.capitalize())
    emotions = ["Tích cực", "Tiêu cực", "Bình thường"]

    # Bổ sung đầy đủ mẫu câu cho tất cả 9 danh mục chi tiêu để chặn lỗi KeyError
    expense_templates = {
        "Ăn uống": ["Ăn bún bò", "Uống trà sữa", "Đi siêu thị mua đồ ăn", "Ăn lẩu cuối tuần", "Cà phê bạn bè", "Mua trái cây"],
        "Di chuyển": ["Đổ xăng xe", "Đi GrabBike", "Bảo dưỡng thay dầu xe", "Vé xe bus tháng", "Gửi xe hầm chung cư"],
        "Giao lưu": ["Đi đám cưới bạn cấp 3", "Mua quà sinh nhật bạn thân", "Tiệc liên hoan lớp", "Góp quỹ liên hoan cuối tháng"],
        "Giải trí": ["Xem phim chiếu rạp", "Mua vé xem concert", "Gia hạn gói Netflix", "Đi chơi boardgame", "Đi cafe nghe nhạc acoustic"],
        "Hóa đơn": ["Tiền điện tháng này", "Tiền nước sinh hoạt", "Tiền mạng Internet Wifi", "Đóng tiền thuê nhà trọ"],
        "Học tập": ["Mua sách thuật toán", "Đăng ký khóa học Udemy", "Mua văn phòng phẩm", "Đóng học phí chứng chỉ tiếng Anh"],
        "Mua sắm": ["Mua áo khoác mới", "Mua sách tiểu thuyết", "Sắm đồ mỹ phẩm skincare", "Mua đôi giày thể thao", "Mua balo đi học"],
        "Phát sinh": ["Sửa xe do thủng lốp", "Đền bù hư hỏng đồ đạc", "Mua ô che mưa đột xuất", "Sửa khóa cửa phòng"],
        "Sức khỏe": ["Mua thuốc cảm cúm", "Khám răng định kỳ", "Mua thực phẩm chức năng Vitamin", "Mua khẩu trang y tế và nước sát khuẩn"]
    }

    current_date = datetime.now()
    print("🚀 Bắt đầu bơm dữ liệu mẫu 6 tháng gần nhất xuống MySQL...")

    # Xóa dữ liệu cũ của user_id = 1 để tránh trùng lặp khi chạy lại nhiều lần (Tùy chọn)
    cursor.execute("DELETE FROM transactions WHERE user_id = %s", (USER_ID,))

    # 3. VÒNG LẶP TẠO DỮ LIỆU BIẾN ĐỘNG THEO LÝ THUYẾT HÀNH VI
    for i in range(5, -1, -1):  # Tạo từ 5 tháng trước tiến dần về tháng hiện tại
        target_month = current_date.month - i
        target_year = current_date.year
        while target_month <= 0:
            target_month += 12
            target_year -= 1

        _, num_days = calendar.monthrange(target_year, target_month)

        # Giả lập ngân sách chi tiêu giới hạn của sinh viên
        monthly_budget = random.randint(3500000, 5000000)
        current_spent = 0

        while current_spent < monthly_budget:
            cat_id, cat_name = random.choice(expense_categories)
            desc = random.choice(expense_templates[cat_name])
            emotion = random.choice(emotions)

            # Số tiền cơ bản từ 20k đến 300k
            amount = random.randint(2, 30) * 10000

            # MÔ PHỎNG TÀI CHÍNH HÀNH VI: Nếu stress (Tiêu cực) + Mua sắm/Giải trí -> Vung tay gấp 2-3 lần
            if emotion == "Tiêu cực" and cat_name in ["Mua sắm", "Giải trí"]:
                amount = amount * random.randint(2, 3)

            if current_spent + amount > monthly_budget:
                amount = monthly_budget - current_spent
                if amount < 10000:
                    break

            current_spent += amount

            # Tạo ngày giờ ngẫu nhiên trong tháng
            day = random.randint(1, num_days)
            hour = random.randint(7, 23)  # Mở rộng khung giờ đến 23h để Isolation Forest bắt được case đêm muộn
            minute = random.randint(0, 59)
            tx_date = datetime(target_year, target_month, day, hour, minute)
            formatted_date = tx_date.strftime("%Y-%m-%d %H:%M:%S")


            cursor.execute('''
                           INSERT INTO transactions (user_id, category_id, description, amount, type, emotion, transaction_time)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)
                           ''', (
                               USER_ID,
                               cat_id,
                               desc,
                               amount,
                               'Chi tiêu',  # Đồng bộ chuỗi hiển thị
                               emotion,
                               formatted_date
                           ))

        print(f"✅ Đã đồng bộ tháng {target_month:02d}/{target_year}: Tổng chi {current_spent:,} VND")

    conn.commit()
    conn.close()
    print("🎉 Bơm dữ liệu chuẩn AI xuống MySQL Server thành công!")


if __name__ == "__main__":
    generate_mock_data()