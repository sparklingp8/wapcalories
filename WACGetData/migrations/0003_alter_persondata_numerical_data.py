# Generated by Django 4.0.6 on 2024-08-07 12:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WACGetData', '0002_alter_persondata_numerical_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='persondata',
            name='numerical_data',
            field=models.JSONField(),
        ),
    ]
