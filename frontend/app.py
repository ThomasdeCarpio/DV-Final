import streamlit as st
import base64
from io import BytesIO
from PIL import Image
import api_client

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="VN Real Estate Analytics", page_icon="🏢", layout="wide")

# --- KHỞI TẠO SESSION STATE ---
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "Tư vấn chung" # Mặc định ban đầu
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Chào bạn! Tôi có thể tư vấn hoặc vẽ biểu đồ giúp bạn."}]
if "is_pending" not in st.session_state: st.session_state.is_pending = False
if "current_code" not in st.session_state: st.session_state.current_code = ""
if "original_code" not in st.session_state: st.session_state.original_code = ""
if "current_explanation" not in st.session_state: st.session_state.current_explanation = ""
if "current_prompt" not in st.session_state: st.session_state.current_prompt = ""

# --- GIAO DIỆN SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Bảng Điều Khiển")
    
    # Sử dụng 'key' để Streamlit tự động ghi nhớ lựa chọn vào session_state
    st.radio(
        "🚀 Chọn chế độ hoạt động:",
        options=["Tư vấn chung", "Vẽ biểu đồ"],
        key="app_mode", 
        disabled=st.session_state.is_pending # Khóa khi đang đợi phê duyệt code
    )
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
st.title(f"🏢 AI Real Estate Agent - {st.session_state.app_mode}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image":
            st.image(base64.b64decode(msg["content"]), use_container_width=True)
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
                        api_client.log_system_action(
                            st.session_state.current_prompt,
                            st.session_state.original_code,
                            edited_code,
                            "Success"
                        )
                        st.session_state.messages.append({"role": "assistant", "type": "image", "content": result["image_base64"]})
                        st.session_state.is_pending = False
                        st.rerun()
                    else:
                        error_msg = result["error_message"]
                        api_client.log_system_action(
                            st.session_state.current_prompt,
                            st.session_state.original_code,
                            edited_code,
                            "Error",
                            error_msg
                        )
                        st.error(f"Lỗi thực thi mã:\n```python\n{error_msg}\n```")
                        st.session_state.current_code = edited_code
        
        with col2:
            if st.button("❌ Hủy bỏ"):
                st.session_state.is_pending = False
                st.rerun()

# --- KHU VỰC TẢI XUỐNG PDF ---
for msg in reversed(st.session_state.messages):
    if msg.get("type") == "image":
        image_bytes = base64.b64decode(msg["content"])
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

# --- CẤU HÌNH INPUT & LOGIC PHÂN NHÁNH ---
st.markdown("---")

# Khởi tạo mặc định để tránh NameError
selected_fields, chart_type, color_scheme = [], "Tự động", "Tự động"

# 1. Chỉ hiển thị Tùy chọn nâng cao nếu đang ở chế độ "Vẽ biểu đồ"
if st.session_state.app_mode == "Vẽ biểu đồ":
    pop_col, _ = st.columns([1, 4])
    with pop_col:
        with st.popover("➕ Tùy chọn nâng cao"):
            st.markdown("### 🛠️ Cấu hình biểu đồ nhanh")
            selected_fields = st.multiselect(
                "Chọn trường dữ liệu:",
                options=['price', 'area', 'price_per_m2', 'bedroom_count', 'bathroom_count', 'house_direction', 'region', 'property_type_name', 'province_name', 'year_month', 'total_rooms']
            )
            chart_type = st.selectbox("Loại biểu đồ:", options=['Tự động', 'Cột (Bar)', 'Đường (Line)', 'Phân tán (Scatter)', 'Tròn (Pie)'])
            color_scheme = st.selectbox("Tông màu:", options=['Tự động', 'Vibrant', 'Pastel', 'High Contrast'])

# 2. Khung nhập yêu cầu
prompt = st.chat_input("Nhập yêu cầu hoặc hướng dẫn sửa code tại đây...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if st.session_state.app_mode == "Tư vấn chung":
            with st.spinner("AI đang suy nghĩ..."):
                answer = api_client.get_general_chat(prompt)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.markdown(answer)
        else:
            # Trong khối NHÁNH 2 (V2 STEP 3)
            if st.session_state.is_pending:
                with st.spinner("AI đang chỉnh sửa mã nguồn..."):
                    ai_response = api_client.modify_ai_code(st.session_state.current_code, prompt)
                    if ai_response:
                        # THÊM DÒNG NÀY: Để lưu lại phản hồi của AI vào lịch sử chat
                        st.session_state.messages.append({"role": "assistant", "content": f"Đã cập nhật code: {ai_response['explanation']}"})
                        
                        st.session_state.current_explanation = ai_response["explanation"]
                        st.session_state.current_code = ai_response["code"]
                        st.rerun()
            else:
                # NẾU LÀ YÊU CẦU MỚI HOÀN TOÀN -> GỌI API TẠO MỚI (Logic cũ)
                full_prompt = prompt
                meta = []
                if selected_fields: meta.append(f"Fields: {selected_fields}")
                if chart_type != "Tự động": meta.append(f"Chart: {chart_type}")
                if color_scheme != "Tự động": meta.append(f"Color: {color_scheme}")
                if meta: full_prompt += "\n(Yêu cầu: " + "; ".join(meta) + ")"

                with st.spinner("Đang viết code mới..."):
                    ai_response = api_client.generate_ai_code(full_prompt)
                    if ai_response:
                        st.session_state.is_pending = True
                        st.session_state.current_prompt = full_prompt
                        st.session_state.current_code = ai_response["code"]
                        st.session_state.original_code = ai_response["code"]
                        st.session_state.current_explanation = ai_response["explanation"]
                        st.rerun()