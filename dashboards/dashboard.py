from typing import Any, Callable

from rest_framework import status
from rest_framework.response import Response

from projects.models import Project
from tasks.models import Task
from tasks.subtasks import get_all_subtree
from .metrics import WidgetType, project_metrics


JSONObject = dict[str, Any] | list[Any] | int


def metric(func: Callable) -> Callable:
    if func.__name__ not in project_metrics:
        raise ValueError(f"Unknown metric: {func.__name__}")
    return func


def get_widget_configuration(config_number: int) -> dict[str, WidgetType]:
    """Convierte un número entero en una configuración de vistas de widgets."""
    metrics = list(project_metrics.keys())
    configuration = {}

    for metric_name in metrics:
        widget_type = config_number % 8
        config_number //= 8
        configuration[metric_name] = WidgetType(widget_type)

    return configuration


def get_config_number(configuration: dict[str, WidgetType]) -> int:
    """Convierte una configuración de vistas de widgets a un número entero."""
    power_eight = 0
    number = 0

    for name, widget_type in configuration.items():
        number += widget_type * (8 ** power_eight)
        power_eight += 1

    return number


class Dashboard:
    def __init__(self, project: Project) -> None:
        self.project = project
        self.configuration = get_widget_configuration(project.widget_config)
        self.response_dict: JSONObject = {}

    def get_response(self) -> Response:
        for metric_name in project_metrics:
            try:
                widget = getattr(self, metric_name)
            except AttributeError:
                continue

            resp = widget(self.configuration[metric_name])
            if resp is not None:
                self.response_dict[metric_name] = resp

        return Response(self.response_dict, status=status.HTTP_200_OK)

    @metric
    def done_tasks_count(self, widget_type: WidgetType) -> JSONObject:
        done_tasks = self.project.tasks.filter(
            parent_task=None,
            status=Task.Status.DONE
        )
        return done_tasks.count()

    @metric
    def all_done_tasks_count(self, widget_type: WidgetType) -> JSONObject:
        done_tasks = get_all_subtree(self.project).filter(
            status=Task.Status.DONE
        )
        return done_tasks.count()

    @metric
    def done_tasks_by_date(self, widget_type: WidgetType) -> JSONObject:
        done_tasks = self.project.tasks.filter(
            parent_task=None,
            status=Task.Status.DONE
        ).order_by("due_date")

        grouped_tasks = {}

        for task in done_tasks:
            due_date = str(task.due_date)
            if due_date not in grouped_tasks:
                grouped_tasks[due_date] = []
            grouped_tasks[due_date].append(task)

        if widget_type in (WidgetType.LINE, WidgetType.VERTICAL_BAR):
            return [
                {"date": key, "count": len(value)}
                for key, value in grouped_tasks.items()
            ]
        else:
            # Heatmap
            max_count = max(len(value) for value in grouped_tasks.values())
            return [
                {"date": key, "count": len(value) / max_count}
                for key, value in grouped_tasks.items()
            ]
