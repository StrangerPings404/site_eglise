# Modules standards
import os

# Modules Tiers
from dotenv import load_dotenv
from flask import Flask, render_template, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Classe du formulaire (ajoutez AVANT les routes)
class ContactForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Envoyer')

# Configuration minimale pour les emails (à compléter plus tard)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

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

if __name__ == "__main__":
    app.run(debug=True)