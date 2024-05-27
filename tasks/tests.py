from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from projects.models import Project
from .models import Task, TaskStatus, TaskPriority


class TasksTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.checo = User.objects.create(
            email="sergioperez@devotion.com",
            first_names="Sergio",
            last_names="Pérez"
        )
        self.verstappen = User.objects.create(
            email="maxverstappen@devotion.com",
            first_names="Max",
            last_names="Verstappen"
        )
        self.hamilton = User.objects.create(
            email="lewishamilton@devotion.com",
            first_names="Lewis",
            last_names="Hamilton"
        )
        self.fsae = Project.objects.create(
            name="FSAE 2024"
        )
        self.fsae.leaders.set([self.checo])
        self.fsae.members.set([self.checo, self.verstappen])
        self.task1 = Task.objects.create(
            name="Tarea 1",
            start_date="2024-01-01",
            due_date="2024-01-01",
            parent_project=self.fsae,
            assignee=self.checo,
            status=TaskStatus.NOT_STARTED,
            priority=TaskPriority.MEDIUM,
        )

    def test_user_story_15(self):
        # H15T3 - Descripción: Intentar crear una subtarea sin ser miembro del proyecto
        # Leonardo Corona Garza
        self.client.force_authenticate(self.hamilton)
        response = self.client.post(
            "/tasks/",
            {
                "name": "Tarea 2",
                "description": "N/A",
                "due_date": "2024-01-01",
                "parent_project": self.fsae.id,
                "parent_task": self.task1.id,
                "assignee": self.checo.id
            }
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Task.objects.count(), 1)

        # H15T4 - Descripción: Crear una subtarea sin ser líder del proyecto (siendo miembro)
        # Leonardo Corona Garza
        self.client.force_authenticate(self.verstappen)
        response = self.client.post(
            "/tasks/",
            {
                "name": "Tarea 2",
                "description": "N/A",
                "due_date": "2024-01-01",
                "parent_project": self.fsae.id,
                "parent_task": self.task1.id,
                "assignee": self.checo.id
            }
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Task.objects.count(), 2)

        # H15T7 - Descripción: Intentar crear una subtarea sin asignado
        # Leonardo Corona Garza
        self.client.force_authenticate(self.checo)
        response = self.client.post(
            "/tasks/",
            {
                "name": "Tarea 2",
                "description": "N/A",
                "due_date": "2024-01-01",
                "parent_project": self.fsae.id,
                "parent_task": self.task1.id,
            }
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.count(), 2)
