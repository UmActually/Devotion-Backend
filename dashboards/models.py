from django.db import models


class DataSource(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, null=False, blank=False)
    mqtt_topic = models.CharField(max_length=64, null=False, blank=False)

    def __str__(self):
        return self.name


class WidgetDisplayType(models.IntegerChoices):
    NUMBER = 0, "Number"
    BAR_CHART = 1, "Bar chart"
    LINE_CHART = 2, "Line chart"
    PIE_CHART = 3, "Pie chart"
    GAUGE = 4, "GAUGE"
    TABLE = 5, "Table"


class Widget(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False)
    display_type = models.SmallIntegerField(choices=WidgetDisplayType.choices, null=False, blank=False)
    data_source = models.ForeignKey('DataSource', on_delete=models.CASCADE, null=False, blank=False)
    dashboard = models.ForeignKey('Dashboard', on_delete=models.CASCADE, null=False, blank=False)
    position = models.SmallIntegerField(null=False, blank=False)
    unit = models.CharField(max_length=16, null=True, blank=True)

    def __str__(self):
        return self.name


class Dashboard(models.Model):
    def __str__(self):
        return self.project.name
