from cryptography.fernet import Fernet

encryption_key = Fernet.generate_key().decode()
print(f"Generated encryption key: {encryption_key}")
