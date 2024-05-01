import uuid
from django.db import models


class TaskStatus(models.IntegerChoices):
    NOT_STARTED = 0, "Not started"
    IN_PROGRESS = 1, "In progress"
    IN_REVIEW = 2, "In review"
    DONE = 3, "Done"


class TaskPriority(models.IntegerChoices):
    LOW = 0, "Low"
    MEDIUM = 1, "Medium"
    HIGH = 2, "High"


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, null=False, blank=False)
    description = models.TextField(max_length=1024, null=True, blank=True)
    status = models.SmallIntegerField(choices=TaskStatus.choices, null=False, blank=False)
    priority = models.SmallIntegerField(choices=TaskPriority.choices, null=False, blank=False)
    start_date = models.DateField(null=False, blank=False)
    due_date = models.DateField(null=False, blank=False)
    parent_project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, null=False, blank=False, related_name="tasks")
    parent_task = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="tasks")
    asignee = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, null=False, blank=False, related_name="tasks")
    event_id = models.CharField(max_length=32, null=False, blank=False)

    def __str__(self):
        return self.name
