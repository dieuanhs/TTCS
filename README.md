# 📊 Smart Finance - Hệ thống quản lý tài chính cá nhân thông minh tích hợp AI

## 📝 1. Giới thiệu dự án

**Smart Finance** là một ứng dụng Web cá nhân hóa quản lý tài chính hành vi, ứng dụng mô hình học sâu để tối ưu hóa trải nghiệm người dùng và khai phá dữ liệu dòng tiền. Dự án được xây dựng và vận hành chặt chẽ theo mô hình kiến trúc ba lớp tách biệt (**3-Tier Architecture**), đảm bảo tính module hóa cao, độc lập phát triển và dễ dàng bảo trì nâng cấp.

### 🚀 Định hướng vai trò chuyên môn: Backend Developer & AI Integration
Dự án tập trung đào sâu năng lực thiết kế API RESTful bằng **FastAPI**, quản trị hệ cơ sở dữ liệu quan hệ **MySQL** qua SQLAlchemy ORM, và cấu trúc hóa các pipeline suy luận AI cục bộ trên RAM để tối ưu hóa hiệu năng I/O cho hệ thống.

### 🌟 Các phân hệ chức năng cốt lõi:
* **Smart Input (NLP):** Nhập liệu bằng một câu văn tự do tiếng Việt (ví dụ: *"uống trà sữa cho đỡ stress hết 40k"*). Pipeline AI tích hợp **Regex + LinearSVC + PhoBERT-base-v2** tự động bóc tách số tiền, nhận diện danh mục và phân tích trạng thái cảm xúc ngữ cảnh trong thời gian thực.
* **Behavioral Analytics (Tài chính hành vi):** Lượng hóa tác động của tâm trạng lên tiền bạc qua hệ số tương quan Pearson ($r$) và chỉ số rủi ro *Risk Score*. Tự động phân loại mô hình hành vi người dùng (*Stress Spending, Euphoric, Stable*) để đưa ra lời khuyên cá nhân hóa vượt qua bài toán *Cold Start*.
* **Adaptive Smart Forecast (Dự báo thích ứng):** Dự phóng số dư tài chính cuối kỳ bằng cách kết hợp tốc độ tiêu tiền (*Burn Rate*), chỉ số xu hướng cảm xúc EMA ngắn hạn, ma trận độ nhạy cảm danh mục và hiệu ứng ngày lương (*Payday Effect*).
* **Anomaly Detection (Phát hiện bất thường):** Ứng dụng mô hình học máy không giám sát **Isolation Forest** để cắm cờ các giao dịch lệch chuẩn dựa trên vectơ đặc trưng 4 chiều `[amount, category_id, hour, day_of_week]`, đi kèm diễn giải bằng ngôn ngữ tự nhiên (XAI).

---

## 🚀 2. Hướng dẫn cài đặt và chạy chương trình

### 📋 Yêu cầu hệ thống trước khi cài đặt:
* Đã cài đặt **Python 3.10+** (Hỗ trợ tốt trên cả Python 3.14).
* Đã cài đặt và đang bật **MySQL Server** (thông qua XAMPP, MySQL Installer hoặc Docker).

### Bước 1: Khởi tạo Cơ sở dữ liệu trong MySQL
1. Mở công cụ quản trị MySQL của bạn (MySQL Workbench hoặc phpMyAdmin).
2. Mở file `database/initialize_and_seed_finance_db.sql` trong dự án.
3. Sao chép toàn bộ nội dung kịch bản SQL và chạy (`Execute`) trên tab Query. 
   *(Mã lệnh này sẽ tự động khởi tạo database `finance_db`, dựng cấu trúc 4 bảng vật lý cốt lõi `users`, `categories`, `transactions`, `budgets` và bơm sẵn dữ liệu sạch 3 tháng 4, 5, 6 năm 2026 của tài khoản mẫu để sẵn sàng Demo).*

### Bước 2: Cài đặt các thư viện Pythondependencies
Mở Terminal tại thư mục gốc của dự án và thực hiện lệnh cài đặt các gói thư viện phụ thuộc:
```bash
pip install fastapi uvicorn sqlalchemy pymysql pydantic streamlit plotly pandas numpy scikit-learn underthesea torch transformers
```
### Bước 3: Khởi chạy ứng dụng Backend (FastAPI)
```bash
cd src/project/backend
uvicorn main:app --reload
```
Server Backend chạy thành công sẽ phân bồi tại địa chỉ: http://127.0.0.1:8000. Mọi người có thể truy cập vào http://127.0.0.1:8000/docs để kiểm tra toàn bộ đặc tả hệ thống API qua Swagger UI.
### Bước 4:Khởi chạy ứng dụng Frontend (Streamlit)
Mở một cửa sổ Terminal mới (giữ nguyên Terminal của Backend đang chạy), điều hướng vào thư mục frontend và chạy lệnh:
```bash
cd src/project/frontend
streamlit run app.py
```
Hệ thống giao diện Premium Fintech Dashboard sẽ tự động bật lên trên trình duyệt mặc định của bạn tại địa chỉ cổng http://localhost:8501.

###Tài khoản mẫu Đăng nhập (Demo Account)
Sau khi chạy script khởi tạo SQL ở Bước 1 thành công, người dùng sử dụng thông tin tài khoản sau để đăng nhập trực tiếp trên giao diện Streamlit:
* tên: anh
* mật khẩu: string
