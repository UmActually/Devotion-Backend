import datetime
from rest_framework import serializers
from global_serializers import CCModelSerializer
from .models import Task, TaskStatus, TaskPriority


class TaskSerializer(CCModelSerializer):
    class Meta:
        model = Task
        fields = ("id", "name", "description")


class TaskDeserializer(serializers.Serializer):
    name = serializers.CharField(max_length=64, required=True)
    description = serializers.CharField(max_length=1024, required=False)
    priority = serializers.IntegerField(required=False)
    start_date = serializers.DateField(required=False)
    due_date = serializers.DateField(required=True)
    parent_project = serializers.CharField(required=True)
    parent_task = serializers.CharField(required=False)
    asignee = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs["parent_task"]:
            if not Task.objects.filter(id=attrs["parent_task"]).exists():
                raise serializers.ValidationError("The parent task does not exist.")

        if not Task.objects.filter(id=attrs["parent_project"]).exists():
            raise serializers.ValidationError("The parent project does not exist.")

        if not Task.objects.filter(id=attrs["asignee"]).exists():
            raise serializers.ValidationError("The asignee does not exist.")

        return attrs

    def create(self, validated_data):
        validated_data.setdefault("priority", TaskPriority.LOW)
        validated_data.setdefault("startDate", datetime.date.today())

        return Task.objects.create(
            name=validated_data["name"],
            description=validated_data.get("description"),
            status=TaskStatus.NOT_STARTED,
            priority=validated_data["priority"],
            startDate=validated_data.get("startDate"),
            dueDate=validated_data["dueDate"],
            parent_project=validated_data["parent_project"],
            parent_task=validated_data.get("parent_task"),
            asignee=validated_data["asignee"]
        )

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.priority = validated_data.get("priority", instance.priority)
        instance.startDate = validated_data.get("startDate", instance.startDate)
        instance.dueDate = validated_data.get("dueDate", instance.dueDate)
        instance.parent_project = validated_data.get("parent_project", instance.parent_project)
        instance.parent_task = validated_data.get("parent_task", instance.parent_task)
        instance.asignee = validated_data.get("asignee", instance.asignee)
        instance.save()
        return instance
