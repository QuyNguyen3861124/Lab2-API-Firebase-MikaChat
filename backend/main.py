import torch
import pyrebase
import firebase_admin
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from firebase_admin import credentials, firestore, auth as admin_auth
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from datetime import datetime, timezone
from pathlib import Path
from omegaconf import OmegaConf
import uvicorn
from contextlib import asynccontextmanager
from logger import logger

BASE_DIR = Path(__file__).resolve().parent
config = OmegaConf.load(BASE_DIR / "config.yaml")

# 1. Cấu hình Firebase
firebase_config = {
    "apiKey": "AIzaSyBM3cE68-pMvO_YNaxhp16YZfjh5H_Tivg",
    "authDomain": "lab2-fb07d.firebaseapp.com",
    "projectId": "lab2-fb07d",
    "databaseURL": "https://lab2-fb07d.firebaseio.com",
    "storageBucket": "lab2-fb07d.firebasestorage.app",
    "messagingSenderId": "944359662903",
    "appId": "1:944359662903:web:a2539d79e3d138b4ee66b2"
}
firebase = pyrebase.initialize_app(firebase_config)
pyrebase_auth = firebase.auth()

cred = credentials.Certificate(BASE_DIR / "firebase-service-account.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin đã kết nối")
db = firestore.client()

# 2. Khởi tạo AI Model (Tải ngay khi chạy script)
class ToxicityClassification:
    def __init__(self):
        logger.info("Bắt đầu tải mô hình AI...")
        model_name = config.model_path
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        # Warm-up: Chạy thử để model nằm sẵn trên RAM
        self("Kiểm tra khởi động")
        logger.info("Mô hình AI đã sẵn sàng!")

    def __call__(self, message):
        inputs = self.tokenizer(message, return_tensors="pt")
        with torch.no_grad():
            logits = self.model(**inputs).logits
        probabilities = torch.sigmoid(logits)[0]
        return "toxic" if probabilities[0].item() > 0.5 else "safe"

classifier = ToxicityClassification()

# 3. Quản lý vòng đời FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Model đã được load ở trên, tại đây ta có thể kiểm tra lại nếu cần
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

class AuthRequest(BaseModel):
    email: str
    password: str

class ChatRequest(BaseModel):
    message: str

def verify_token(authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]
        uid = admin_auth.verify_id_token(token)["uid"]
        logger.debug(f"Token hợp lệ cho {uid}")
        return uid
    except Exception as e:
        logger.warning(f"Token không hợp lệ: {str(e)[:30]}")
        raise HTTPException(status_code=401)

# 4. Các cổng API
@app.post("/auth/login")
def login(req: AuthRequest):
    try:
        logger.debug(f"Đang đăng nhập Firebase: {req.email}")
        user = pyrebase_auth.sign_in_with_email_and_password(req.email, req.password)
        logger.info(f"Đăng nhập Firebase thành công: {req.email}")
        return {"email": req.email, "uid": user['localId'], "idToken": user['idToken']}
    except Exception as e:
        logger.warning(f"Đăng nhập Firebase thất bại: {req.email} - {str(e)[:50]}")
        raise HTTPException(status_code=401)

@app.post("/auth/signup")
def signup(req: AuthRequest):
    try:
        logger.debug(f"Đang đăng ký Firebase: {req.email}")
        user = pyrebase_auth.create_user_with_email_and_password(req.email, req.password)
        logger.info(f"Đăng ký Firebase thành công: {req.email}")
        return {"email": req.email, "uid": user['localId']}
    except Exception as e:
        logger.warning(f"Đăng ký Firebase thất bại: {req.email} - {str(e)[:50]}")
        raise HTTPException(status_code=400)

@app.post("/chat")
def chat(req: ChatRequest, uid: str = Depends(verify_token)):
    user_msg = req.message 
    label = classifier(user_msg)
    bot_reply = "Tin nhắn độc hại! 🛑" if label == "toxic" else "Tin nhắn lịch sự ✅"
    ts = datetime.now(timezone.utc)
    
    try:
        messages_ref = db.collection("chats").document(uid).collection("messages")
        messages_ref.add({"role": "user", "content": user_msg, "ts": ts})
        messages_ref.add({"role": "assistant", "content": bot_reply, "ts": ts})
        logger.info(f"📤 [{label.upper()}] {uid}: {user_msg[:40]}...")
    except Exception as e:
        logger.error(f"✗ Lỗi lưu Firebase: {str(e)}")
        raise HTTPException(status_code=500)
    
    return {"reply": bot_reply}

@app.get("/chat/messages")
def get_messages(limit: int = 8, uid: str = Depends(verify_token)):
    try:
        logger.debug(f"📥 Đang lấy {limit} tin nhắn từ Firebase cho {uid}...")
        messages_ref = db.collection("chats").document(uid).collection("messages")
        docs = messages_ref.order_by("ts", direction=firestore.Query.DESCENDING).limit(limit).stream()
        messages = []
        for doc in docs:
            data = doc.to_dict()
            ts_value = data.get("ts")
            if hasattr(ts_value, "isoformat"):
                ts_value = ts_value.isoformat()
            messages.append({
                "role": data.get("role"),
                "content": data.get("content"),
                "ts": ts_value,
            })
        logger.info(f"✓ Lấy {len(messages)} tin nhắn từ Firebase")
        return {"messages": list(reversed(messages))}
    except Exception as e:
        logger.error(f"✗ Lỗi truy vấn Firebase: {str(e)}")
        raise HTTPException(status_code=500)

@app.get("/login_google", response_class=HTMLResponse)
def login_google():
    return """
    <html>
    <body style="text-align:center; padding-top:100px; font-family:sans-serif;">
        <button id="btn" style="padding:15px 30px; background:#4285F4; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold;">NHẤN ĐỂ XÁC THỰC GOOGLE</button>
        <script src="https://www.gstatic.com/firebasejs/9.6.1/firebase-app-compat.js"></script>
        <script src="https://www.gstatic.com/firebasejs/9.6.1/firebase-auth-compat.js"></script>
        <script>
            const firebaseConfig = { apiKey: "AIzaSyBM3cE68-pMvO_YNaxhp16YZfjh5H_Tivg", authDomain: "lab2-fb07d.firebaseapp.com" };
            firebase.initializeApp(firebaseConfig);
            document.getElementById('btn').onclick = () => {
                const provider = new firebase.auth.GoogleAuthProvider();
                firebase.auth().signInWithPopup(provider).then(res => {
                    res.user.getIdToken().then(token => {
                        window.location.replace("http://localhost:8501/?token=" + token + "&email=" + encodeURIComponent(res.user.email));
                    });
                });
            };
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Khởi động Chat App Backend...")
    logger.info("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)