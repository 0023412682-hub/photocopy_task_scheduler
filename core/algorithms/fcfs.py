import copy
import re

try:
    from core.models import GanttBlock
    from core.metrics import build_simulation_result
except Exception:  # chạy tương thích khi đặt core trên sys.path
    from models import GanttBlock
    from metrics import build_simulation_result


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
        "algorithm": "FCFS",
        "current_task_id": current_task.task_id if current_task else None,
        "completed_count": len(completed_tasks),
        "total_count": total_count,
        "avg_waiting_time": avg_waiting_time,
        "avg_turnaround_time": avg_turnaround_time,
        "current_time": current_time,
    })


def run_fcfs(tasks, on_step=None):
    """
    FCFS: tác vụ đến trước xử lý trước.
    Nếu các tác vụ cùng arrival_time = 0, thứ tự hàng đợi lấy theo mã T001, T002...
    """
    tasks_copy = _prepare_tasks(tasks)

    tasks_copy.sort(
        key=lambda task: (
            task.arrival_time,
            get_task_number(task.task_id),
            str(task.task_id),
        )
    )

    completed_tasks = []
    gantt_chart = []
    current_time = 0

    for task in tasks_copy:
        if task.arrival_time > current_time:
            gantt_chart.append(GanttBlock("IDLE", current_time, task.arrival_time))
            current_time = task.arrival_time

        start_time = current_time
        end_time = start_time + task.burst_time

        task.start_time = start_time
        task.completion_time = end_time
        task.turnaround_time = task.completion_time - task.arrival_time
        task.waiting_time = task.turnaround_time - task.burst_time
        task.response_time = task.start_time - task.arrival_time

        gantt_chart.append(GanttBlock(task.task_id, start_time, end_time))

        current_time = end_time
        completed_tasks.append(task)

        _notify_step(
            on_step=on_step,
            current_task=task,
            completed_tasks=completed_tasks,
            total_count=len(tasks_copy),
            current_time=current_time,
        )

    return build_simulation_result("FCFS", completed_tasks, gantt_chart)


fcfs_schedule = run_fcfs
