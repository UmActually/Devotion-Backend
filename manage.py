#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import time
import webbrowser


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devotion.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    if sys.argv[1] == 'removemigrations':
        os.system('find . -path "*/migrations/*.py" -not -name "__init__.py" -delete')
        os.system('find . -path "*/migrations/*.pyc" -delete')
        return

    if "runserver" in sys.argv and not os.path.exists("coconut.png"):
        print("\n.", end="")
        time.sleep(1)
        print(".", end="")
        time.sleep(1)
        print(".")
        time.sleep(1)
        webbrowser.open_new_tab("https://i.imgflip.com/64vhkk.png")
        raise FileNotFoundError(
            """The coconut tree (Cocos nucifera) is a member of the palm tree family (Arecaceae) and the only living
species of the genus Cocos.[1] The term "coconut" (or the archaic "cocoanut")[2] can refer to the whole coconut palm,
the seed, or the fruit, which botanically is a drupe, not a nut. They are ubiquitous in coastal tropical regions and
are a cultural icon of the tropics.""")

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
