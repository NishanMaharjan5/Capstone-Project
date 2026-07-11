import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. Generate one with "
        "python3 -c \"import secrets; print(secrets.token_hex(32))\" and set it "
        "before starting the app."
    )

ALGORITHM = "HS256"
