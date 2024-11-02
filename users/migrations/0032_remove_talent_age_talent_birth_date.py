# Generated by Django 4.2.7 on 2024-10-15 19:40

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0031_talent_age'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='talent',
            name='age',
        ),
        migrations.AddField(
            model_name='talent',
            name='birth_date',
            field=models.DateField(default=datetime.date.today),
        ),
    ]