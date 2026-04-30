from flask_wtf.csrf import CSRFProtect
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

from config import Config
from models import db, Category, Concert, News, Comment, AdminUser
from forms import (
    ReservationForm,
    CommentForm,
    LoginForm,
    ConcertForm,
    NewsForm,
)
from forms import DeleteForm


app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "admin_login"

@app.context_processor
def inject_categories():
    from models import Category
    return dict(Category=Category)

@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))

# Commande simple pour créer la base et un admin par défaut
@app.cli.command("init-db")
def init_db():
    """Initialise la base de données et crée un admin par défaut."""
    db.drop_all()
    db.create_all()

    # Catégories de base
    jazz = Category(name="Jazz")
    rock = Category(name="Rock")
    electro = Category(name="Electro")
    db.session.add_all([jazz, rock, electro])

    # Admin par défaut
    admin = AdminUser(
        username="admin",
        password_hash=generate_password_hash("admin"),
    )
    db.session.add(admin)
    db.session.commit()
    print("Base initialisée avec admin/admin")

# Page d’accueil : X dernières actualités + X concerts à venir
@app.route("/")
def index():
    latest_news = News.query.order_by(News.created_at.desc()).limit(5).all()
    upcoming_concerts = (
        Concert.query.filter(Concert.date >= datetime.now())
        .order_by(Concert.date.asc())
        .limit(5)
        .all()
    )
    categories = Category.query.all()
    return render_template(
        "index.html",
        latest_news=latest_news,
        upcoming_concerts=upcoming_concerts,
        categories=categories,
    )

# Liste des concerts avec filtres
@app.route("/concerts")
def concerts_list():
    type_filter = request.args.get("type")
    place_filter = request.args.get("place")
    date_filter = request.args.get("date")  # format YYYY-MM-DD

    query = Concert.query

    if type_filter:
        query = query.filter(Concert.type == type_filter)
    if place_filter:
        query = query.filter(Concert.place.contains(place_filter))
    if date_filter:
        try:
            date_obj = datetime.strptime(date_filter, "%Y-%m-%d")
            query = query.filter(
                Concert.date >= date_obj,
                Concert.date < date_obj + timedelta(days=1),
            )
        except ValueError:
            pass

    concerts = query.order_by(Concert.date.asc()).all()
    return render_template("concerts_list.html", concerts=concerts)

# Détail d’un concert : réservation + commentaires + concerts passés
@app.route("/concert/<int:concert_id>", methods=["GET", "POST"])
def concert_detail(concert_id):
    concert = Concert.query.get_or_404(concert_id)
    reservation_form = ReservationForm()
    comment_form = CommentForm()

    # Traitement réservation
    if reservation_form.submit.data and reservation_form.validate_on_submit():
        requested_seats = reservation_form.seats.data
        if requested_seats <= concert.remaining_seats:
            concert.reserved_seats += requested_seats
            db.session.commit()
            flash("Réservation effectuée avec succès.", "success")
        else:
            flash("Pas assez de places disponibles.", "danger")
        return redirect(url_for("concert_detail", concert_id=concert.id))

    # Traitement commentaire (uniquement si concert passé)
    if comment_form.submit.data and comment_form.validate_on_submit():
        if concert.is_past:
            comment = Comment(
                author_name=comment_form.author_name.data,
                content=comment_form.content.data,
                concert=concert,
            )
            db.session.add(comment)
            db.session.commit()
            flash("Commentaire ajouté.", "success")
        else:
            flash("Les commentaires ne sont possibles que pour les concerts passés.", "warning")
        return redirect(url_for("concert_detail", concert_id=concert.id))

    # Optionnel : météo si concert dans les 15 jours (placeholder)
    weather_info = None
    if 0 <= (concert.date - datetime.now()).days <= 15:
        weather_info = "Météo prévue : Ensoleillé (exemple statique)."

    return render_template(
        "concert_detail.html",
        concert=concert,
        reservation_form=reservation_form,
        comment_form=comment_form,
        weather_info=weather_info,
    )

# Actualités par catégorie
@app.route("/actualites")
@app.route("/actualites/<int:category_id>")
def news_list(category_id=None):
    categories = Category.query.all()
    if category_id:
        news_items = (
            News.query.filter(News.category_id == category_id)
            .order_by(News.created_at.desc())
            .all()
        )
    else:
        news_items = News.query.order_by(News.created_at.desc()).all()
    return render_template(
        "news_list.html",
        news_items=news_items,
        categories=categories,
        selected_category_id=category_id,
    )

# Login admin
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for("admin_dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = AdminUser.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for("admin_dashboard"))
        flash("Identifiants invalides.", "danger")
    return render_template("admin_login.html", form=form)

# Logout admin
@app.route("/admin/logout", methods=["GET", "POST"])
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for("index"))

# Dashboard admin
@app.route("/admin")
@login_required
def admin_dashboard():
    concerts = Concert.query.order_by(Concert.date.desc()).all()
    news_items = News.query.order_by(News.created_at.desc()).all()
    categories = Category.query.all()
    delete_form = DeleteForm()
    return render_template(
        "admin_dashboard.html",
        concerts=concerts,
        news_items=news_items,
        categories=categories,
        delete_form=delete_form
    )

# Création / édition / suppression concerts
@app.route("/admin/concert/new", methods=["GET", "POST"])
@login_required
def admin_concert_new():
    form = ConcertForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        concert = Concert(
            title=form.title.data,
            date=form.date.data,
            place=form.place.data,
            type=form.type.data,
            total_seats=form.total_seats.data,
            description=form.description.data,
            category_id=form.category_id.data,
        )
        db.session.add(concert)
        db.session.commit()
        flash("Concert créé.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_concert_form.html", form=form)

@app.route("/admin/concert/<int:concert_id>/edit", methods=["GET", "POST"])
@login_required
def admin_concert_edit(concert_id):
    concert = Concert.query.get_or_404(concert_id)
    form = ConcertForm(obj=concert)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    if form.validate_on_submit():
        form.populate_obj(concert)
        db.session.commit()
        flash("Concert mis à jour.", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_concert_form.html", form=form)

@app.route("/admin/concert/<int:concert_id>/delete", methods=["POST"])
@login_required
def admin_concert_delete(concert_id):
    concert = Concert.query.get_or_404(concert_id)
    db.session.delete(concert)
    db.session.commit()
    flash("Concert supprimé.", "info")
    return redirect(url_for("admin_dashboard"))

# Création / édition / suppression actualités
@app.route("/admin/news/new", methods=["GET", "POST"])
@login_required
def admin_news_new():
    form = NewsForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    if form.validate_on_submit():
        news = News(
            title=form.title.data,
            content=form.content.data,
            category_id=form.category_id.data,
        )
        db.session.add(news)
        db.session.commit()
        flash("Actualité créée.", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_news_form.html", form=form)

@app.route("/admin/news/<int:news_id>/edit", methods=["GET", "POST"])
@login_required
def admin_news_edit(news_id):
    news = News.query.get_or_404(news_id)
    form = NewsForm(obj=news)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    if form.validate_on_submit():
        form.populate_obj(news)
        db.session.commit()
        flash("Actualité mise à jour.", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_news_form.html", form=form)

@app.route("/admin/news/<int:news_id>/delete", methods=["POST"])
@login_required
def admin_news_delete(news_id):
    news = News.query.get_or_404(news_id)
    db.session.delete(news)
    db.session.commit()
    flash("Actualité supprimée.", "info")
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
