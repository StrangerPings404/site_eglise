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
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
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

class LoginForm(FlaskForm):
    username = StringField('Nom d’utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Connexion')

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

#Route events
@app.route('/api/events')
def get_events():
    events = Event.query.all()
    return jsonify([{
        'id' : event.id,
        'title' : event.title,
        'start' : event.start.isoformat(),
        'end' : event.end.isoformat() if event.end else None,
        'description' : event.description
    } for event in events])

#Route gallery
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Fichier vide'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        new_photo = Photo(filename=filename, caption=request.form.get('caption'))
        db.session.add(new_photo)
        db.session.commit()
        
        return jsonify({'success': True, 'filename': filename})
    
    return jsonify({'error': 'Type de fichier non autorisé'}), 400

@app.route('/galerie')
def galerie():
    photos = Photo.query.order_by(Photo.date_uploaded.desc()).all()
    return render_template('galerie.html', photos=photos)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/photos')
def get_photos():
    photos = Photo.query.order_by(Photo.date_uploaded.desc()).all()
    return jsonify([{
        'id': photo.id,
        'url': f"/uploads/{photo.filename}",
        'caption': photo.caption,
        'date': photo.date_uploaded.isoformat()
    } for photo in photos])

#Route YouTeube
@app.route('/videos')
def videos():
    videos = Video.query.all()
    return render_template('videos.html', videos=videos)

# Route YouTeube
@app.route('/add_video', methods=['POST'])
def add_video():
    data = request.get_json()
    new_video = Video(
        youtube_id=data['youtube_id'],
        title=data['title'],
        description=data.get('description', '')
    )
    db.session.add(new_video)
    db.session.commit()
    return jsonify({'success': True})

#Route API YouTeube Retour
@app.route('/api/videos')
def get_videos():
    videos = Video.query.order_by(Video.date_added.desc()).all()
    return jsonify([{
        'id': video.id,
        'youtube_id': video.youtube_id,
        'title': video.title,
        'description': video.description
    } for video in videos])

# Route Don
@app.route('/don', methods=['GET', 'POST'])
def don():
    if request.method == 'POST':
        try:
            # Créer un paiement Stripe
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': 'Don à l\'église',
                        },
                        'unit_amount': int(float(request.form['amount'])*100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=url_for('don_success', _external=True),
                cancel_url=url_for('don', _external=True),
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            flash(f"Erreur: {str(e)}", 'danger')
    return render_template('don.html')

#Don Validé
@app.route('/don/success')
def don_success():
    return render_template('don_success.html')    

# Route d'Authentification
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        admin = Admin.query.first()
        if admin and admin.username == username and check_password_hash(admin.password, password):
            login_user(admin)
            return redirect(url_for('admin_panel'))
        flash('Identifiants incorrects', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Admin Panel
@app.route('/admin')
@login_required
def admin_panel():
    events = Event.query.all()
    photos = Photo.query.all()
    videos = Video.query.all()
    return render_template('admin/panel.html',
                         events=events,
                         photos=photos,
                         videos=videos)

# Event Management
@app.route('/manage-events')
@login_required
def manage_events():
    events = Event.query.order_by(Event.start.desc()).all()
    return render_template('admin/events.html', events=events)

# Ajout Evenement
@app.route('/admin/add-event', methods=['POST'])
@login_required
def add_event():
    if request.method == 'POST':
        try:
            new_event = Event(
                title=request.form['title'],
                start=datetime.strptime(request.form['start'], '%Y-%m-%dT%H:%M'),  # Format datetime-local
                end=datetime.strptime(request.form['end'], '%Y-%m-%dT%H:%M') if request.form.get('end') else None,
                description=request.form.get('description', '')
            )
            db.session.add(new_event)
            db.session.commit()
            flash('Événement ajouté avec succès!', 'success')
        except ValueError as e:
            flash('Format de date invalide', 'danger')
        except Exception as e:
            flash(f"Erreur: {str(e)}", 'danger')
        return redirect(url_for('manage_events'))

# Suppression d'événement
@app.route('/admin/delete-event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Événement supprimé', 'success')
    return redirect(url_for('manage_events'))

# Gallery Management
@app.route('/manage-gallery')
@login_required
def manage_gallery():
    photos = Photo.query.all()
    return render_template('admin/gallery.html', photos=photos)

# Suppression de Photo 
@app.route('/admin/delete-photo/<int:photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        flash(f"Erreur lors de la suppression du fichier: {str(e)}", "danger")
    
    db.session.delete(photo)
    db.session.commit()
    flash("Photo supprimée avec succès", "success")
    return redirect(url_for('manage_gallery'))

# Video Management
@app.route('/manage-videos')
@login_required
def manage_videos():
    videos = Video.query.all()
    return render_template('admin/videos.html', videos=videos)


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