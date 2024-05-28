import time
import uuid
from django.db import models
from devotion.apis import google_api
from tasks.models import Task


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, null=False, blank=False)
    description = models.TextField(max_length=1024, null=True, blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="projects")
    leaders = models.ManyToManyField("users.User", related_name="leader_of")
    members = models.ManyToManyField("users.User", related_name="member_of")
    progress = models.FloatField(default=0, null=False, blank=False)
    calendar_id = models.CharField(max_length=128, null=True, blank=True)

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
            done_tasks = len([t for t in tasks if t.status == Task.Status.DONE])
            project.progress = (done_tasks / len(tasks)) * 100
        project.save()
        print(project.name, "-", project.progress)
        time.sleep(1)


def migrate_calendars() -> None:
    """Crea calendarios para los proyectos."""
    for project in Project.objects.filter(parent__isnull=True):
        print("Adding calendar for", project.name)
        calendar_id = google_api.calendars().insert(body={
            "summary": project.name,
            "description": project.description,
            "timeZone": "America/Mexico_City"
        }).execute()["id"]

        print(f"https://calendar.google.com/calendar/embed?src={calendar_id}&ctz=America%2FMexico_City")

        project.calendar_id = calendar_id
        project.save()

        print("Getting all tasks")
        all_tasks = project.tasks.all()

        def recurse_project(_project: Project) -> None:
            nonlocal all_tasks
            for subproject in _project.projects.all():
                recurse_project(subproject)
                all_tasks |= _project.tasks.all()

        recurse_project(project)

        print("Adding events")
        for task in all_tasks:
            event_id = google_api.events().insert(calendarId=project.calendar_id, body={
                "start": {"date": task.due_date.isoformat()},
                "end": {"date": task.due_date.isoformat()},
                "summary": task.name,
                "description": task.description
            }, sendUpdates="none").execute()["id"]

            task.event_id = event_id
            task.save()
            print("Added event for", task.name)
            time.sleep(1)

        google_api.acl().insert(calendarId=calendar_id, body={
            "role": "reader",
            "scope": {
                "type": "domain",
                "value": "itesm.mx"
            }
        }, sendNotifications=False).execute()
        print("Added domain ACL")
        time.sleep(1)
