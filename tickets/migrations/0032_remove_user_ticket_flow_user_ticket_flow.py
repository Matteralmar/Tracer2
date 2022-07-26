# Generated by Django 4.0 on 2022-07-25 12:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0031_remove_user_ticket_flow_user_ticket_flow'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='ticket_flow',
        ),
        migrations.AddField(
            model_name='user',
            name='ticket_flow',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tickets.project'),
        ),
    ]
