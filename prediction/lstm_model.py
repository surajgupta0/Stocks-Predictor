import numpy as np
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam
from sklearn.metrics import mean_absolute_percentage_error
from datetime import datetime, timedelta
import os
import pickle

MODEL_DIR = "models"
LAST_CHECKED_DAY_FILE = "last_checked_day.txt"

def load_stock_data(symbol, period="1y"):
    stock = yf.Ticker(symbol)
    df = stock.history(period=period)
    return df

def train_lstm_model(historical_data, symbol, mv, period="1y"):
    data = historical_data['Close'].values
    data = data.reshape(-1, 1)
    
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)
    
        
    # Split data into training and testing sets
    train_size = int(len(scaled_data) * 0.7)
    train_data = scaled_data[:train_size]
    test_data = scaled_data[train_size:]
    
    # Prepare training data
    X_train, y_train = [], []
    for i in range(mv, len(train_data)):
        X_train.append(train_data[i-mv:i, 0])
        y_train.append(train_data[i, 0])
    
    X_train, y_train = np.array(X_train), np.array(y_train)
    X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

    # Train the model
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)))
    model.add(LSTM(units=50, return_sequences=False))
    model.add(Dense(units=25))
    model.add(Dense(units=1))
    
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X_train, y_train, batch_size=1, epochs=1)
    
    # Prepare testing data
    X_test, y_test = [], []
    for i in range(mv, len(test_data)):
        X_test.append(test_data[i-mv:i, 0])
        y_test.append(test_data[i, 0])
    
    
    if len(X_test) > 0:
        X_test, y_test = np.array(X_test), np.array(y_test)
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))
        
        # Predict on testing data
        y_pred_scaled = model.predict(X_test)
        y_pred = scaler.inverse_transform(y_pred_scaled)
        y_test = scaler.inverse_transform(y_test.reshape(-1, 1))
        
        # Calculate accuracy percentage (MAPE)
        accuracy_percentage = 100 - mean_absolute_percentage_error(y_test, y_pred) * 100
    else:
        accuracy_percentage = None
        y_pred = np.array([])
    
    model_path = os.path.join(MODEL_DIR, f"{symbol}_{mv}mv_{period}_model.h5")
    scaler_path = os.path.join(MODEL_DIR, f"{symbol}_{mv}mv_{period}_scaler.pkl")
    accurary_path = os.path.join(MODEL_DIR, f"{symbol}_{mv}mv_{period}_accuracy.txt")
    
    model.save(model_path)
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    
    with open(accurary_path, 'w') as f:
        f.write(str(accuracy_percentage))
        
    return model, scaler, accuracy_percentage

def load_model_and_scaler(symbol, mv, period = "1y"):
    model_path = os.path.join(MODEL_DIR, f"{symbol}_{mv}mv_{period}_model.h5")
    scaler_path = os.path.join(MODEL_DIR, f"{symbol}_{mv}mv_{period}_scaler.pkl")
    accuracy_score_path = os.path.join(MODEL_DIR, f"{symbol}_{mv}mv_{period}_accuracy.txt")
    
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        model = load_model(model_path)
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        # Recompile the model with a new optimizer instance
        model.compile(optimizer=Adam(), loss='mean_squared_error')
        
        # Read accuracy score from file
        if os.path.exists(accuracy_score_path):
            with open(accuracy_score_path, 'r') as f:
                accuracy_percentage = float(f.read().strip())
        else:
            accuracy_percentage = None
        
        return model, scaler, accuracy_percentage
    else:
        return None, None, None

def delete_model_files():
    for file_name in os.listdir(MODEL_DIR):
        file_path = os.path.join(MODEL_DIR, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)
    print("Model files deleted.")

def check_and_delete_models():
    today = datetime.now().date()
    if os.path.exists(LAST_CHECKED_DAY_FILE):
        with open(LAST_CHECKED_DAY_FILE, 'r') as f:
            last_checked_day = f.read().strip()
        if last_checked_day != str(today):
            delete_model_files()
            with open(LAST_CHECKED_DAY_FILE, 'w') as f:
                f.write(str(today))
    else:
        delete_model_files()
        with open(LAST_CHECKED_DAY_FILE, 'w') as f:
            f.write(str(today))

def calculate_moving_average(data, window_size=60):
    moving_average = data.rolling(window=window_size).mean()
    moving_average.index = moving_average.index.strftime('%Y-%m-%d')
    return moving_average

def predict_next_days_price(symbol, days=5, mv=60, years='1y'):
    check_and_delete_models()
    model, scaler, accuracy_percentage = load_model_and_scaler(symbol, mv, years)
    if model is None or scaler is None or accuracy_percentage is None:
        historical_data = load_stock_data(symbol, years)
        model, scaler, accuracy_percentage = train_lstm_model(historical_data, symbol, mv, years)
    
    historical_data = load_stock_data(symbol, years)
    data = historical_data['Close'].values
    scaled_data = scaler.transform(data.reshape(-1, 1))

    
    # Predict future prices
    last_mv_days = scaled_data[-mv:]
    X_future = []
    X_future.append(last_mv_days)
    X_future = np.array(X_future)
    X_future = np.reshape(X_future, (X_future.shape[0], X_future.shape[1], 1))
    
    predicted_prices = []
    for _ in range(days):
        predicted_price = model.predict(X_future)
        predicted_prices.append(predicted_price[0][0])
        last_mv_days = np.append(last_mv_days[1:], predicted_price)
        X_future = []
        X_future.append(last_mv_days)
        X_future = np.array(X_future)
        X_future = np.reshape(X_future, (X_future.shape[0], X_future.shape[1], 1))
    
    predicted_prices = scaler.inverse_transform(np.array(predicted_prices).reshape(-1, 1))
    
    moving_average = calculate_moving_average(historical_data['Close'], mv)
    
    return moving_average, predicted_prices, accuracy_percentage