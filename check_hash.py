from werkzeug.security import check_password_hash
from app.core.security import get_password_hash

h = "scrypt:32768:8:1$aVihCc0k9gkdndO8$835e26fd641498f6e7608edce6ca76dc3973de2326906200553e3a94299b170c2f884780c081f64030f100947aa8e3f234bb7accaa8737c474870d850ae0883c"

for candidate in ["password123", "password", "123456", "admin", "12345678", "AdminPassword123!"]:
    res = check_password_hash(h, candidate)
    if res:
        print(f"La clave original de ese hash es: {candidate}")
        break
else:
    print("Ninguna de esas era. Vamos a actualizar la clave en SQLite a bcrypt de 'password123'.")
