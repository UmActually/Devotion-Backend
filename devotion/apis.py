import json
from typing import TYPE_CHECKING, Iterable
from rest_framework import serializers
from google.oauth2 import service_account
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from devotion.settings import env_variable
if TYPE_CHECKING:
    # en if para evitar circular imports
    from projects.models import Project
    from tasks.models import Task

GoogleAPIException = HttpError

google_api = discovery.build(
    'calendar', 'v3',
    credentials=service_account.Credentials.from_service_account_info(
        json.loads(env_variable("GOOGLE_SERVICE_ACCOUNT")),
        scopes=['https://www.googleapis.com/auth/calendar']
    )
)


def is_tec_email(email: str) -> bool:
    return email.endswith("@itesm.mx") or email.endswith("@tec.mx")


def acl_callback(_request_id, _response, exception) -> None:
    if exception is not None:
        raise serializers.ValidationError("Error al actualizar permisos en el calendario.")


def get_calendar_id(task: "Task") -> str:
    project = task.parent_project
    while project:
        if project.calendar_id:
            return project.calendar_id
        project = project.parent
    raise serializers.ValidationError("No se encontró el calendario del proyecto.")


def create_calendar(project: "Project") -> None:
    try:
        calendar_id = google_api.calendars().insert(body={
            "summary": project.name,
            "description": project.description,
            "timeZone": "America/Mexico_City"
        }).execute()["id"]
    except GoogleAPIException:
        raise serializers.ValidationError("Error al crear el calendario.")

    project.calendar_id = calendar_id
    project.save()

    batch = google_api.new_batch_http_request(callback=acl_callback)
    batch.add(google_api.acl().insert(
        calendarId=calendar_id,
        sendNotifications=False,
        body={
            "role": "reader",
            "scope": {
                "type": "domain",
                "value": "itesm.mx"
            }
        }
    ))

    members = project.members.all()
    leaders = project.leaders.all()

    for member in members:
        email = member.email
        # Recordemos que hay usuarios de prueba jiji
        if not is_tec_email(email):
            continue
        batch.add(google_api.acl().insert(
            calendarId=calendar_id,
            sendNotifications=True,
            body={
                "role": "owner" if member in leaders else "writer",
                "scope": {
                    "type": "user",
                    "value": email
                }
            }
        ))

    batch.execute()


def _update_calendar_info(project: "Project", modified_data: Iterable[str]) -> None:
    body = {}
    if "name" in modified_data:
        body["summary"] = project.name
    if "description" in modified_data:
        body["description"] = project.description
    try:
        google_api.calendars().patch(calendarId=project.calendar_id, body=body).execute()
    except GoogleAPIException:
        raise serializers.ValidationError("Error al actualizar la información del calendario.")


def _update_calendar_acl(project: "Project", **kwargs: set[str]) -> None:
    old_leaders = kwargs["old_leaders"]
    new_leaders = set(map(lambda x: x.email, project.leaders.all()))
    old_members = kwargs["old_members"]
    new_members = set(map(lambda x: x.email, project.members.all()))
    old_mortals = old_members - old_leaders
    new_mortals = new_members - new_leaders

    promoted_demoted = (new_leaders & old_mortals) | (old_leaders & new_mortals)
    added_members = new_members - old_members
    removed_members = old_members - new_members

    calendar_id = project.calendar_id
    batch = google_api.new_batch_http_request(callback=acl_callback)

    # miembros eliminados
    for member_email in removed_members:
        if not is_tec_email(member_email):
            continue
        batch.add(google_api.acl().delete(
            calendarId=calendar_id,
            ruleId=f"user:{member_email}"
        ))

    # miembros que cambiaron de rol
    for member_email in promoted_demoted:
        if not is_tec_email(member_email):
            continue
        batch.add(google_api.acl().patch(
            calendarId=calendar_id,
            ruleId=f"user:{member_email}",
            sendNotifications=True,
            body={
                "role": "owner" if member_email in new_leaders else "writer"
            }
        ))

    # miembros añadidos
    for member_email in added_members:
        if not is_tec_email(member_email):
            continue
        batch.add(google_api.acl().insert(
            calendarId=calendar_id,
            sendNotifications=True,
            body={
                "role": "owner" if member_email in new_leaders else "writer",
                "scope": {
                    "type": "user",
                    "value": member_email
                }
            }
        ))

    batch.execute()


def update_calendar(project: "Project", modified_data: Iterable[str], **kwargs: set[str]) -> None:
    if "name" in modified_data or "description" in modified_data:
        _update_calendar_info(project, modified_data)
    if "leaders" in modified_data or "members" in modified_data:
        _update_calendar_acl(project, **kwargs)


def delete_calendar(calendar_id: str) -> None:
    google_api.calendars().delete(calendarId=calendar_id).execute()


def create_event(task: "Task") -> None:
    try:
        event_id = google_api.events().insert(
            calendarId=get_calendar_id(task),
            sendUpdates="none",
            body={
                "start": {"date": task.due_date.isoformat()},
                "end": {"date": task.due_date.isoformat()},
                "summary": task.name,
                "description": task.description
            }
        ).execute()["id"]
    except GoogleAPIException:
        raise serializers.ValidationError("Error al crear el evento.")

    task.event_id = event_id
    task.save()


def update_event(task: "Task", modified_data: Iterable[str]) -> None:
    body = {}
    if "name" in modified_data:
        body["summary"] = task.name
    if "description" in modified_data:
        body["description"] = task.description
    if "due_date" in modified_data:
        due_date = task.due_date.isoformat()
        body["start"] = {"date": due_date}
        body["end"] = {"date": due_date}

    try:
        google_api.events().patch(
            calendarId=get_calendar_id(task),
            eventId=task.event_id,
            sendUpdates="none",
            body=body
        ).execute()
    except GoogleAPIException as e:
        print(e)
        raise serializers.ValidationError("Error al actualizar el evento.")


def delete_event(task: "Task") -> None:
    google_api.events().delete(
        calendarId=get_calendar_id(task),
        eventId=task.event_id
    ).execute()
