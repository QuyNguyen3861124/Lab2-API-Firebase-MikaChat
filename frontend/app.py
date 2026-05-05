import streamlit as st
from collections import deque
from api_client import signup, login, get_messages, send_chat

st.set_page_config(page_title="Mika Chat", layout="wide")

# CSS: Căn lề tin nhắn & Ẩn hoàn toàn icon "đầu"
st.markdown("""
<style>
    /* User bên phải */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        flex-direction: row-reverse !important;
        text-align: right !important;
    }
    /* Ẩn icon người/robot */
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
        display: none;
    }
    /* Bong bóng chat */
    [data-testid="stChatMessageContent"] {
        border-radius: 15px;
        padding: 10px 15px;
        background-color: #f1f3f4;
        display: inline-block;
    }
    /* User message background */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
        background-color: #007bff !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

if "user" not in st.session_state: st.session_state.user = None
if "messages" not in st.session_state: st.session_state.messages = deque([], maxlen=8)
if "show_signup" not in st.session_state: st.session_state.show_signup = False

# Hứng dữ liệu Google
if "token" in st.query_params and "email" in st.query_params and not st.session_state.user:
    st.session_state.user = {"email": st.query_params["email"], "idToken": st.query_params["token"]}
    st.query_params.clear()

# GIAO DIỆN CHÍNH
if st.session_state.user:
    if not st.session_state.get("loaded_messages"):
        try:
            data = get_messages(st.session_state.user["idToken"])
            for msg in data.get("messages", []):
                st.session_state.messages.append(msg)
        except Exception:
            st.warning("Không tải được lịch sử chat.")
        st.session_state.loaded_messages = True

    col_l, col_r = st.columns([1, 1])
    with col_l: st.markdown("### Mika Chat")
    with col_r: 
        st.markdown(f"<p style='text-align: right;'>👤 {st.session_state.user['email']}</p>", unsafe_allow_html=True)
        if st.button("Đăng xuất"):
            st.session_state.user = None
            st.session_state.loaded_messages = False
            st.session_state.messages.clear()
            st.rerun()
    st.divider()

    for msg in list(st.session_state.messages):
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
        
    prompt = st.chat_input("Nhập tin nhắn...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        try:
            res = send_chat(st.session_state.user["idToken"], prompt)
            st.session_state.messages.append({"role": "assistant", "content": res["reply"]})
            st.rerun()
        except Exception as e: 
            st.error(f"Lỗi Backend: {str(e)}")
            # Remove the user message if failed
            st.session_state.messages.pop()

else:
    # KHÔI PHỤC KHUNG ĐĂNG NHẬP / ĐĂNG KÝ
    st.markdown("<h1 style='text-align: center;'>Mika Chat</h1>", unsafe_allow_html=True)
    if st.session_state.show_signup:
        with st.form("signup"):
            email = st.text_input("Email Đăng ký")
            pw = st.text_input("Mật khẩu", type="password")
            if st.form_submit_button("Tạo tài khoản"):
                try: signup(email, pw); st.success("Xong! Hãy đăng nhập"); st.session_state.show_signup = False; st.rerun()
                except: st.error("Lỗi đăng ký")
        if st.button("Đã có tài khoản?"): st.session_state.show_signup = False; st.rerun()
    else:
        with st.form("login"):
            email = st.text_input("Email")
            pw = st.text_input("Mật khẩu", type="password")
            if st.form_submit_button("Đăng nhập"):
                try: st.session_state.user = login(email, pw); st.rerun()
                except Exception as e: st.error(f"Sai thông tin: {str(e)}")
        if st.button("Đăng ký tài khoản mới"): st.session_state.show_signup = True; st.rerun()
        
        st.markdown('<a href="http://localhost:8000/login_google" target="_self" style="text-decoration:none;"><div style="width:100%; padding:10px; border:1px solid #dadce0; background:white; text-align:center; cursor:pointer; color:#3c4043; border-radius:5px; font-weight:bold;">Tiếp tục với Google</div></a>', unsafe_allow_html=True)
