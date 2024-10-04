# Generated by Django 4.2.7 on 2024-10-03 20:43

from django.db import migrations, models
import users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0021_rename_city_job_location_remove_job_residence'),
    ]

    operations = [
        migrations.AddField(
            model_name='recruiter',
            name='recommendation_letter',
            field=models.FileField(blank=True, null=True, upload_to=users.models.recommendation_letter_upload_path),
        ),
    ]
