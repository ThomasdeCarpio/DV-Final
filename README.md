# 🏢 Trợ lý Phân tích Bất động sản Việt Nam (AI Agent)

Dự án sử dụng AI (Gemini) để tư vấn và tự động hóa việc vẽ biểu đồ phân tích thị trường bất động sản Việt Nam với quy trình: **AI tạo code -> Người dùng duyệt -> Thực thi cục bộ.**

## 🛠 1. Yêu cầu hệ thống
*   **Python:** Phiên bản 3.9 trở lên.
*   **Thư viện:** FastAPI, Streamlit, Pandas, Matplotlib, Seaborn, Google Generative AI.

## 🔑 2. Lấy Gemini API Key
1.  Truy cập **[Google AI Studio](https://aistudio.google.com/)**.
2.  Đăng nhập bằng tài khoản Google.
3.  Nhấn **"Get API key"** -> **"Create API key in new project"**.
4.  Sao chép mã API (có dạng `AIzaSy...`).

## ⚙️ 3. Cài đặt môi trường
1.  **Tạo file `.env`:** Trong thư mục `backend/`, tạo file tên `.env` và dán mã API vào:
    ```text
    GEMINI_API_KEY=dán_mã_của_bạn_vào_đây
    ```
2.  **Cài đặt thư viện:** Mở terminal và chạy lệnh:
    ```bash
    # Tại thư mục gốc
    pip install -r backend/requirements.txt
    pip install -r frontend/requirements.txt
    ```

## 🚀 4. Cách chạy ứng dụng

Bạn cần mở **2 terminal** song song:

### Terminal 1: Chạy Backend (FastAPI)
```bash
cd backend
uvicorn main:app --reload
```
*Backend chạy tại: http://localhost:8000*

### Terminal 2: Chạy Frontend (Streamlit)
```bash
cd frontend
streamlit run app.py
```
*Giao diện sẽ tự động mở trên trình duyệt tại: http://localhost:8501*

## 📖 5. Hướng dẫn sử dụng nhanh
1.  **Tư vấn:** Chọn chế độ "Tư vấn chung" để hỏi đáp về thị trường.
2.  **Vẽ biểu đồ:**
    *   Nhập yêu cầu (VD: "So sánh giá theo vùng miền").
    *   AI sẽ hiển thị mã Python và giải thích.
    *   Bạn có thể sửa code trực tiếp hoặc chat tiếp để AI sửa lại.
    *   Nhấn **"Phê duyệt & Chạy"** để hiển thị biểu đồ trên Dashboard (bên phải).
3.  **Báo cáo:** Sử dụng nút **"Giải thích"** trên biểu đồ để AI phân tích số liệu, sau đó tải báo cáo về dạng PDF.
