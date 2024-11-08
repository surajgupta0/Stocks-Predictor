from django.contrib import admin
from .models import Portfolio, Alert, Stock


admin.site.register(Portfolio)
admin.site.register(Alert)
admin.site.register(Stock)