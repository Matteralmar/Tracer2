# Generated by Django 4.0 on 2022-08-11 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='title',
            field=models.CharField(max_length=32),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='deadline',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.TextField(choices=[('Roles', (('tester', 'Tester'), ('developer', 'Developer'), ('project_manager', 'Project Manager'))), ('Actions', (('tester', 'Inspect'), ('developer', 'Contribute'), ('project_manager', 'Manage')))]),
        ),
    ]