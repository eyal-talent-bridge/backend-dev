# Generated by Django 4.2.7 on 2024-10-04 14:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0025_talent_notified_jobs'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='talent',
            name='notified_jobs',
        ),
    ]