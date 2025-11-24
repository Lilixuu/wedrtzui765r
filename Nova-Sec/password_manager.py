# Wir importieren die Funktionen zum Verschlüsseln und Entschlüsseln von Passwörtern
from security import encrypt_password, decrypt_password

# --- Passwort speichern ---
def save_password(title: str, password: str, key: bytes) -> str:
    """
    Verschlüsselt das Passwort und gibt es als Base64-String zurück.
    """
    token = encrypt_password(key, password)   # Passwort wird verschlüsselt → bytes
    return token.decode()                     # Bytes werden in einen String (Base64) umgewandelt

# --- Passwort laden (alle Passwörter entschlüsseln) ---
def load_passwords(data: dict, key: bytes) -> dict:
    """
    Entschlüsselt alle Passwörter in einem Dictionary.
    
    data = {title: {"Name": name, "Passwort": verschlüsselt_str, "Notizen": notes}}
    Rückgabe: {title: {"Name": name, "Passwort": plain_pwd, "Notizen": notes}}
    """
    decrypted = {}  # Neues Dictionary für entschlüsselte Passwörter

    # Gehe jedes Passwort durch
    for title, info in data.items():
        try:
            pwd = decrypt_password(key, info["Passwort"].encode())  # Entschlüsseln
        except Exception:
            pwd = "Fehler"  # Falls etwas schiefgeht

        # Neues Dictionary mit Name, entschlüsseltem Passwort und Notizen
        decrypted[title] = {
            "Name": info.get("Name", ""),
            "Passwort": pwd,
            "Notizen": info.get("Notizen", "")
        }

    return decrypted  # Alles zurückgeben
