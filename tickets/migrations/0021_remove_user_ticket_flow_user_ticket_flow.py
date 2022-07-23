# Generated by Django 4.0 on 2022-07-22 22:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0020_remove_user_ticket_flow_user_ticket_flow'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='ticket_flow',
        ),
        migrations.AddField(
            model_name='user',
            name='ticket_flow',
            field=models.ManyToManyField(blank=True, null=True, to='tickets.Project'),
        ),
    ]
