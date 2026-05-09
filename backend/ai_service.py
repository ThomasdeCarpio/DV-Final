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
    
CHART_SYSTEM_PROMPT = f"""
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
3. Không sử dụng `plt.show()`. Thiết lập kích thước biểu đồ: `plt.figure(figsize=(10, 6))`.
"""

# --- PROMPTS FOR GENERAL CHAT ---
CHAT_SYSTEM_PROMPT = f"""
Bạn là một Chuyên gia Tư vấn Bất động sản Việt Nam.
Dựa trên cấu trúc dữ liệu sau: {DATASET_SCHEMA}

NHIỆM VỤ:
1. Trả lời các câu hỏi về chuyên môn, xu hướng và cách phân tích dữ liệu.
2. Đề xuất các hướng phân tích hay (vd: So sánh giá theo vùng miền, tìm mối tương quan giữa diện tích và giá).
3. Tuyệt đối KHÔNG tạo mã Python trong chế độ này.
4. Nếu người dùng muốn vẽ biểu đồ, hãy nhắc họ chuyển sang chế độ 'Vẽ biểu đồ'.
"""

def generate_chart_code(user_prompt: str) -> dict:
    model = genai.GenerativeModel('gemini-3-flash-preview', system_instruction=CHART_SYSTEM_PROMPT)
    response = model.generate_content(f"Yêu cầu: {user_prompt}\nTrả về JSON.")
    try:
        raw_text = response.text.strip()
        raw_text = re.sub(r'^```json', '', raw_text)
        raw_text = re.sub(r'```$', '', raw_text).strip()
        return json.loads(raw_text)
    except:
        raise Exception("AI failed to return JSON.")

def generate_chat_response(user_prompt: str) -> str:
    model = genai.GenerativeModel('gemini-3-flash-preview', system_instruction=CHAT_SYSTEM_PROMPT)
    response = model.generate_content(user_prompt)
    return response.text

# --- PROMPTS FOR CODE MODIFICATION (V2 STEP 3) ---
MODIFY_SYSTEM_PROMPT = f"""
Bạn là một Chuyên gia Review Code. Nhiệm vụ của bạn là SỬA ĐỔI mã Python hiện có dựa trên yêu cầu của người dùng.

DỮ LIỆU HIỆN TẠI: {DATASET_SCHEMA}

QUY TẮC:
1. Nhận vào đoạn code hiện tại và chỉ thực hiện các thay đổi mà người dùng yêu cầu (vd: đổi màu, thêm tiêu đề, lọc thêm dữ liệu).
2. Luôn trả về toàn bộ đoạn code đã sửa trong định dạng JSON:
{{
    "explanation": "Giải thích bạn đã sửa những gì bằng tiếng Việt.",
    "code": "Toàn bộ mã Python sau khi đã sửa."
}}
3. Đảm bảo mã vẫn sử dụng DataFrame `df` và các thư viện pandas, plt, sns.
"""

def modify_chart_code(current_code: str, user_instruction: str) -> dict:
    model = genai.GenerativeModel('gemini-3-flash-preview', system_instruction=MODIFY_SYSTEM_PROMPT)
    
    prompt = f"Code hiện tại:\n{current_code}\n\nYêu cầu sửa đổi: {user_instruction}\n\nTrả về JSON."
    response = model.generate_content(prompt)
    
    try:
        raw_text = response.text.strip()
        raw_text = re.sub(r'^```json', '', raw_text)
        raw_text = re.sub(r'```$', '', raw_text).strip()
        return json.loads(raw_text)
    except:
        raise Exception("AI failed to return valid JSON for modification.")