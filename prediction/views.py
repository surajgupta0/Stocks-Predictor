from django.shortcuts import render, redirect, get_object_or_404
from .models import Stock, Portfolio, Alert
from .utils import fetch_live_data
from .lstm_model import predict_next_days_price, load_stock_data
from .forms import AlertForm
from django.contrib.auth.decorators import login_required
from background_task import background
from background_task.models import Task
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.http import JsonResponse
import datetime
import requests
import json
from datetime import datetime, timedelta
import asyncio
from django.core.cache import cache
import csv
import os
import pandas as pd
import yfinance as yf

@login_required
def toggle_portfolio(request):
    if request.method == "POST" :
        symbol = request.POST.get('symbol')
        security_name = request.POST.get('security_name')
        stock = get_object_or_404(Stock, symbol=symbol)
        # Check if the stock is already in the user's portfolio
        portfolio_item, created = Portfolio.objects.get_or_create(user=request.user, symbol=symbol)
        
        if created:
            # Item was added to the portfolio
            portfolio_item.stocks.add(stock)
            return JsonResponse({'status': 'added'})
        else:
            # Item already exists, so we remove it
            portfolio_item.delete()
            return JsonResponse({'status': 'removed'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
def portfolio(request):
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return render(request, 'portfolio.html')
        
    user_portfolio = Portfolio.objects.filter(user=request.user)
    portfolio_data = []
    
    paginator = Paginator(user_portfolio, 10)  # Show 10 stocks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    for portfolio in page_obj.object_list:
        stocks = portfolio.stocks.all()
        portfolio_data.append({
            'symbol': stocks[0].symbol,
            'security_name': stocks[0].stock_name,
            'current_price': stocks[0].current_price,
            'volume':  stocks[0].volume,
            'market_cap':  stocks[0].market_cap,
            'change':  stocks[0].change,
            'percent_change':  stocks[0].percentage_change,
        })


    return JsonResponse({
        'stock_data': portfolio_data,
        'has_previous': page_obj.has_previous(),
        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'has_next': page_obj.has_next(),
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        'page_number': page_obj.number,
        'total_pages': page_obj.paginator.num_pages,
    })

API_KEY = 'crv8hkpr01qpfkburgdgcrv8hkpr01qpfkburge0 '  # Replace with your Finnhub API key
def fetch_all_stocks():
    response = requests.get(f'https://finnhub.io/api/v1/stock/symbol?exchange=US&token={API_KEY}')
    return response.json()

@background(schedule=60*60*24)
def update_stock_data():
    print('Updating stock data...')
    all_stocks = fetch_all_stocks()
    count = 0
    for stock in all_stocks:
        symbol = stock['symbol']
        stock_name = stock['description']
        stock_data = fetch_live_data(symbol)
        count = count + 1
        print(f"Updating {symbol} ({count}/{len(all_stocks)})")
        try:
            Stock.objects.update_or_create(
                symbol=symbol,
                defaults={
                    'stock_name': stock_name,
                    'current_price': stock_data['current_price'],
                    'change': stock_data['change'],
                    'percentage_change': stock_data['percent_change'],
                    'volume': stock_data['volume'],
                    'moving_average': stock_data['moving_average'],
                    'market_cap': stock_data['market_cap'],
                    'last_updated': timezone.now()
                }
            )
        except Exception as e:
            print(f"Error updating {symbol}: {e}")

def is_task_scheduled(task_name):
    return Task.objects.filter(task_name=task_name, failed_at__isnull=True, run_at__gt=timezone.now()).exists()

def stock_list(request):
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return render(request, 'stock_list.html')
    
    if not is_task_scheduled('prediction.views.update_stock_data'):
        update_stock_data(repeat=60*30*24)  # Schedule to run every 24 hours
        
    stocks = Stock.objects.all()
    paginator = Paginator(stocks, 10)  # Show 10 stocks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    stock_data = [{
        'symbol': stock.symbol,
        'stock_name': stock.stock_name,
        'current_price': stock.current_price,
        'volume': stock.volume,
        'market_cap': stock.market_cap,
        'change': stock.change,
        'percent_change': stock.percentage_change,
    } for stock in page_obj.object_list]
    
    return JsonResponse({
        'stock_data': stock_data,
        'has_previous': page_obj.has_previous(),
        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'has_next': page_obj.has_next(),
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        'page_number': page_obj.number,
        'total_pages': page_obj.paginator.num_pages,
    })

