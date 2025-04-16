# Modules standards
import os

# Modules Tiers
from dotenv import load_dotenv
from flask import Flask, render_template, flash, jsonify, request, redirect, send_from_directory, url_for
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.utils import secure_filename

load_dotenv()

#-----------------------------
#Configuration du site
#-----------------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Calendar
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
db = SQLAlchemy(app)

#Gallery
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Configuration minimale pour les emails (à compléter plus tard)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

#db.init_app(app)


#---------------------
# FONCTIONS UTILITAIRE
#---------------------

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

#---------------------
# MODELES
#---------------------

#Classe de table
class Event(db.Model):
    """Modèle pour les évènements du calendar."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime)
    description = db.Column(db.Text)

#Class Photo

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.String(200))
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)

# Classe du formulaire
class ContactForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Envoyer')

# Classe YouTeube
class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    youtube_id = db.Column(db.String(20), nullable=False)  # Ex: "dQw4w9WgXcQ"
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)




#-----------------------
#   ROUTES
#-----------------------

#Route Principale
@app.route("/")
def home():
    return render_template("index.html")

#Route Contact
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

#------------------------
#INITIALISATION
#------------------------

# Créer le dossier uploads si inexistant
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)