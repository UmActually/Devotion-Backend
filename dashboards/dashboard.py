import datetime
from typing import Any, Callable

import pytz
from django.db.models.query import QuerySet
from rest_framework import status
from rest_framework.response import Response

from projects.models import Project, get_widget_configuration
from tasks.models import Task
from tasks.subtasks import get_all_subtree
from .metrics import WidgetType, project_metrics

JSONObject = dict[str, Any] | list[Any] | int
MONTHS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def metric(func: Callable) -> Callable:
    if func.__name__ not in project_metrics:
        raise ValueError(f"Unknown metric: {func.__name__}")
    return func


class Dashboard:
    USE_TEST_WIDGET_CONFIG = True
    TEST_WIDGET_CONFIG = {
        "done_tasks_count": WidgetType.NUMBER,
        "all_done_tasks_count": WidgetType.NUMBER,
        "done_tasks_by_date": WidgetType.LINE,
        "tasks_by_status": WidgetType.VERTICAL_BAR,
        "tasks_by_priority": WidgetType.VERTICAL_BAR,
        "user_workload": WidgetType.HEAT_MAP,
        "project_progress": WidgetType.GAUGE,
        "all_project_progress": WidgetType.GAUGE
    }

    def __init__(self, project: Project) -> None:
        self.project = project
        self.project_tasks: QuerySet = project.tasks.filter(parent_task__isnull=True)
        self.project_subtasks: QuerySet = get_all_subtree(project)
        self.response_dict: JSONObject = {}

        self.configuration: dict[str, WidgetType] = self.TEST_WIDGET_CONFIG \
            if self.USE_TEST_WIDGET_CONFIG else get_widget_configuration(project.widget_config)

        self.today = datetime.datetime.now(pytz.timezone("Mexico/General")).date()
        self.end_date = self.today - datetime.timedelta(days=self.today.weekday() + 1)
        self.start_date = self.end_date - datetime.timedelta(days=35)
        self.tasks_last_weeks = self.project_tasks.filter(
            start_date__gte=self.start_date,
            start_date__lt=self.end_date
        ).order_by("due_date")

        self.last_weeks_labels = []
        for i in range(5):
            start_date = self.start_date + datetime.timedelta(days=i * 7)
            end_date = start_date + datetime.timedelta(days=6)
            self.last_weeks_labels.append(
                f"{start_date.day} {MONTHS[start_date.month - 1]}"
                f" - {end_date.day} {MONTHS[end_date.month - 1]}")

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
        tasks = self.tasks_last_weeks.filter(
            status=Task.Status.DONE
        ).order_by("due_date")

        week_counts = [0 for _ in range(5)]

        for task in tasks:
            days_difference = (task.start_date - self.start_date).days
            index = days_difference // 7
            week_counts[index] += 1

        return [
            {"name": label, "value": count}
            for label, count in zip(self.last_weeks_labels, week_counts)
        ]

    @metric
    def tasks_by_status(self, widget_type: WidgetType) -> JSONObject:
        not_started_tasks = self.project_tasks.filter(
            status=Task.Status.NOT_STARTED
        ).count()

        in_progress_tasks = self.project_tasks.filter(
            status=Task.Status.IN_PROGRESS
        ).count()

        in_review_tasks = self.project_tasks.filter(
            status=Task.Status.IN_REVIEW
        ).count()

        done_tasks = self.project_tasks.filter(
            status=Task.Status.DONE
        ).count()

        labels = (
            "No iniciado",
            "En progreso",
            "En revisión",
            "Completado"
        )

        counts = (
            not_started_tasks,
            in_progress_tasks,
            in_review_tasks,
            done_tasks
        )

        if widget_type == WidgetType.HEAT_MAP:
            max_count = max(value for _, value in counts)
            return [
                {"name": label, "value": count / max_count}
                for label, count in zip(labels, counts)
            ]
        else:
            return [
                {"name": label, "value": count}
                for label, count in zip(labels, counts)
            ]

    @metric
    def tasks_by_priority(self, widget_type: WidgetType) -> JSONObject:
        low_tasks = self.project_tasks.filter(
            priority=Task.Priority.LOW
        ).count()

        medium_tasks = self.project_tasks.filter(
            priority=Task.Priority.MEDIUM
        ).count()

        high_tasks = self.project_tasks.filter(
            priority=Task.Priority.HIGH
        ).count()

        labels = (
            "Baja",
            "Media",
            "Alta"
        )

        counts = (
            low_tasks,
            medium_tasks,
            high_tasks
        )

        if widget_type == WidgetType.HEAT_MAP:
            max_count = max(value for _, value in counts)
            return [
                {"name": label, "value": count / max_count}
                for label, count in zip(labels, counts)
            ]
        else:
            return [
                {"name": label, "value": count}
                for label, count in zip(labels, counts)
            ]

    @metric
    def user_workload(self, widget_type: WidgetType) -> JSONObject:
        user_workload = {}
        # Caso Heat Map
        if widget_type == WidgetType.HEAT_MAP:
                for task in self.tasks_last_weeks:
                    if str(task.assignee) not in user_workload:
                        user_workload[str(task.assignee)] = [{"name": label, "value": 0} for label in self.last_weeks_labels]
                    days_difference = (task.start_date - self.start_date).days
                    index = days_difference // 7
                    user_workload[str(task.assignee)][index]["value"] += 1
                return [
                    {"name": user, "series": counts}
                    for user, counts in user_workload.items()
                ]
        # Caso Vertical Bar o Horizontal Bar
        else:
            for task in self.project_tasks:
                if task.assignee:
                    assignee_name = str(task.assignee)
                    if assignee_name not in user_workload:
                        user_workload[assignee_name] = 0
                    user_workload[assignee_name] += 1
            return [{"name": key, "value": value} for key, value in user_workload.items()]
