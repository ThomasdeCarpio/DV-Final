import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

# Load variables from the .env file into the system
load_dotenv()

# Get the key and configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is missing! Check your .env file.")

# Configure Gemini API
genai.configure(api_key=api_key)

# Define the exact dataset schema to prevent AI hallucinations
DATASET_SCHEMA = """
Tên cột | Kiểu dữ liệu | Ý nghĩa
- property_type_name (str): Loại bất động sản (Nhà, Biệt thự/Nhà liền kề, ...)
- province_name (str): Tỉnh/Thành phố
- district_name (str): Quận/Huyện
- ward_name (str): Phường/Xã
- price (float): Giá bán tổng (Tỷ VNĐ)
- area (float): Diện tích (m2)
- floor_count (float): Số tầng
- frontage_width (float): Mặt tiền (m)
- road_width (float): Đường vào (m)
- bedroom_count (float): Số phòng ngủ
- bathroom_count (float): Số phòng tắm
- house_direction (str): Hướng nhà (Đông, Tây, Nam, Bắc...)
- published_at (datetime): Ngày đăng tin
- price_per_m2 (float): Giá trên 1 m2 (Triệu VNĐ/m2)
- year_month (str): Năm-Tháng (vd: 2025-09)
- area_cluster (str): Nhóm diện tích (<50m2, 50-100m2...)
- total_rooms (float): Tổng số phòng (ngủ + tắm)
- region (str): Vùng miền (Bắc, Trung, Nam)
"""

SYSTEM_PROMPT = f"""
Bạn là một Chuyên gia Trực quan hóa Dữ liệu (Chart Engineer) phân tích thị trường Bất động sản Việt Nam.
Dữ liệu của tôi được lưu trong pandas DataFrame tên là `df`.

CẤU TRÚC DỮ LIỆU:
{DATASET_SCHEMA}

QUY TẮC BẮT BUỘC:
1. Chỉ viết mã Python sử dụng thư viện `pandas`, `matplotlib.pyplot` (plt), và `seaborn` (sns).
2. TRẢ VỀ ĐÚNG ĐỊNH DẠNG JSON sau:
{{
    "explanation": "Giải thích ngắn gọn bằng tiếng Việt về biểu đồ này và ý nghĩa các cột được sử dụng.",
    "code": "Mã Python để vẽ biểu đồ (thêm comment tiếng Việt vào code)."
}}
3. Không sử dụng `plt.show()`, chỉ cần cấu hình biểu đồ (tôi sẽ tự xử lý hiển thị).
4. Thiết lập kích thước biểu đồ: `plt.figure(figsize=(10, 6))`.
5. Luôn chọn màu sắc chuyên nghiệp và dễ nhìn.
"""

def generate_chart_code(user_prompt: str) -> dict:
    model = genai.GenerativeModel('gemini-3-flash-preview', system_instruction=SYSTEM_PROMPT)
    
    response = model.generate_content(
        f"Yêu cầu của người dùng: {user_prompt}\n\nTrả về đúng định dạng JSON, không kèm markdown code block (như ```json)."
    )
    
    try:
        # Clean the response just in case Gemini adds markdown formatting
        raw_text = response.text.strip()
        raw_text = re.sub(r'^```json', '', raw_text)
        raw_text = re.sub(r'```$', '', raw_text).strip()
        
        result = json.loads(raw_text)
        return result
    except json.JSONDecodeError:
        raise Exception("AI did not return a valid JSON format. Raw output: " + response.text)