import copy
import re
from collections import deque

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


def _notify_step(on_step, current_task, completed_tasks, total_count, current_time, remaining_time=None):
    if on_step is None:
        return

    avg_waiting_time, avg_turnaround_time = _calculate_current_metrics(completed_tasks)
    on_step({
        "algorithm": "Round Robin",
        "current_task_id": current_task.task_id if current_task else None,
        "completed_count": len(completed_tasks),
        "total_count": total_count,
        "avg_waiting_time": avg_waiting_time,
        "avg_turnaround_time": avg_turnaround_time,
        "current_time": current_time,
        "remaining_time": dict(remaining_time or {}),
    })


def run_round_robin(tasks, time_quantum=3, on_step=None):
    """
    Round Robin: mỗi tác vụ chạy tối đa time_quantum rồi quay về cuối hàng đợi nếu chưa xong.
    Lưu ý: nếu time_quantum >= mọi burst_time thì Round Robin sẽ giống FCFS, đó là đúng lý thuyết.
    """
    time_quantum = _to_int(time_quantum, 3)
    if time_quantum <= 0:
        raise ValueError("time_quantum phải lớn hơn 0")

    tasks_copy = _prepare_tasks(tasks)

    tasks_copy.sort(
        key=lambda task: (
            task.arrival_time,
            get_task_number(task.task_id),
            str(task.task_id),
        )
    )

    remaining_time = {
        task.task_id: task.burst_time
        for task in tasks_copy
    }

    first_start_time = {
        task.task_id: None
        for task in tasks_copy
    }

    completed_tasks = []
    gantt_chart = []
    ready_queue = deque()

    current_time = 0
    index = 0
    total_count = len(tasks_copy)

    while len(completed_tasks) < total_count:
        while index < total_count and tasks_copy[index].arrival_time <= current_time:
            ready_queue.append(tasks_copy[index])
            index += 1

        if not ready_queue:
            if index >= total_count:
                break

            next_arrival_time = tasks_copy[index].arrival_time
            if current_time < next_arrival_time:
                gantt_chart.append(GanttBlock("IDLE", current_time, next_arrival_time))
                current_time = next_arrival_time

            _notify_step(
                on_step=on_step,
                current_task=None,
                completed_tasks=completed_tasks,
                total_count=total_count,
                current_time=current_time,
                remaining_time=remaining_time,
            )
            continue

        current_task = ready_queue.popleft()

        if first_start_time[current_task.task_id] is None:
            first_start_time[current_task.task_id] = current_time

        start_time = current_time
        run_time = min(time_quantum, remaining_time[current_task.task_id])
        end_time = start_time + run_time

        gantt_chart.append(GanttBlock(current_task.task_id, start_time, end_time))

        current_time = end_time
        remaining_time[current_task.task_id] -= run_time

        while index < total_count and tasks_copy[index].arrival_time <= current_time:
            ready_queue.append(tasks_copy[index])
            index += 1

        if remaining_time[current_task.task_id] > 0:
            ready_queue.append(current_task)
        else:
            current_task.start_time = first_start_time[current_task.task_id]
            current_task.completion_time = current_time
            current_task.turnaround_time = current_task.completion_time - current_task.arrival_time
            current_task.waiting_time = current_task.turnaround_time - current_task.burst_time
            current_task.response_time = current_task.start_time - current_task.arrival_time
            completed_tasks.append(current_task)

        _notify_step(
            on_step=on_step,
            current_task=current_task,
            completed_tasks=completed_tasks,
            total_count=total_count,
            current_time=current_time,
            remaining_time=remaining_time,
        )

    completed_tasks.sort(key=lambda task: (task.completion_time, get_task_number(task.task_id)))

    return build_simulation_result(
        f"Round Robin q={time_quantum}",
        completed_tasks,
        gantt_chart,
    )


round_robin = run_round_robin
