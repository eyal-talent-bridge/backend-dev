# Generated by Django 4.2.7 on 2024-10-27 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0033_alter_job_recruiter'),
    ]

    operations = [
        migrations.AddField(
            model_name='talent',
            name='desired_salary',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
    ]