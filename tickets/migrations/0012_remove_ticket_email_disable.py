# Generated by Django 4.0 on 2022-07-20 14:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0011_alter_project_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticket',
            name='email_disable',
        ),
    ]
