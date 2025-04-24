# Sử dụng image Python chính thức
FROM python:3.11-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép file requirements.txt và cài đặt dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn
COPY . .

# Expose cổng mà FastAPI chạy
EXPOSE 8000

# # Chạy ứng dụng
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]