import uuid
from django.db import models


class Invite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="invites",
        null=True, blank=True, default=None)
    task = models.ForeignKey(
        "tasks.Task", on_delete=models.CASCADE, related_name="invites",
        null=True, blank=True, default=None)
    expiration_date = models.DateTimeField(null=False, blank=False)
