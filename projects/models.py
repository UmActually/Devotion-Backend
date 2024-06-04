import uuid
from django.db import models


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, null=False, blank=False)
    description = models.TextField(max_length=1024, null=True, blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="projects")
    leaders = models.ManyToManyField("users.User", related_name="leader_of")
    members = models.ManyToManyField("users.User", related_name="member_of")
    progress = models.FloatField(default=0, null=False, blank=False)
    widget_config = models.IntegerField(default=1877248, null=False, blank=False)
    calendar_id = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return self.name
