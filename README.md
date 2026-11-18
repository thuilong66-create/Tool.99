# LC79_HU

Ứng dụng Flask độc lập cho Render.

## Deploy
1. Tạo GitHub repository riêng hoặc upload riêng thư mục này.
2. Render → New → Web Service → kết nối repository.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn app:app`
5. Deploy.

API health: `/health`

Mọi URL API đều có thể đổi bằng Environment Variables:
- LC79_API_URL

Lưu ý: API lịch sử có thể thay đổi cấu trúc hoặc yêu cầu quyền truy cập. Dự đoán chỉ là phân tích dữ liệu lịch sử/hash, không đảm bảo kết quả.
