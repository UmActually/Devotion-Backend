import datetime
from typing import Any, Iterable

import pytz
from django.db.models import QuerySet
from rest_framework.request import Request

from projects.models import Project
from .models import Task
from .serializers import SubtaskTableSerializer, SubtaskCalendarSerializer, SubtaskKanbanSerializer


JSONObject = dict[str, Any]


def group_tasks_as_calendar(tasks: Iterable[Task], start_date: datetime.date | None) -> JSONObject | list[JSONObject]:
    data = {}

    # Y EN TIEMPO LINEAL PAPITO QUE MAS QUIERES
    for task in tasks:
        if start_date is None:
            # Si start_date es None, se usan fechas (iOS)
            date = task.due_date.isoformat()
        else:
            # Si start_date tiene valor, se usan índices (web)
            days_difference = (task.due_date - start_date).days
            calendar_row = days_difference // 7
            calendar_col = days_difference % 7
            date = (calendar_row, calendar_col)

        if date not in data:
            data[date] = []
        data[date].append(SubtaskCalendarSerializer(task).data)

    if start_date is None:
        return data

    return [
        {"date": key, "tasks": value}
        for key, value in data.items()
    ]


def table_view_type(response: JSONObject, tasks: QuerySet) -> None:
    response["tasks"] = SubtaskTableSerializer(tasks, many=True).data


def calendar_view_type(response: JSONObject, tasks: QuerySet, platform: str) -> None:
    today = datetime.datetime.now(pytz.timezone("Mexico/General")).date()
    days_difference = today.weekday() + 8

    start_date = None

    if platform == "web":
        start_date = today - datetime.timedelta(days=days_difference)
        end_date = start_date + datetime.timedelta(days=35)
        tasks = tasks.filter(
            due_date__gte=start_date,
            due_date__lt=end_date
        ).order_by("due_date")

        today_row = days_difference // 7
        today_col = days_difference % 7
        response["today"] = [today_row, today_col]

    response["tasks"] = group_tasks_as_calendar(tasks, start_date)


def kanban_view_type(response: JSONObject, tasks: QuerySet) -> None:
    tasks = tasks.order_by("status", "-priority")
    tasks = {
        "notStarted": tasks.filter(status=Task.Status.NOT_STARTED),
        "inProgress": tasks.filter(status=Task.Status.IN_PROGRESS),
        "inReview": tasks.filter(status=Task.Status.IN_REVIEW),
        "done": tasks.filter(status=Task.Status.DONE)
    }
    response["tasks"] = {
        key: SubtaskKanbanSerializer(value, many=True).data
        for key, value in tasks.items()
    }


def get_all_subtree(project_or_task: Project | Task, assignee_id: str | None = None) -> QuerySet:
    """Obtiene todas las tareas debajo de un proyecto o tarea."""
    all_tasks: QuerySet = project_or_task.tasks
    all_tasks = all_tasks.filter(assignee_id=assignee_id) if assignee_id else (
        all_tasks.all())
    is_task = isinstance(project_or_task, Task)

    def recurse(_project_or_task: Project | Task) -> None:
        nonlocal all_tasks

        subitems = _project_or_task.tasks if is_task else (
            _project_or_task.projects)

        for subitem in subitems.all():
            recurse(subitem)
            if assignee_id:
                all_tasks |= subitem.tasks.filter(assignee_id=assignee_id)
            else:
                all_tasks |= subitem.tasks.all()

    recurse(project_or_task)
    return all_tasks


def handle_subtasks_response(
        request: Request, response: JSONObject, project_or_task: Project | Task) -> None:

    is_task = isinstance(project_or_task, Task)
    platform = request.query_params.get("platform", "web")
    view_type = request.query_params.get("view", "table")
    get_subtree = request.query_params.get("subtree", "false") == "true"
    filter_assigned = request.query_params.get("assigned", "false") == "true"
    assignee_id = request.user.id if filter_assigned else None

    if get_subtree:
        tasks = get_all_subtree(project_or_task, assignee_id)
    else:
        tasks = project_or_task.tasks.all() if is_task else (
            project_or_task.tasks.filter(parent_task__isnull=True))
        if assignee_id:
            tasks = tasks.filter(assignee_id=assignee_id)

    if view_type == "calendar":
        calendar_view_type(response, tasks, platform)
    elif view_type == "kanban":
        kanban_view_type(response, tasks)
    else:
        table_view_type(response, tasks)

    if platform == "ios":
        response["tasks"] = {
            "type": view_type,
            "data": response["tasks"]
        }


def handle_global_calendar_response(request: Request, response: JSONObject) -> None:
    user = request.user
    tasks = Task.objects.filter(parent_project__in=user.member_of.all())
    calendar_view_type(response, tasks)
