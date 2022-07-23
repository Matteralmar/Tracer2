# Generated by Django 4.0 on 2022-07-23 20:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0025_remove_user_ticket_flow_user_ticket_flow'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='tester',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tickets.user'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tickets', to='tickets.user'),
        ),
    ]
