# app.py
import os
import sys
import subprocess

def install_package(package):
    print(f"Installing missing package: {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}: {e}")
        raise

# Auto-install missing dependencies
required_packages = {
    'flask_sqlalchemy': 'flask_sqlalchemy',
    'apscheduler': 'apscheduler',
    'dotenv': 'python-dotenv',
    'folium': 'folium',
    'joblib': 'joblib',
    'requests': 'requests',
    'pandas': 'pandas',
    'sklearn': 'scikit-learn',
    'tensorflow': 'tensorflow'
}

for module_name, package_name in required_packages.items():
    try:
        if module_name == 'sklearn':
            import sklearn
        elif module_name == 'dotenv':
            import dotenv
        elif module_name == 'tensorflow':
            import tensorflow
        else:
            __import__(module_name)
    except ImportError:
        install_package(package_name)

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import joblib
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import folium
from folium.plugins import HeatMap
import smtplib
from email.mime.text import MIMEText
import numpy as np

# Load environment variables from .env
load_dotenv()

# ---------------- Config ----------------
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '').strip()
ALERT_EMAIL = os.getenv('ALERT_EMAIL', '').strip()
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '').strip()
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com').strip()
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '465').strip())

# App & DB
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///firepred.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------------- Models ----------------
class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    email = db.Column(db.String(120), nullable=True)   # email for alerts
    phone = db.Column(db.String(50), nullable=True)    # optional
    active = db.Column(db.Boolean, default=True)

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    temp = db.Column(db.Float)
    humidity = db.Column(db.Float)
    wind = db.Column(db.Float)
    rainfall = db.Column(db.Float)
    risk_label = db.Column(db.String(50))
    risk_prob = db.Column(db.Float)

# ---------------- Model Loading ----------------
MODEL = None
LABEL_ENCODER = None
SCALER = None


def load_keras_model():
    global MODEL, LABEL_ENCODER, SCALER
    try:
        from tensorflow.keras.models import load_model
        MODEL = load_model('models/fire_model.h5')
        LABEL_ENCODER = joblib.load('models/label_encoder.pkl')
        SCALER = joblib.load('models/scaler.pkl')
        print("Loaded Deep Learning model (Keras), scaler, and label encoder.")
        return True
    except Exception as e:
        print("No trained DL model found or failed to load. Using heuristic fallback. Err:", e)
        return False

# Initial Load
load_keras_model()

# ---------------- Helpers ----------------
def fetch_weather(lat, lon):
    """
    Fetch current weather from OpenWeatherMap (metric units).
    If it fails, fallback to Open-Meteo.
    Returns dict with temp (C), humidity (%), wind (m/s), rainfall (mm last 1h)
    """
    if OPENWEATHER_API_KEY:
        try:
            url = ("https://api.openweathermap.org/data/2.5/weather"
                   f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric")
            r = requests.get(url, timeout=12)
            r.raise_for_status()
            j = r.json()
            temp = j['main']['temp']
            humidity = j['main']['humidity']
            wind = j.get('wind', {}).get('speed', 0.0)
            rainfall = j.get('rain', {}).get('1h', 0.0) if j.get('rain') else 0.0
            return {'temp': round(float(temp), 2),
                    'humidity': round(float(humidity), 2),
                    'wind': round(float(wind), 2),
                    'rainfall': round(float(rainfall), 2)}
        except Exception as e:
            print(f"OpenWeatherMap failed ({e}). Falling back to Open-Meteo...")

    # Fallback to Open-Meteo (No API Key Required)
    try:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               "&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m")
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        j = r.json()
        temp = j['current']['temperature_2m']
        humidity = j['current']['relative_humidity_2m']
        wind = j['current']['wind_speed_10m'] / 3.6 # Convert km/h to m/s
        rainfall = j['current']['precipitation'] # mm
        print("Successfully fetched weather from Open-Meteo fallback.")
        return {'temp': round(float(temp), 2),
                'humidity': round(float(humidity), 2),
                'wind': round(float(wind), 2),
                'rainfall': round(float(rainfall), 2)}
    except Exception as e:
        print(f"Both APIs failed: {e}")
        # Final absolute fallback if both fail (return safe averages so the app doesn't crash)
        return {'temp': 25.0, 'humidity': 50.0, 'wind': 5.0, 'rainfall': 0.0}

def predict_risk(temp, humidity, wind, rainfall):
    """
    If ML model present, use it. Otherwise use simple heuristic.
    Returns (label, probability_score)
    """
    if MODEL is not None and SCALER is not None:
        try:
            # 1. Prepare input
            X_input = np.array([[temp, humidity, wind, rainfall]])
            # 2. Scale
            X_scaled = SCALER.transform(X_input)
            # 3. Predict (returns array of probabilities per class)
            probs = MODEL.predict(X_scaled, verbose=0)[0]
            idx = int(probs.argmax())
            label = LABEL_ENCODER.inverse_transform([idx])[0]
            return label, float(probs[idx])
        except Exception as e:
            print("Model predict error, falling back to heuristic:", e)

    # Heuristic fallback (same as training script)
    score = 0.4*temp - 0.35*humidity + 0.35*wind - 0.25*rainfall
    if score < -5:
        label = 'Low'
    elif score < 5:
        label = 'Moderate'
    elif score < 12:
        label = 'High'
    else:
        label = 'Extreme'
    # map score to 0..1 roughly (for display only)
    prob = min(0.99, max(0.01, (score + 20) / 40))
    return label, float(prob)

