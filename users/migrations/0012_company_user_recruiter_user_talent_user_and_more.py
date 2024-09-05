# Generated by Django 5.0.8 on 2024-09-05 16:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_remove_company_user_remove_recruiter_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='user',
            field=models.OneToOneField(default='a86619c9-8728-4dd1-83b4-da460fa46fda', on_delete=django.db.models.deletion.CASCADE, related_name='company_profile', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='recruiter',
            name='user',
            field=models.OneToOneField(default='a86619c9-8728-4dd1-83b4-da460fa46fda', on_delete=django.db.models.deletion.CASCADE, related_name='recruiter_profile', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='talent',
            name='user',
            field=models.OneToOneField(default='a86619c9-8728-4dd1-83b4-da460fa46fda', on_delete=django.db.models.deletion.CASCADE, related_name='talent_profile', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='company',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='recruiter',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='talent',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
