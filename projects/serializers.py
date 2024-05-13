from rest_framework import serializers

from devotion.apis import create_calendar, update_calendar
from devotion.serializers import CCModelSerializer
from users.models import User
from .models import Project


def get_project_or_error(project_id: str) -> Project:
    try:
        return Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        raise serializers.ValidationError("El proyecto papá no existe.")


def check_members_exist(members: list[str]) -> None:
    if not all(User.objects.filter(id=member).exists() for member in members):
        raise serializers.ValidationError("Uno o más miembros/líderes no existen.")


def check_members_are_subset(members: list[str], parent_members: set[str]) -> None:
    if not set(members).issubset(parent_members):
        raise serializers.ValidationError("Uno o más miembros/líderes no pertenecen al proyecto papá.")


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
        self.context["is_subproject"] = is_subproject

        leaders = attrs["leaders"].split(",") if "leaders" in attrs else []
        members = attrs["members"].split(",") if "members" in attrs else []

        if is_subproject:
            parent_id = attrs.get("parent") or self.instance.parent_id
            parent = get_project_or_error(parent_id)
            if self.instance and str(self.instance.id) == str(parent_id):
                raise serializers.ValidationError("Un proyecto no puede ser su propio papá.")
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
        else:
            create_calendar(project)

        return project

    def update(self, instance, validated_data):
        old_leader_emails = set()
        old_member_emails = set()

        if "leaders" in validated_data or "members" in validated_data:
            old_leaders = instance.leaders.all()
            old_members = instance.members.all()
            old_leader_emails = set(map(lambda x: x.email, old_leaders))
            old_member_emails = set(map(lambda x: x.email, old_members))

            if "leaders" in validated_data:
                validated_data["leaders"] = set(validated_data["leaders"].split(","))
            else:
                validated_data["leaders"] = set(map(lambda x: str(x.id), old_leaders))

            if "members" in validated_data:
                validated_data["members"] = set(validated_data["members"].split(","))
            else:
                validated_data["members"] = set(map(lambda x: str(x.id), old_members))

            validated_data["members"] = validated_data["members"].union(validated_data["leaders"])

        for attr, value in validated_data.items():
            if attr in ("leaders", "members"):
                getattr(instance, attr).set(value)
            else:
                setattr(instance, attr, value)

        instance.save()

        update_calendar(
            instance,
            validated_data.keys(),
            old_leaders=old_leader_emails,
            old_members=old_member_emails
        )

        return instance
