import datetime
from typing import Any, Callable

import pytz
from django.contrib.auth.models import AnonymousUser
from django.db.models.query import QuerySet
from rest_framework import status
from rest_framework.response import Response

from devotion.serializers import camel_case
from users.models import User
from projects.models import Project, get_widget_configuration
from tasks.models import Task
from tasks.subtasks import get_all_subtree
from tasks.serializers import TaskDashboardSerializer
from .metrics import project_metrics, set_display_types
from .metrics import WidgetType as W


JSONObject = dict[str, Any] | list[Any] | int


class DashboardBadRequest(Exception):
    pass


def metric(*display_types: W) -> Callable:
    def decorator(func: Callable) -> Callable:
        if func.__name__ not in project_metrics():
            raise ValueError(f"Unknown metric: {func.__name__}")
        set_display_types(func.__name__, display_types)

        def wrapper(self: 'Dashboard', widget_type: W) -> JSONObject:
            if widget_type not in display_types:
                raise DashboardBadRequest(
                    f"El tipo de widget {widget_type} no es "
                    f"válido para la métrica {func.__name__}.")

            resp = func(self, widget_type)

            return {
                "displayType": widget_type.value,
                "data": resp
            }

        return wrapper
    return decorator


class Dashboard:
    USE_TEST_WIDGET_CONFIG = False
    TEST_WIDGET_CONFIG = {
        "done_tasks_count": W.NUMBER,
        "all_done_tasks_count": W.NUMBER,
        "done_tasks_by_date": W.LINE,
        "tasks_by_status": W.VERTICAL_BAR,
        "tasks_by_priority": W.VERTICAL_BAR,
        "user_workload": W.HEAT_MAP,
        "project_progress": W.GAUGE,
        "all_project_progress": W.GAUGE
    }

    def __init__(self, project: Project, user: User | AnonymousUser) -> None:
        self.project = project
        self.user = user
        self.project_tasks: QuerySet = project.tasks.filter(parent_task__isnull=True)
        self.project_subtasks: QuerySet = get_all_subtree(project)

        self.configuration: dict[str, W] = self.TEST_WIDGET_CONFIG \
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
                f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')}")

    def get_response(self) -> Response:
        data: JSONObject = self.get_task_widgets()
        data["name"] = self.project.name

        for metric_name in project_metrics():
            try:
                widget = getattr(self, metric_name)
            except AttributeError:
                continue

            try:
                resp = widget(self.configuration[metric_name])
            except DashboardBadRequest as e:
                return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            if resp is not None:
                data[camel_case(metric_name)] = resp

        return Response(data, status=status.HTTP_200_OK)

    # Task widgets

    def get_task_widgets(self) -> JSONObject:
        if self.user == AnonymousUser():
            return {}

        is_leader = self.user in self.project.leaders.all()
        tasks_to_do = self.project_subtasks.filter(
            assignee_id=self.user.id,
            status__in=(Task.Status.NOT_STARTED, Task.Status.IN_PROGRESS)
        )

        if is_leader:
            tasks_to_verify = self.project_tasks.filter(
                status=Task.Status.IN_REVIEW
            )
        else:
            tasks_to_verify = self.project_subtasks.filter(
                assignee_id=self.user.id,
                status=Task.Status.IN_REVIEW
            )

        return {
            "tasksToDo": TaskDashboardSerializer(tasks_to_do, many=True).data,
            "tasksToVerify": TaskDashboardSerializer(tasks_to_verify, many=True).data
        }

    # Metric widgets

    @metric(W.NUMBER)
    def done_tasks_count(self, widget_type: W) -> JSONObject:
        done_tasks = self.project_tasks.filter(
            status=Task.Status.DONE
        )
        return [{
            "name": "Tareas Completadas",
            "value": done_tasks.count()
        }]

    @metric(W.NUMBER)
    def all_done_tasks_count(self, widget_type: W) -> JSONObject:
        done_tasks = self.project_subtasks.filter(
            status=Task.Status.DONE
        )
        return [{
            "name": "Tareas y subtareas completadas",
            "value": done_tasks.count()
        }]

    @metric(W.LINE, W.VERTICAL_BAR, W.HORIZONTAL_BAR, W.HEAT_MAP)
    def done_tasks_by_date(self, widget_type: W) -> JSONObject:
        tasks = self.tasks_last_weeks.filter(
            status=Task.Status.DONE
        ).order_by("due_date")

        week_counts = [0 for _ in range(5)]

        if widget_type == W.LINE:
            series = []
            for task in tasks:
                days_difference = (task.start_date - self.start_date).days
                index = days_difference // 7
                week_counts[index] += 1

            for label, count in zip(self.last_weeks_labels, week_counts):
                series.append({"name": label, "value": count})

            return [
                {"name": "Completed Tasks", "series": series}
            ]

        else:
            for task in tasks:
                days_difference = (task.start_date - self.start_date).days
                index = days_difference // 7
                week_counts[index] += 1

            return [
                {"name": label, "value": count}
                for label, count in zip(self.last_weeks_labels, week_counts)
            ]

    @metric(W.PIE, W.VERTICAL_BAR, W.HORIZONTAL_BAR, W.HEAT_MAP)
    def tasks_by_status(self, widget_type: W) -> JSONObject:
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

        return [
            {"name": label, "value": count}
            for label, count in zip(labels, counts)
        ]

    @metric(W.PIE, W.VERTICAL_BAR, W.HORIZONTAL_BAR, W.HEAT_MAP)
    def tasks_by_priority(self, widget_type: W) -> JSONObject:
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

        if widget_type == W.HEAT_MAP:
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

    @metric(W.HEAT_MAP, W.PIE, W.VERTICAL_BAR, W.HORIZONTAL_BAR, W.NUMBERS)
    def user_workload(self, widget_type: W) -> JSONObject:
        user_workload = {}

        # Caso Heat Map
        if widget_type == W.HEAT_MAP:
            for task in self.tasks_last_weeks:
                if str(task.assignee) not in user_workload:
                    user_workload[str(task.assignee)] = [
                        {"name": label, "value": 0} for label in self.last_weeks_labels
                    ]

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

    @metric(W.GAUGE)
    def project_progress(self, widget_type: W) -> JSONObject:
        return [{"name": self.project.name, "value": self.project.progress}]
