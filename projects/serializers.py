from rest_framework import serializers

from devotion.apis import create_calendar, update_calendar
from devotion.serializers import CCModelSerializer
from users.models import User
from .models import Project, DEFAULT_WIDGET_CONFIG


def get_project_or_error(project_id: str) -> Project:
    try:
        return Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        raise serializers.ValidationError("El proyecto papá no existe.")


def check_members_exist(members: list[str] | set[str]) -> None:
    if not all(User.objects.filter(id=member).exists() for member in members):
        raise serializers.ValidationError("Uno o más miembros/líderes no existen.")


def check_members_are_subset(members: list[str] | set[str], parent_members: set[str]) -> None:
    if not set(members).issubset(parent_members):
        raise serializers.ValidationError("Uno o más miembros/líderes no pertenecen al proyecto papá.")


class ProjectSerializer(CCModelSerializer):
    class Meta:
        model = Project
        fields = ("id", "name", "description")


class SubprojectSerializer(CCModelSerializer):
    class Meta:
        model = Project
        fields = ("id", "name", "description", "progress")


class ProjectDeserializer(serializers.Serializer):
    name = serializers.CharField(max_length=64, required=True)
    description = serializers.CharField(max_length=1024, required=False)
    parent = serializers.CharField(required=False)
    leaders = serializers.CharField(required=True, min_length=36)
    members = serializers.CharField(required=True, allow_blank=True)

    def validate(self, attrs):
        leaders = set(attrs["leaders"].split(","))
        members = set(attrs["members"].split(",")) \
            if "members" in attrs and attrs["members"] else set()
        members = members.union(leaders)

        if "parent" in attrs:
            parent_id = attrs["parent"]
            parent = get_project_or_error(parent_id)
            parent_members = set(map(lambda m: str(m.id), parent.members.all()))
            check_members_are_subset(members, parent_members)
        else:
            check_members_exist(members)

        attrs["leaders"] = leaders
        attrs["members"] = members

        return attrs

    def create(self, validated_data):
        project = Project.objects.create(
            name=validated_data["name"],
            description=validated_data.get("description"),
            widget_config=DEFAULT_WIDGET_CONFIG
        )

        project.leaders.set(validated_data["leaders"])
        project.members.set(validated_data["members"])

        if "parent" in validated_data:
            project.parent_id = validated_data["parent"]
            project.save()
        else:
            create_calendar(project)

        return project


class ProjectUpdateDeserializer(ProjectDeserializer):
    def validate(self, attrs):
        is_subproject = "parent" in attrs or self.instance.parent_id is not None
        self.context["is_subproject"] = is_subproject

        old_leaders = self.instance.leaders.all()
        old_members = self.instance.members.all()

        leaders = set(attrs["leaders"].split(",")) if "leaders" in attrs \
            else set(map(lambda m: str(m.id), old_leaders))

        members = set(attrs["members"].split(",")) if "members" in attrs and attrs["members"] \
            else set(map(lambda m: str(m.id), old_members))

        members = members.union(leaders)

        if is_subproject:
            parent_id = attrs.get("parent") or self.instance.parent_id
            parent = get_project_or_error(parent_id)
            if str(self.instance.id) == str(parent_id):
                raise serializers.ValidationError("Un proyecto no puede ser su propio papá.")
            parent_members = set(map(lambda m: str(m.id), parent.members.all()))
            check_members_are_subset(members, parent_members)
        else:
            check_members_exist(members)

        attrs["leaders"] = leaders
        attrs["members"] = members
        self.context["old_leader_emails"] = set(map(lambda x: x.email, old_leaders))
        self.context["old_member_emails"] = set(map(lambda x: x.email, old_members))

        return attrs

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr in ("leaders", "members"):
                getattr(instance, attr).set(value)
            else:
                setattr(instance, attr, value)

        instance.save()

        if not self.context["is_subproject"]:
            update_calendar(
                instance,
                validated_data.keys(),
                old_leaders=self.context["old_leader_emails"],
                old_members=self.context["old_member_emails"]
            )

        return instance
