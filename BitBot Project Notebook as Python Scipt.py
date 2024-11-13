### BitBot Project Notebook as Python Script

# BitBot Project Notebook as Python Script
# This script follows the notebook structure, with each section representing a cell in the notebook.

# ========== Section 1: Data Loading and Preprocessing ==========
# Description: Import, clean, and preprocess historical Bitcoin data for model training.

# Import necessary libraries
import pandas as pd
import numpy as np
import os

# Define paths for historical and processed data
historical_data_path = "1_data/1_historical/"
processed_data_path = "1_data/2_processed/"

# Load raw historical data (example: CSV format)
def load_historical_data(filename):
    filepath = os.path.join(historical_data_path, filename)
    return pd.read_csv(filepath)

# Preprocess the data (example: fill missing values and add technical indicators)
def preprocess_data(df):
    df.fillna(method='ffill', inplace=True)  # Forward fill missing values
    df['SMA_50'] = df['Close'].rolling(window=50).mean()  # 50-day Simple Moving Average
    return df

# Save processed data
def save_processed_data(df, filename):
    if not os.path.exists(processed_data_path):
        os.makedirs(processed_data_path)
    df.to_csv(os.path.join(processed_data_path, filename), index=False)

# Example usage
df_raw = load_historical_data("bitcoin_data.csv")  # Replace with actual filename
df_processed = preprocess_data(df_raw)
save_processed_data(df_processed, "bitcoin_data_processed.csv")


# ========== Section 2: Model Training and Saving ==========
# Description: Train individual models on different timeframes and save them.

# Import machine learning libraries
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

# Define model paths
model_paths = {
    "micro": "3_models/1_micro_model/",
    "mid": "3_models/2_mid_model/",
    "swing": "3_models/3_swing_model/",
    "trend": "3_models/4_trend_model/"
}

# Ensure model directories exist
for path in model_paths.values():
    os.makedirs(path, exist_ok=True)

# Function to train and save a model (example with RandomForest)
def train_and_save_model(df, model_type):
    X = df[['SMA_50']]  # Example feature
    y = df['Close'].shift(-1) > df['Close']  # Example target: binary direction
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Save model
    joblib.dump(model, os.path.join(model_paths[model_type], f"{model_type}_model.joblib"))

# Example usage for micro timeframe
df_processed = pd.read_csv("1_data/2_processed/bitcoin_data_processed.csv")  # Load preprocessed data
train_and_save_model(df_processed, "micro")  # Train micro model


# ========== Section 3: Trading Bot Logic ==========
# Description: Implement trading logic based on model predictions.

# Import necessary libraries for trading logic
import joblib

# Load trained model
def load_model(model_type):
    return joblib.load(os.path.join(model_paths[model_type], f"{model_type}_model.joblib"))

# Define a simple trading strategy
def trading_logic(df, model_type):
    model = load_model(model_type)
    X = df[['SMA_50']]
    predictions = model.predict(X)
    # Example logic: Buy if model predicts uptrend
    for idx, prediction in enumerate(predictions):
        if prediction:
            print(f"Trade {idx}: Buy signal based on {model_type} model prediction")

# Example usage
trading_logic(df_processed, "micro")  # Trading logic for micro model


# ========== Section 4: Logging and Reporting ==========
# Description: Set up logging and report generation.

import logging

# Set up logging
logging.basicConfig(filename='6_logs/trading_bot.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def log_trade(action, details):
    logging.info(f"Trade action: {action}, Details: {details}")

# Example logging
log_trade("BUY", {"price": 40000, "model": "micro_model"})


# ========== Section 5: Testing and Validation ==========
# Description: Run tests for each component in the bot's pipeline.

# Import unittest for testing
import unittest

class TestDataProcessing(unittest.TestCase):
    def test_preprocess_data(self):
        df = pd.DataFrame({'Close': [1, 2, None, 4, 5]})
        processed_df = preprocess_data(df)
        self.assertFalse(processed_df['Close'].isnull().any())

class TestModelTraining(unittest.TestCase):
    def test_model_training(self):
        df = pd.DataFrame({'SMA_50': [1, 2, 3, 4], 'Close': [1, 0, 1, 0]})
        try:
            train_and_save_model(df, "micro")
            self.assertTrue(os.path.exists(model_paths["micro"] + "micro_model.joblib"))
        except Exception as e:
            self.fail(f"Model training failed with error: {e}")

# Run tests
unittest.main(argv=[''], verbosity=2, exit=False)
