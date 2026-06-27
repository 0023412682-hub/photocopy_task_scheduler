try:
    from core.models import SimulationResult
except Exception:
    from models import SimulationResult


def calculate_average_waiting_time(tasks):
    if not tasks:
        return 0
    return round(sum(task.waiting_time for task in tasks) / len(tasks), 2)


def calculate_average_turnaround_time(tasks):
    if not tasks:
        return 0
    return round(sum(task.turnaround_time for task in tasks) / len(tasks), 2)


def calculate_average_response_time(tasks):
    if not tasks:
        return 0
    return round(sum(task.response_time for task in tasks) / len(tasks), 2)


def build_simulation_result(algorithm_name, tasks, gantt_chart):
    return SimulationResult(
        algorithm_name=algorithm_name,
        tasks=tasks,
        gantt_chart=gantt_chart,
        average_waiting_time=calculate_average_waiting_time(tasks),
        average_turnaround_time=calculate_average_turnaround_time(tasks),
        average_response_time=calculate_average_response_time(tasks),
    )