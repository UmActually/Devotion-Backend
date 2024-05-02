import datetime
from typing import Any, Iterable

import pytz
from rest_framework import serializers
from rest_framework.response import Response

from devotion.apis import create_event, update_event
from devotion.serializers import CCModelSerializer
from projects.models import Project
from users.serializers import UserMinimalSerializer
from .models import Task, TaskStatus, TaskPriority


def get_project_or_error(project_id: str) -> Project:
    try:
        return Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        raise serializers.ValidationError("El proyecto papá no existe.")


def get_task_or_error(task_id: str) -> Task:
    try:
        return Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        raise serializers.ValidationError("La tarea papá no existe.")


def check_project_membership(asignee_id: str, project: Project) -> None:
    if asignee_id not in map(lambda m: str(m.id), project.members.all()):
        raise serializers.ValidationError("El asignado no pertenece al proyecto papá.")


class TaskSerializer(CCModelSerializer):
    class Meta:
        model = Task
        fields = ("id", "name", "description")


class TaskViewSerializer(CCModelSerializer):
    asignee = UserMinimalSerializer()

    class Meta:
        model = Task
        fields = ("id", "name", "description", "status", "priority",
                  "start_date", "due_date", "asignee", "parent_project", "parent_task")


class SubtaskViewSerializer(CCModelSerializer):
    asignee = serializers.StringRelatedField()

    class Meta:
        model = Task
        fields = ("id", "name", "description", "status", "priority",
                  "start_date", "due_date", "asignee", "parent_project", "parent_task")


class SubtaskCalendarSerializer(CCModelSerializer):
    class Meta:
        model = Task
        fields = ("id", "name", "status", "priority")


class TaskDeserializer(serializers.Serializer):
    name = serializers.CharField(max_length=128, required=True)
    description = serializers.CharField(max_length=1024, required=False)
    priority = serializers.IntegerField(required=False)
    start_date = serializers.DateField(required=False)
    due_date = serializers.DateField(required=True)
    parent_project = serializers.CharField(required=True)
    parent_task = serializers.CharField(required=False)
    asignee = serializers.CharField(required=True)

    def validate(self, attrs):
        # TODO: En teoría, falta revisar que no se haga un ciclo en
        #  la jerarquía de tareas y proyectos.

        parent_project = get_project_or_error(attrs["parent_project"]) \
            if "parent_project" in attrs else self.instance.parent_project

        self.context["parent_project"] = parent_project
        self.context["parent_project_task_count"] = parent_project.tasks.count()

        if "parent_task" in attrs:
            parent_task = get_task_or_error(attrs["parent_task"])
            if self.instance and self.instance.id == parent_task.id:
                raise serializers.ValidationError("Una tarea no puede ser su propia tarea papá.")
            if parent_task.parent_project_id != parent_project.id:
                raise serializers.ValidationError("La nueva tarea papá no pertenece al mismo proyecto.")

        asignee_id = attrs.get("asignee") or str(self.instance.asignee_id)
        check_project_membership(asignee_id, parent_project)

        if "priority" in attrs and attrs["priority"] not in TaskPriority.values:
            raise serializers.ValidationError("Valor de prioridad inválido.")

        try:
            start_date = attrs.get("start_date") or self.instance.start_date
        except AttributeError:
            return attrs

        due_date = attrs.get("due_date") or self.instance.due_date

        if start_date > due_date:
            raise serializers.ValidationError(
                "La fecha de inicio no puede ser después de la fecha de entrega.")

        return attrs

    def create(self, validated_data):
        validated_data.setdefault("priority", TaskPriority.MEDIUM)
        validated_data.setdefault("start_date", min(datetime.date.today(), validated_data["due_date"]))
        parent_project = self.context["parent_project"]
        task_count = self.context["parent_project_task_count"]

        task = Task.objects.create(
            name=validated_data["name"],
            description=validated_data.get("description"),
            status=TaskStatus.NOT_STARTED,
            priority=validated_data["priority"],
            start_date=validated_data.get("start_date"),
            due_date=validated_data["due_date"],
            parent_project_id=validated_data["parent_project"],
            parent_task_id=validated_data.get("parent_task"),
            asignee_id=validated_data["asignee"]
        )

        parent_project.progress *= task_count
        parent_project.progress /= task_count + 1
        parent_project.save()

        create_event(task)
        return task

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr in ("parent_project", "parent_task", "asignee"):
                attr += "_id"
            setattr(instance, attr, value)

        instance.save()
        update_event(instance, validated_data.keys())
        return instance


def _group_tasks_as_calendar(tasks: Iterable[Task], start_date: datetime.date) -> list[list[dict[str, Any]]]:
    date = start_date
    data = [[{"date": "", "tasks": []} for _ in range(7)] for _ in range(5)]

    for week in data:
        for day in week:
            day["date"] = date.isoformat()
            date += datetime.timedelta(days=1)

    date = start_date
    week = 0
    weekday = 0

    # Y EN TIEMPO LINEAL PAPITO QUE MAS QUIERES
    for task in tasks:
        day_difference = (task.due_date - date).days
        if day_difference != 0:
            date = task.due_date
            week += (weekday + day_difference) // 7
            weekday = (weekday + day_difference) % 7
        data[week][weekday]["tasks"].append(TaskViewSerializer(task).data)

    return data


def group_tasks_as_calendar(tasks: Iterable[Task], start_date: datetime.date) -> list[dict[str, Any]]:
    data = {}

    # Y EN TIEMPO LINEAL PAPITO QUE MAS QUIERES
    for task in tasks:
        days_difference = (task.due_date - start_date).days
        calendar_row = days_difference // 7
        calendar_col = days_difference % 7
        if (calendar_row, calendar_col) not in data:
            data[(calendar_row, calendar_col)] = []
        data[(calendar_row, calendar_col)].append(SubtaskCalendarSerializer(task).data)

    return [
        {"date": key, "tasks": value}
        for key, value in data.items()
    ]


def calendar_view_type(response: Response, project_or_task: Project | Task) -> None:
    today = datetime.datetime.now(pytz.timezone("Mexico/General")).date()
    days_difference = today.weekday() + 8
    start_date = today - datetime.timedelta(days=days_difference)
    end_date = start_date + datetime.timedelta(days=35)
    tasks = project_or_task.tasks.filter(
        parent_task__isnull=True,
        due_date__gte=start_date,
        due_date__lt=end_date
    ).order_by("due_date")
    response["tasks"] = group_tasks_as_calendar(tasks, start_date)
    today_row = days_difference // 7
    today_col = days_difference % 7
    response["today"] = [today_row, today_col]
