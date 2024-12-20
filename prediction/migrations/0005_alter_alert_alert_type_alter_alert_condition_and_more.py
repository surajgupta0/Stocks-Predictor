# Generated by Django 5.1.1 on 2024-10-19 10:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prediction', '0004_alert'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alert',
            name='alert_type',
            field=models.CharField(choices=[('price_threshold', 'Price Threshold'), ('moving_average', 'Moving Average'), ('percentage_change', 'Percentage Change'), ('predicted_price', 'Predicted Price'), ('volume', 'Volume')], default='price_threshold', max_length=20),
        ),
        migrations.AlterField(
            model_name='alert',
            name='condition',
            field=models.CharField(choices=[('above', 'Above'), ('below', 'Below'), ('crosses', 'Crosses'), ('percentage_gain', 'Percentage Gain'), ('percentage_loss', 'Percentage Loss')], default='above', max_length=20),
        ),
        migrations.AlterField(
            model_name='alert',
            name='expiry_date',
            field=models.DateField(blank=True, max_length=10, null=True),
        ),
    ]
