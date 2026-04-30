from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    IntegerField,
    PasswordField,
    SubmitField,
    DateTimeLocalField,
    SelectField,
)
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf import FlaskForm
from wtforms import SubmitField

class DeleteForm(FlaskForm):
    submit = SubmitField("Supprimer")

# Formulaire de réservation de places
class ReservationForm(FlaskForm):
    name = StringField("Nom", validators=[DataRequired(), Length(max=80)])
    seats = IntegerField(
        "Nombre de places",
        validators=[DataRequired(), NumberRange(min=1, max=20)],
    )
    submit = SubmitField("Réserver")

# Formulaire de commentaire
class CommentForm(FlaskForm):
    author_name = StringField("Nom", validators=[DataRequired(), Length(max=80)])
    content = TextAreaField("Mon commentaire", validators=[DataRequired()])
    submit = SubmitField("Envoyer")

# Login admin
class LoginForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired()])
    password = PasswordField("Mot de passe", validators=[DataRequired()])
    submit = SubmitField("Se connecter")

# Formulaire de concert (admin)
class ConcertForm(FlaskForm):
    title = StringField("Titre", validators=[DataRequired()])
    date = DateTimeLocalField(
        "Date et heure",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()],
    )
    place = StringField("Lieu", validators=[DataRequired()])
    type = StringField("Type (Jazz, Rock...)", validators=[DataRequired()])
    total_seats = IntegerField(
        "Nombre total de places",
        validators=[DataRequired(), NumberRange(min=1)],
    )
    description = TextAreaField("Description")
    category_id = SelectField("Catégorie", coerce=int)
    submit = SubmitField("Enregistrer")

# Formulaire d’actualité (admin)
class NewsForm(FlaskForm):
    title = StringField("Titre", validators=[DataRequired()])
    content = TextAreaField("Contenu", validators=[DataRequired()])
    category_id = SelectField("Catégorie", coerce=int)
    submit = SubmitField("Enregistrer")
