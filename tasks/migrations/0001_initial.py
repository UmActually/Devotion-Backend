# Generated by Django 5.0.4 on 2024-05-28 19:26

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
                ('description', models.TextField(blank=True, max_length=1024, null=True)),
                ('status', models.SmallIntegerField(choices=[(0, 'Not started'), (1, 'In progress'), (2, 'In review'), (3, 'Done')])),
                ('priority', models.SmallIntegerField(choices=[(0, 'Low'), (1, 'Medium'), (2, 'High')])),
                ('start_date', models.DateField()),
                ('due_date', models.DateField()),
                ('event_id', models.CharField(max_length=32)),
            ],
        ),
    ]
