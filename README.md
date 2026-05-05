# BÁO CÁO BÀI THỰC HÀNH 2: XÂY DỰNG HỆ THỐNG MIKA CHAT AI
## (FastAPI - Streamlit - Firebase)

---

## 1. Thông tin sinh viên
* **Họ và tên:** Nguyễn Lê Ngọc Quý
* **MSSV:** 24120422
* **Môn học:** Tư duy tính toán
* **Trường:** Đại học Khoa học Tự nhiên – ĐHQG-HCM
* **Đề tài:** Xây dựng ứng dụng Chatbot phân loại nội dung độc hại tích hợp cơ sở dữ liệu và xác thực người dùng.

---

## 2. Mô tả bài toán
Trong bối cảnh các nền tảng trực tuyến ngày càng phát triển, việc kiểm soát nội dung độc hại là một vấn đề quan trọng. Bài thực hành này xây dựng hệ thống chatbot có khả năng:
* **Phân loại nội dung:** Tự động nhận diện tin nhắn độc hại hoặc không độc hại.
* **Lưu trữ lịch sử:** Quản lý lịch sử trò chuyện riêng biệt theo từng tài khoản người dùng.
* **Xác thực bảo mật:** Đảm bảo quyền riêng tư thông qua hệ thống đăng nhập.

---

## 3. Kiến trúc hệ thống
Hệ thống được xây dựng theo mô hình **3 lớp (3-tier architecture)**:

### 3.1 Frontend (Streamlit)
* Xây dựng giao diện người dùng trực quan bằng thư viện Streamlit.
* **Chức năng:** Đăng ký/đăng nhập, gửi tin nhắn, hiển thị lịch sử và giao tiếp với Backend qua API.

### 3.2 Backend (FastAPI)
* Xử lý logic chính bằng Framework FastAPI.
* **Chức năng:** Nhận request, xác thực Token, gọi mô hình AI và kết nối Database.

### 3.3 Database (Firebase)
* **Firebase Authentication:** Quản lý đăng nhập bằng Email/Password hoặc Google.
* **Cloud Firestore:** Lưu trữ dữ liệu hội thoại dưới dạng NoSQL.

---

## 4. Thiết kế cơ sở dữ liệu
Dữ liệu được tổ chức trên **Firestore** theo cấu trúc phân cấp:

> **chats (collection)**  
> └── **{uid} (document)**  
>      └── **messages (sub-collection)**  
>           ├── message_id_1 { role, content, ts }  
>           └── ...

### 4.1 Các trường dữ liệu trong messages:
* **role:** Xác định vai trò gửi là `user` hoặc `assistant`.
* **content:** Nội dung văn bản của tin nhắn.
* **ts (timestamp):** Thời gian gửi để sắp xếp hội thoại đúng thứ tự.

---

## 5. Mô hình AI
Hệ thống tích hợp mô hình Deep Learning từ thư viện **Transformers**:

* **Thành phần:** Sử dụng `AutoTokenizer` để tiền xử lý và `AutoModelForSequenceClassification` để phân loại.
* **Mô hình gốc:** `unitary/toxic-bert` từ Hugging Face.[cite: 5]
* **Logic phân loại:**
    * Chuyển văn bản thành Tensor.
    * Dự đoán xác suất qua mô hình BERT.
    * Áp dụng ngưỡng (Threshold) **0.5**:
        * **> 0.5**: Tin nhắn độc hại 🛑
        * **≤ 0.5**: Tin nhắn lịch sự ✅

---

## 6. Công nghệ sử dụng
| Thành phần | Công nghệ |
| :--- | :--- |
| **Backend** | FastAPI |
| **Frontend** | Streamlit |
| **AI Model** | PyTorch + Transformers (`toxic-bert`) |
| **Database** | Firebase Firestore |
| **Authentication** | Firebase Auth |
| **Config** | OmegaConf |

---

## 7. Cấu trúc mã nguồn

### 7.1 File `requirements.txt`
```text
fastapi
uvicorn
streamlit
requests
torch
transformers
pyrebase4
firebase-admin
omegaconf
```

### 7.2 Backend Logic (`backend/main.py`)
Đoạn mã xử lý phân loại độc hại:
```python
def __call__(self, message):
    inputs = self.tokenizer(message, return_tensors="pt")
    with torch.no_grad():
        logits = self.model(**inputs).logits
    probabilities = torch.sigmoid(logits)[0]
    return "toxic" if probabilities[0].item() > 0.5 else "safe"
```

---

## 8. Quy trình hoạt động
1. Người dùng đăng nhập và nhận Token từ Firebase.
2. Frontend gửi request kèm header `Authorization` chứa Token.
3. Backend xác thực Token và xử lý tin nhắn bằng AI Model.
4. AI trả về nhãn, Backend lưu hội thoại vào Firestore.
5. Frontend hiển thị phản hồi cho người dùng.

---

## 9. Hướng dẫn cài đặt và chạy

### 9.1 Cài thư viện
```bash
py -m pip install -r requirements.txt
```

### 9.2 Chạy Backend
```bash
cd backend
py main.py
```

### 9.3 Chạy Frontend
```bash
cd frontend
py -m streamlit run app.py
```

---

## 10. Kết quả, Hạn chế và Phát triển

### Kết quả
* Xây dựng thành công Chatbot Full-stack có khả năng nhận diện nội dung xấu và lưu trữ dữ liệu theo người dùng.

### Hạn chế
* Mô hình `toxic-bert` chủ yếu xử lý tiếng Anh, độ chính xác với tiếng Việt chưa tối ưu.
* Chưa có tính năng chat real-time.

### Hướng phát triển
* Fine-tune mô hình với tập dữ liệu tiếng Việt.
* Triển khai hệ thống lên Cloud (AWS/GCP).

---

## 11. Video Demo
Link: https://drive.google.com/drive/folders/1ROHJQbF3dcNHXmzqmSzaQdylThQk83yR?hl=vi

---

## 12. Kết luận
Bài thực hành cung cấp kiến thức nền tảng về việc xây dựng ứng dụng thông minh, kết hợp giữa lập trình Web API và AI, giúp sinh viên làm quen với quy trình phát triển sản phẩm thực tế.
