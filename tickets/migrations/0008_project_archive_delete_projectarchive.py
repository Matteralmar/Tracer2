# Generated by Django 4.0 on 2022-07-12 23:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0007_projectarchive'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='archive',
            field=models.BooleanField(default=False),
        ),
        migrations.DeleteModel(
            name='ProjectArchive',
        ),
    ]
