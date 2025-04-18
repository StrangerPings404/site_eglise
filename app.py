# Modules standards
import os
from datetime import datetime

# Modules Tiers
from dotenv import load_dotenv
from flask import Flask, render_template, flash, jsonify, request, redirect, send_from_directory, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
import stripe

load_dotenv()

# Initialisation de l'application
app = Flask(__name__)

# Configuration de base
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DB_SECRET_KEY'] = os.getenv('DB_SECRET_KEY', 'default-secret-key-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['STRIPE_PUBLIC_KEY'] = os.getenv('STRIPE_PUBLIC_KEY')
app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY')

# Configuration email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

# Initialisation des extensions
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
stripe.api_key = app.config['STRIPE_SECRET_KEY']

# Configuration Admin
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Middleware
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Fonction utilitaire
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Modèles
class Event(db.Model):
    """Modèle pour les évènements du calendrier."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime)
    description = db.Column(db.Text)

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.String(200))
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    youtube_id = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, default='admin')
    password = db.Column(db.String(100))

class Don(db.Model):
    __tablename__ = 'dons'
    id = db.Column(db.Integer, primary_key=True)
    montant = db.Column(EncryptedType(db.Float, app.config['DB_SECRET_KEY'], AesEngine, 'pkcs5'))

class ContactForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Envoyer')

# Routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route('/calendrier')
def calendrier():
    return render_template('calendrier.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        flash('Merci pour votre message !', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html', form=form)

# ... (toutes vos autres routes restent inchangées)

# Initialisation
with app.app_context():
    db.create_all()
    if not Admin.query.first():
        hashed_pw = generate_password_hash(ADMIN_PASSWORD, method='pbkdf2:sha256')
        admin = Admin(username=ADMIN_USERNAME, password=hashed_pw)
        db.session.add(admin)
        db.session.commit()
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

if __name__ == "__main__":
    app.run(debug=True)