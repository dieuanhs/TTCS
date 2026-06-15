USE finance_db;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS budgets;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. BẢNG NGƯỜI DÙNG (Users)

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------
-- 2. BẢNG DANH MỤC (Categories)
-- -----------------------------------------------------
CREATE TABLE categories (
    category_id INT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL -- 'income' hoặc 'expense'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------
-- 3. BẢNG GIAO DỊCH (Transactions)
-- -----------------------------------------------------
CREATE TABLE transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    description TEXT NOT NULL,
    amount DOUBLE NOT NULL,
    type VARCHAR(50) NOT NULL,
    emotion VARCHAR(50) DEFAULT 'Bình thường', -- Kết quả phân lớp cảm xúc từ pipeline PhoBERT
    transaction_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Các ràng buộc toàn vẹn dữ liệu (ACID Constraints)
    CONSTRAINT fk_transactions_user
        FOREIGN KEY (user_id)
        REFERENCES users (user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_transactions_category
        FOREIGN KEY (category_id)
        REFERENCES categories (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------
-- 4. BẢNG NGÂN SÁCH (Budgets)
-- -----------------------------------------------------
CREATE TABLE budgets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    `limit` DOUBLE NOT NULL DEFAULT 0.0,
    month INT NOT NULL,
    year INT NOT NULL,

    CONSTRAINT fk_budgets_user
        FOREIGN KEY (user_id)
        REFERENCES users (user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_budgets_category
        FOREIGN KEY (category_id)
        REFERENCES categories (category_id),
    -- Đảm bảo tính độc nhất: một người dùng chỉ thiết lập duy nhất 1 hạn mức cho 1 danh mục trong chu kỳ tháng
    CONSTRAINT uq_user_category_period
        UNIQUE (user_id, category_id, month, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



-- DỮ LIỆU BẢNG 1: NGƯỜI DÙNG MẪU (User 1)

INSERT INTO users (user_id, full_name, email, password, created_at) VALUES
(1, 'anh', 'anh@gmail.com', 'string', '2026-03-31 08:00:00');

INSERT INTO categories (category_id, category_name, type) VALUES
(1, 'Ăn uống', 'expense'),
(2, 'Di chuyển', 'expense'),
(3, 'Giao lưu', 'expense'),
(4, 'Giải trí', 'expense'),
(5, 'Hóa đơn', 'expense'),
(6, 'Học tập', 'expense'),
(7, 'Mua sắm', 'expense'),
(8, 'Phát sinh', 'expense'),
(9, 'Sức khỏe', 'expense'),
(10, 'Thu nhập', 'income');

INSERT INTO budgets (id, user_id, category_id, `limit`, month, year) VALUES
(1, 1, 1, 2000000, 4, 2026), -- Hạn mức tháng 4: 2.000.000 VND
(2, 1, 1, 2500000, 5, 2026), -- Hạn mức tháng 5: 2.500.000 VND
(3, 1, 1, 1500000, 6, 2026); -- Hạn mức tháng 6 (Tháng hiện tại): 1.500.000 VND

INSERT INTO transactions (user_id, category_id, description, amount, type, emotion, transaction_time, created_at) VALUES

-- CHU KỲ THÁNG 4/2026: Giai đoạn chi tiêu biến động theo tâm trạng stress học tập
(1, 1, 'Mua trái cây', 130000, 'Chi tiêu', 'Tiêu cực', '2026-04-27 11:34:00', '2026-04-27 11:34:00'),
(1, 1, 'Mua trái cây', 60000, 'Chi tiêu', 'Tích cực', '2026-04-24 17:23:00', '2026-04-24 17:23:00'),
(1, 3, 'Sắm đồ skincare', 280000, 'Chi tiêu', 'Tiêu cực', '2026-04-11 08:19:00', '2026-04-11 08:19:00'),
(1, 1, 'Ăn lẩu cuối tuần', 90000, 'Chi tiêu', 'Tích cực', '2026-04-25 08:24:00', '2026-04-25 08:24:00'),
(1, 3, 'Mua áo mới', 110000, 'Chi tiêu', 'Bình thường', '2026-04-20 08:56:00', '2026-04-20 08:56:00'),
(1, 5, 'Tiền điện', 170000, 'Chi tiêu', 'Bình thường', '2026-04-12 07:38:00', '2026-04-12 07:38:00'),
(1, 5, 'Tiền điện', 60000, 'Chi tiêu', 'Tiêu cực', '2026-04-12 15:44:00', '2026-04-12 15:44:00'),
(1, 1, 'Đi siêu thị mua đồ ăn', 260000, 'Chi tiêu', 'Tiêu cực', '2026-04-13 22:01:00', '2026-04-13 22:01:00'),
(1, 5, 'Tiền điện', 230000, 'Chi tiêu', 'Bình thường', '2026-04-30 18:14:00', '2026-04-30 18:14:00'),
(1, 1, 'Mua trái cây', 120000, 'Chi tiêu', 'Tích cực', '2026-04-03 22:24:00', '2026-04-03 22:24:00'),
(1, 1, 'Ăn bún bò', 20000, 'Chi tiêu', 'Tích cực', '2026-04-24 16:40:00', '2026-04-24 16:40:00'),
(1, 1, 'Uống trà sữa', 40000, 'Chi tiêu', 'Tích cực', '2026-04-09 15:06:00', '2026-04-09 15:06:00'),
(1, 4, 'Đi Pub', 240000, 'Chi tiêu', 'Tiêu cực', '2026-04-14 20:54:00', '2026-04-14 20:54:00'),
(1, 4, 'Xem phim chiếu rạp', 290000, 'Chi tiêu', 'Tích cực', '2026-04-09 22:05:00', '2026-04-09 22:05:00'),
(1, 2, 'Gửi xe tháng', 240000, 'Chi tiêu', 'Bình thường', '2026-04-23 18:24:00', '2026-04-23 18:24:00'),
(1, 5, 'Tiền trọ', 150000, 'Chi tiêu', 'Tích cực', '2026-04-10 11:22:00', '2026-04-10 11:22:00'),
(1, 4, 'Đi Pub', 270000, 'Chi tiêu', 'Tích cực', '2026-04-30 08:54:00', '2026-04-30 08:54:00'),
(1, 2, 'Gửi xe tháng', 290000, 'Chi tiêu', 'Tiêu cực', '2026-04-06 09:05:00', '2026-04-06 09:05:00'),
(1, 2, 'Bảo dưỡng xe', 230000, 'Chi tiêu', 'Tích cực', '2026-04-08 15:32:00', '2026-04-08 15:32:00'),
(1, 2, 'Vé xe bus', 240000, 'Chi tiêu', 'Tích cực', '2026-04-07 10:39:00', '2026-04-07 10:39:00'),
(1, 4, 'Đăng ký Netflix', 160000, 'Chi tiêu', 'Tích cực', '2026-04-25 09:33:00', '2026-04-25 09:33:00'),
(1, 4, 'Mua vé concert', 120000, 'Chi tiêu', 'Tích cực', '2026-04-11 18:41:00', '2026-04-11 18:41:00'),
(1, 3, 'Mua giày', 260000, 'Chi tiêu', 'Tích cực', '2026-04-12 17:47:00', '2026-04-12 17:47:00'),
(1, 1, 'Ăn bún bò', 150000, 'Chi tiêu', 'Tiêu cực', '2026-04-25 14:07:00', '2026-04-25 14:07:00'),
(1, 5, 'Tiền trọ', 100000, 'Chi tiêu', 'Tiêu cực', '2026-04-30 18:20:00', '2026-04-30 18:20:00'),
(1, 3, 'Mua sách', 60000, 'Chi tiêu', 'Tích cực', '2026-04-09 20:34:00', '2026-04-09 20:34:00'),
(1, 2, 'Bảo dưỡng xe', 130000, 'Chi tiêu', 'Bình thường', '2026-04-07 09:48:00', '2026-04-07 09:48:00'),

-- CHU KỲ THÁNG 5/2026: Giai đoạn có dòng tiền thu nhập lớn và săn sale giải trí tăng mạnh
(1, 1, 'đi ăn gà texas hết 200k khá vui ', 200000, 'Chi tiêu', 'Tích cực', '2026-05-01 22:38:46', '2026-05-01 15:38:46'),
(1, 10, 'nhận 10 tr lương tháng', 10000000, 'Thu nhập', 'Tích cực', '2026-05-01 23:09:18', '2026-05-01 16:09:18'),
(1, 5, 'trả tiền trọ hết 2tr', 2000000, 'Chi tiêu', 'Bình thường', '2026-05-08 22:22:36', '2026-05-08 15:22:36'),
(1, 1, 'mua thịt hết 200k', 200000, 'Chi tiêu', 'Bình thường', '2026-05-08 22:23:00', '2026-05-08 15:23:00'),
(1, 2, 'Đi bảo dưỡng xe hết 300k xót ruột quá', 300000, 'Chi tiêu', 'Tiêu cực', '2026-05-08 22:30:41', '2026-05-08 15:30:41'),
(1, 4, 'đi nghe nhạc hết 300k vui quá', 300000, 'Chi tiêu', 'Tích cực', '2026-05-15 16:37:21', '2026-05-15 09:37:21'),
(1, 1, 'mệt quá nên đi ăn ngoài hết 35k', 35000, 'Chi tiêu', 'Tiêu cực', '2026-05-22 19:06:19', '2026-05-22 12:06:19'),
(1, 3, 'mua quà tặng bạn hết 150k', 150000, 'Chi tiêu', 'Bình thường', '2026-05-22 19:07:04', '2026-05-22 12:07:04'),
(1, 4, 'đi hát karaoke xả stress hết 150k', 150000, 'Chi tiêu', 'Tiêu cực', '2026-05-22 19:07:58', '2026-05-22 12:07:58'),
(1, 4, 'đi thủy cung hết 150k', 150000, 'Chi tiêu', 'Bình thường', '2026-05-22 20:48:14', '2026-05-22 13:48:14'),
(1, 1, 'mua đồ ăn vặt cho đỡ buồn hết 30k', 30000, 'Chi tiêu', 'Tiêu cực', '2026-05-22 20:49:08', '2026-05-22 13:49:08'),
(1, 1, 'uống trà sữa cho đỡ stress hết 40k', 40000, 'Chi tiêu', 'Tiêu cực', '2026-05-22 20:49:43', '2026-05-22 13:49:43'),
(1, 5, 'trả tiền mạng hết 75k', 75000, 'Chi tiêu', 'Bình thường', '2026-05-22 21:00:54', '2026-05-22 14:00:54'),
(1, 10, 'nhận 3 củ tiền lương parttime vui quá', 3000000, 'Thu nhập', 'Tích cực', '2026-05-29 18:04:36', '2026-05-29 11:04:36'),
(1, 7, 'mua quần áo mới hết 450k', 450000, 'Chi tiêu', 'Tích cực', '2026-05-29 18:05:27', '2026-05-29 11:05:27'),
(1, 7, 'săn sale mỹ phẩm hết 358k', 358000, 'Chi tiêu', 'Tích cực', '2026-05-29 22:30:08', '2026-05-29 15:30:08'),

-- CHU KỲ THÁNG 6/2026: Tháng hiện tại phục vụ thuật toán Burn Rate, Isolation Forest
(1, 1, 'mua thịt hết 150k', 150000, 'Chi tiêu', 'Bình thường', '2026-06-05 20:57:09', '2026-06-05 13:57:09'),
(1, 10, 'nhận lương được 5 triệu', 5000000, 'Thu nhập', 'Tích cực', '2026-06-05 20:57:33', '2026-06-05 13:57:33'),
(1, 5, 'trả tiền trọ hết 1554k', 1554000, 'Chi tiêu', 'Bình thường', '2026-06-12 21:16:22', '2026-06-12 14:16:22'),
(1, 6, 'mua vở viết hết 15k', 15000, 'Chi tiêu', 'Bình thường', '2026-06-12 21:27:03', '2026-06-12 14:27:03'),
(1, 1, 'mệt nên đi ăn cơm gà hết 35k', 35000, 'Chi tiêu', 'Tiêu cực', '2026-06-12 21:39:39', '2026-06-12 21:39:39'),
(1, 1, 'buồn nên mua trà sữa hết 35k', 35000, 'Chi tiêu', 'Tiêu cực', '2026-06-15 16:55:30', '2026-06-15 09:55:30'),
(1, 9, 'mua thuốc đau đầu hết 75k', 75000, 'Chi tiêu', 'Tiêu cực', '2026-06-15 16:56:20', '2026-06-15 09:56:20'),
(1, 1, 'mua rau hết 25k', 25000, 'Chi tiêu', 'Bình thường', '2026-06-15 16:58:46', '2026-06-15 09:58:46'),
(1, 2, 'trả tiền vé tháng xe bus hết 140k', 140000, 'Chi tiêu', 'Bình thường', '2026-06-15 16:59:13', '2026-06-15 09:59:13'),
(1, 3, 'mua quà sinh nhật cho bạn hết 150k', 150000, 'Chi tiêu', 'Tích cực', '2026-06-15 16:59:49', '2026-06-15 09:59:49'),
(1, 4, 'đi thủy cung hết 150k rất vui', 150000, 'Chi tiêu', 'Tích cực', '2026-06-15 17:06:31', '2026-06-15 10:06:31'),
(1, 7, 'mua sửa rửa mặt hết 223k', 223000, 'Chi tiêu', 'Bình thường', '2026-06-15 17:10:13', '2026-06-15 10:10:13');
