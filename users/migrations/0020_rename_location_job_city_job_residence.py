# Generated by Django 4.2.7 on 2024-10-03 08:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_alter_company_divisions'),
    ]

    operations = [
        migrations.RenameField(
            model_name='job',
            old_name='location',
            new_name='city',
        ),
        migrations.AddField(
            model_name='job',
            name='residence',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]