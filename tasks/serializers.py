import datetime
from rest_framework import serializers
from global_serializers import CCModelSerializer
from users.models import User
from projects.models import Project
from .models import Task, TaskStatus, TaskPriority


def get_project_or_error(project_id: str) -> Project:
    try:
        return Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        raise serializers.ValidationError("The parent project does not exist.")


def get_task_or_error(task_id: str) -> Task:
    try:
        return Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        raise serializers.ValidationError("The parent task does not exist.")


def check_project_membership(asignee_id: str, project: Project) -> None:
    if asignee_id not in map(lambda m: str(m.id), project.members.all()):
        raise serializers.ValidationError("The asignee is not a member of the parent project.")


class TaskSerializer(CCModelSerializer):
    class Meta:
        model = Task
        fields = ("id", "name", "description")


class TaskViewSerializer(CCModelSerializer):
    asignee = serializers.StringRelatedField()

    class Meta:
        model = Task
        fields = ("id", "name", "description", "status", "priority",
                  "start_date", "due_date", "asignee")


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

        if "parent_task" in attrs:
            parent_task = get_task_or_error(attrs["parent_task"])
            if self.instance and self.instance.id == parent_task.id:
                raise serializers.ValidationError("A task cannot be its own parent.")
            if parent_task.parent_project_id != parent_project.id:
                raise serializers.ValidationError("The parent task does not belong to the same parent project.")

        asignee_id = attrs.get("asignee") or str(self.instance.asignee_id)
        check_project_membership(asignee_id, parent_project)

        if "priority" in attrs and attrs["priority"] not in TaskPriority.values:
            raise serializers.ValidationError("Invalid priority value.")

        if "start_date" in attrs and "due_date" in attrs and attrs["start_date"] > attrs["due_date"]:
            raise serializers.ValidationError("Start date must be before due date.")

        return attrs

    def create(self, validated_data):
        validated_data.setdefault("priority", TaskPriority.MEDIUM)
        validated_data.setdefault("start_date", min(datetime.date.today(), validated_data["due_date"]))

        return Task.objects.create(
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

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr in ("parent_project", "parent_task", "asignee"):
                attr += "_id"
            setattr(instance, attr, value)
        instance.save()
        return instance