def add_to_recently_viewed(request, data):
    recently_viewed = request.session.get('recently_viewed', {})
    symbol = list(data.keys())[0]
    if symbol not in recently_viewed:
        recently_viewed[symbol] = data[symbol]
        request.session['recently_viewed'] = recently_viewed

@login_required
def stock_detail(request, symbol):
    """
    Fetch detailed stock information such as historical data, summary, news, charts, and statistics.
    """
    
    stock = yf.Ticker(symbol)
    api_key = 'crv8hkpr01qpfkburgdgcrv8hkpr01qpfkburge0'
    
    # Fetch historical data (e.g., last 1 year of data)
    historical_data = stock.history(period='max')
    
    if historical_data.empty:
        return render(request, 'not_found.html')
    
    # Convert DataFrame rows to dictionaries
    data_as_dict = historical_data.sort_values(by='Date', ascending=False).reset_index().to_dict(orient='records')
    
    # Pagination for historical data
    paginator = Paginator(data_as_dict, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Fetch stock summary and statistics
    stock_info = stock.info
    sess = request.session.get('recently_viewed', {})
    
    stock_in_portfolio = Portfolio.objects.filter(user=request.user, symbol=symbol).exists()
    
    try:
        # Fetch summary data
        market_cap = stock_info.get('marketCap', 'N/A')
        stock_name = stock_info.get('longName','NA')
        current_price = historical_data['Close'][-1]
        previous_close = stock_info.get('previousClose', 'N/A')
        open_price = stock_info.get('open', 'N/A')
        bid = stock_info.get('bid', 'N/A')
        bid_size = stock_info.get('bidSize', 'N/A')
        ask = stock_info.get('ask', 'N/A')
        ask_size = stock_info.get('askSize', 'N/A')
        day_range = '$'+str(stock_info.get('dayLow', 'N/A'))+' - $'+ str(stock_info.get('dayHigh', 'N/A'))
        week_52_range = '$'+str(stock_info.get('fiftyTwoWeekLow', 'N/A'))+' - $'+ str(stock_info.get('fiftyTwoWeekHigh', 'N/A'))
        volume = stock_info.get('volume', 'N/A')
        avg_volume = stock_info.get('averageVolume', 'N/A')
        net_assets = stock_info.get('totalAssets', 'N/A')
        nav = stock_info.get('navPrice', 'N/A')
        pe_ratio = stock_info.get('trailingPE', '--')  # Might not always be available
        yield_percentage = stock_info.get('yield', 'N/A')
        ytd_return = stock_info.get('ytdReturn', 'N/A')
        beta = stock_info.get('beta', 'N/A')
        expense_ratio = stock_info.get('annualHoldingsTurnover', 'N/A')
        news = stock.news  
        chart_data = historical_data[['Close']]
        opening = historical_data['Open'][-1]
        closing = historical_data['Close'][-1]
        change = round(float(closing - opening), 2)
        percent_change = (change / opening) * 100 if opening != 0 else 0
        financial_data = fetch_financial_data(symbol)
        context = {
            'symbol': symbol,
            'page_obj': page_obj,
            'current_price':current_price,
            'previous_close': previous_close,
            'open_price': open_price,
            'bid': bid,
            'bid_size':bid_size,
            'ask':ask,
            'ask_size': ask_size,
            'historical_data': historical_data,
            'market_cap': market_cap,
            'pe_ratio': pe_ratio,
            'day_range': day_range,
            'week_52_range': week_52_range,
            'net_assets': net_assets,
            'nav': nav,
            'beta': beta,
            'yield_percentage': yield_percentage,
            'ytd_return': ytd_return,
            'volume': volume,
            'avg_volume': avg_volume,
            'expense_ratio': expense_ratio,
            'news': news,
            'stock_name':stock_name,
            'chart_data': chart_data.to_dict(),
            'recently_viewed': dict(reversed(list(sess.items()))),
            'stock_in_portfolio': stock_in_portfolio,
            'financial_data': financial_data,
            'chart_data' : prepare_chart_data(financial_data)
        }
    except IndexError:
        context = {
            'symbol': symbol,
            'page_obj': page_obj,
            'current_price' : 'N/A',
            'previous_close': 'N/A', 
            'open_price': 'N/A', 
            'bid': 'N/A', 
            'bid_size': 'N/A',
            'ask': 'N/A',
            'ask_size': 'N/A', 
            'historical_data': 'N/A', 
            'market_cap': 'N/A', 
            'pe_ratio': 'N/A', 
            'day_range': 'N/A', 
            'week_52_range': 'N/A', 
            'net_assets': 'N/A', 
            'nav': 'N/A', 
            'beta': 'N/A', 
            'yield_percentage': 'N/A', 
            'ytd_return': 'N/A', 
            'volume': 'N/A', 
            'avg_volume': 'N/A', 
            'expense_ratio': 'N/A', 
            'news': 'N/A', 
            'stock_name': 'N/A',
            'chart_data': 'N/A',
            'chart_data': chart_data.to_dict(),
            'recently_viewed': dict(reversed(list(sess.items()))),
            'stock_in_portfolio': stock_in_portfolio,
            'financial_data': financial_data,
            'chart_data' : prepare_chart_data(financial_data)
        }
    
    if(len(sess) >= 5):
        sess.pop(list(sess.items())[0][0])
    data = {symbol:{
                'name':stock_name,
                'current_price':round(current_price,2),
                'change': round(change,2),
                'percent_change':round(percent_change,2)
    }}
    
    add_to_recently_viewed(request,data)
    return render(request, 'stock_details.html', context)

def prepare_chart_data(financial_data):
    chart_data = {
        'labels': [],
        'total_assets': [],
        'total_liabilities': [],
        'total_equity': []
    }
    for report in financial_data:
        chart_data['labels'].insert(0, report['fiscalDateEnding'])
        chart_data['total_assets'].insert(0,report['totalAssets'])
        chart_data['total_liabilities'].insert(0,report['totalLiabilities'])
        chart_data['total_equity'].insert(0,report['totalShareholderEquity'])
    return chart_data

ALPHA_VANTAGE_API_KEY = 'VGUHOPQA1DK8HNBS'
def fetch_financial_data(symbol):
    url = f'https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}'
    response = requests.get(url)
    data = response.json()
    return data.get('annualReports', [])

def get_stock_data(request, symbol):
    """
    API view to fetch historical stock data for a given symbol and period.
    """
    period = request.GET.get('period', '1y')  # Default to 1 year if no period is specified
    stock = yf.Ticker(symbol)
    if period == '1d':
        historical_data = stock.history(period=period, interval='1m')
    else:
        historical_data = stock.history(period=period)
        
    historical_data.dropna(inplace=True)
    
    try:
        historical_data = stock.history(period=period)
    except Exception:
        historical_data = stock.history(period='max')
    # Convert the index (which contains Timestamp objects) to strings
    historical_data.index = historical_data.index.strftime('%Y-%m-%d')

    # Extract the closing price and date
    close_data = historical_data['Close'].to_dict()  # Convert to dictionary
    open_data = historical_data['Open'].to_dict()  # Convert to dictionary
    
    return JsonResponse({'Close': close_data,'Open': open_data, 'period': period})


def search_suggestions(request):
    
    
    all_stocks = Stock.objects.all().values('symbol', 'stock_name')
    
    query = request.GET.get('q', '').lower()
    suggestions = []
    result = []
    
    for stock in all_stocks:
        symbol = stock['symbol'].lower()
        name = stock['stock_name'].lower()

        # Check if the query matches the symbol or name
        if query in symbol or query in name:
            result.append(stock)
    suggestions = [{'symbol': res['symbol'], 'name': res['stock_name']} for res in result]

    return JsonResponse(suggestions, safe=False)

FINNHUB_API_KEY = 'crv8hkpr01qpfkburgdgcrv8hkpr01qpfkburge0'
FINNHUB_HOLIDAYS_URL = 'https://finnhub.io/api/v1/stock/market-holiday?exchange=US&token=' + FINNHUB_API_KEY

def get_public_holidays():
    response = requests.get(FINNHUB_HOLIDAYS_URL)
    holidays = response.json()
    holiday_dates = [holiday['atDate'] for holiday in holidays['data']]
    return holiday_dates

def exclude_weekends_and_holidays(dates):
    holidays = get_public_holidays()
    filtered_dates = []
    for date in dates:
        if date.weekday() < 5 and date.strftime('%Y-%m-%d') not in holidays:
            filtered_dates.append(date)
    return filtered_dates

def predict_stock(request):
    if request.method == 'POST':
        symbol = request.POST['symbol']
        days = int(request.POST['days'])
        moving_avg_window = int(request.POST['moving_avg'])
        years = request.POST['years']
        
        moving_average, predicted_prices, accuracy_percentage = predict_next_days_price(symbol, days, moving_avg_window, years)
        historical_data = load_stock_data(symbol,years)
        historical_prices = historical_data['Close'].values.tolist()
        dates = historical_data.index.strftime('%Y-%m-%d').tolist()
        real_stock_price = historical_prices[-days:]
        model_prices = predicted_prices[:days].flatten().tolist()
        
        future_dates = [(datetime.now() + timedelta(days=i)).date() for i in range(1, days + 1)]
        future_dates = exclude_weekends_and_holidays(future_dates)
        
        predicted_prices_with_dates = dict(list(zip([date.strftime('%Y-%m-%d') for date in future_dates], model_prices)))
        
        # Align moving average dates with historical data dates
        moving_average = moving_average.dropna()

        current_price = float(historical_data['Close'][-1])
        pred_price = float(model_prices[-1] if model_prices != 'None' else 0)
        
        changes = round(pred_price - current_price, 2)
        percent_change = round((changes / current_price) * 100, 2)
        
        context = {
            'predicted_prices': predicted_prices_with_dates,
            'accuracy_score': accuracy_percentage,
            'moving_average': json.dumps(moving_average.to_dict()),
            'real_stock_price': json.dumps(real_stock_price),
            'historical_prices': json.dumps(historical_prices[moving_avg_window:]),
            'dates': json.dumps(dates[moving_avg_window:]),
            'future_dates': json.dumps([date.strftime('%Y-%m-%d') for date in future_dates]),
            'post': request.POST,
            'symbol': symbol,
            'stock_name' : yf.Ticker(symbol).info.get('longName','NA'),
            'current_price' : current_price,
            'changes': changes,
            'percent_change': percent_change,
        }
        
        return render(request, 'stock_prediction.html', context)
    
    return render(request, 'stock_prediction.html')

NEWS_API_KEY = 'df3d782d8e35493abb300208eed1f3d8'  # Replace with your News API key

def fetch_news(query=None, category=None):
    url = 'https://newsapi.org/v2/top-headlines'
    params = {
        'apiKey': NEWS_API_KEY,
        'country': 'us',
    }
    if query:
        params['q'] = query
    if category:
        params['category'] = category

    response = requests.get(url, params=params)
    return response.json().get('articles', [])

def news_list(request):
    query = request.GET.get('q')
    category = request.GET.get('category')
    articles = fetch_news(query=query, category=category)

    categories = [
        'business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology'
    ]
    return render(request, 'news_list.html', {'articles': articles, 'categories': categories})


@login_required
def alerts_view(request):
    alerts = Alert.objects.filter(user=request.user).order_by('-created_at')
    if request.method == 'POST':
        form = AlertForm(request.POST)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.user = request.user
            alert.save()
            return redirect('alerts')
        else:
            print(form.errors)  # Debugging: Print form errors
    else:
        form = AlertForm()
    return render(request, 'alert_settings.html', {'form': form, 'alerts': alerts})

@login_required
def get_alert(request, alert_id):
    alert = get_object_or_404(Alert, id=alert_id, user=request.user)
    data = {
        'stock': alert.stock,
        'alert_type': alert.alert_type,
        'condition': alert.condition,
        'threshold': alert.threshold,
        'expiry_date': alert.expiry_date,
    }
    return JsonResponse(data)

@login_required
def update_alert(request, alert_id):
    alert = get_object_or_404(Alert, id=alert_id, user=request.user)
    if request.method == 'POST':
        form = AlertForm(request.POST, instance=alert)
        if form.is_valid():
            form.save()
            return redirect('alerts')
    else:
        form = AlertForm(instance=alert)
    return render(request, 'alert_settings.html', {'form': form, 'alerts': Alert.objects.filter(user=request.user).order_by('-created_at')})

@login_required
def delete_alert(request, alert_id):
    alert = get_object_or_404(Alert, id=alert_id, user=request.user)
    if request.method == 'POST':
        alert.delete()
        return redirect('alerts')
    return render(request, 'alert_settings.html', {'form': AlertForm(), 'alerts': Alert.objects.filter(user=request.user).order_by('-created_at')})