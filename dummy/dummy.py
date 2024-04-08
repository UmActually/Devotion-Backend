from time import sleep
from random import sample
import api


def populate_fsae_friendly() -> None:
    with open("users.txt") as f:
        user_names = f.read().split("\n")

    with open("lipsums.txt") as f:
        fsae_description, short_lipsum, medium_lipsum, long_lipsum = f.read().split("\n")

    department_names = ["Chasis", "Electrónica", "Suspensión", "Finanzas", "Marketing", "Motor"]

    users: dict[str, tuple[str, str]] = {}
    departments: dict[str, str] = {}

    for name in user_names:
        first, last = name.split(" ", maxsplit=1)
        id_, token = api.create_user(first, last)
        users[name] = (id_, token)
        print(id_, "-", name)
        sleep(1)

    all_user_ids = list(map(lambda x: x[0], users.values()))

    fsae_id = api.create_project(
        users["Sergio Pérez"][1],
        "FSAE 2024",
        fsae_description,
        [users["Sergio Pérez"][0]],
        all_user_ids
    )

    print(fsae_id, "- FSAE 2024")
    sleep(1)

    for user, department in zip(users.values(), department_names):
        id_ = api.create_project(
            user[1],
            department,
            long_lipsum,
            [user[0]],
            list(sample(all_user_ids, 3)),
            fsae_id
        )
        print(id_, "-", department)
        sleep(1)


def populate_random() -> None:
    pass


if __name__ == "__main__":
    populate_fsae_friendly()
