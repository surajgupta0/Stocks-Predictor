from django.db import models
from django.contrib.auth.models import User
from datetime import date

class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    stock_name = models.CharField(max_length=255)
    current_price = models.FloatField(default=0.0)
    change = models.FloatField(default=0.0)
    percentage_change = models.FloatField(default=0.0)
    volume = models.BigIntegerField(default=0.0)
    moving_average = models.FloatField(default=0.0)
    market_cap = models.BigIntegerField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.symbol
    

class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=255)
    stocks = models.ManyToManyField(Stock)

    def __str__(self):
        return self.symbol

class Alert(models.Model):
    ALERT_TYPES = [
        ('price_threshold', 'Price Threshold'),
        ('moving_average', 'Moving Average'),
        ('percentage_change', 'Percentage Change'),
        ('volume', 'Volume'),
    ]

    CONDITIONS = [
        ('above', 'Above'),
        ('below', 'Below'),
        ('crosses', 'Crosses'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.CharField(max_length=10)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, default='price_threshold')
    condition = models.CharField(max_length=20, choices=CONDITIONS, default='above')
    threshold = models.FloatField(default=0.0)
    expiry_date = models.DateField(default=date.today, max_length=10, null=True, blank=True)  # Changed to CharField
    created_at = models.DateTimeField(auto_now_add=True)
    notification_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.stock} - {self.get_alert_type_display()} - {self.get_condition_display()} - {self.threshold}"