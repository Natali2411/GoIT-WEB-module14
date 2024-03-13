from dotenv.main import load_dotenv
from pydantic import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    sqlalchemy_database_url: str
    sqlalchemy_test_database_url: str
    rate_limit_requests_per_minute: int
    redis_host: str
    redis_port: int

    authjwt_secret_key: str
    authjwt_algorithm: str
    # authjwt_token_location: str

    cloudinary_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str

    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int
    mail_server: str

    secret_key: str
    algorithm: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
