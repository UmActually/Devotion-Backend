# Generated by Django 5.0.4 on 2024-05-28 19:26

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DataSource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=64)),
                ('mqtt_topic', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='Widget',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=64)),
                ('display_type', models.SmallIntegerField(choices=[(0, 'Number'), (1, 'Bar chart'), (2, 'Line chart'), (3, 'Pie chart'), (4, 'Gauge'), (5, 'Table')])),
                ('position', models.SmallIntegerField()),
                ('unit', models.CharField(blank=True, max_length=16, null=True)),
            ],
        ),
    ]
