import uuid
from django.db import models


class DataSource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, null=False, blank=False)
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="data_sources",
    )
    mqtt_topic = models.CharField(max_length=64, null=False, blank=False)

    def __str__(self):
        return self.mqtt_topic


class WidgetDisplayType(models.IntegerChoices):
    NUMBER = 0, "Number"
    BAR_CHART = 1, "Bar chart"
    LINE_CHART = 2, "Line chart"
    PIE_CHART = 3, "Pie chart"
    GAUGE = 4, "Gauge"
    TABLE = 5, "Table"


class Widget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, null=False, blank=False)
    display_type = models.SmallIntegerField(
        choices=WidgetDisplayType.choices, null=False, blank=False
    )
    data_source = models.ForeignKey(
        "DataSource", on_delete=models.CASCADE, null=False, blank=False
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="widgets",
    )
    position = models.SmallIntegerField(null=False, blank=False)
    unit = models.CharField(max_length=16, null=True, blank=True)

    def __str__(self):
        return self.name
