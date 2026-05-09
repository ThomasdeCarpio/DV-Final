import streamlit as st
import base64
from io import BytesIO
from PIL import Image
import api_client

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="VN Real Estate Analytics", page_icon="🏢", layout="wide")

# --- KHỞI TẠO SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Chào bạn! Tôi là trợ lý phân tích dữ liệu Bất động sản. Bạn muốn vẽ biểu đồ gì hôm nay?"}
    ]
if "is_pending" not in st.session_state:
    st.session_state.is_pending = False
if "current_code" not in st.session_state:
    st.session_state.current_code = ""
if "original_code" not in st.session_state:
    st.session_state.original_code = ""
if "current_explanation" not in st.session_state:
    st.session_state.current_explanation = ""
if "current_prompt" not in st.session_state:
    st.session_state.current_prompt = ""

# --- GIAO DIỆN SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Bảng Điều Khiển")
    st.markdown("---")
    st.subheader("📁 Dữ liệu hiện tại")
    st.success("Đã kết nối: `cleaned_vietnam_real_estates.csv`")
    
    with st.expander("📄 Xem Cấu Trúc Dữ Liệu (Schema)"):
        st.markdown("""
        - **property_type_name**: Loại BĐS
        - **province_name, district_name**: Tỉnh/Quận
        - **price**: Giá (Tỷ VNĐ)
        - **area**: Diện tích (m2)
        - **price_per_m2**: Giá/m2 (Triệu VNĐ)
        - **bedroom_count, bathroom_count**: Số phòng
        - **house_direction**: Hướng nhà
        - **region**: Vùng miền (Bắc, Trung, Nam)
        - **year_month**: Thời gian đăng tin
        """)
    
    st.markdown("---")
    st.info("💡 **Hướng dẫn:** Nhập yêu cầu vào khung chat. AI sẽ tạo code. Bạn có thể chỉnh sửa màu sắc, tiêu đề trước khi nhấn Phê duyệt để vẽ biểu đồ.")

# --- GIAO DIỆN CHÍNH (CHAT LỊCH SỬ) ---
st.title("📊 Trực Quan Hóa Dữ Liệu Bất Động Sản AI")

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image":
            image_data = base64.b64decode(msg["content"])
            st.image(image_data, use_container_width=True)
        else:
            st.markdown(msg["content"])

# --- KHU VỰC CHỜ PHÊ DUYỆT CODE ---
if st.session_state.is_pending:
    st.markdown("### ⚠️ Cần Phê Duyệt Code")
    with st.container(border=True):
        st.info(f"**Giải thích từ AI:** {st.session_state.current_explanation}")
        
        # Hộp chỉnh sửa code (Người dùng có quyền can thiệp)
        edited_code = st.text_area(
            "Mã Python (Bạn có thể chỉnh sửa trước khi chạy):", 
            value=st.session_state.current_code, 
            height=250
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("✅ Phê duyệt & Chạy", type="primary", use_container_width=True):
                with st.spinner("Đang thực thi mã cục bộ..."):
                    result = api_client.execute_local_code(edited_code)
                    
                    if result["status"] == "success":
                        # Lưu log thành công
                        api_client.log_system_action(
                            st.session_state.current_prompt,
                            st.session_state.original_code,
                            edited_code,
                            "Success"
                        )
                        # Thêm ảnh vào lịch sử chat
                        st.session_state.messages.append({"role": "assistant", "type": "image", "content": result["image_base64"]})
                        st.session_state.is_pending = False
                        st.rerun()
                    else:
                        # Lưu log thất bại
                        error_msg = result["error_message"]
                        api_client.log_system_action(
                            st.session_state.current_prompt,
                            st.session_state.original_code,
                            edited_code,
                            "Error",
                            error_msg
                        )
                        st.error(f"Lỗi thực thi mã:\n```python\n{error_msg}\n```")
                        st.session_state.current_code = edited_code # Giữ lại code đã sửa để người dùng thử lại
        
        with col2:
            if st.button("❌ Hủy bỏ"):
                st.session_state.is_pending = False
                st.rerun()

# --- KHU VỰC TẢI XUỐNG PDF ---
# Tìm biểu đồ gần nhất trong lịch sử để cho phép tải xuống
for msg in reversed(st.session_state.messages):
    if msg.get("type") == "image":
        image_bytes = base64.b64decode(msg["content"])
        
        # Chuyển đổi PNG sang PDF trong bộ nhớ
        image = Image.open(BytesIO(image_bytes))
        pdf_buffer = BytesIO()
        image.convert('RGB').save(pdf_buffer, format='PDF')
        
        st.download_button(
            label="📥 Tải biểu đồ gần nhất (PDF)",
            data=pdf_buffer.getvalue(),
            file_name="bieu_do_bds.pdf",
            mime="application/pdf"
        )
        break

# --- KHUNG NHẬP YÊU CẦU CHAT ---
# Khóa khung chat nếu đang có code chờ phê duyệt
prompt = st.chat_input("VD: Vẽ biểu đồ cột so sánh giá nhà trung bình ở 3 vùng Bắc, Trung, Nam", disabled=st.session_state.is_pending)

if prompt:
    # 1. Hiển thị tin nhắn người dùng
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.current_prompt = prompt
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Gọi AI tạo code
    with st.chat_message("assistant"):
        with st.spinner("Đang phân tích yêu cầu và viết code..."):
            ai_response = api_client.generate_ai_code(prompt)
            
            if ai_response:
                # Kích hoạt trạng thái chờ phê duyệt
                st.session_state.is_pending = True
                st.session_state.current_code = ai_response["code"]
                st.session_state.original_code = ai_response["code"]
                st.session_state.current_explanation = ai_response["explanation"]
                st.rerun() # Tải lại giao diện để hiển thị khu vực phê duyệt