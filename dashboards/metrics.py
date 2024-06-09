from enum import IntEnum


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


PROJECT_METRICS: dict[str, tuple[WidgetType, ...]] = {
    "done_tasks_count": (),
    "all_done_tasks_count": (),
    "done_tasks_by_date": (),
    "tasks_by_status": (),
    "tasks_by_priority": (),
    "user_workload": (),
    "project_progress": (),
    "all_project_progress": ()
}


def project_metrics() -> list[str]:
    return list(PROJECT_METRICS.keys())


def set_display_types(metric_name: str, display_types: tuple[WidgetType, ...]) -> None:
    PROJECT_METRICS[metric_name] = display_types


def get_display_types(metric_name: str) -> tuple[WidgetType, ...]:
    return PROJECT_METRICS[metric_name]
