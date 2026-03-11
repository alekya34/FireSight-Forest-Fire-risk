
import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sqlalchemy import create_engine
import joblib

# Configuration
DB_URI = 'sqlite:///instance/firepred.db'
CSV_PATH = 'data/fire_data.csv'
MODEL_DIR = 'models'
MODEL_PATH = os.path.join(MODEL_DIR, 'fire_model.h5')
SCALER_PATH = os.path.join(MODEL_DIR, 'scaler.pkl')
ENCODER_PATH = os.path.join(MODEL_DIR, 'label_encoder.pkl')

def load_data():
    """
    Load data from CSV and Database, merging them.
    """
    # 1. Load Static CSV Data
    if os.path.exists(CSV_PATH):
        print(f"Loading static data from {CSV_PATH}...")
        df_csv = pd.read_csv(CSV_PATH)
        # Ensure consistent columns
        df_csv = df_csv[['temp', 'humidity', 'wind', 'rainfall', 'risk']]
    else:
        print("Warning: CSV data not found.")
        df_csv = pd.DataFrame(columns=['temp', 'humidity', 'wind', 'rainfall', 'risk'])

    # 2. Load Dynamic DB Data
    print(f"Loading dynamic data from {DB_URI}...")
    try:
        engine = create_engine(DB_URI)
        # We read from the 'prediction' table. 
        # NOTE: Ideally, we should filter for 'verified' data, but for now we take all.
        # Mapping DB columns to feature names if necessary
        query = "SELECT temp, humidity, wind, rainfall, risk_label as risk FROM prediction"
        df_db = pd.read_sql(query, engine)
    except Exception as e:
        print(f"Warning: Could not load data from DB (maybe empty or connection failed): {e}")
        df_db = pd.DataFrame(columns=['temp', 'humidity', 'wind', 'rainfall', 'risk'])

    # 3. Merge
    df_final = pd.concat([df_csv, df_db], ignore_index=True)
    print(f"Total samples: {len(df_final)} (CSV: {len(df_csv)}, DB: {len(df_db)})")
    
    # Drop rows with missing values
    df_final.dropna(inplace=True)
    return df_final

def create_model(input_shape, num_classes):
    """
    Build a simple Feed-Forward Neural Network (DNN).
    """
    model = keras.Sequential([
        layers.Dense(64, activation='relu', input_shape=(input_shape,)),
        layers.Dropout(0.2),
        layers.Dense(32, activation='relu'),
        layers.Dense(num_classes, activation='softmax')
    ])
    
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model

def train():
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # 1. Load Data
    df = load_data()
    if len(df) < 10:
        print("Not enough data to train. Exiting.")
        return

    X = df[['temp', 'humidity', 'wind', 'rainfall']].values
    y = df['risk'].values

    # 2. Encode Labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    num_classes = len(le.classes_)
    print("Classes:", le.classes_)

    # 3. Scale Features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 4. Split
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_enc, test_size=0.2, random_state=42)

    # 5. Build Model
    model = create_model(input_shape=X_train.shape[1], num_classes=num_classes)
    
    # 6. Train
    print("Starting training...")
    history = model.fit(
        X_train, y_train,
        epochs=50,
        batch_size=32,
        validation_split=0.2,
        verbose=1
    )

    # 7. Evaluate
    loss, acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"Test Accuracy: {acc:.4f}")

    # 8. Save Artifacts
    model.save(MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(le, ENCODER_PATH)
    print(f"Model saved to {MODEL_PATH}")
    print(f"Scaler saved to {SCALER_PATH}")
    print(f"Encoder saved to {ENCODER_PATH}")

if __name__ == '__main__':
    train()
