import os


class Config:

    SECRET_KEY = os.getenv("SECRET_KEY")
    UPLOAD_FOLDER = 'static\images'

    SQLALCHEMY_DATABASE_URI = os.getenv("DB_URI")

    MAIL_SERVER= 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv('EMAIL')
    MAIL_PASSWORD = os.getenv('EMAIL_PASS')