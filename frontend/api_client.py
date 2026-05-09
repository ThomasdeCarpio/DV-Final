import requests
import streamlit as st

BASE_URL = "http://localhost:8000"

def generate_ai_code(prompt: str):
    """Gửi yêu cầu vẽ biểu đồ tới AI."""
    try:
        response = requests.post(f"{BASE_URL}/api/ai/generate", json={"prompt": prompt})
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Lỗi từ AI: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Không thể kết nối tới Backend. Hãy chắc chắn rằng FastAPI đang chạy trên cổng 8000.")
        return None

def execute_local_code(code: str, dataset_path: str = "../data/cleaned_vietnam_real_estates.csv"):
    """Gửi code đã được phê duyệt để chạy cục bộ và lấy biểu đồ."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/execute", 
            json={"code": code, "dataset_path": dataset_path}
        )
        if response.status_code == 200:
            return {"status": "success", "image_base64": response.json()["image_base64"]}
        else:
            return {"status": "error", "error_message": response.json().get("detail", "Lỗi không xác định")}
    except Exception as e:
         return {"status": "error", "error_message": str(e)}

def log_system_action(prompt: str, original_code: str, edited_code: str, status: str, error_msg: str = None):
    """Lưu trữ lịch sử tương tác."""
    try:
        requests.post(f"{BASE_URL}/api/logs", json={
            "prompt": prompt,
            "original_code": original_code,
            "edited_code": edited_code,
            "status": status,
            "error_message": error_msg
        })
    except:
        pass # Chấp nhận bỏ qua nếu lỗi log để không gián đoạn UI

def get_general_chat(prompt: str):
    """Gửi yêu cầu trò chuyện tư vấn tới AI."""
    try:
        response = requests.post(f"{BASE_URL}/api/ai/chat", json={"prompt": prompt})
        if response.status_code == 200:
            return response.json()["content"]
        else:
            return f"Lỗi từ AI: {response.text}"
    except:
        return "Lỗi kết nối tới Backend."
    
def modify_ai_code(current_code: str, prompt: str):
    """Gửi code hiện tại và yêu cầu sửa đổi tới AI."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/ai/modify", 
            json={"current_code": current_code, "prompt": prompt}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Lỗi khi sửa code: {response.text}")
            return None
    except:
        st.error("Lỗi kết nối tới Backend.")
        return None