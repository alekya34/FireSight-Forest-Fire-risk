
import os
import joblib
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model

try:
    print("Loading model...")
    model = load_model('models/fire_model.h5')
    scaler = joblib.load('models/scaler.pkl')
    le = joblib.load('models/label_encoder.pkl')
    print("Model loaded successfully.")

    # Test Prediction
    # temp=30, humidity=50, wind=10, rainfall=0
    input_data = np.array([[30, 50, 10, 0]])
    scaled_data = scaler.transform(input_data)
    
    print("Predicting...")
    probs = model.predict(scaled_data, verbose=0)
    pred_idx = probs.argmax()
    label = le.inverse_transform([pred_idx])[0]
    
    print(f"Prediction Success! Label: {label}, Prob: {probs[0][pred_idx]:.2f}")
    
except Exception as e:
    print("Verification Failed:", e)
