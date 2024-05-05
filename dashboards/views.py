from django.db.models.query import QuerySet
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from projects.models import Project
from tasks.serializers import TaskDashboardSerializer

def get_all_subtree_tasks(project_id: str) -> QuerySet:
    """Obtiene todas las tareas de un proyecto y sus subproyectos."""
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"message": "Proyecto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    all_tasks: QuerySet = project.tasks.all()

    def recurse_project(_project: Project) -> None:
        nonlocal all_tasks
        for subproject in _project.projects.all():
            all_tasks |= subproject.tasks.all()
            recurse_project(subproject)

    recurse_project(project)
    return all_tasks


class DashboardView(APIView): 
    def get(self, request: Request, project_id: str) -> Response:
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"message": "Proyecto no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
        
        response = {}
        
        if user := request.user:
            all_tasks = get_all_subtree_tasks(project.id).filter(assignee=user)

            tasksToDo = all_tasks.filter(status=0) | all_tasks.filter(status=1)
            tasksToVerify = all_tasks.filter(status=2)

            response["tasksToDo"] = TaskDashboardSerializer(tasksToDo, many=True).data
            response["tasksToVerify"] = TaskDashboardSerializer(tasksToVerify, many=True).data

        return Response(response, status=status.HTTP_200_OK)