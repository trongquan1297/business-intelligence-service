import google.generativeai as genai
from config import GEMINI_API_KEY
from app.services.user_service import get_user_role
from app.services.permission_service import check_table_access, get_allowed_tables_prompt
import json

# Cấu hình Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def convert_to_sql(question: str, username: str) -> tuple:
    """Convert Vietnamese question to SQL with role-based access control using Gemini"""
    # Get user role
    role = get_user_role(username)
    if not role:
        raise Exception("Không tìm thấy role của user")

    # Get allowed tables prompt
    allowed_tables_prompt = get_allowed_tables_prompt(role)
    
    prompt = f"""
    Nhiệm vụ của bạn là:
    1. Kiểm tra xem câu hỏi có liên quan đến việc phân tích dữ liệu từ các bảng được cung cấp hay không.
    2. Nếu liên quan, chuyển đổi câu hỏi thành câu lệnh SQL tương thích với ClickHouse và cung cấp metadata.
    3. Nếu không liên quan, trả về một phản hồi hài hước mà không tạo SQL.
    4. Nếu câu hỏi vượt quá phạm vi truy cập, trả về một phản hồi hước.
    5. Nếu câu lệnh SQL từ các bảng không có sẵn, trả về thông báo không liên quan.
    Chỉ được sử dụng các bảng sau đây theo role {role}:
    {allowed_tables_prompt}
    Câu hỏi: "{question}" 
    Trả về kết quả theo định dạng JSON với format sau:
    - Nếu câu hỏi liên quan đến phân tích dữ liệu:
    {{
        "sql_query": "Câu lệnh SQL hoàn chỉnh",
        "explanation": "Giải thích SQL bằng tiếng Việt",
        "chart_title": "Tiêu đề gợi ý cho biểu đồ",
        "suggested_chart_type": "Loại biểu đồ phù hợp nhất (Line Chart, Bar Chart, Pie Chart, Scatter Plot, Box Plot)",
        "recommendation": ["Câu hỏi gợi ý 1", "Câu hỏi gợi ý 2", "Câu hỏi gợi ý 3"],
        "columns": {{
            "column1": {{
                "display_name": "Tên hiển thị cột category",
                "description": "Mô tả cột 1",
                "type": "numeric/categorical/date"
            }},
            "column2": {{
                "display_name": "Tên hiển thị cột numeric", 
                "description": "Mô tả cột 2",
                "type": "numeric"
            }}
        }}
    }}
    - Nếu câu hỏi không liên quan, vượt quá phạm vi, không có quyền truy vấn các bảng sẵn có:
    {{
        "sql_query": "",
        "explanation": "Phản hồi hước bằng tiếng Việt",
        "chart_title": "",
        "suggested_chart_type": "",
        "recommendation": [],
        "columns": {{}}
    }}
    Lưu ý:
    - Đảm bảo JSON format phải chính xác
    - Các tên cột phải khớp với kết quả SQL query
    - Tiêu đề biểu đồ phải mô tả được nội dung phân tích.
    - Sử dụng cú pháp ClickHouse:
      + Cột `created_at` thường là kiểu `DateTime`
      + Khi dùng `GROUP BY`, tất cả cột không tổng hợp trong `SELECT` phải có trong `GROUP BY`, hoặc dùng hàm tổng hợp như `any()`, `max()`, `min()` cho các cột không nhóm.
      + Không sử dụng các hàm không tồn tại trong ClickHouse.
    - column2 phải là cột số biểu thị số lượng đo lường mà không phải id, column1 có thể là cột thời gian hoặc phân loại.
    - Gợi ý `suggested_chart_type` dựa trên dữ liệu dự kiến từ SQL.
    - Các bảng có sẵn: 
      + transactions(transaction_id, order_id, order_info, partner_id, device_id, store_id, amount, payment_method, bank_code, provider_code, status, device_type, created_at, updated_at)
      + partners(partner_id, partner_name, status)
      + pos_devices(device_id, name, device_provider_code, type, status)
      + partner_stores(store_id, partner_id, name, status, created_at, updated_at)
    - Nếu câu hỏi không nhắc đến hoặc không ám chỉ việc phân tích dữ liệu từ các bảng này, coi là không liên quan.
    """

    try:
        # Khởi tạo model Gemini
        model = genai.GenerativeModel('gemini-2.0-flash-lite')  # Thay đổi tên model nếu cần
        
        # Gửi yêu cầu tới Gemini
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json"  # Yêu cầu phản hồi dạng JSON
            }
        )
        
        # Lấy nội dung phản hồi
        result = response.text  # Gemini trả về text, không phải object như OpenAI
        parsed_result = json.loads(result)  # Parse JSON từ string

        sql_query = parsed_result.get("sql_query", "")
        
        # Nếu có SQL, kiểm tra quyền truy cập
        if sql_query:
            if not check_table_access(sql_query, role):
                raise Exception("Câu truy vấn sử dụng bảng không được phép truy cập")
        
        # Chuẩn hóa suggested_chart_type
        suggested_chart_type = parsed_result.get("suggested_chart_type", "Bar Chart")
        valid_chart_types = ["Line Chart", "Bar Chart", "Pie Chart", "Scatter Plot", "Box Plot"]
        if suggested_chart_type not in valid_chart_types:
            suggested_chart_type = "Bar Chart"

        return (
            sql_query,
            parsed_result.get("explanation", ""),
            parsed_result.get("chart_title", ""),
            suggested_chart_type,
            parsed_result.get("recommendation", []),
            parsed_result.get("columns", {})
        )
    except Exception as e:
        print(f"Error in convert_to_sql with Gemini: {str(e)}")
        raise Exception(f"Không thể chuyển đổi thành SQL từ Gemini: {str(e)}")