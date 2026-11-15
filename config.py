import os

from dotenv import load_dotenv


load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} not found in .env")
    return value


def _boolean(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


DATABASE_URL = _required("DATABASE_URL")
SECRET_KEY = _required("SECRET_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SPEECH_PROVIDER = os.getenv("SPEECH_PROVIDER", "browser").strip().lower()
PRONUNCIATION_QUEUE_NAME = os.getenv(
    "PRONUNCIATION_QUEUE_NAME", "interviewiq:pronunciation"
)
PRONUNCIATION_PROVIDER = os.getenv(
    "PRONUNCIATION_PROVIDER", "local_wav2vec2"
).strip().lower()
LOCAL_PRONUNCIATION_MODEL = os.getenv(
    "LOCAL_PRONUNCIATION_MODEL",
    "facebook/wav2vec2-lv-60-espeak-cv-ft",
)
AUDIO_RETENTION_SECONDS = int(os.getenv("AUDIO_RETENTION_SECONDS", "900"))
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
AZURE_SPEECH_LANGUAGE = os.getenv("AZURE_SPEECH_LANGUAGE", "en-US")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "2880")
)
COOKIE_SECURE = _boolean("COOKIE_SECURE")
AUTO_CREATE_TABLES = _boolean("AUTO_CREATE_TABLES")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")
SMTP_USE_TLS = _boolean("SMTP_USE_TLS", default=True)
SENTRY_DSN = os.getenv("SENTRY_DSN")
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "production")
SENTRY_TRACES_SAMPLE_RATE = float(
    os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0")
)
