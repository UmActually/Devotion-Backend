# Generated by Django 5.0.4 on 2024-05-28 19:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dashboards', '0001_initial'),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='datasource',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='data_sources', to='projects.project'),
        ),
        migrations.AddField(
            model_name='widget',
            name='data_source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboards.datasource'),
        ),
        migrations.AddField(
            model_name='widget',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='widgets', to='projects.project'),
        ),
    ]
