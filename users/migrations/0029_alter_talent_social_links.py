# Generated by Django 4.2.7 on 2024-10-06 05:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0028_customuser_newsletter'),
    ]

    operations = [
        migrations.AlterField(
            model_name='talent',
            name='social_links',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
