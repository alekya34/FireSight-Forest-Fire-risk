# 🔥 FireSight: Forest Fire Risk Prediction

## 📌 Overview

FireSight is a **Deep Learning-based web application** designed to predict the likelihood of a forest fire using environmental and meteorological data. The system analyzes parameters such as **Temperature, Humidity, Wind Speed, and Rainfall** to estimate forest fire risk and support **early warning and prevention efforts**.

The application also integrates **real-time weather data** using APIs and provides instant predictions through a **Deep Neural Network (DNN)** model.

---

## 🚀 Features

* 🌦 **Real-Time Weather Integration**
  Automatically fetches live environmental data (Temperature, Humidity, Wind Speed, Rainfall) using the **OpenWeather API**, with a fallback to **Open-Meteo**, based on user-provided latitude and longitude.

* 🔍 **Instant Risk Prediction**
  Uses a **Deep Neural Network (DNN)** model to classify forest fire risk.

* 💻 **User-Friendly Interface**
  A clean web interface built with **HTML, CSS, and Flask** for easy interaction.

* 📊 **Data-Driven Insights**
  Uses historical weather and forest fire datasets for accurate predictions.

* 📧 **Email Notifications**
  Sends alerts or risk reports to the user's email for critical fire risk conditions.

---

## 🛠 Technologies Used

### Backend

* Python
* Flask

### Deep Learning

* TensorFlow / Keras
* Scikit-learn
* Pandas
* NumPy

### Frontend

* HTML5
* CSS3
* JavaScript

### Data

* CSV-based historical forest fire datasets

---

## 📂 Project Structure

```
FireSight-Forest-Fire-risk/
│
├── templates/          # HTML files
├── static/             # CSS, JavaScript, images
├── dataset/            # Training datasets
├── model/              # Saved trained models
├── train_model_dnn.py  # Model training script
├── app.py              # Main Flask application
├── requirements.txt    # Project dependencies
├── README.md
└── .gitignore
```

---

## ⚙️ Setup & Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/alekya34/FireSight-Forest-Fire-risk.git
cd FireSight-Forest-Fire-risk
```

---

### 2️⃣ Create and Activate Virtual Environment

**Windows**

```bash
python -m venv env
env\Scripts\activate
```

**Mac/Linux**

```bash
python3 -m venv env
source env/bin/activate
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Configure Environment Variables

Create a `.env` file in the root directory and add the following:

```
OPENWEATHER_API_KEY=your_openweather_api_key_here
ALERT_EMAIL=your_email_address
EMAIL_PASSWORD=your_app_password
```

---

### 5️⃣ Train the Model (Optional)

If you want to train the deep learning model from scratch:

```bash
python train_model_dnn.py
```

---

### 6️⃣ Run the Application

```bash
python app.py
```

The application will run at:

```
http://127.0.0.1:5000
```

or

```
http://localhost:5000
```

---

## 📊 Usage

1. Open the web application in your browser.
2. Enter the required location parameters:

   * **Latitude** (Example: `40.71`)
   * **Longitude** (Example: `-74.00`)
   * **Email** *(optional – to receive risk reports)*
3. Click **Analyze Risk**.
4. The system fetches real-time weather data and predicts the **Forest Fire Risk Level** instantly.

---

## 🔮 Future Enhancements

* 🗺 Interactive map visualization for high-risk forest areas
* 📡 Integration with additional weather APIs
* 📈 Larger datasets to improve prediction accuracy
* ☁️ Cloud deployment for public access
* 📱 Mobile-friendly interface

---

GitHub: https://github.com/alekya34

---

⭐ If you found this project useful, feel free to **star the repository**.
