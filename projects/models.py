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

    def __str__(self):
        return self.name
