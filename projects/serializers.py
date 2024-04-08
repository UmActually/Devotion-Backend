from rest_framework import serializers
from dashboards.models import Dashboard

from global_serializers import CCModelSerializer
from users.models import User
from .models import Project


class ProjectSerializer(CCModelSerializer):
    class Meta:
        model = Project
        fields = ("id", "name", "description")


class ProjectDeserializer(serializers.Serializer):
    name = serializers.CharField(max_length=64, required=True)
    description = serializers.CharField(max_length=1024, required=False)
    parent = serializers.CharField(required=False)
    leaders = serializers.CharField(required=True)
    members = serializers.CharField(required=True)

    def validate(self, attrs):
        if "parent" in attrs and not Project.objects.filter(id=attrs["parent"]).exists():
                raise serializers.ValidationError("The parent project does not exist.")

        leaders = attrs["leaders"].split(",")
        members = attrs["members"].split(",")

        if not all(User.objects.filter(id=leader).exists() for leader in leaders):
            raise serializers.ValidationError("One or more leaders do not exist.")

        if not all(User.objects.filter(id=member).exists() for member in members):
            raise serializers.ValidationError("One or more members do not exist.")

        return attrs

    def create(self, validated_data):
        project = Project.objects.create(
            name=validated_data["name"],
            description=validated_data.get("description"),
        )
        project.leaders.set(validated_data["leaders"].split(","))
        project.members.set(validated_data["members"].split(","))

        if "parent" in validated_data:
            project.parent_id = validated_data["parent"]
            project.save()

        Dashboard.objects.create(project=project)
        return project

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.leaders.set(validated_data.get("leaders", instance.leaders.all()))
        instance.members.set(validated_data.get("members", instance.members.all()))
        instance.save()
        return instance
