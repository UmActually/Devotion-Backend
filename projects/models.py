from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False)
    description = models.TextField(max_length=1024, null=True, blank=True)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)
    leaders = models.JSONField(max_length=256, null=False, blank=False)
    members = models.JSONField(max_length=256, null=False, blank=False)
    dashboard = models.OneToOneField(
        "dashboards.Dashboard", on_delete=models.CASCADE, null=False, blank=False,
        related_name="project")

    def __str__(self):
        return self.name
