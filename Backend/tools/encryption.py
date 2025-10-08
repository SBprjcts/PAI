from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

# Load generated key
key = os.getenv('CRYPTOGRAPHY_KEY')
cipher = Fernet(key)

def encrypt(text: str) -> str:
    text = str(text)
    token = cipher.encrypt(text.encode())
    return token

def decrypt(token: str) -> str:
    data = cipher.decrypt(token.decode())
    text = data.decode()
    return text
