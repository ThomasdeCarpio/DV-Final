import streamlit as st
import base64
from io import BytesIO
from PIL import Image
import api_client
import uuid # Cần thiết để định danh các cell trong dashboard

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="VN Real Estate Analytics", page_icon="🏢", layout="wide")

# --- KHỞI TẠO SESSION STATE ---
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "Tư vấn chung"
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Chào bạn! Tôi có thể tư vấn hoặc vẽ biểu đồ giúp bạn."}]
if "dashboard_cells" not in st.session_state:
    st.session_state.dashboard_cells = [] # Lưu trữ kết quả báo cáo (V3)
if "is_pending" not in st.session_state: st.session_state.is_pending = False
if "current_code" not in st.session_state: st.session_state.current_code = ""
if "original_code" not in st.session_state: st.session_state.original_code = ""
if "current_explanation" not in st.session_state: st.session_state.current_explanation = ""
if "current_prompt" not in st.session_state: st.session_state.current_prompt = ""
if "editor_version" not in st.session_state:
    st.session_state.editor_version = 0

# --- HÀM TRỢ GIÚP DASHBOARD (V3) ---
def move_cell(index, direction):
    new_index = index + direction
    if 0 <= new_index < len(st.session_state.dashboard_cells):
        st.session_state.dashboard_cells[index], st.session_state.dashboard_cells[new_index] = \
        st.session_state.dashboard_cells[new_index], st.session_state.dashboard_cells[index]

def delete_cell(index):
    st.session_state.dashboard_cells.pop(index)

def add_to_dashboard(cell_type, content, caption=""):
    st.session_state.dashboard_cells.append({
        "id": str(uuid.uuid4()),
        "type": cell_type,
        "content": content,
        "caption": caption,
        "editing": False
    })

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

# --- CHIA CỘT GIAO DIỆN CHÍNH (V3 SPLIT VIEW) ---
col_chat, col_dash = st.columns([4, 6])

# ==========================================
# CỘT TRÁI: AI AGENT & CHAT
# ==========================================
# ==========================================
# CỘT TRÁI: AI AGENT & CHAT (Hợp nhất Review vào Chat)
# ==========================================
with col_chat:
    st.title(f"💬 AI Agent")
    
    # CHIỀU CAO CỐ ĐỊNH CHO KHUNG CHAT ĐỂ TRÁNH CUỘN TRANG
    chat_container = st.container(height=650) 
    
    with chat_container:
        # 1. HIỂN THỊ LỊCH SỬ CHAT
        for i, msg in enumerate(st.session_state.messages):
            with st.chat_message(msg["role"]):
                if msg.get("type") == "image":
                    st.image(base64.b64decode(msg["content"]), use_container_width=True)
                else:
                    st.markdown(msg["content"])
                    if msg["role"] == "assistant" and i > 0:
                        if st.button("💾 Lưu vào Dashboard", key=f"save_msg_{i}"):
                            add_to_dashboard("markdown", msg["content"])
                            st.toast("Đã thêm vào Dashboard!")

        # 2. KHU VỰC CHỜ PHÊ DUYỆT (NẰM TRONG CHAT CONTAINER)
        if st.session_state.is_pending:
            with st.chat_message("assistant"):
                st.warning("⚠️ **Đang chờ phê duyệt mã nguồn**")
                st.info(f"**Giải thích:** {st.session_state.current_explanation}")
                
                # Editor nằm ngay trong khung chat
                edited_code = st.text_area(
                    "Chỉnh sửa mã Python:", 
                    value=st.session_state.current_code, 
                    height=250,
                    key=f"editor_{st.session_state.editor_version}" 
                )
                
                c1, c2 = st.columns([1, 1])
                with c1:
                    if st.button("✅ Phê duyệt & Chạy", type="primary", use_container_width=True):
                        # Spinner cũng xuất hiện tại đây
                        with st.spinner("Đang thực thi..."):
                            result = api_client.execute_local_code(edited_code)
                            if result["status"] == "success":
                                add_to_dashboard("chart", result["image_base64"], st.session_state.current_prompt)
                                st.session_state.is_pending = False
                                st.success("Đã thêm vào Dashboard!")
                                st.rerun()
                            else:
                                st.error(f"Lỗi: {result['error_message']}")
                with c2:
                    if st.button("❌ Hủy bỏ", use_container_width=True):
                        st.session_state.is_pending = False
                        st.rerun()

    # 3. KHU VỰC NHẬP LIỆU (Input & Logic Phân Nhánh)
    st.markdown("---")
    # Tùy chọn nâng cao (giữ nguyên)
    selected_fields, chart_type, color_scheme = [], "Tự động", "Tự động"
    if st.session_state.app_mode == "Vẽ biểu đồ":
        pop_col, _ = st.columns([1, 2])
        with pop_col:
            with st.popover("➕ Tùy chọn"):
                selected_fields = st.multiselect("Trường:", options=['price', 'area', 'region', 'property_type_name', 'province_name', 'year_month', 'total_rooms'])
                chart_type = st.selectbox("Loại:", options=['Tự động', 'Bar', 'Line', 'Scatter', 'Pie'])
                color_scheme = st.selectbox("Màu:", options=['Tự động', 'Vibrant', 'Pastel'])

    prompt = st.chat_input("Nhập yêu cầu tại đây...")
    
    if prompt:
        # Thêm tin nhắn người dùng vào lịch sử
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Mở context của chat_container để hiển thị spinner tại đó
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                if st.session_state.app_mode == "Tư vấn chung":
                    with st.spinner("AI đang suy nghĩ..."):
                        answer = api_client.get_general_chat(prompt)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                        st.rerun()
                else:
                    if st.session_state.is_pending:
                        with st.spinner("AI đang chỉnh sửa mã nguồn..."):
                            ai_response = api_client.modify_ai_code(st.session_state.current_code, prompt)
                            if ai_response:
                                st.session_state.messages.append({"role": "assistant", "content": f"Đã cập nhật code: {ai_response['explanation']}"})
                                st.session_state.current_explanation = ai_response["explanation"]
                                st.session_state.current_code = ai_response["code"]
                                
                                st.session_state.editor_version += 1 
                                
                                st.rerun()
                    else:
                        # Logic tạo mới code
                        full_prompt = prompt
                        meta = []
                        if selected_fields: meta.append(f"Fields: {selected_fields}")
                        if chart_type != "Tự động": meta.append(f"Chart: {chart_type}")
                        if meta: full_prompt += f"\n(Yêu cầu: {'; '.join(meta)})"
                        
                        with st.spinner("AI đang thiết kế biểu đồ..."):
                            ai_response = api_client.generate_ai_code(full_prompt)
                            if ai_response:
                                st.session_state.is_pending = True
                                st.session_state.current_prompt = prompt
                                st.session_state.current_code = ai_response["code"]
                                st.session_state.original_code = ai_response["code"]
                                st.session_state.current_explanation = ai_response["explanation"]
                                st.rerun()

