from cryptography.fernet import Fernet  # Für sichere Verschlüsselung
import base64                          # Um Bytes in lesbare Strings zu verwandeln
import hashlib                         # Für Hashing (SHA256)

# --- Master-Key zu Fernet-Key generieren ---
def generate_key_from_master(master_key: str) -> bytes:
    """
    Aus dem Master-Key wird ein Fernet-Key gemacht.
    Wir nutzen SHA256, um einen sicheren Hash zu erzeugen,
    und wandeln diesen dann in Base64, damit Fernet ihn nutzen kann.
    """
    hash = hashlib.sha256(master_key.encode()).digest()  # SHA256-Hash aus Master-Key
    fernet_key = base64.urlsafe_b64encode(hash)         # Base64 → Fernet-kompatibel
    return fernet_key

# --- Passwort verschlüsseln ---
def encrypt_password(key: bytes, password: str) -> bytes:
    """
    Verschlüsselt ein Passwort mit dem Fernet-Key.
    """
    f = Fernet(key)             # Fernet-Objekt mit Key erstellen
    token = f.encrypt(password.encode())  # Passwort in Bytes → verschlüsseln
    return token

# --- Passwort entschlüsseln ---
def decrypt_password(key: bytes, token: bytes) -> str:
    """
    Entschlüsselt ein verschlüsseltes Passwort mit dem Fernet-Key.
    """
    f = Fernet(key)           # Fernet-Objekt mit Key erstellen
    pwd = f.decrypt(token)    # Verschlüsselten Token wieder entschlüsseln
    return pwd.decode()       # Bytes → String zurück
