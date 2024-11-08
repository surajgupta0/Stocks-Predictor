import yfinance as yf
from django.core.mail import send_mail
from django.conf import settings

def fetch_live_data(symbol):
    """
    Fetch real-time data for a given stock symbol using yfinance.
    Returns a dictionary with price, volume, market cap, and 52-week change.
    """
    stock = yf.Ticker(symbol)
    data = stock.history(period="max")  # Get the last 5 days of data
        
    try:
        current_price = data['Close'][-1]  # Today's closing price
        opening = data['Open'][-1]  # Previous day's closing price
        closing = data['Close'][-1]
        volume = data['Volume'][-1]
        change = round(float(closing - opening), 2)
        percent_change = (change / opening) * 100 if opening != 0 else 0
        market_cap = str(stock.info.get('marketCap',0)).replace('-', '')
        return {
            'symbol': symbol,
            'current_price': current_price,
            'volume': volume,
            'market_cap': market_cap,
            'percent_change': round(float(percent_change),3),
            'change': change,
            'moving_average': calculate_moving_average(data['Close'], 5)  # Calculate 5-day moving average
        }
    except IndexError:
        return {
            'symbol': symbol,
            'current_price': '0',
            'volume': '0',
            'market_cap': '0',
            'percent_change': 0,
            'change': 0,
            'moving_average': 0
        }
        
def calculate_moving_average(prices, period):
    if len(prices) < period:
        return None  # Not enough data to calculate the moving average
    return sum(prices[-period:]) / period

def send_alert_email(user, alert):
    subject = f"Stock Alert: {alert.stock}"
    message = f"Your alert for {alert.stock} has been triggered.\n\nCondition: {alert.get_condition_display()}\nThreshold: {alert.threshold}\n\nThank you for using StockSavvy!"
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    send_mail(subject, message, email_from, recipient_list)