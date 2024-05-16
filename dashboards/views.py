from django.db.models.query import QuerySet
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from projects.models import Project
from tasks.serializers import TaskDashboardSerializer
from .serializers import (
    WidgetSerializer,
    WidgetDeserializer,
    DataSourceSerializer,
    DataSourceDeserializer,
)
from .models import DataSource, Widget


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_widget(request: Request) -> Response:
    serializer = WidgetDeserializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    widget = serializer.save()
    return Response(WidgetSerializer(widget).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_data_source(request: Request) -> Response:
    data = request.data
    serializer = DataSourceDeserializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data_source = serializer.save()

    return Response(
        DataSourceSerializer(data_source).data, status=status.HTTP_201_CREATED
    )


def get_all_subtree_tasks(project_id: str) -> QuerySet:
    """Obtiene todas las tareas de un proyecto y sus subproyectos."""
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response(
            {"message": "Proyecto no encontrado."}, status=status.HTTP_404_NOT_FOUND
        )

    all_tasks: QuerySet = project.tasks.all()

    def recurse_project(_project: Project) -> None:
        nonlocal all_tasks
        for subproject in _project.projects.all():
            all_tasks |= subproject.tasks.all()
            recurse_project(subproject)

    recurse_project(project)
    return all_tasks


class DashboardView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return []
        return [IsAuthenticated()]

    def get(self, request: Request, project_id: str) -> Response:
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {"message": "Proyecto no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(e)

        response = {}

        try:
            response["widgets"] = WidgetSerializer(
                project.widgets.all(), many=True
            ).data
            response["projectName"] = project.name

            if user := request.user:
                all_tasks = get_all_subtree_tasks(project.id).filter(assignee=user)

                tasksToDo = all_tasks.filter(status=0) | all_tasks.filter(status=1)
                tasksToVerify = all_tasks.filter(status=2)

                response["tasksToDo"] = TaskDashboardSerializer(
                    tasksToDo, many=True
                ).data
                response["tasksToVerify"] = TaskDashboardSerializer(
                    tasksToVerify, many=True
                ).data
                response["dataSources"] = DataSourceSerializer(
                    project.data_sources.all(), many=True
                ).data
        except Exception as e:
            print(e)

        return Response(response, status=status.HTTP_200_OK)


class DataSourceView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return []
        return [IsAuthenticated()]

    def get(self, request: Request, data_source_id: str) -> Response:
        project_id = data_source_id
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {"message": "Proyecto no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            response = DataSourceSerializer(project.data_sources.all(), many=True).data
        except Exception as e:
            print(e)

        return Response(response, status=status.HTTP_200_OK)

    def delete(self, request: Request, data_source_id: str) -> Response:
        try:
            data_source = DataSource.objects.get(id=data_source_id)
        except DataSource.DoesNotExist:
            return Response(
                {"message": "La fuente de datos no existe."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data_source.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request: Request, data_source_id: str) -> Response:
        try:
            data_source = DataSource.objects.get(id=data_source_id)
        except DataSource.DoesNotExist:
            return Response(
                {"message": "La fuente de datos no existe."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DataSourceDeserializer(data=request.data, instance=data_source)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class WidgetView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return []
        return [IsAuthenticated()]

    def delete(self, request: Request, widget_id: str) -> Response:
        try:
            widget = Widget.objects.get(id=widget_id)
        except Widget.DoesNotExist:
            return Response(
                {"message": "El widget no existe."}, status=status.HTTP_404_NOT_FOUND
            )

        widget.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request: Request, widget_id: str) -> Response:
        try:
            widget = Widget.objects.get(id=widget_id)
        except Widget.DoesNotExist:
            return Response(
                {"message": "El widget no existe."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = WidgetDeserializer(data=request.data, instance=widget)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_all_data_sources(request) -> Response:
    return Response(
        DataSourceSerializer(DataSource.objects.all(), many=True).data,
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def get_all_widgets(request) -> Response:
    return Response(
        WidgetSerializer(Widget.objects.all(), many=True).data,
        status=status.HTTP_200_OK,
    )
