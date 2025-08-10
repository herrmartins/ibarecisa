from .base import *

DEBUG = False
SECRET_KEY = "test-secret"
ALLOWED_HOSTS = ["*"]

from pathlib import Path, PurePath
BASE_DIR = Path(__file__).resolve().parents[2]
TMP_DIR = BASE_DIR / "tmp_test"
TMP_DIR.mkdir(exist_ok=True)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": TMP_DIR / "db.sqlite3",
        "TEST": {"NAME": TMP_DIR / "db_test.sqlite3"},
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
MEDIA_ROOT = TMP_DIR / "media"
