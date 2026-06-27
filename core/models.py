from dataclasses import dataclass

@dataclass
class Task:
    task_id: str
    customer_name: str
    task_type: str
    arrival_time: int
    burst_time: int
    priority: int
    print_option: str = ""

    completion_time: int = 0
    turnaround_time: int = 0
    waiting_time: int = 0
    response_time: int = 0
    status: str = "Đang chờ"

@dataclass
class GanttBlock:
    task_id: str
    start_time: int
    end_time: int

@dataclass
class SimulationResult:
    algorithm_name: str
    tasks: list
    gantt_chart: list
    average_waiting_time: float
    average_turnaround_time: float
    average_response_time: float