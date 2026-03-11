# train_model.py
import pandas as pd
import numpy as np
import os
import joblib

# TensorFlow / Keras
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report

# Ensure models dir
os.makedirs('models', exist_ok=True)

# 1. Load Data
df = pd.read_csv('data/fire_data.csv')
features = ['temp','humidity','wind','rainfall']
X = df[features]
y = df['risk']

# 2. Encode Labels
le = LabelEncoder()
y_enc = le.fit_transform(y)
# Provide categorical mapping for report later
class_names = le.classes_
print("Classes:", class_names)

# 3. Scaling (Critical for DL)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4. Split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_enc, test_size=0.2, random_state=42, stratify=y_enc)

# 5. Build Deep Learning Model (Sequential DNN)
model = keras.Sequential([
    layers.Input(shape=(4,)),           # 4 features
    layers.Dense(16, activation='relu'),
    layers.Dense(8, activation='relu'),
    layers.Dense(4, activation='softmax') # 4 output classes
])

model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# 6. Train
print("Training Neural Network...")
model.fit(X_train, y_train, epochs=50, batch_size=16, verbose=1)

# 7. Evaluate
loss, acc = model.evaluate(X_test, y_test, verbose=0)
print(f"\nTest Accuracy: {acc:.4f}")

probs = model.predict(X_test)
preds = probs.argmax(axis=1)
print(classification_report(y_test, preds, target_names=class_names))

# 8. Save Artifacts
model.save('models/fire_model.h5')
joblib.dump(le, 'models/label_encoder.pkl')
joblib.dump(scaler, 'models/scaler.pkl')

print("Saved models/fire_model.h5, label_encoder.pkl, and scaler.pkl")
