# Stock Predictor

This project is a stock prediction application built with Django. It uses LSTM models to predict future stock prices based on historical data.

## Features

- Predict future stock prices using LSTM models
- View historical stock data
- Search for stock symbols and names
- User authentication and profile management
- Password reset functionality

## Project Structure



## Installation

1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd stock_predictor
    ```

2. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Apply the migrations:
    ```sh
    python manage.py migrate
    ```

4. Create a superuser:
    ```sh
    python manage.py createsuperuser
    ```

5. Run the development server:
    ```sh
    python manage.py runserver
    ```

## Usage

- Access the application at `http://127.0.0.1:8000/`
- Use the admin panel at `http://127.0.0.1:8000/admin/` to manage users and data

## Configuration

- Update the `FINNHUB_API_KEY` in [`prediction/views.py`](prediction/views.py) with your Finnhub API key.
- Configure the database settings in [`stock_predictor/settings.py`](stock_predictor/settings.py).

## License

This project is licensed under the MIT License.
