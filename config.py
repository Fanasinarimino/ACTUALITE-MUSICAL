import os

class Config:
    # Clé secrète pour CSRF / sessions
    SECRET_KEY = "un_secret_au_hasard"
    # Connexion MariaDB (adapter user/password/host/db)
    SQLALCHEMY_DATABASE_URI = "mysql://fanasina:password@localhost/musique_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WTF_CSRF_ENABLED = True


