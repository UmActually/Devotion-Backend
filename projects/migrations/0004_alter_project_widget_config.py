# Generated by Django 5.0.4 on 2024-06-04 04:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0003_project_widget_config'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='widget_config',
            field=models.IntegerField(default=1877248),
        ),
    ]
