from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "ecommerce"
    ES_HOST: str = "http://localhost:9200"
    ES_INDEX: str = "products"
    # Optional: when set, POST/PUT/DELETE endpoints require header X-API-Key
    ADMIN_API_KEY: str = ""
    # Comma-separated list of allowed frontend origins ("*" = any)
    CORS_ORIGINS: str = "*"
    # Public URL to ping so Render's free tier doesn't sleep (Render sets this)
    RENDER_EXTERNAL_URL: str = ""

    model_config = {
        "env_file": os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env"),
        "extra": "ignore",
    }


settings = Settings()
