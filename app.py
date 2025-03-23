from flask import Flask, request, render_template, send_file, session, redirect, url_for
import os
import numpy as np
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from flask import Flask, render_template, request, redirect, url_for, flash, session

from flask import Flask

from werkzeug.security import generate_password_hash, check_password_hash

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView




app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = "your_secret_key"

db = SQLAlchemy(app)

# Database Model
class EyeDiseasePrediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    prediction = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# User Model with Admin Role
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)  # Admin flag

# Add Models to Flask-Admin

with app.app_context():
    db.create_all()




# register and login

# **Register Route**
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered!", "warning")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)  # Hash the password
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# **Login Route**
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):  # Verify password
            session['user'] = user.name
            session["user_id"] = user.id  # ✅ Store user ID in session
            session["is_admin"] = user.is_admin  # ✅ Store admin status

            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password!", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')



@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for("login"))

    predictions = EyeDiseasePrediction.query.order_by(EyeDiseasePrediction.timestamp.desc()).all()

    if request.method == "POST":
        files = request.files.getlist("file")
        predictions_list = []

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(file_path)

                prediction, confidence = predict_eye_disease(file_path)
                predictions_list.append((filename, prediction, confidence))

                # Store in the database
                new_prediction = EyeDiseasePrediction(
                    filename=filename, prediction=prediction, confidence=confidence
                )
                db.session.add(new_prediction)
                db.session.commit()

        session["predictions"] = predictions_list

    return render_template("dashboard.html", user=session["user"], predictions=predictions)



@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have logged out.", "info")
    return redirect(url_for('home'))




# Load trained model
MODEL_PATH = "cateye.h5"
model = load_model(MODEL_PATH)

# Class Labels
class_labels = ["Cataract", "Diabetic Retinopathy", "Glaucoma", "Normal"]

# Upload folders
UPLOAD_FOLDER = "static/uploads"
REPORTS_FOLDER = "reports"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["REPORTS_FOLDER"] = REPORTS_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(img_path, target_size=(256, 256)):
    img = image.load_img(img_path, target_size=target_size)
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0
    return img_array

def predict_eye_disease(img_path):
    img_array = preprocess_image(img_path)
    prediction = model.predict(img_array)
    predicted_class = np.argmax(prediction)
    confidence = np.max(prediction) * 100
    return class_labels[predicted_class], confidence

# **HOME PAGE - Only Eye Disease Details**
@app.route("/")
def home():
    return render_template("index.html")

# **UPLOAD PAGE - Image Upload & Prediction**
@app.route("/upload", methods=["GET", "POST"])
def upload_file():

    if "user" not in session:  # Check if user is logged in
        flash("Please log in first!", "danger")
        return redirect(url_for("login"))
    
    if request.method == "POST":
        files = request.files.getlist("file")
        predictions = []

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(file_path)

                prediction, confidence = predict_eye_disease(file_path)
                predictions.append((filename, prediction, confidence))

                # Store in the database
                new_prediction = EyeDiseasePrediction(
                    filename=filename, prediction=prediction, confidence=confidence
                )
                db.session.add(new_prediction)
                db.session.commit()

        session["predictions"] = predictions
        return render_template("result.html", predictions=predictions)

    return render_template("upload.html")

@app.route("/download_report")
def download_report():
    predictions = session.get("predictions", [])
    if not predictions:
        return "No report available. Please upload an image first.", 400

    report_path = os.path.join(app.config["REPORTS_FOLDER"], "eye_disease_report.pdf")

    c = canvas.Canvas(report_path)
    c.setFont("Helvetica", 14)
    c.drawString(100, 800, "Eye Disease Classification Report")
    c.drawString(100, 780, "----------------------------------")

    y = 750
    for filename, prediction, confidence in predictions:
        c.drawString(100, y, f"{filename}: {prediction} (Confidence: {confidence:.2f}%)")
        y -= 20

    c.save()
    return send_file(report_path, as_attachment=True)



@app.route("/history")
def view_history():
    if "user" not in session:  # Check if user is logged in
        flash("Please log in first!", "danger")
        return redirect(url_for("login"))
    
    predictions = EyeDiseasePrediction.query.order_by(EyeDiseasePrediction.timestamp.desc()).all()

    # Convert UTC timestamps to local timezone
    local_tz = pytz.timezone("Asia/Kolkata")  # Change this to your timezone
    for prediction in predictions:
        prediction.local_timestamp = prediction.timestamp.replace(tzinfo=pytz.utc).astimezone(local_tz)

    return render_template("history.html", predictions=predictions)


@app.route("/profile")
def profile():
    if "user_id" not in session:  # Ensure the user is logged in
        flash("Please log in first!", "danger")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])  # Fetch user details from the database
    if not user:  # ✅ Check if the user exists
        flash("User not found!", "danger")
        return redirect(url_for("login"))

    return render_template("profile.html", user=user)





if __name__ == "__main__":
    app.run(debug=True)
