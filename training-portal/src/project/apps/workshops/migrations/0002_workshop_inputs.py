# Generated by Django 3.2.18 on 2023-04-12 01:09

from django.db import migrations
import project.apps.workshops.models


class Migration(migrations.Migration):

    dependencies = [
        ('workshops', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='workshop',
            name='inputs',
            field=project.apps.workshops.models.JSONField(default=[], verbose_name='request inputs'),
        ),
    ]
