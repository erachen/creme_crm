# Generated by Django 2.2.11 on 2020-03-06 12:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('tickets', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='status',
            name='is_closed',
            field=models.BooleanField(default=False, verbose_name='Is a "closed" status?'),
        ),
    ]
