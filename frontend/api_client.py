import requests

API_BASE = "http://localhost:8000"

def signup(email: str, password: str):
    r = requests.post(f"{API_BASE}/auth/signup", json={"email": email, "password": password})
    r.raise_for_status()
    return r.json()

def login(email: str, password: str):
    r = requests.post(f"{API_BASE}/auth/login", json={"email": email, "password": password}, timeout=20)
    r.raise_for_status()
    return r.json()

def get_messages(id_token: str, limit: int = 8):
    r = requests.get(f"{API_BASE}/chat/messages", params={"limit": limit}, headers={"Authorization": f"Bearer {id_token}"})
    r.raise_for_status()
    return r.json()

def send_chat(token, message):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_BASE}/chat", json={"message": message}, headers=headers, timeout=20)
    return response.json()