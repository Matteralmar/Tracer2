# Generated by Django 4.0 on 2022-07-31 07:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0040_alter_ticket_due_to'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='due_to',
            field=models.DateField(blank=True, null=True),
        ),
    ]