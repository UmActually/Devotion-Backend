import datetime
import uuid
from time import sleep
import requests


BASE_URL = "http://localhost:8000/"


class HTTPException(Exception):
    def __init__(self, r: requests.Response) -> None:
        self.status_code = r.status_code
        self.text = r.text

    def __str__(self) -> str:
        return f"HTTP {self.status_code}\nResponse: {self.text}"


def acentoless(text: str) -> str:
    return text.lower().replace("á", "a").replace("é", "e").replace("í", "i") \
        .replace("ó", "o").replace("ú", "u").replace("ñ", "n").replace("ä", "a") \
        .replace("ö", "o")


def email_from_name(first: str, last: str, attempt: int = 1) -> str:
    first = acentoless(first).split(" ")[0]
    last = acentoless(last).split(" ")[0]
    return f"{first}{last}{'' if attempt == 1 else attempt}@example.com"


def login(email: str, password: str) -> str:
    endpoint = "login/"

    r = requests.post(BASE_URL + endpoint, data={
        "email": email,
        "password": password
    })

    if not r:
        raise HTTPException(r)

    return r.json()["access"]


def create_user(first_names: str, last_names: str, email: str | None = None) -> tuple[str, str]:
    endpoint = "users/"
    attempt = 1

    while True:
        r = requests.post(BASE_URL + endpoint, data={
            "email": email or email_from_name(first_names, last_names, attempt),
            "first_names": first_names,
            "last_names": last_names,
            "password": "M4NGOtech"
        })

        if not r:
            if r.status_code == 400 and "email is already in use" in r.text:
                print("[!] Retrying with new email.")
                attempt += 1
                sleep(1)
                continue
            raise HTTPException(r)
        break

    json = r.json()
    return json["id"], json["token"]


def create_project(
        user_token: str, name: str, description: str, leaders: list[str],
        members: list[str], parent: str | None = None) -> str:
    endpoint = "projects/"

    r = requests.post(BASE_URL + endpoint, headers={
        "Authorization": "Bearer " + user_token
    }, data={
        "name": name,
        "description": description,
        "parent": parent,
        "leaders": ",".join(leaders),
        "members": ",".join(members)
    })

    if not r:
        raise HTTPException(r)

    json = r.json()
    return json["id"]


def create_project_(
        user_token: str, name: str, description: str, leaders: list[str],
        members: list[str], parent: str | None = None) -> str:
    return str(uuid.uuid4())


def create_task(
        user_token: str, name: str, description: str, parent_project: str,
        assignee: str, due_date: datetime.date, start_date: datetime.date | None = None,
        parent_task: str | None = None, priority: int | None = None) -> str:
    endpoint = "tasks/"

    r = requests.post(BASE_URL + endpoint, headers={
        "Authorization": "Bearer " + user_token
    }, data={
        "name": name,
        "description": description,
        "parent_project": parent_project,
        "assignee": assignee,
        "due_date": due_date.strftime("%Y-%m-%d"),
        "start_date": start_date.strftime("%Y-%m-%d") if start_date else None,
        "parent_task": parent_task,
        "priority": priority
    })

    if not r:
        raise HTTPException(r)

    json = r.json()
    return json["id"]


def create_task_(
        user_token: str, name: str, description: str, parent_project: str,
        assignee: str, due_date: datetime.date, start_date: datetime.date | None = None,
        parent_task: str | None = None, priority: int | None = None) -> str:
    return str(uuid.uuid4())


def update_task_dates(
        user_token: str, task_id: str, due_date: datetime.date,
        start_date: datetime.date | None = None) -> str:
    endpoint = f"tasks/{task_id}"

    r = requests.put(BASE_URL + endpoint, headers={
        "Authorization": "Bearer " + user_token
    }, data={
        "due_date": due_date.strftime("%Y-%m-%d"),
        "start_date": start_date.strftime("%Y-%m-%d") if start_date else None
    })

    if not r:
        raise HTTPException(r)

    json = r.json()
    return json["id"]
