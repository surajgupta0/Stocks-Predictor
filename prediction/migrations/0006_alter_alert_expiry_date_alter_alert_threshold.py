# Generated by Django 5.1.1 on 2024-10-19 18:32

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prediction', '0005_alter_alert_alert_type_alter_alert_condition_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alert',
            name='expiry_date',
            field=models.DateField(blank=True, default=datetime.date.today, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='alert',
            name='threshold',
            field=models.FloatField(default=0.0),
        ),
    ]
