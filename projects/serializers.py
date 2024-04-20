from uuid import UUID

from rest_framework import serializers
from dashboards.models import Dashboard

from global_serializers import CCModelSerializer
from users.models import User
from .models import Project


def get_project_or_error(project_id: str) -> Project:
    try:
        return Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        raise serializers.ValidationError("The parent project does not exist.")


def check_members_exist(members: list[str]) -> None:
    if not all(User.objects.filter(id=member).exists() for member in members):
        raise serializers.ValidationError("One or more members/leaders do not exist.")


def check_members_are_subset(members: list[str], parent_members: set[str]) -> None:
    if not set(members).issubset(parent_members):
        raise serializers.ValidationError("One or more members/leaders are not members of the parent project.")


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
        is_subproject = "parent" in attrs or (
            self.instance is not None and self.instance.parent_id is not None)

        leaders = attrs["leaders"].split(",") if "leaders" in attrs else []
        members = attrs["members"].split(",") if "members" in attrs else []

        if is_subproject:
            parent_id = attrs.get("parent") or self.instance.parent_id
            parent = get_project_or_error(parent_id)
            if self.instance and str(self.instance.id) == str(parent_id):
                raise serializers.ValidationError("A project cannot be its own parent.")
            parent_members = set(map(lambda m: str(m.id), parent.members.all()))
            check_members_are_subset(leaders, parent_members)
            check_members_are_subset(members, parent_members)
        else:
            check_members_exist(leaders)
            check_members_exist(members)

        return attrs

    def create(self, validated_data):
        project = Project.objects.create(
            name=validated_data["name"],
            description=validated_data.get("description"),
        )

        leaders = set(validated_data["leaders"].split(","))
        members = set(validated_data["members"].split(",")).union(leaders)

        project.leaders.set(leaders)
        project.members.set(members)

        if "parent" in validated_data:
            project.parent_id = validated_data["parent"]
            project.save()

        Dashboard.objects.create(project=project)
        return project

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr in ("leaders", "members"):
                getattr(instance, attr).set(set(value.split(",")))
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance
