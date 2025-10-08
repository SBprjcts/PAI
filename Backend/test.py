from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

# Generate a key once and store it securely (e.g. environment variable, key vault)
key = os.getenv('CRYPTOGRAPHY_KEY')
cipher = Fernet(key)

# Encrypt
token = cipher.encrypt(b"My secret data")

# Decrypt
data = cipher.decrypt(token)
print(data.decode())  # "My secret data"
