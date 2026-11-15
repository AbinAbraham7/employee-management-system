from getpass import getpass
from werkzeug.security import generate_password_hash

password = getpass("Enter admin password: ")

if len(password) < 5:
    print("Password must contain at least 12 characters.")
else:
    password_hash = generate_password_hash(
        password,
        method="pbkdf2:sha256"
    )

    print("\nGenerated hash:\n")
    print(password_hash)