from django.urls import path
from . import views

urlpatterns = [
    path('toggle-portfolio/', views.toggle_portfolio, name='toggle_portfolio'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('prediction', views.predict_stock, name='predict_stock'),
    path('', views.stock_list, name='dashboard'),
    path('stocks/<str:symbol>/', views.stock_detail, name='stock_details'),
    path('api/stock-data/<str:symbol>/', views.get_stock_data, name='get_stock_data'),
    path('search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('news/', views.news_list, name='news_list'),
    path('alerts/', views.alerts_view, name='alerts'),
    path('get_alert/<int:alert_id>/', views.get_alert, name='get_alert'),
    path('update_alert/<int:alert_id>/', views.update_alert, name='update_alert'),
    path('delete_alert/<int:alert_id>/', views.delete_alert, name='delete_alert'),
]
