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

    @metric
    def tasks_by_status(self, widget_type: WidgetType) -> JSONObject:
        not_started_tasks = self.project_tasks.filter(
            parent_task=None,
            status=Task.Status.NOT_STARTED
        ).count()
        
        in_progress_tasks = self.project_tasks.filter(
            parent_task=None,
            status=Task.Status.IN_PROGRESS
        ).count()
        
        in_review_tasks = self.project_tasks.filter(
            parent_task=None,
            status=Task.Status.IN_REVIEW
        ).count()
        
        done_tasks = self.project_tasks.filter(
            parent_task=None,
            status=Task.Status.DONE
        ).count()
        
        grouped_tasks = [
            (Task.Status.NOT_STARTED, not_started_tasks),
            (Task.Status.IN_PROGRESS, in_progress_tasks),
            (Task.Status.IN_REVIEW, in_review_tasks),
            (Task.Status.DONE, done_tasks)
        ]
        
        status_translation = {
            "NOT_STARTED": "No iniciado",
            "IN_PROGRESS": "En progreso",
            "IN_REVIEW": "En revisión",
            "DONE": "Completado"
        }

        if widget_type == WidgetType.VERTICAL_BAR:
            return [
                {"name": status_translation[key.name], "value": value}
                for key, value in grouped_tasks
            ]
        elif widget_type == WidgetType.HORIZONTAL_BAR:
            return [
                {"name": key, "value": value}
                for key, value in grouped_tasks
            ]
        elif widget_type == WidgetType.PIE:
            return [
                {"name": key, "value": value}
                for key, value in grouped_tasks
            ]
        else:
            # Heatmap
            max_count = max(value for _, value in grouped_tasks)
            return [
                {"name": key, "value": value / max_count}
                for key, value in grouped_tasks
            ]
            
    @metric
    def tasks_by_priority(self, widget_type: WidgetType) -> JSONObject:
        priority_labels = {
        0: "Baja",
        1: "Media",
        2: "Alta"
        }
        
        tasks = self.project_tasks.filter(
            parent_task=None
        ).order_by("priority")

        grouped_tasks = {}

        for task in tasks:
            priority = task.priority
            if priority not in grouped_tasks:
                grouped_tasks[priority] = []
            grouped_tasks[priority].append(task)

        if widget_type in (WidgetType.VERTICAL_BAR, WidgetType.HORIZONTAL_BAR):
            return [
                {"name": priority_labels.get(key, "null"), "value": len(value)}
                for key, value in grouped_tasks.items()
            ]
        else:
            # Heatmap
            max_count = max(len(value) for value in grouped_tasks.values())
            return [
                {"name": priority_labels.get(key, "null"), "value": len(value) / max_count}
                for key, value in grouped_tasks.items()
            ]
