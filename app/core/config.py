import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        # jwt token
        self.JWT_ALGORITHM = os.getenv("JWT_ALRORITHM", "HS256")
        self.JWT_SECRETE_KEY = os.getenv("JWT_SECRETE_KEY", "")
        self.JWT_TOKEN_EXPIRE_MINUTES = float(os.getenv("JWT_TOKEN_EXPIRE_MINUTES", "60"))


settings = Settings()