# ==========================================
# CỘT PHẢI: OUTPUT SCREEN (JUPYTER-LIKE)
# ==========================================
with col_dash:
    st.subheader("🖥️ Báo cáo phân tích (Dashboard)")
    
    if not st.session_state.dashboard_cells:
        st.info("Chưa có nội dung. Hãy vẽ biểu đồ hoặc thêm text cell để bắt đầu.")
    
    for i, cell in enumerate(st.session_state.dashboard_cells):
        with st.container(border=True):
            if cell["type"] == "chart":
                st.image(base64.b64decode(cell["content"]), use_container_width=True)
                st.caption(f"📊 {cell['caption']}")
            
            elif cell["type"] == "markdown":
                if cell.get("editing", False):
                    new_text = st.text_area("Chỉnh sửa Markdown:", value=cell["content"], key=f"edit_{cell['id']}")
                    if st.button("✔️ Lưu", key=f"save_{cell['id']}"):
                        st.session_state.dashboard_cells[i]["content"] = new_text
                        st.session_state.dashboard_cells[i]["editing"] = False
                        st.rerun()
                else:
                    st.markdown(cell["content"])

            # Toolbar điều khiển cell (V3 Phase 3 - Đã thêm nút Explain)
            t1, t2, t3, t4, t5, _ = st.columns([1, 1, 1, 1, 2, 4])
            with t1:
                if st.button("⬆️", key=f"up_{cell['id']}"): move_cell(i, -1); st.rerun()
            with t2:
                if st.button("⬇️", key=f"down_{cell['id']}"): move_cell(i, 1); st.rerun()
            with t3:
                if st.button("🗑️", key=f"del_{cell['id']}"): delete_cell(i); st.rerun()
            with t4:
                if cell["type"] == "markdown":
                    if st.button("✏️", key=f"btn_edit_{cell['id']}"):
                        st.session_state.dashboard_cells[i]["editing"] = True
                        st.rerun()
            with t5:
                # NÚT GIẢI THÍCH CHO BIỂU ĐỒ (V3 PHASE 3)
                if cell["type"] == "chart":
                    if st.button("🤖 Giải thích", key=f"explain_{cell['id']}", help="AI sẽ phân tích số liệu trên biểu đồ"):
                        with st.spinner("AI đang đọc biểu đồ..."):
                            analysis = api_client.explain_chart_image(cell["content"])
                            # Thêm một markdown cell ngay dưới chart này
                            st.session_state.dashboard_cells.insert(i + 1, {
                                "id": str(uuid.uuid4()),
                                "type": "markdown",
                                "content": f"**📊 Phân tích số liệu:**\n\n{analysis}",
                                "editing": False
                            })
                            st.rerun()

    if st.button("➕ Thêm Markdown Cell"):
        add_to_dashboard("markdown", "### Nhập nội dung...")
        st.session_state.dashboard_cells[-1]["editing"] = True
        st.rerun()