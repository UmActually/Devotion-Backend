import time
import uuid
from django.db import models
from tasks.models import TaskStatus


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, null=False, blank=False)
    description = models.TextField(max_length=1024, null=True, blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="projects")
    leaders = models.ManyToManyField("users.User", related_name="leader_of")
    members = models.ManyToManyField("users.User", related_name="member_of")
    progress = models.FloatField(default=0, null=False, blank=False)

    def __str__(self):
        return self.name


def migrate_leaders_members() -> None:
    """Convierte los líderes de proyectos en miembros también."""
    for project in Project.objects.all():
        current_leaders = project.leaders.all()
        current_members = project.members.all()
        new_members = set(current_members).union(set(current_leaders))
        project.members.set(new_members)
        print(project.name, "-", [m.first_names for m in current_members], "->", [m.first_names for m in new_members])
        time.sleep(1)


def migrate_projects_progress() -> None:
    """Calcula el progreso de los proyectos."""
    for project in Project.objects.all():
        tasks = project.tasks.all()
        if len(tasks) == 0:
            project.progress = 0
        else:
            done_tasks = len([t for t in tasks if t.status == TaskStatus.DONE])
            project.progress = (done_tasks / len(tasks)) * 100
        project.save()
        print(project.name, "-", project.progress)
        time.sleep(1)