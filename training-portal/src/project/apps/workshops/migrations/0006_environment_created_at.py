# Generated by Django 3.2.20 on 2023-07-18 04:07

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('workshops', '0005_auto_20230718_0356'),
    ]

    operations = [
        migrations.AddField(
            model_name='environment',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
