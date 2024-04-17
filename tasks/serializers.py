import datetime
from rest_framework import serializers
from global_serializers import CCModelSerializer
from users.models import User
from projects.models import Project
from .models import Task, TaskStatus, TaskPriority


class TaskSerializer(CCModelSerializer):
    class Meta:
        model = Task
        fields = ("id", "name", "description")


class TaskViewSerializer(CCModelSerializer):
    asignee = serializers.StringRelatedField()

    class Meta:
        model = Task
        fields = ("id", "name", "description", "status", "priority",
                  "start_date", "due_date", "asignee", "parent_task")


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
        if "parent_task" in attrs and not Task.objects.filter(id=attrs["parent_task"]).exists():
            raise serializers.ValidationError("The parent task does not exist.")

        if not Project.objects.filter(id=attrs["parent_project"]).exists():
            raise serializers.ValidationError("The parent project does not exist.")

        if not User.objects.filter(id=attrs["asignee"]).exists():
            raise serializers.ValidationError("The asignee does not exist.")

        if "priority" in attrs and attrs["priority"] not in TaskPriority.values:
            raise serializers.ValidationError("Invalid priority value.")

        if "start_date" in attrs and attrs["start_date"] > attrs["due_date"]:
            raise serializers.ValidationError("Start date must be before due date.")

        return attrs

    def create(self, validated_data):
        validated_data.setdefault("priority", TaskPriority.LOW)
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
        # TODO: esto está medio sucio, y ni funciona. Hay que lograr que no se
        #  tengan que escribir todos los campos para editar solo uno. Checar Project y User también.

        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.priority = validated_data.get("priority", instance.priority)
        instance.start_date = validated_data.get("start_date", instance.start_date)
        instance.due_date = validated_data.get("due_date", instance.due_date)
        instance.parent_project = validated_data.get("parent_project", instance.parent_project)
        instance.parent_task = validated_data.get("parent_task", instance.parent_task)
        instance.asignee = validated_data.get("asignee", instance.asignee)
        instance.save()
        return instance