def send_email(to_email, subject, body):
    """
    Send email alert using SMTP (if credentials provided in .env).
    """
    if not (ALERT_EMAIL and EMAIL_PASSWORD):
        print("❌ Email credentials (ALERT_EMAIL/EMAIL_PASSWORD) not configured.")
        return False

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = ALERT_EMAIL
    msg['To'] = to_email
    
    try:
        print(f"📧 Connecting to SMTP {EMAIL_HOST}:{EMAIL_PORT}...")
        if EMAIL_PORT == 465:
            with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, timeout=15) as server:
                server.login(ALERT_EMAIL, EMAIL_PASSWORD)
                server.sendmail(ALERT_EMAIL, [to_email], msg.as_string())
                print(f"✅ Email sent successfully to {to_email}")
                return True
        else:
            with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=15) as server:
                server.starttls()
                server.login(ALERT_EMAIL, EMAIL_PASSWORD)
                server.sendmail(ALERT_EMAIL, [to_email], msg.as_string())
                print(f"✅ Email sent successfully to {to_email}")
                return True
    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP Auth Error: Invalid User/Password or App Password required.")
        raise
    except Exception as e:
        print(f"❌ SMTP Error: {e}")
        raise


def generate_heatmap_file():
    """
    Generate static/heatmap.html using latest prediction per location.
    Adds red markers for High/Extreme for clarity.
    """
    locs = Location.query.filter_by(active=True).all()
    points = []
    for loc in locs:
        p = Prediction.query.filter_by(location_id=loc.id).order_by(Prediction.timestamp.desc()).first()
        if p:
            wmap = {'Low': 0.2, 'Moderate': 0.5, 'High': 0.8, 'Extreme': 1.0}
            weight = wmap.get(p.risk_label, 0.2)
            points.append([loc.lat, loc.lon, weight])

    if not points:
        # Save a default empty map so iframe won't fail
        m = folium.Map(location=[20.0, 78.0], zoom_start=6)
        folium.TileLayer('OpenStreetMap').add_to(m)
        os.makedirs('static', exist_ok=True)
        m.save('static/heatmap.html')
        print("Saved default heatmap (no points).")
        return

    avg_lat = sum([pt[0] for pt in points]) / len(points)
    avg_lon = sum([pt[1] for pt in points]) / len(points)
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=6)
    HeatMap(points, radius=25, blur=15, min_opacity=0.4).add_to(m)

    # add markers for clarity (High/Extreme)
    for loc in locs:
        p = Prediction.query.filter_by(location_id=loc.id).order_by(Prediction.timestamp.desc()).first()
        if p and p.risk_label in ['High', 'Extreme']:
            folium.Marker(
                [loc.lat, loc.lon],
                popup=f"{loc.name}: {p.risk_label} ({p.risk_prob:.2f})",
                icon=folium.Icon(color='red', icon='exclamation-sign')
            ).add_to(m)

    os.makedirs('static', exist_ok=True)
    m.save('static/heatmap.html')
    print(f"Saved heatmap with {len(points)} points.")

def check_all_locations():
    """
    Main job: fetch weather for each active location, predict, store, alert if needed, and generate heatmap.
    """
    with app.app_context():
        print("Running check_all_locations() at", datetime.utcnow().isoformat())
        locs = Location.query.filter_by(active=True).all()
        for loc in locs:
            try:
                w = fetch_weather(loc.lat, loc.lon)
                label, prob = predict_risk(w['temp'], w['humidity'], w['wind'], w['rainfall'])
                p = Prediction(location_id=loc.id,
                               timestamp=datetime.utcnow(),
                               temp=w['temp'], humidity=w['humidity'], wind=w['wind'],
                               rainfall=w['rainfall'], risk_label=label, risk_prob=prob)
                db.session.add(p)
                db.session.commit()
                print(f"[{loc.name}] {label} ({prob:.2f}) — {w}")

                # Alerting (email only here). Add throttling in production to avoid spam.
                if label in ['High', 'Extreme'] and loc.email:
                    body = (f"ALERT: {loc.name}\nRisk: {label} ({prob:.2f})\n"
                            f"Location: {loc.lat}, {loc.lon}\n"
                            f"Weather: temp={w['temp']}C, humidity={w['humidity']}%, wind={w['wind']}m/s, rain={w['rainfall']}mm")
                    
                    # Print to terminal as requested
                    print("\n" + "="*30)
                    print(f"🔥 FOREST FIRE ALERT FOR: {loc.name} 🔥")
                    print(body)
                    print("="*30 + "\n")

                    try:
                        send_email(loc.email, "Forest Fire Risk Alert", body)
                    except Exception as e:
                        print("Email error:", e)
            except Exception as e:
                print(f"Error checking {loc.name}: {e}")

        # regenerate heatmap after loop
        try:
            generate_heatmap_file()
        except Exception as e:
            print("Heatmap generation failed:", e)

