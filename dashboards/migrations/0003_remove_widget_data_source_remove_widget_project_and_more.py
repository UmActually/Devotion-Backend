# Generated by Django 5.0.4 on 2024-06-03 21:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0002_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='widget',
            name='data_source',
        ),
        migrations.RemoveField(
            model_name='widget',
            name='project',
        ),
        migrations.DeleteModel(
            name='DataSource',
        ),
        migrations.DeleteModel(
            name='Widget',
        ),
    ]
