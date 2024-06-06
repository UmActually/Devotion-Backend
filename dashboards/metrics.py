from enum import IntEnum
from typing import NamedTuple


class WidgetType(IntEnum):
    """Widget display types"""
    NUMBER = 0
    NUMBERS = 1
    VERTICAL_BAR = 2
    HORIZONTAL_BAR = 3
    LINE = 4
    PIE = 5
    HEAT_MAP = 6
    GAUGE = 7


class ProjectMetric(NamedTuple):
    name: str
    display_types: tuple[WidgetType, ...]


project_metrics: dict[str, ProjectMetric] = {
    "done_tasks_count": ProjectMetric(
        "No. tareas completadas",
        (WidgetType.NUMBER,)
    ),

    "all_done_tasks_count": ProjectMetric(
        "No. tareas completadas (total)",
        (WidgetType.NUMBER,)
    ),

    "done_tasks_by_date": ProjectMetric(
        "Tareas completadas por fecha",
        (WidgetType.LINE, WidgetType.VERTICAL_BAR, WidgetType.HEAT_MAP)
    ),

    "tasks_by_status": ProjectMetric(
        "Tareas por estado",
        (WidgetType.VERTICAL_BAR, WidgetType.HORIZONTAL_BAR, WidgetType.PIE)
    ),

    "tasks_by_priority": ProjectMetric(
        "Tareas por prioridad",
        (WidgetType.VERTICAL_BAR, WidgetType.HORIZONTAL_BAR, WidgetType.PIE, WidgetType.HEAT_MAP)
    ),

    "user_workload": ProjectMetric(
        "Carga de trabajo de usuarios",
        (WidgetType.NUMBERS, WidgetType.VERTICAL_BAR, WidgetType.HORIZONTAL_BAR, WidgetType.PIE, WidgetType.HEAT_MAP)
    ),

    "project_progress": ProjectMetric(
        "Progreso del proyecto",
        (WidgetType.GAUGE,)
    ),

    "all_project_progress": ProjectMetric(
        "Progreso del proyecto (total)",
        (WidgetType.GAUGE,)
    )
}
