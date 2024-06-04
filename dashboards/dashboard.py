from typing import Any, Callable

from django.db.models.query import QuerySet
from rest_framework import status
from rest_framework.response import Response

from projects.models import Project, get_widget_configuration
from tasks.models import Task
from tasks.subtasks import get_all_subtree
from .metrics import WidgetType, project_metrics


JSONObject = dict[str, Any] | list[Any] | int


def metric(func: Callable) -> Callable:
    if func.__name__ not in project_metrics:
        raise ValueError(f"Unknown metric: {func.__name__}")
    return func


class Dashboard:
    USE_TEST_WIDGET_CONFIG = False
    TEST_WIDGET_CONFIG = {
        "done_tasks_count": WidgetType.NUMBER,
        "all_done_tasks_count": WidgetType.NUMBER,
        "done_tasks_by_date": WidgetType.LINE,
        "tasks_by_status": WidgetType.VERTICAL_BAR,
        "tasks_by_priority": WidgetType.VERTICAL_BAR,
        "user_workload": WidgetType.NUMBERS,
        "project_progress": WidgetType.GAUGE,
        "all_project_progress": WidgetType.GAUGE
    }

    def __init__(self, project: Project) -> None:
        self.project = project
        self.project_tasks: QuerySet = project.tasks
        self.project_subtasks: QuerySet = get_all_subtree(project)
        self.response_dict: JSONObject = {}

        self.configuration: dict[str, WidgetType] = self.TEST_WIDGET_CONFIG \
            if self.USE_TEST_WIDGET_CONFIG else get_widget_configuration(project.widget_config)

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
        done_tasks = self.project_tasks.filter(
            parent_task=None,
            status=Task.Status.DONE
        )
        return done_tasks.count()

    @metric
    def all_done_tasks_count(self, widget_type: WidgetType) -> JSONObject:
        done_tasks = self.project_subtasks.filter(
            status=Task.Status.DONE
        )
        return done_tasks.count()

    @metric
    def done_tasks_by_date(self, widget_type: WidgetType) -> JSONObject:
        done_tasks = self.project_tasks.filter(
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
