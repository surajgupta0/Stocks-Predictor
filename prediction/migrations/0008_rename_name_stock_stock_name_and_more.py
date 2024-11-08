# Generated by Django 5.1.1 on 2024-10-22 11:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prediction', '0007_alert_notification_sent_alter_alert_alert_type_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stock',
            old_name='name',
            new_name='stock_name',
        ),
        migrations.RemoveField(
            model_name='stock',
            name='past_performance_score',
        ),
        migrations.RemoveField(
            model_name='stock',
            name='sector',
        ),
        migrations.RemoveField(
            model_name='stock',
            name='stock_type',
        ),
        migrations.RemoveField(
            model_name='stock',
            name='volatility',
        ),
        migrations.AddField(
            model_name='stock',
            name='change',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='stock',
            name='last_updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='stock',
            name='moving_average',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='stock',
            name='percentage_change',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='stock',
            name='volume',
            field=models.BigIntegerField(default=0.0),
        ),
        migrations.AlterField(
            model_name='stock',
            name='current_price',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='stock',
            name='market_cap',
            field=models.BigIntegerField(default=0.0),
        ),
        migrations.AlterField(
            model_name='stock',
            name='symbol',
            field=models.CharField(max_length=10, unique=True),
        ),
    ]