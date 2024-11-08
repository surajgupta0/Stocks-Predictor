# tasks.py

from background_task import background
from django.core.mail import send_mail
from django.conf import settings
from .models import Alert
from .utils import fetch_live_data, send_alert_email
from datetime import date

@background(schedule=60)  # Schedule to run every 60 seconds
def check_alerts():
    alerts = Alert.objects.filter(notification_sent=False, expiry_date__gte=date.today())
    for alert in alerts:
        live_data = fetch_live_data(alert.stock)
        if evaluate_alert_condition(alert, live_data):
            send_alert_email(alert.user, alert)
            alert.notification_sent = True
            alert.save()

def evaluate_alert_condition(alert, live_data):
    """
    Evaluate if the alert condition is met based on the live data.
    """
    if alert.alert_type == 'price_threshold':
        if alert.condition == 'above' and live_data['current_price'] > alert.threshold:
            return True
        elif alert.condition == 'below' and live_data['current_price'] < alert.threshold:
            return True
        elif alert.condition == 'crosses' and live_data['current_price'] == alert.threshold:
            return True
    elif alert.alert_type == 'percentage_change':
        if alert.condition == 'above' and live_data['percent_change'] > alert.threshold:
            return True
        elif alert.condition == 'below' and live_data['percent_change'] < alert.threshold:
            return True
        elif alert.condition == 'crosses' and live_data['percent_change'] == alert.threshold:
            return True
    elif alert.alert_type == 'moving_average':
        if alert.condition == 'above' and live_data['moving_average'] > alert.threshold:
            return True
        elif alert.condition == 'below' and live_data['moving_average'] < alert.threshold:
            return True
        elif alert.condition == 'crosses' and live_data['moving_average'] == alert.threshold:
            return True
    elif alert.alert_type == 'volume':
        if alert.condition == 'above' and live_data['volume'] > alert.threshold:
            return True
        elif alert.condition == 'below' and live_data['volume'] < alert.threshold:
            return True
        elif alert.condition == 'crosses' and live_data['volume'] == alert.threshold:
            return True
    # Add more alert types and conditions as needed
    return False

def send_alert_email(user, alert):
    subject = f"Stock Alert: {alert.stock}"
    message = f"Your alert for {alert.stock} has been triggered.\n\nCondition: {alert.get_condition_display()}\nThreshold: {alert.threshold}\n\nThank you for using StockSavvy!"
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    send_mail(subject, message, email_from, recipient_list)
    

def fetch_live_data(stock_symbol):
    # Replace with your actual API call
    stock = yf.Ticker(symbol)
    data = stock.history(period="max")
    return {
        'price': data['Close'][-1],
        'percentage_change': (change / opening) * 100 if opening != 0 else 0,
        'moving_average': data.get('moving_average'),  # Add moving average if available
        'volume': data['Volume'][-1],
    }
    
def calculate_moving_average(prices, period):
    if len(prices) < period:
        return None  # Not enough data to calculate the moving average
    return sum(prices[-period:]) / period