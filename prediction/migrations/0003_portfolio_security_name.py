# Generated by Django 5.1.1 on 2024-10-10 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prediction', '0002_remove_portfolio_stocks_portfolio_stock_symbol_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='portfolio',
            name='security_name',
            field=models.CharField(default='', max_length=255),
        ),
    ]