# ---------------- Routes ----------------
@app.route('/')
def index():
    locs = Location.query.all()
    return render_template('index.html', locations=locs)

@app.route('/add_location', methods=['POST'])
def add_location():
    name = request.form.get('name')
    lat = float(request.form.get('lat'))
    lon = float(request.form.get('lon'))
    email = request.form.get('email', '').strip() or None
    phone = request.form.get('phone', '').strip() or None
    loc = Location(name=name, lat=lat, lon=lon, email=email, phone=phone, active=True)
    db.session.add(loc)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/heatmap')
def heatmap():
    # ensure latest file exists
    generate_heatmap_file()
    return render_template('heatmap.html')

@app.route('/run_now', methods=['POST'])
def run_now():
    # run a single check synchronously (button on UI)
    check_all_locations()
    return redirect(url_for('index'))

@app.route('/api/predict', methods=['POST'])
def api_predict():
    try:
        data = request.json or {}
        lat = data.get('lat')
        lon = data.get('lon')
        if lat is None or lon is None:
            return jsonify({'error': 'lat and lon required'}), 400
        
        # 1. Fetch Weather
        try:
            w = fetch_weather(float(lat), float(lon))
        except Exception as e:
            return jsonify({'error': f"Weather API Error: {str(e)}"}), 400
            
        # 2. Predict Risk
        label, prob = predict_risk(w['temp'], w['humidity'], w['wind'], w['rainfall'])
        
        # 3. Send Email if requested
        user_email = data.get('email')
        email_status = "Not requested"
        if user_email:
            try:
                subject = f"Ignis Prediction: {label} Risk Detected"
                body = (f"Forest Fire Prediction Results:\n\n"
                        f"Risk Level: {label}\n"
                        f"Confidence: {prob*100:.1f}%\n\n"
                        f"Weather Conditions:\n"
                        f"Temperature: {w['temp']}°C\n"
                        f"Humidity: {w['humidity']}%\n"
                        f"Wind Speed: {w['wind']} m/s\n"
                        f"Rainfall: {w['rainfall']} mm\n\n"
                        f"Location: {lat}, {lon}")
                if send_email(user_email, subject, body):
                    email_status = "Sent"
                else:
                    email_status = "Not Requested (No Creds)"
            except Exception as e:
                # Capture email error but don't fail the whole request
                print(f"Email Sending Failed: {e}")
                email_status = f"Failed: {str(e)}"

        return jsonify({'weather': w, 'risk': label, 'probability': prob, 'email_monitor': email_status})

    except Exception as e:
        # Catch-all for any other crash (e.g. model not loaded)
        return jsonify({'error': f"Server Error: {str(e)}"}), 500
@app.route('/check_now', methods=['POST'])
def check_now():
    from datetime import datetime
    print(f"Running check_all_locations() at {datetime.now().isoformat()}")
    try:
        check_all_locations()
        return {"status": "success", "message": "Check completed successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route('/retrain', methods=['POST'])
def retrain_model():
    """
    Trigger model retraining (Transfer Learning) on current data.
    """
    try:
        print("Starting Retraining Process...")
        # Run training script as subprocess
        subprocess.check_call([sys.executable, 'train_model_dnn.py'])
        
        # Reload model into memory
        success = load_keras_model()
        if success:
            return jsonify({'status': 'success', 'message': 'Model retrained and reloaded successfully.'})
        else:
            return jsonify({'status': 'warning', 'message': 'Training ran but model reload failed.'}), 500
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'message': f'Training script failed: {e}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/test_email', methods=['POST'])
def test_email_route():
    recipient = request.form.get('email')
    if not recipient:
        return jsonify({'status': 'error', 'message': 'Email required'}), 400
    try:
        send_email(recipient, "Test Alert: Forest Fire App", "This is a test email triggered from the Dashboard.\nIf you received this, the alert system is working!")
        return jsonify({'status': 'success', 'message': f'Test email sent to {recipient}'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500





# ---------------- Main ----------------
if __name__ == '__main__':
    # create DB inside app context
    with app.app_context():
        db.create_all()

    # scheduler
    scheduler = BackgroundScheduler()
    # Run immediately once at start and then every 30 minutes
    scheduler.add_job(func=check_all_locations, trigger='interval', minutes=30, next_run_time=datetime.utcnow())
    scheduler.start()

    # run app (disable reloader so scheduler runs only once)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
