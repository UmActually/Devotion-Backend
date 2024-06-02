import datetime

import pytz
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from projects.models import Project
from tasks.models import Task
from .models import Invite


def bad_request(message: str) -> Response:
    return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_invite(request: Request) -> Response:
    """
    Crea una invitación.

    Campos:
    - email
    - project
    """
    data = request.data
    has_project = "project" in data
    has_task = "task" in data

    # Que loco un XOR
    if has_project == has_task:
        return bad_request("Debes especificar un proyecto o una tarea.")

    task = None
    if has_project:
        try:
            project = Project.objects.get(id=data["project"])
        except Project.DoesNotExist:
            return bad_request("Proyecto no encontrado.")
    else:
        try:
            task = Task.objects.get(id=data["task"])
        except Task.DoesNotExist:
            return bad_request("Tarea no encontrada.")
        project = task.parent_project

    if request.user not in project.leaders.all():
        return Response(
            {"message": "No eres líder del proyecto."},
            status=status.HTTP_403_FORBIDDEN)

    now = datetime.datetime.now(pytz.timezone("Mexico/General"))
    invite = Invite.objects.create(
        project_id=project if has_project else None,
        task_id=task if has_task else None,
        expiration_date=now + datetime.timedelta(days=7),
    )

    return Response({
        "id": invite.id,
    }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def get_invite(_request: Request, invite_id: str) -> Response:
    """Obtiene la información de una invitación."""
    try:
        invite = Invite.objects.get(id=invite_id)
    except Invite.DoesNotExist:
        return Response({"message": "Invitación no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    if invite.expiration_date < datetime.datetime.now(pytz.timezone("Mexico/General")):
        invite.delete()
        return Response({"message": "Invitación expirada."}, status=status.HTTP_410_GONE)

    is_task = invite.task is not None
    return Response({
        "is_task": is_task,
        "resource": invite.task.id if is_task else invite.project.id,
    }, status=status.HTTP_200_OK)
