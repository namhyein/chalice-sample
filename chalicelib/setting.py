import os

# DEFAULT
STAGE = os.getenv("STAGE", "dev")
DOMAIN = (
    os.getenv("DOMAIN_PROD") if STAGE == "prod" else
    "http://localhost:3000" if STAGE == "local" else
    os.getenv("DOMAIN_DEV")
)

# AWS
AWS_REGION = os.getenv("AWS_REGION")
SLACK_QUEUE = os.getenv("SLACK_QUEUE")
BUCKET_NAME = os.getenv("BUCKET_NAME")

# MONGODB
MONGODB_HOSTNAME = os.getenv("MONGODB_HOSTNAME")
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")

# GOOGLE
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Wine&News Email
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Authentication
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

DEFAULT_HEADERS = {
    "Content-Type": "application/json",
}

