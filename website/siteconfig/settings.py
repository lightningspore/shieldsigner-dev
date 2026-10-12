import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get("DEBUG", "1") == "1"
# This read-only site has no login, cookies or user sessions.
SECRET_KEY = os.environ.get("SECRET_KEY", "local-documentation-only-no-auth-or-sessions")
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver", "shieldsigner.dev", "www.shieldsigner.dev"]
INSTALLED_APPS = ["django.contrib.staticfiles", "knowledge"]
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware", "whitenoise.middleware.WhiteNoiseMiddleware", "django.middleware.common.CommonMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware"]
ROOT_URLCONF = "siteconfig.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.request"]}}]
DATABASES = {}
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
CONTENT_DIR = BASE_DIR / "content"
PUBLIC_DIR = BASE_DIR / "public"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
