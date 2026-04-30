from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Catégories pour actualités et concerts (Jazz, Rock, Electro, etc.)
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

# Concerts
class Concert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    place = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(80), nullable=False)  # ex: "Jazz", "Rock"
    total_seats = db.Column(db.Integer, nullable=False, default=100)
    reserved_seats = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    category = db.relationship("Category", backref="concerts")

    # Indique si le concert est passé
    @property
    def is_past(self):
        return self.date < datetime.now()

    # Places restantes pour la réservation
    @property
    def remaining_seats(self):
        return self.total_seats - self.reserved_seats

# Actualités musicales
class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    category = db.relationship("Category", backref="news")

# Commentaires sur les concerts passés
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_name = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    concert_id = db.Column(db.Integer, db.ForeignKey("concert.id"), nullable=False)
    concert = db.relationship("Concert", backref="comments")

# Utilisateur admin pour la partie Administration
class AdminUser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
