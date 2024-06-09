import uuid
from django.db import models
from dashboards.metrics import project_metrics, WidgetType

INT_BASE = len(WidgetType)


def get_widget_configuration(config_number: int) -> dict[str, WidgetType]:
    """Convierte un número entero en una configuración de vistas de widgets."""
    metrics = list(project_metrics.keys())
    configuration = {}

    for metric_name in metrics:
        widget_type = config_number % INT_BASE
        config_number //= INT_BASE
        configuration[metric_name] = WidgetType(widget_type)

    return configuration


def get_config_number(configuration: dict[str, WidgetType]) -> int:
    """Convierte una configuración de vistas de widgets a un número entero."""
    exponent = 0
    number = 0

    for name, widget_type in configuration.items():
        number += widget_type * (INT_BASE ** exponent)
        exponent += 1

    return number


DEFAULT_WIDGET_CONFIG = {
    "done_tasks_count": WidgetType.NUMBER,
    "all_done_tasks_count": WidgetType.NUMBER,
    "done_tasks_by_date": WidgetType.LINE,
    "tasks_by_status": WidgetType.VERTICAL_BAR,
    "tasks_by_priority": WidgetType.VERTICAL_BAR,
    "user_workload": WidgetType.NUMBERS,
    "project_progress": WidgetType.GAUGE,
    "all_project_progress": WidgetType.GAUGE
}

assert len(DEFAULT_WIDGET_CONFIG) == len(project_metrics), "La configuración de widgets no coincide con las métricas."
DEFAULT_WIDGET_CONFIG = get_config_number(DEFAULT_WIDGET_CONFIG)


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, null=False, blank=False)
    description = models.TextField(max_length=1024, null=True, blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="projects")
    leaders = models.ManyToManyField("users.User", related_name="leader_of")
    members = models.ManyToManyField("users.User", related_name="member_of")
    progress = models.FloatField(default=0, null=False, blank=False)
    widget_config = models.IntegerField(default=DEFAULT_WIDGET_CONFIG, null=False, blank=False)
    calendar_id = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return self.name
