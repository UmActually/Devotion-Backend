from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from projects.models import Project, get_config_number, get_widget_configuration
from .dashboard import Dashboard
from .metrics import WidgetType, get_display_types


def bad_request(message: str) -> Response:
    return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)


class DashboardView(APIView):
    def get(self, request: Request, project_id: str) -> Response:
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"message": "El proyecto no existe."}, status=status.HTTP_404_NOT_FOUND)

        dashboard = Dashboard(project, request.user)
        return dashboard.get_response()

    # TODO: Validar que el usuario sea miembro o líder del proyecto, quizás
    def put(self, request: Request, project_id: str) -> Response:
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"message": "El proyecto no existe."}, status=status.HTTP_404_NOT_FOUND)

        config = get_widget_configuration(project.widget_config)
        for metric_name, new_display_type_number in request.data.items():
            try:
                display_types = get_display_types(metric_name)
            except KeyError:
                return bad_request("Una o más métricas no son válidas.")

            try:
                new_display_type = WidgetType(int(new_display_type_number))
            except ValueError:
                return bad_request("Uno o más tipos de widgets no son válidos.")

            if new_display_type not in display_types:
                return bad_request(f"El tipo de widget {new_display_type} no es válido para la métrica {metric_name}.")

            config[metric_name] = WidgetType(new_display_type)

        if request.data:
            project.widget_config = get_config_number(config)
            project.save()

        dashboard = Dashboard(project, request.user)
        return dashboard.get_response()
