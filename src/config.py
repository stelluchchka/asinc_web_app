from pydantic_settings import BaseSettings, SettingsConfigDict
from sanic import Sanic
from cors import add_cors_headers
from options import setup_options

SECRET_KEY = "gfdmhghif38yrf9ew0jkf32"

app = Sanic("MyApp", strict_slashes=False)
app.config.FORWARDED_SECRET = "gfdmhghif38yrf9ew0jkf32"
# app.config.REAL_IP_HEADER = "CF-Connecting-IP"
# app.config.PROXIES_COUNT = 2

# CORS
app.register_listener(setup_options, "before_server_start")
app.register_middleware(add_cors_headers, "response")


# DB
class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    @property
    def DATABASE_URL_asyncpg(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    def DATABASE_URL_psycopg2(self):
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
