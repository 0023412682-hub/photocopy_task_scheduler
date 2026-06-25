import copy
import re

from models import GanttBlock
from utils.metrics import build_simulation_result


def get_task_number(task_id):
    match = re.search(r"\d+", str(task_id))
    if match:
        return int(match.group())
    return 999999


def _to_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def _prepare_tasks(tasks):
    tasks_copy = copy.deepcopy(tasks or [])

    for index, task in enumerate(tasks_copy):
        if not getattr(task, "task_id", None):
            task.task_id = f"T{index + 1:03d}"
        task.arrival_time = _to_int(getattr(task, "arrival_time", 0), 0)
        task.burst_time = max(1, _to_int(getattr(task, "burst_time", 1), 1))
        task.priority = _to_int(getattr(task, "priority", 1), 1)

    return tasks_copy


def _calculate_current_metrics(completed_tasks):
    if not completed_tasks:
        return 0, 0

    avg_waiting_time = sum(task.waiting_time for task in completed_tasks) / len(completed_tasks)
    avg_turnaround_time = sum(task.turnaround_time for task in completed_tasks) / len(completed_tasks)
    return avg_waiting_time, avg_turnaround_time


def _notify_step(on_step, current_task, completed_tasks, total_count, current_time):
    if on_step is None:
        return

    avg_waiting_time, avg_turnaround_time = _calculate_current_metrics(completed_tasks)
    on_step({
        "algorithm": "Priority",
        "current_task_id": current_task.task_id if current_task else None,
        "completed_count": len(completed_tasks),
        "total_count": total_count,
        "avg_waiting_time": avg_waiting_time,
        "avg_turnaround_time": avg_turnaround_time,
        "current_time": current_time,
    })


def run_priority(tasks, on_step=None):
    """
    Priority non-preemptive: priority nhỏ hơn nghĩa là ưu tiên cao hơn.
    """
    tasks_copy = _prepare_tasks(tasks)

    completed_tasks = []
    gantt_chart = []
    remaining_tasks = tasks_copy[:]
    current_time = 0

    while remaining_tasks:
        available_tasks = [
            task for task in remaining_tasks
            if task.arrival_time <= current_time
        ]

        if not available_tasks:
            next_task = min(
                remaining_tasks,
                key=lambda task: (
                    task.arrival_time,
                    task.priority,
                    get_task_number(task.task_id),
                    str(task.task_id),
                )
            )
            if current_time < next_task.arrival_time:
                gantt_chart.append(GanttBlock("IDLE", current_time, next_task.arrival_time))
                current_time = next_task.arrival_time

            _notify_step(
                on_step=on_step,
                current_task=None,
                completed_tasks=completed_tasks,
                total_count=len(tasks_copy),
                current_time=current_time,
            )
            continue

        selected_task = min(
            available_tasks,
            key=lambda task: (
                task.priority,
                task.arrival_time,
                get_task_number(task.task_id),
                str(task.task_id),
            )
        )

        start_time = current_time
        end_time = start_time + selected_task.burst_time

        selected_task.start_time = start_time
        selected_task.completion_time = end_time
        selected_task.turnaround_time = selected_task.completion_time - selected_task.arrival_time
        selected_task.waiting_time = selected_task.turnaround_time - selected_task.burst_time
        selected_task.response_time = selected_task.start_time - selected_task.arrival_time

        gantt_chart.append(GanttBlock(selected_task.task_id, start_time, end_time))

        current_time = end_time
        completed_tasks.append(selected_task)
        remaining_tasks.remove(selected_task)

        _notify_step(
            on_step=on_step,
            current_task=selected_task,
            completed_tasks=completed_tasks,
            total_count=len(tasks_copy),
            current_time=current_time,
        )

    return build_simulation_result("Priority", completed_tasks, gantt_chart)


priority_scheduling = run_priority
