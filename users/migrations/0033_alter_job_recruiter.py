# Generated by Django 4.2.7 on 2024-10-26 16:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0032_remove_talent_age_talent_birth_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='recruiter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='jobs', to='users.recruiter'),
        ),
    ]