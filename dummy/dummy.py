import json
import datetime
import getpass
from time import sleep
from random import randint, choice, sample
import faker
import api


admin_token = ""


with open("pools/lipsums.txt") as f:
    fsae_description, short_lipsum, medium_lipsum, long_lipsum = f.read().split("\n")

with open("pools/users.txt") as f:
    user_names = f.read().split("\n")

with open("pools/tree.txt") as f:
    tree = f.read().split("\n")

users: list[tuple[str, str]] = []
projects: list[tuple[str, str]] = []
tasks: list[tuple[str, str]] = []
current_line_index = 0
line_count = len(tree)
fake = faker.Faker("es_MX")


def get_indentation_level(line: str) -> int:
    return (len(line) - len(line.lstrip())) // 4


def create_tree_item(
        members: list[str], parent_project: str | None = None, parent_task: str | None = None,
        nest_level: int = 0, checo_perez_id: str | None = None) -> None:
    """Qué función más hermosa. Gracias, Wicho. Sé que estarás orgulloso de mí."""
    global current_line_index

    prev_line_item = None
    prev_line_is_task = False

    while True:
        try:
            current_line = tree[current_line_index]
            stripped_line = current_line.strip()
            indentation_level = get_indentation_level(current_line)
        except IndexError:
            return

        # Regresar un nivel si terminó el bloque
        if indentation_level < nest_level:
            return

        # Continuar con el siguiente nivel
        if indentation_level > nest_level:
            members_subset = members if prev_line_is_task else sample(members, randint(1, len(members)))
            create_tree_item(
                members=members_subset,
                parent_project=parent_project if prev_line_is_task else prev_line_item,
                parent_task=prev_line_item if prev_line_is_task else parent_task,
                nest_level=indentation_level
            )

        # Proyecto
        elif stripped_line.startswith("["):
            item_name = stripped_line[1:-1]
            project_id = api.create_project(
                user_token=admin_token,
                name=item_name,
                description=medium_lipsum,
                leaders=(
                    [checo_perez_id]
                    if nest_level == 0 and checo_perez_id
                    else [choice(members)]
                ),
                members=members,
                parent=parent_project
            )
            projects.append((project_id, item_name))
            # noinspection PyUnusedLocal
            prev_line_item = project_id
            prev_line_is_task = False
            print(current_line)
            sleep(0.75)
            current_line_index += 1

        # Tarea
        else:
            start_date = fake.date_this_year()
            due_date = start_date + datetime.timedelta(days=randint(1, 60))
            task_id = api.create_task(
                user_token=admin_token,
                name=stripped_line,
                description=short_lipsum,
                asignee=choice(members),
                start_date=start_date,
                due_date=due_date,
                priority=randint(0, 2),
                parent_project=parent_project,
                parent_task=parent_task
            )
            tasks.append((task_id, stripped_line))
            # noinspection PyUnusedLocal
            prev_line_item = task_id
            prev_line_is_task = True
            print(current_line)
            sleep(0.75)
            current_line_index += 1


def create_fsae_users() -> None:
    for name in user_names:
        first, last = name.split(" ", maxsplit=1)
        id_, token = api.create_user(first, last)
        users.append((id_, name))
        print(name)
        sleep(0.75)


def create_fsae_tree() -> None:
    all_user_ids = list(map(lambda x: x[0], users))
    checo_perez_id = all_user_ids[0]

    # Algo muy bien
    create_tree_item(all_user_ids, checo_perez_id=checo_perez_id)


def populate_fsae_friendly() -> None:
    global admin_token

    if not admin_token:
        print("Make sure an admin user exists.")
        admin_email = input("Admin email: ")
        admin_password = getpass.getpass("Admin password: ")
        admin_token = api.login(admin_email, admin_password)

    create_fsae_users()
    create_fsae_tree()

    with open("fsae_friendly_data.json", "w") as f_:
        json.dump({
            "users": users,
            "projects": projects,
            "tasks": tasks
        }, f_, indent=2)


def populate_random() -> None:
    pass


if __name__ == "__main__":
    populate_fsae_friendly()
