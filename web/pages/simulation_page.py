import base64
import copy
import html
import importlib
import json
import math
import re
import sys
import time
import textwrap
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import streamlit as st


# =========================================================
# IMPORT COMPATIBILITY
# =========================================================
# File thuật toán trong các bản dự án có thể nằm ở:
# - core/algorithms/fcfs.py
# - algorithms/fcfs.py
# - hoặc trực tiếp fcfs.py, sjf.py, priority.py, round_robin.py ở thư mục gốc.
# Thêm path trước khi import để trang Simulation không bị báo "chưa import được thuật toán".
_CURRENT_FILE = Path(__file__).resolve()
_PROJECT_ROOT_CANDIDATES = [
    _CURRENT_FILE.parent,
    Path.cwd(),
]

try:
    _PROJECT_ROOT_CANDIDATES.append(_CURRENT_FILE.parents[2])
except Exception:
    pass

for _root in _PROJECT_ROOT_CANDIDATES:
    for _path in (_root, _root / "core", _root / "web"):
        _path_text = str(_path)
        if _path.exists() and _path_text not in sys.path:
            sys.path.insert(0, _path_text)


def _import_algorithm(
    module_candidates: list[str],
    func_candidates: str | list[str],
) -> Callable[..., Any] | None:
    if isinstance(func_candidates, str):
        func_candidates = [func_candidates]

    for module_name in module_candidates:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue

        for func_name in func_candidates:
            func = getattr(module, func_name, None)
            if callable(func):
                return func

    return None


def _import_attr(module_candidates: list[str], attr_name: str, default: Any = None) -> Any:
    for module_name in module_candidates:
        try:
            module = importlib.import_module(module_name)
            value = getattr(module, attr_name, None)
            if value is not None:
                return value
        except Exception:
            continue
    return default


run_fcfs = _import_algorithm(
    ["core.algorithms.fcfs", "algorithms.fcfs", "core.fcfs", "fcfs"],
    ["run_fcfs", "fcfs_schedule"],
)
run_sjf = _import_algorithm(
    ["core.algorithms.sjf", "algorithms.sjf", "core.sjf", "sjf"],
    ["run_sjf", "sjf_schedule"],
)
run_priority = _import_algorithm(
    ["core.algorithms.priority", "algorithms.priority", "core.priority", "priority"],
    ["run_priority", "priority_scheduling"],
)
run_round_robin = _import_algorithm(
    ["core.algorithms.round_robin", "algorithms.round_robin", "core.round_robin", "round_robin"],
    ["run_round_robin", "round_robin"],
)

PROJECT_DEFAULT_QUANTUM = _import_attr(
    ["assets.constants", "utils.constants", "core.constants", "constants"],
    "DEFAULT_TIME_QUANTUM",
    3,
)


# ====================== THEME ======================
PRIMARY = "#005BAC"
PRIMARY_DARK = "#004A99"
BG = "#F4F7FB"
WHITE = "#FFFFFF"
TEXT = "#1F2937"
MUTED = "#64748B"
BORDER = "#D9E2EC"
LIGHT_LINE = "#E2E8F0"
RED = "#D71920"
GREEN = "#16A34A"
GREEN_DARK = "#15803D"
GREEN_BG = "#F0FDF4"
ORANGE = "#F97316"
ORANGE_DARK = "#C2410C"
ORANGE_BG = "#FFF7ED"
PURPLE = "#7C3AED"
PURPLE_BG = "#F5F3FF"
BLUE_BG = "#EFF6FF"

DEFAULT_QUANTUM = 3
if PROJECT_DEFAULT_QUANTUM:
    try:
        DEFAULT_QUANTUM = int(PROJECT_DEFAULT_QUANTUM)
    except Exception:
        DEFAULT_QUANTUM = 3

EVENT_STEP_SECONDS = 0.05
AUTO_ADVANCE_STEPS = 5
HEAVY_REFRESH_EVERY = 2
PX_PER_TIME = 26

TASK_COLORS = [
    "#0B63CE", "#16A34A", "#F97316", "#7C3AED",
    "#DC2626", "#0891B2", "#2563EB", "#9333EA",
    "#EA580C", "#059669", "#BE123C", "#0F766E",
]
BASE_DIR = Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) >= 3 else Path.cwd()


# =========================================================
# SHARED TASK PERSISTENCE
# =========================================================
# Dùng chung với task_page.py. Nếu Streamlit bị tạo session mới khi chuyển trang
# bằng ?page=..., Simulation vẫn nạp lại được danh sách tác vụ vừa import.
TASK_STORE_FILE = BASE_DIR / ".photocopy_shared_tasks.json"
SIMULATION_STORE_FILE = BASE_DIR / ".photocopy_simulation_payload.json"
TASK_FIELDS = [
    "task_id",
    "customer_name",
    "task_type",
    "arrival_time",
    "burst_time",
    "priority",
    "print_option",
    "status",
    "processing_method",
    "cover_pages",
    "color_pages",
    "bw_pages",
    "total_pages",
    "completion_time",
    "turnaround_time",
    "waiting_time",
    "response_time",
    "simulation_algorithm",
]


def task_to_plain_dict(task: Any) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for key in TASK_FIELDS:
        row[key] = val(task, key, "")
    for key in (
        "arrival_time",
        "burst_time",
        "priority",
        "cover_pages",
        "color_pages",
        "bw_pages",
        "total_pages",
        "completion_time",
        "turnaround_time",
        "waiting_time",
        "response_time",
    ):
        if row.get(key, "") == "":
            row[key] = 0
        row[key] = to_int(row.get(key), 0)
    return row


def save_tasks_to_store(source: list[Any] | None = None) -> None:
    try:
        data = [task_to_plain_dict(task) for task in (source if source is not None else tasks())]
        TASK_STORE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def load_tasks_from_store() -> list[dict[str, Any]]:
    try:
        if not TASK_STORE_FILE.exists():
            return []
        raw = json.loads(TASK_STORE_FILE.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return []
        loaded: list[dict[str, Any]] = []
        for index, item in enumerate(raw):
            if not isinstance(item, dict):
                continue
            task_id = str(item.get("task_id") or f"T{index + 1:03d}").strip()
            if not task_id:
                continue
            cover = max(0, to_int(item.get("cover_pages"), 0))
            color = max(0, to_int(item.get("color_pages"), 0))
            bw = max(0, to_int(item.get("bw_pages"), 0))
            total_pages = max(0, to_int(item.get("total_pages"), cover + color + bw))
            if cover == 0 and color == 0 and bw == 0 and total_pages > 0:
                bw = total_pages
            loaded.append({
                **item,
                "task_id": task_id,
                "customer_name": str(item.get("customer_name") or "Khách lẻ"),
                "task_type": str(item.get("task_type") or "In tài liệu"),
                "arrival_time": to_int(item.get("arrival_time"), 0),
                "burst_time": max(1, to_int(item.get("burst_time"), 1)),
                "priority": max(1, to_int(item.get("priority"), 1)),
                "cover_pages": cover,
                "color_pages": color,
                "bw_pages": bw,
                "total_pages": cover + color + bw,
                "print_option": str(item.get("print_option") or ""),
                "status": str(item.get("status") or "Đang chờ"),
                "processing_method": str(item.get("processing_method") or "Tính theo số trang"),
                "completion_time": to_int(item.get("completion_time"), 0),
                "turnaround_time": to_int(item.get("turnaround_time"), 0),
                "waiting_time": to_int(item.get("waiting_time"), 0),
                "response_time": to_int(item.get("response_time"), 0),
                "simulation_algorithm": str(item.get("simulation_algorithm") or ""),
            })
        return loaded
    except Exception:
        return []


def restore_tasks_if_needed() -> None:
    if st.session_state.get("tasks"):
        return
    persisted = load_tasks_from_store()
    if persisted:
        st.session_state["tasks"] = persisted


# ====================== HTML HELPERS ======================
def html_block(value: str) -> str:
    """
    Chuẩn hóa HTML trước khi đưa vào st.markdown.

    Streamlit dùng Markdown, nên nếu HTML multiline bị thụt >= 4 khoảng trắng,
    Markdown sẽ xem đó là code block và hiện nguyên <div> ra màn hình.
    Hàm này dedent + lstrip từng dòng để không còn raw HTML.
    """
    dedented = textwrap.dedent(str(value)).strip()
    return "\n".join(line.lstrip() for line in dedented.splitlines())


def render_html(value: str) -> None:
    st.markdown(html_block(value), unsafe_allow_html=True)


# ====================== ICON HELPERS ======================
def _norm_name(name: str) -> str:
    name = str(name or "").strip().lower().replace(" ", "_").replace("-", "_")
    return re.sub(r"[^a-z0-9_]+", "", name)


def _icon_dirs() -> list[Path]:
    cwd = Path.cwd()
    here = Path(__file__).resolve()
    paths = [
        BASE_DIR / "assets" / "icons",
        BASE_DIR / "web" / "assets" / "icons",
        BASE_DIR / "utils" / "icons",
        here.parents[1] / "assets" / "icons" if len(here.parents) > 1 else cwd / "assets" / "icons",
        cwd / "assets" / "icons",
        cwd / "web" / "assets" / "icons",
        cwd / "utils" / "icons",
    ]
    result: list[Path] = []
    for p in paths:
        if p not in result:
            result.append(p)
    return result


@st.cache_data(show_spinner=False)
def _icon_path(name: str) -> str:
    if not name:
        return ""
    raw = str(name).strip()
    direct = Path(raw)
    if direct.is_file():
        return str(direct)

    names = [raw]
    if not raw.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".svg")):
        names += [f"{raw}.png", f"{raw}.jpg", f"{raw}.jpeg", f"{raw}.webp", f"{raw}.svg"]
    target = _norm_name(Path(raw).stem)

    for folder in _icon_dirs():
        if not folder.exists():
            continue
        for n in names:
            p = folder / n
            if p.exists():
                return str(p)
        for p in folder.iterdir():
            if p.is_file() and _norm_name(p.stem) == target:
                return str(p)
    return ""


@st.cache_data(show_spinner=False)
def icon_uri(name: str) -> str:
    path = _icon_path(name)
    if not path:
        return ""
    p = Path(path)
    suffix = p.suffix.lower().replace(".", "") or "png"
    mime = "svg+xml" if suffix == "svg" else suffix
    return f"data:image/{mime};base64," + base64.b64encode(p.read_bytes()).decode("utf-8")


def icon(name: str, size: int = 24, cls: str = "") -> str:
    src = icon_uri(name)
    if not src:
        return ""
    class_attr = f' class="{cls}"' if cls else ""
    return f'<img{class_attr} src="{src}" style="width:{size}px;height:{size}px;object-fit:contain;" />'


def task_icon_html(task_type: Any, size: int = 44) -> str:
    text = str(task_type or "").lower()
    candidates = ["Printer"]
    if "scan" in text:
        candidates = ["Scan", "Scanner", "Printer"]
    elif "sao" in text or "copy" in text or "photo" in text:
        candidates = ["Copy", "Photocopy", "Printer"]
    for name in candidates:
        img = icon(name, size)
        if img:
            return img
    if "scan" in text:
        return f'<div class="emoji-printer" style="font-size:{size}px">📠</div>'
    if "sao" in text or "copy" in text or "photo" in text:
        return f'<div class="emoji-printer" style="font-size:{size}px">📄</div>'
    return f'<div class="emoji-printer" style="font-size:{size}px">🖨️</div>'


def printer_line_icon(color: str = PRIMARY, size: int = 44) -> str:
    """Icon máy in dạng SVG để đổi màu theo từng tác vụ/thuật toán."""
    safe_color = html.escape(str(color or PRIMARY))
    safe_size = max(24, to_int(size, 44))
    stroke = max(2, round(safe_size / 18, 1))
    return html_block(
        f'<svg class="task-printer-svg" width="{safe_size}" height="{safe_size}" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="printer">'
        f'<rect x="18" y="6" width="28" height="16" rx="2.5" fill="#FFFFFF" stroke="{safe_color}" stroke-width="{stroke}"/>'
        f'<rect x="9" y="22" width="46" height="25" rx="5" fill="#FFFFFF" stroke="{safe_color}" stroke-width="{stroke}"/>'
        f'<rect x="20" y="39" width="24" height="17" rx="2.5" fill="#FFFFFF" stroke="{safe_color}" stroke-width="{stroke}"/>'
        f'<line x1="24" y1="45" x2="40" y2="45" stroke="{safe_color}" stroke-width="{stroke}" stroke-linecap="round"/>'
        f'<line x1="24" y1="50" x2="40" y2="50" stroke="{safe_color}" stroke-width="{stroke}" stroke-linecap="round"/>'
        f'<circle cx="47" cy="30" r="2.7" fill="{safe_color}"/>'
        '</svg>'
    )


# ====================== GENERIC TASK HELPERS ======================
def init_state() -> None:
    if "tasks" not in st.session_state:
        st.session_state["tasks"] = []

    defaults = {
        "sim_results": OrderedDict(),
        "sim_normalized_tasks": [],
        "sim_task_color_map": {},
        "sim_current_time": 0,
        "sim_max_time": 0,
        "sim_timeline_points": [0],
        "sim_timeline_index": 0,
        "sim_running": False,
        "sim_finished": False,
        "sim_note": "",
        "sim_quantum": DEFAULT_QUANTUM,
        "sim_last_tick": 0.0,
        "sim_task_signature": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    restore_tasks_if_needed()


def tasks() -> list[Any]:
    restore_tasks_if_needed()
    return st.session_state.get("tasks", []) or []


def val(obj: Any, key: str, default: Any = "") -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def put(obj: Any, key: str, value: Any) -> None:
    if isinstance(obj, dict):
        obj[key] = value
    else:
        setattr(obj, key, value)


def to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(value))
    except Exception:
        return default


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except Exception:
        return default


def fmt(value: Any) -> str:
    try:
        return f"{float(value):.2f}"
    except Exception:
        return str(value)


def task_number(task_id: Any) -> int:
    match = re.search(r"\d+", str(task_id or ""))
    return int(match.group()) if match else 999999


def sort_tasks_by_task_id(source: list[Any]) -> list[Any]:
    return sorted(source or [], key=lambda t: (task_number(val(t, "task_id", "")), str(val(t, "task_id", ""))))


def input_task_signature(source: list[Any] | None = None) -> str:
    """Chữ ký chỉ dựa trên dữ liệu đầu vào, không dựa trên status/kết quả mô phỏng."""
    source = tasks() if source is None else (source or [])
    rows: list[tuple[Any, ...]] = []
    for task in sort_tasks_by_task_id(source):
        rows.append((
            str(val(task, "task_id", "")),
            str(val(task, "customer_name", "")),
            str(val(task, "task_type", "")),
            to_int(val(task, "arrival_time", 0), 0),
            to_int(val(task, "burst_time", 0), 0),
            to_int(val(task, "priority", 1), 1),
            to_int(val(task, "cover_pages", 0), 0),
            to_int(val(task, "color_pages", 0), 0),
            to_int(val(task, "bw_pages", 0), 0),
            to_int(val(task, "total_pages", 0), 0),
            str(val(task, "print_option", "")),
            str(val(task, "processing_method", "")),
        ))
    return repr(rows)


def reset_simulation_for_task_change() -> None:
    st.session_state["sim_results"] = OrderedDict()
    st.session_state["sim_normalized_tasks"] = []
    st.session_state["sim_task_color_map"] = build_task_color_map(tasks())
    st.session_state["sim_current_time"] = 0
    st.session_state["sim_max_time"] = 0
    st.session_state["sim_timeline_points"] = [0]
    st.session_state["sim_timeline_index"] = 0
    st.session_state["sim_running"] = False
    st.session_state["sim_finished"] = False
    st.session_state["sim_note"] = ""
    st.session_state["sim_last_tick"] = 0.0
    st.session_state["latest_simulation_payload"] = None
    st.session_state["simulation_results"] = {}
    st.session_state["sim_task_signature"] = input_task_signature()


def sync_simulation_input_tasks() -> None:
    current_signature = input_task_signature()
    previous_signature = str(st.session_state.get("sim_task_signature", ""))
    if previous_signature == "":
        st.session_state["sim_task_signature"] = current_signature
        st.session_state["sim_task_color_map"] = build_task_color_map(tasks())
        return
    if current_signature != previous_signature:
        reset_simulation_for_task_change()


def normalize_status(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in ("hoàn thành", "hoan thanh", "completed", "complete", "done", "completed"):
        return "COMPLETED"
    if text in ("đang xử lý", "dang xu ly", "processing", "running", "run"):
        return "RUNNING"
    return "WAITING"


def display_task_type(task_type: Any) -> str:
    raw = str(task_type or "In tài liệu").strip()
    if not raw:
        return "In tài liệu"
    return raw[:1].upper() + raw[1:]


def clone_task_for_algorithm(task: Any, index: int) -> Any:
    """Đưa task về object có attribute để các hàm thuật toán cũ dùng được."""
    try:
        cloned = copy.deepcopy(task)
    except Exception:
        cloned = task

    if isinstance(cloned, dict):
        cloned = SimpleNamespace(**cloned)

    defaults = {
        "task_id": f"T{index + 1:03d}",
        "customer_name": "Khách lẻ",
        "task_type": "In tài liệu",
        "arrival_time": 0,
        "burst_time": 1,
        "priority": 1,
        "status": "WAITING",
    }
    for key, default in defaults.items():
        if val(cloned, key, None) is None or str(val(cloned, key, "")).strip() == "":
            put(cloned, key, default)

    cover_pages = max(0, to_int(val(cloned, "cover_pages", 0), 0))
    color_pages = max(0, to_int(val(cloned, "color_pages", 0), 0))
    bw_pages = max(0, to_int(val(cloned, "bw_pages", 0), 0))
    total_pages = max(0, to_int(val(cloned, "total_pages", cover_pages + color_pages + bw_pages), cover_pages + color_pages + bw_pages))

    # Tương thích dữ liệu cũ: nếu chưa có 3 cột trang, dùng priority như số trang trắng đen.
    if cover_pages == 0 and color_pages == 0 and bw_pages == 0 and total_pages == 0:
        legacy_qty = max(0, to_int(val(cloned, "priority", 0), 0))
        if legacy_qty > 0:
            bw_pages = legacy_qty
            total_pages = legacy_qty

    put(cloned, "original_arrival_time", to_int(val(cloned, "arrival_time", 0), 0))
    put(cloned, "arrival_time", 0)
    put(cloned, "burst_time", max(1, to_int(val(cloned, "burst_time", 1), 1)))
    put(cloned, "priority", max(1, to_int(val(cloned, "priority", 1), 1)))
    put(cloned, "cover_pages", cover_pages)
    put(cloned, "color_pages", color_pages)
    put(cloned, "bw_pages", bw_pages)
    put(cloned, "total_pages", total_pages)
    put(cloned, "print_option", str(val(cloned, "print_option", "")))
    put(cloned, "processing_method", str(val(cloned, "processing_method", "Tính theo số trang")))
    put(cloned, "status", "WAITING")
    return cloned


def prepare_simulation_tasks() -> tuple[list[Any], str]:
    source = tasks()
    normalized = [clone_task_for_algorithm(t, i) for i, t in enumerate(source)]
    normalized = sort_tasks_by_task_id(normalized)
    note = (
        "Chế độ hàng đợi: tất cả tác vụ được xem là đã có trong hàng đợi tại t=0 "
        "để FCFS/SJF/Priority/Round Robin thể hiện sự khác nhau."
    )
    return normalized, note


def build_task_color_map(source: list[Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for i, task in enumerate(sort_tasks_by_task_id(source)):
        out[str(val(task, "task_id", f"T{i + 1:03d}"))] = TASK_COLORS[i % len(TASK_COLORS)]
    return out


def result_gantt(result: Any) -> list[Any]:
    return list(val(result, "gantt_chart", []) or [])


def result_tasks(result: Any) -> list[Any]:
    return list(val(result, "tasks", []) or [])


def find_current_block(gantt: list[Any], now: int) -> Any | None:
    for block in gantt:
        start = to_int(val(block, "start_time", 0), 0)
        end = to_int(val(block, "end_time", 0), 0)
        if start <= now < end:
            return block
    return None


def get_display_block(gantt: list[Any], now: int) -> Any | None:
    # Nếu đúng thời điểm kết thúc block, vẫn giữ block đó 1 nhịp để thấy 100%.
    for block in reversed(gantt):
        task_id = str(val(block, "task_id", ""))
        end = to_int(val(block, "end_time", 0), 0)
        if task_id != "IDLE" and now == end:
            return block
    return find_current_block(gantt, now)


def calculate_task_executed_service(result: Any, task_id: str, now: int) -> int:
    executed = 0
    for block in result_gantt(result):
        block_task_id = str(val(block, "task_id", ""))
        if block_task_id != str(task_id):
            continue
        start = to_int(val(block, "start_time", 0), 0)
        end = to_int(val(block, "end_time", 0), 0)
        if now <= start:
            continue
        executed += max(0, min(now, end) - start)
    return executed


def calculate_executed_service(result: Any, now: int) -> int:
    executed = 0
    for block in result_gantt(result):
        task_id = str(val(block, "task_id", ""))
        if task_id == "IDLE":
            continue
        start = to_int(val(block, "start_time", 0), 0)
        end = to_int(val(block, "end_time", 0), 0)
        if now <= start:
            continue
        executed += max(0, min(now, end) - start)
    return executed


def completed_tasks_until(result: Any, now: int) -> list[Any]:
    completed = []
    for task in result_tasks(result):
        completion = to_int(val(task, "completion_time", 999999), 999999)
        if completion <= now:
            completed.append(task)
    return completed


def count_waiting_tasks(result: Any, now: int, running_task_id: str | None) -> int:
    count = 0
    for task in result_tasks(result):
        tid = str(val(task, "task_id", ""))
        if running_task_id and tid == running_task_id:
            continue
        arrival = to_int(val(task, "arrival_time", 0), 0)
        completion = to_int(val(task, "completion_time", 0), 0)
        if arrival <= now < completion:
            count += 1
    return count


def calculate_live_metrics(result: Any, now: int) -> tuple[float, float]:
    arrived = []
    for task in result_tasks(result):
        if to_int(val(task, "arrival_time", 0), 0) <= now:
            arrived.append(task)
    if not arrived:
        return 0.0, 0.0

    waits: list[float] = []
    turns: list[float] = []
    for task in arrived:
        tid = str(val(task, "task_id", ""))
        arrival = to_int(val(task, "arrival_time", 0), 0)
        completion = to_int(val(task, "completion_time", now), now)
        observed_end = min(now, completion)
        turnaround = max(0, observed_end - arrival)
        executed = calculate_task_executed_service(result, tid, now)
        waiting = max(0, turnaround - executed)
        waits.append(waiting)
        turns.append(turnaround)
    return sum(waits) / len(waits), sum(turns) / len(turns)


def final_avg_metrics(result: Any) -> tuple[float, float]:
    task_list = result_tasks(result)
    if not task_list:
        return 0.0, 0.0
    waits = [to_float(val(t, "waiting_time", 0), 0.0) for t in task_list]
    turns = [to_float(val(t, "turnaround_time", 0), 0.0) for t in task_list]
    return sum(waits) / len(waits), sum(turns) / len(turns)


# ====================== ALGORITHM ======================
def algorithm_infos(normalized_tasks: list[Any], quantum: int) -> OrderedDict[str, dict[str, Any]]:
    def clone_source() -> list[Any]:
        return copy.deepcopy(normalized_tasks)

    return OrderedDict([
        ("FCFS", {
            "index": "1",
            "title": "FCFS (First Come First Serve)",
            "short": "FCFS",
            "color": PRIMARY,
            "bg": BLUE_BG,
            "printer_icon": "B_Printer",
            "runner": lambda: run_fcfs(clone_source()) if run_fcfs else None,
        }),
        ("SJF", {
            "index": "2",
            "title": "SJF (Shortest Job First)",
            "short": "SJF",
            "color": GREEN_DARK,
            "bg": GREEN_BG,
            "printer_icon": "G_Printer",
            "runner": lambda: run_sjf(clone_source()) if run_sjf else None,
        }),
        ("PRIORITY", {
            "index": "3",
            "title": "PRIORITY (Có ưu tiên)",
            "short": "Prio",
            "color": ORANGE_DARK,
            "bg": ORANGE_BG,
            "printer_icon": "R_Printer",
            "runner": lambda: run_priority(clone_source()) if run_priority else None,
        }),
        ("ROUND ROBIN", {
            "index": "4",
            "title": f"ROUND ROBIN (Quantum = {quantum})",
            "short": f"RR q={quantum}",
            "color": PURPLE,
            "bg": PURPLE_BG,
            "printer_icon": "P_Printer",
            "runner": lambda: run_round_robin(clone_source(), quantum) if run_round_robin else None,
        }),
    ])


def stamp_result(result: Any, key: str) -> Any:
    if result is None:
        return result
    names = {
        "FCFS": "FCFS",
        "SJF": "SJF",
        "PRIORITY": "Priority",
        "ROUND ROBIN": "Round Robin",
    }
    try:
        setattr(result, "algorithm_name", names.get(key, key))
        setattr(result, "algorithm_key", key)
    except Exception:
        pass
    return result


def selected_algorithm_keys() -> list[str]:
    """Giữ hành vi bản desktop cũ: mặc định chạy cả 4 thuật toán."""
    return ["FCFS", "SJF", "PRIORITY", "ROUND ROBIN"]


def get_preferred_result_key() -> str | None:
    results: OrderedDict[str, Any] = st.session_state.get("sim_results", OrderedDict())
    if not results:
        return None

    selected = [key for key in selected_algorithm_keys() if key in results]
    if selected:
        return selected[-1]

    if "ROUND ROBIN" in results:
        return "ROUND ROBIN"

    return next(reversed(results))



# =========================================================
# SHARED SIMULATION PERSISTENCE
# =========================================================
def gantt_block_to_plain(block: Any) -> dict[str, Any]:
    return {
        "task_id": str(val(block, "task_id", "")),
        "start_time": to_int(val(block, "start_time", val(block, "start", 0)), 0),
        "end_time": to_int(val(block, "end_time", val(block, "end", 0)), 0),
    }


def simulation_result_to_plain(result: Any) -> dict[str, Any]:
    algorithm_name = val(result, "algorithm_name", val(result, "algorithm", val(result, "name", "Chưa chạy")))
    algorithm_key = val(result, "algorithm_key", "")
    task_list = [task_to_plain_dict(task) for task in result_tasks(result)]
    gantt_list = [gantt_block_to_plain(block) for block in result_gantt(result)]
    avg_waiting, avg_turnaround = final_avg_metrics(result)
    avg_response = to_float(
        val(result, "average_response_time", val(result, "avg_response_time", val(result, "avg_response", 0))),
        0.0,
    )

    return {
        "algorithm_name": str(algorithm_name),
        "algorithm_key": str(algorithm_key),
        "tasks": task_list,
        "gantt_chart": gantt_list,
        "average_waiting_time": round(avg_waiting, 2),
        "average_turnaround_time": round(avg_turnaround, 2),
        "average_response_time": round(avg_response, 2),
    }


def plain_result_map() -> OrderedDict[str, dict[str, Any]]:
    results: OrderedDict[str, Any] = st.session_state.get("sim_results", OrderedDict())
    out: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for key, result in results.items():
        out[str(key)] = simulation_result_to_plain(result)
    return out


def build_serializable_progress_payload(is_finished: bool = False) -> dict[str, Any]:
    result_map = plain_result_map()
    preferred_key = get_preferred_result_key()
    preferred_result = result_map.get(preferred_key) if preferred_key else None

    return {
        "tasks": [task_to_plain_dict(task) for task in tasks()],
        "results": list(result_map.values()),
        "result_map": result_map,
        "preferred_result": preferred_result,
        "task_results": preferred_result.get("tasks", []) if preferred_result else [],
        "gantt_blocks": preferred_result.get("gantt_chart", []) if preferred_result else [],
        "algorithm": preferred_key or "Chưa chạy",
        "algorithm_name": val(preferred_result, "algorithm_name", preferred_key or "Chưa chạy") if preferred_result else "Chưa chạy",
        "current_time": to_int(st.session_state.get("sim_current_time", 0), 0),
        "max_time": to_int(st.session_state.get("sim_max_time", 0), 0),
        "timeline_points": list(st.session_state.get("sim_timeline_points", [0])),
        "timeline_index": to_int(st.session_state.get("sim_timeline_index", 0), 0),
        "is_running": bool(st.session_state.get("sim_running", False)),
        "is_finished": bool(is_finished or st.session_state.get("sim_finished", False)),
        "selected_keys": selected_algorithm_keys() if result_map else [],
        "task_signature": input_task_signature(),
        "saved_at": time.time(),
    }


def publish_simulation_payload(payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if payload is None:
        if not st.session_state.get("sim_results"):
            return None
        payload = build_serializable_progress_payload(
            is_finished=bool(st.session_state.get("sim_finished", False))
        )

    # Các trang Comparison/Report đang đọc 2 khóa này.
    st.session_state["latest_simulation_payload"] = payload
    st.session_state["simulation_results"] = payload

    # Thêm vài alias để nếu trang khác đọc tên cũ/mới vẫn nhận được dữ liệu CPU.
    st.session_state["latest_cpu_payload"] = payload
    st.session_state["cpu_payload"] = payload
    st.session_state["simulation_payload_ready"] = bool(payload.get("result_map") or payload.get("results"))

    report_payload = st.session_state.get("report_payload")
    if not isinstance(report_payload, dict):
        report_payload = {}
    report_payload["cpu"] = payload
    st.session_state["report_payload"] = report_payload
    return payload


def save_simulation_to_store(payload: dict[str, Any] | None = None) -> None:
    try:
        payload = publish_simulation_payload(payload)
        if not payload:
            return
        stored = {
            "payload": payload,
            "state": {
                "sim_results": payload.get("result_map", {}),
                "sim_normalized_tasks": [task_to_plain_dict(task) for task in st.session_state.get("sim_normalized_tasks", [])],
                "sim_task_color_map": dict(st.session_state.get("sim_task_color_map", {})),
                "sim_current_time": to_int(st.session_state.get("sim_current_time", 0), 0),
                "sim_max_time": to_int(st.session_state.get("sim_max_time", 0), 0),
                "sim_timeline_points": list(st.session_state.get("sim_timeline_points", [0])),
                "sim_timeline_index": to_int(st.session_state.get("sim_timeline_index", 0), 0),
                "sim_running": bool(st.session_state.get("sim_running", False)),
                "sim_finished": bool(st.session_state.get("sim_finished", False)),
                "sim_note": str(st.session_state.get("sim_note", "")),
                "sim_quantum": to_int(st.session_state.get("sim_quantum", DEFAULT_QUANTUM), DEFAULT_QUANTUM),
                "sim_task_signature": input_task_signature(),
            },
        }
        SIMULATION_STORE_FILE.write_text(json.dumps(stored, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def load_simulation_from_store() -> dict[str, Any] | None:
    try:
        if not SIMULATION_STORE_FILE.exists():
            return None
        raw = json.loads(SIMULATION_STORE_FILE.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return None
        return raw
    except Exception:
        return None


def restore_simulation_if_needed() -> None:
    if st.session_state.get("sim_results"):
        publish_simulation_payload()
        return

    stored = load_simulation_from_store()
    if not stored:
        return

    state = stored.get("state") if isinstance(stored.get("state"), dict) else {}
    payload = stored.get("payload") if isinstance(stored.get("payload"), dict) else None
    stored_signature = str(state.get("sim_task_signature") or (payload or {}).get("task_signature") or "")
    current_signature = input_task_signature()

    # Không phục hồi kết quả cũ nếu người dùng đã đổi danh sách tác vụ.
    if stored_signature and current_signature and stored_signature != current_signature:
        return

    result_map = state.get("sim_results") or (payload or {}).get("result_map") or {}
    if not isinstance(result_map, dict) or not result_map:
        return

    st.session_state["sim_results"] = OrderedDict((str(k), v) for k, v in result_map.items())
    st.session_state["sim_normalized_tasks"] = state.get("sim_normalized_tasks") or st.session_state.get("tasks", [])
    st.session_state["sim_task_color_map"] = state.get("sim_task_color_map") or build_task_color_map(tasks())
    st.session_state["sim_current_time"] = to_int(state.get("sim_current_time"), to_int((payload or {}).get("current_time"), 0))
    st.session_state["sim_max_time"] = to_int(state.get("sim_max_time"), to_int((payload or {}).get("max_time"), 0))
    st.session_state["sim_timeline_points"] = list(state.get("sim_timeline_points") or (payload or {}).get("timeline_points") or [0])
    st.session_state["sim_timeline_index"] = to_int(state.get("sim_timeline_index"), to_int((payload or {}).get("timeline_index"), 0))
    st.session_state["sim_running"] = bool(state.get("sim_running", False))
    st.session_state["sim_finished"] = bool(state.get("sim_finished", (payload or {}).get("is_finished", False)))
    st.session_state["sim_note"] = str(state.get("sim_note", st.session_state.get("sim_note", "")))
    st.session_state["sim_quantum"] = to_int(state.get("sim_quantum"), DEFAULT_QUANTUM)
    st.session_state["sim_task_signature"] = stored_signature or current_signature

    if payload:
        publish_simulation_payload(payload)
    else:
        publish_simulation_payload()

def build_timeline_points(max_time: int) -> list[int]:
    """
    Bám logic desktop cũ: timeline đi từng đơn vị thời gian 0, 1, 2...
    để Round Robin và progress bar cập nhật liên tục, không nhảy cóc theo block.
    """
    max_time = max(0, to_int(max_time, 0))
    return list(range(0, max_time + 1))


def build_progress_payload(is_finished: bool = False) -> dict[str, Any]:
    return build_serializable_progress_payload(is_finished=is_finished)


def emit_simulation_progress(
    on_simulation_progress: Callable[[dict[str, Any]], Any] | None = None,
    is_finished: bool = False,
) -> dict[str, Any] | None:
    if not st.session_state.get("sim_results"):
        return None

    payload = build_progress_payload(is_finished=is_finished)
    publish_simulation_payload(payload)
    save_simulation_to_store(payload)

    if on_simulation_progress:
        try:
            on_simulation_progress(payload)
        except Exception:
            pass

    return payload



def run_all_algorithms(
    on_simulation_progress: Callable[[dict[str, Any]], Any] | None = None,
) -> None:
    if not tasks():
        st.warning("Chưa có dữ liệu tác vụ. Hãy nạp dữ liệu ở trang Danh sách tác vụ trước.")
        return

    missing = []
    if run_fcfs is None:
        missing.append("run_fcfs")
    if run_sjf is None:
        missing.append("run_sjf")
    if run_priority is None:
        missing.append("run_priority")
    if run_round_robin is None:
        missing.append("run_round_robin")

    if missing:
        st.error(
            "Chưa import được thuật toán: "
            + ", ".join(missing)
            + ". Hãy kiểm tra thư mục `core/algorithms` hoặc `algorithms` trong dự án."
        )
        return

    quantum = max(1, to_int(st.session_state.get("sim_quantum", DEFAULT_QUANTUM), DEFAULT_QUANTUM))
    normalized, note = prepare_simulation_tasks()

    for task in normalized:
        put(task, "status", "WAITING")

    infos = algorithm_infos(normalized, quantum)
    results: OrderedDict[str, Any] = OrderedDict()

    for key in selected_algorithm_keys():
        info = infos[key]
        try:
            result = info["runner"]()
        except Exception as exc:
            st.error(f"Không chạy được thuật toán {key}: {exc}")
            st.session_state["sim_results"] = OrderedDict()
            st.session_state["sim_running"] = False
            return

        if result is None:
            st.error(f"Thuật toán {key} không trả về kết quả.")
            st.session_state["sim_results"] = OrderedDict()
            st.session_state["sim_running"] = False
            return

        results[key] = stamp_result(result, key)

    max_time = 0
    for result in results.values():
        gantt = result_gantt(result)
        if gantt:
            max_time = max(max_time, to_int(val(gantt[-1], "end_time", 0), 0))

    if max_time <= 0:
        st.warning("Danh sách tác vụ chưa có thời gian xử lý hợp lệ.")
        return

    timeline_points = build_timeline_points(max_time)

    st.session_state["sim_results"] = results
    st.session_state["sim_normalized_tasks"] = normalized
    st.session_state["sim_task_color_map"] = build_task_color_map(normalized)
    st.session_state["sim_current_time"] = timeline_points[0]
    st.session_state["sim_max_time"] = max_time
    st.session_state["sim_timeline_points"] = timeline_points
    st.session_state["sim_timeline_index"] = 0
    st.session_state["sim_running"] = True
    st.session_state["sim_finished"] = False
    st.session_state["sim_note"] = note
    st.session_state["sim_last_tick"] = time.time()
    st.session_state["sim_task_signature"] = input_task_signature()
    st.session_state["footer_status"] = "Đang mô phỏng thuật toán"

    emit_simulation_progress(on_simulation_progress, is_finished=False)


def reset_simulation() -> None:
    """Làm mới riêng trạng thái mô phỏng, không xóa st.session_state["tasks"]."""
    st.session_state["sim_results"] = OrderedDict()
    st.session_state["sim_normalized_tasks"] = []
    st.session_state["sim_task_color_map"] = build_task_color_map(tasks())
    st.session_state["sim_current_time"] = 0
    st.session_state["sim_max_time"] = 0
    st.session_state["sim_timeline_points"] = [0]
    st.session_state["sim_timeline_index"] = 0
    st.session_state["sim_running"] = False
    st.session_state["sim_finished"] = False
    st.session_state["sim_note"] = ""
    st.session_state["sim_last_tick"] = 0.0
    st.session_state["sim_task_signature"] = input_task_signature()
    st.session_state["latest_simulation_payload"] = None
    st.session_state["simulation_results"] = {}
    st.session_state["latest_cpu_payload"] = None
    st.session_state["cpu_payload"] = {}
    st.session_state["simulation_payload_ready"] = False
    st.session_state["footer_status"] = "Sẵn sàng mô phỏng"
    try:
        SIMULATION_STORE_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def apply_result_to_source_tasks() -> None:
    results: OrderedDict[str, Any] = st.session_state.get("sim_results", OrderedDict())
    if not results:
        return

    preferred_key = get_preferred_result_key()
    if preferred_key is None:
        return

    result = results[preferred_key]
    simulated_by_id = {str(val(t, "task_id", "")): t for t in result_tasks(result)}

    source = tasks()
    for task in source:
        tid = str(val(task, "task_id", ""))
        simulated = simulated_by_id.get(tid)
        if simulated is None:
            continue

        put(task, "status", "Hoàn thành")
        put(task, "completion_time", val(simulated, "completion_time", 0))
        put(task, "turnaround_time", val(simulated, "turnaround_time", 0))
        put(task, "waiting_time", val(simulated, "waiting_time", 0))
        put(task, "response_time", val(simulated, "response_time", 0))
        put(task, "simulation_algorithm", preferred_key)

    st.session_state["tasks"] = source
    save_tasks_to_store(source)
    # Không reset kết quả vì chữ ký đầu vào không tính status/kết quả mô phỏng.
    st.session_state["sim_task_signature"] = input_task_signature(source)
    st.session_state["sim_finished"] = True
    publish_simulation_payload()
    save_simulation_to_store()


def finish_simulation(
    on_simulation_progress: Callable[[dict[str, Any]], Any] | None = None,
    on_simulation_finished: Callable[..., Any] | None = None,
) -> None:
    max_time = to_int(st.session_state.get("sim_max_time", 0), 0)
    st.session_state["sim_current_time"] = max_time
    st.session_state["sim_running"] = False
    st.session_state["sim_finished"] = True
    st.session_state["sim_timeline_index"] = max(0, len(st.session_state.get("sim_timeline_points", [0])) - 1)

    apply_result_to_source_tasks()

    payload = emit_simulation_progress(on_simulation_progress, is_finished=True)
    st.session_state["footer_status"] = "Mô phỏng hoàn thành, danh sách tác vụ đã cập nhật"

    if on_simulation_finished:
        try:
            on_simulation_finished(st.session_state.get("tasks", []), payload)
        except TypeError:
            on_simulation_finished(st.session_state.get("tasks", []))


def advance_tick(
    on_simulation_progress: Callable[[dict[str, Any]], Any] | None = None,
    on_simulation_finished: Callable[..., Any] | None = None,
) -> None:
    if not st.session_state.get("sim_running", False):
        return

    max_time = to_int(st.session_state.get("sim_max_time", 0), 0)
    if max_time <= 0:
        return

    timeline_points = list(st.session_state.get("sim_timeline_points") or build_timeline_points(max_time))
    if not timeline_points:
        timeline_points = [0]

    index = to_int(st.session_state.get("sim_timeline_index", 0), 0)

    if index >= len(timeline_points) - 1:
        finish_simulation(on_simulation_progress, on_simulation_finished)
        return

    index += 1
    current = timeline_points[index]

    st.session_state["sim_timeline_points"] = timeline_points
    st.session_state["sim_timeline_index"] = index
    st.session_state["sim_current_time"] = min(current, max_time)
    st.session_state["sim_last_tick"] = time.time()

    heavy_refresh = (
        index % HEAVY_REFRESH_EVERY == 0
        or index >= len(timeline_points) - 1
    )

    if heavy_refresh:
        emit_simulation_progress(on_simulation_progress, is_finished=False)

    if index >= len(timeline_points) - 1 or st.session_state["sim_current_time"] >= max_time:
        finish_simulation(on_simulation_progress, on_simulation_finished)


# ====================== CSS + HTML ======================
def css() -> None:
    render_html(f"""
    <style>
    .stApp {{ background:{BG}; }}
    div[data-testid="stVerticalBlock"] {{ gap:.75rem; }}
    .sim-grid-top {{ display:grid; grid-template-columns: 37% 63%; gap:10px; margin-top:2px; }}
    .sim-section {{ background:{WHITE}; border:1px solid {BORDER}; }}
    .sim-section-head {{ display:flex; align-items:center; gap:10px; padding:12px 16px; border-bottom:1px solid {LIGHT_LINE}; color:{PRIMARY}; font-weight:900; font-size:16px; text-transform:uppercase; }}
    .sim-section-head img {{ width:24px; height:24px; object-fit:contain; }}
    .control-body {{ padding:14px 18px 8px; text-align:center; min-height:88px; display:flex; flex-direction:column; align-items:center; justify-content:center; }}
    .task-count-title {{ color:{MUTED}; font-weight:900; font-size:16px; line-height:1.25; }}
    .task-count {{ color:{PRIMARY}; font-size:34px; font-weight:900; line-height:1.12; margin-top:6px; }}
    .status-line, .note-line {{ display:none!important; }}
    .queue-wrap {{ overflow-x:auto; padding:16px 14px 12px; white-space:nowrap; }}
    .task-card {{ display:inline-grid; grid-template-columns:58px 1fr; align-items:center; width:214px; min-height:96px; background:{WHITE}; border:1px solid {BORDER}; margin-right:10px; padding:10px 12px; vertical-align:top; box-sizing:border-box; }}
    .task-card.small {{ width:190px; min-height:82px; grid-template-columns:50px 1fr; }}
    .task-card-icon {{ display:flex; align-items:center; justify-content:center; }}
    .task-printer-svg {{ display:block; filter:drop-shadow(0 1px 1px rgba(15,23,42,.08)); }}
    .task-card-info {{ min-width:0; overflow:hidden; }}
    .task-id {{ font-size:15px; font-weight:900; line-height:1.1; }}
    .task-customer {{ color:{TEXT}; font-size:13px; font-weight:800; margin-top:5px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .task-type {{ color:{TEXT}; font-size:12.5px; font-weight:900; margin-top:7px; }}
    .task-detail-grid, .task-mini-detail, .task-total-pages {{ display:none!important; }}
    .task-status {{ font-size:10px; font-weight:900; margin-top:8px; text-transform:uppercase; }}
    .algo-grid {{ display:grid; grid-template-columns: 1fr 1fr; gap:12px; margin-top:12px; }}
    .algo-card {{ background:{WHITE}; border:1px solid {BORDER}; }}
    .algo-head {{ display:flex; align-items:center; gap:10px; padding:9px 12px 3px; font-weight:900; }}
    .algo-index {{ color:{WHITE}; min-width:26px; height:26px; display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:900; }}
    .algo-body {{ display:grid; grid-template-columns:68px 1fr 170px; gap:12px; padding:6px 12px 10px; align-items:start; }}
    .printer-box {{ width:64px; height:64px; display:flex; align-items:center; justify-content:center; }}
    .progress-outer {{ height:20px; border:1px solid #111827; background:#fff; position:relative; overflow:hidden; margin-top:4px; }}
    .progress-fill {{ height:100%; }}
    .progress-text {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; color:#fff; text-shadow: -1px -1px #000, 1px -1px #000, -1px 1px #000, 1px 1px #000; font-size:12px; font-weight:900; }}
    .progress-caption {{ font-size:11px; font-weight:900; margin-top:8px; }}
    .small-stats {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:0; margin-top:12px; }}
    .small-stat {{ text-align:center; border-right:1px solid {LIGHT_LINE}; padding:0 6px; }}
    .small-stat:last-child {{ border-right:0; }}
    .small-stat-title {{ color:{MUTED}; font-size:10px; font-weight:900; }}
    .small-stat-value {{ color:{TEXT}; font-size:13px; font-weight:900; margin-top:4px; }}
    .metric-box {{ border:1px solid; min-height:92px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:12px; text-align:center; font-size:12px; font-weight:900; }}
    .algo-queue {{ background:#F8FAFC; border:1px solid #CBD5E1; padding:8px; overflow-x:auto; white-space:nowrap; margin:0 12px 12px; }}
    .gantt-wrap {{ background:{WHITE}; border:1px solid {BORDER}; margin-top:14px; }}
    .gantt-svg-wrap {{ overflow-x:auto; padding:18px 12px 14px; }}
    .empty-box {{ color:{MUTED}; font-weight:900; padding:24px; text-align:center; }}
    .stButton button {{ border-radius:7px!important; min-height:42px; font-weight:900!important; border:0!important; box-shadow:0 2px 5px rgba(0,0,0,.08); }}
    .stNumberInput input {{ border-radius:0!important; }}
    .button-icon-row {{ display:grid; grid-template-columns:38px 1fr; align-items:center; gap:6px; }}
    .sim-icon-actions {{ display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:8px; justify-content:center; padding:8px 16px 16px; }}
    .sim-icon-action {{ min-height:42px; border:1px solid transparent; text-decoration:none!important; color:#fff!important; display:flex; align-items:center; justify-content:center; gap:8px; border-radius:4px; box-shadow:0 2px 5px rgba(0,0,0,.10); transition:all .15s ease; font-size:14px; font-weight:900; box-sizing:border-box; }}
    .sim-icon-action:hover {{ transform:translateY(-1px); filter:brightness(.98); color:#fff!important; }}
    .sim-icon-action.run {{ background:{GREEN}; border-color:{GREEN}; }}
    .sim-icon-action.pause {{ background:{ORANGE}; border-color:{ORANGE}; }}
    .sim-icon-action.reset {{ background:{PRIMARY}; border-color:{PRIMARY}; }}
    .sim-icon-action.disabled {{ opacity:.45; filter:grayscale(.35); pointer-events:none; cursor:not-allowed; }}
    .sim-icon-action-img {{ width:28px; height:28px; display:flex; align-items:center; justify-content:center; flex:0 0 28px; }}
    .sim-icon-action-img img {{ width:26px!important; height:26px!important; object-fit:contain!important; }}
    .sim-icon-action-text {{ display:inline!important; white-space:nowrap; }}
    @media(max-width:1100px){{ .sim-grid-top,.algo-grid{{grid-template-columns:1fr;}} .algo-body{{grid-template-columns:62px 1fr;}} .metric-box{{grid-column:1 / -1;}} }}
    </style>
    """)


def section_open(title: str, icon_name: str) -> str:
    return html_block(f"""
    <div class="sim-section">
        <div class="sim-section-head">{icon(icon_name, 24)}<span>{html.escape(title)}</span></div>
    """)


def section_close() -> str:
    return "</div>"


def status_color(status: str) -> str:
    if status == "RUNNING":
        return GREEN
    if status == "COMPLETED":
        return "#2563EB"
    return ORANGE


def make_task_card(task: Any, color_map: dict[str, str], status: str = "WAITING", small: bool = False) -> str:
    tid = str(val(task, "task_id", ""))
    customer = str(val(task, "customer_name", "Khách lẻ"))
    ttype = display_task_type(val(task, "task_type", "In tài liệu"))
    task_color = color_map.get(tid, PRIMARY)
    status = normalize_status(status)
    cls = "task-card small" if small else "task-card"
    icon_size = 34 if small else 44

    # Card chỉ giữ thông tin nhận diện. Bỏ toàn bộ dòng BT/P/Bìa/Màu/Đen/Tổng trang
    # vì icon/nội dung cũ đã đủ trực quan và các dòng này làm giao diện bị rối.
    if small:
        return html_block(f"""
        <div class="{cls}">
            <div class="task-card-icon">{printer_line_icon(task_color, icon_size)}</div>
            <div class="task-card-info">
                <div class="task-id" style="color:{task_color}">{html.escape(tid)}</div>
                <div class="task-type">{html.escape(ttype)}</div>
                <div class="task-status" style="color:{status_color(status)}">{status}</div>
            </div>
        </div>
        """)

    return html_block(f"""
    <div class="{cls}">
        <div class="task-card-icon">{printer_line_icon(task_color, icon_size)}</div>
        <div class="task-card-info">
            <div class="task-id" style="color:{task_color}">{html.escape(tid)}</div>
            <div class="task-customer">{html.escape(customer)}</div>
            <div class="task-type">{html.escape(ttype)}</div>
            <div class="task-status" style="color:{status_color(status)}">{status}</div>
        </div>
    </div>
    """)

def _query_value(name: str) -> str:
    try:
        value = st.query_params.get(name, "")
    except Exception:
        try:
            params = st.experimental_get_query_params()
            value = params.get(name, "")
        except Exception:
            value = ""
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value or "")


def _clear_sim_action_query() -> None:
    try:
        st.query_params["page"] = "simulation"
        for name in ("sim_action", "sim_nonce"):
            try:
                del st.query_params[name]
            except Exception:
                pass
    except Exception:
        try:
            st.experimental_set_query_params(page="simulation")
        except Exception:
            pass


def handle_sim_action_query(
    on_simulation_progress: Callable[[dict[str, Any]], Any] | None = None,
    on_simulation_finished: Callable[..., Any] | None = None,
) -> None:
    action = _query_value("sim_action").strip().lower()
    if not action:
        return

    nonce = _query_value("sim_nonce") or action
    if st.session_state.get("_last_sim_action_nonce") == nonce:
        _clear_sim_action_query()
        return

    st.session_state["_last_sim_action_nonce"] = nonce

    try:
        if action == "run":
            if not st.session_state.get("sim_running", False):
                run_all_algorithms(on_simulation_progress)
        elif action == "toggle":
            is_running = bool(st.session_state.get("sim_running", False))
            can_pause_resume = bool(st.session_state.get("sim_results")) and not bool(st.session_state.get("sim_finished", False))
            if can_pause_resume:
                st.session_state["sim_running"] = not is_running
                st.session_state["sim_last_tick"] = time.time()
                save_simulation_to_store()
        elif action == "reset":
            reset_simulation()
    finally:
        _clear_sim_action_query()
        st.rerun()


def sim_action_href(action: str) -> str:
    return f"?page=simulation&sim_action={html.escape(action)}&sim_nonce={time.time_ns()}"


def icon_action_button(icon_name: str, label: str, action: str, cls: str = "", disabled: bool = False, fallback: str = "●") -> str:
    img = icon(icon_name, 26)
    if not img:
        img = f'<span style="font-size:22px;line-height:1;color:#fff">{html.escape(fallback)}</span>'
    label_safe = html.escape(label)
    class_name = f"sim-icon-action {html.escape(cls)}" + (" disabled" if disabled else "")
    if disabled:
        return html_block(
            f'<div class="{class_name}" title="{label_safe}">'
            f'<span class="sim-icon-action-img">{img}</span>'
            f'<span class="sim-icon-action-text">{label_safe}</span>'
            '</div>'
        )
    return html_block(
        f'<a class="{class_name}" href="{sim_action_href(action)}" target="_self" title="{label_safe}">'
        f'<span class="sim-icon-action-img">{img}</span>'
        f'<span class="sim-icon-action-text">{label_safe}</span>'
        '</a>'
    )


# ====================== TOP SECTION ======================
def render_controls(
    on_simulation_progress: Callable[[dict[str, Any]], Any] | None = None,
) -> None:
    current = to_int(st.session_state.get("sim_current_time", 0), 0)
    max_time = to_int(st.session_state.get("sim_max_time", 0), 0)
    is_running = bool(st.session_state.get("sim_running", False))
    is_finished = bool(st.session_state.get("sim_finished", False))

    if is_running:
        status = "● Đang mô phỏng thuật toán"
        color = GREEN
    elif is_finished:
        status = "● Đã hoàn thành mô phỏng"
        color = "#2563EB"
    elif st.session_state.get("sim_results"):
        status = "● Đã tạm dừng"
        color = ORANGE
    else:
        status = "● Sẵn sàng mô phỏng"
        color = MUTED

    with st.container(border=True):
        render_html(
            f'<div class="sim-section-head sim-control-head">{icon("Simulation_Setup", 24)}<span>THIẾT LẬP MÔ PHỎNG</span></div>'
        )
        render_html(
            f"""
            <div class="control-body">
                <div class="task-count-title">▣ Số tác vụ đang chờ</div>
                <div class="task-count">{len(tasks())}</div>
            </div>
            """
        )

        pause_label = "Tạm dừng" if is_running else "Tiếp tục"
        pause_icon = "Pause" if is_running else "Continue"
        can_pause_resume = bool(st.session_state.get("sim_results")) and not is_finished
        actions_html = "".join([
            icon_action_button("Run_Simulation", "Chạy mô phỏng", "run", "run", disabled=is_running, fallback="▶"),
            icon_action_button(pause_icon, pause_label, "toggle", "pause", disabled=not can_pause_resume, fallback="⏸" if is_running else "▶"),
            icon_action_button("Reset", "Làm mới", "reset", "reset", disabled=False, fallback="↻"),
        ])
        render_html(f'<div class="sim-icon-actions">{actions_html}</div>')

def render_main_queue() -> None:
    display_tasks = st.session_state.get("sim_normalized_tasks") or tasks()
    color_map = st.session_state.get("sim_task_color_map") or build_task_color_map(display_tasks)
    title = f"DANH SÁCH TÁC VỤ ({len(tasks())})"

    cards = ""
    if display_tasks:
        for task in sort_tasks_by_task_id(display_tasks):
            raw_status = val(task, "status", "WAITING")
            if st.session_state.get("sim_finished"):
                raw_status = "COMPLETED"
            cards += make_task_card(task, color_map, raw_status, small=False)
    else:
        cards = '<div class="empty-box">Chưa có dữ liệu tác vụ. Hãy nạp dữ liệu ở trang Danh sách tác vụ trước.</div>'

    render_html(
        section_open(title, "Info_data")
        + f'<div class="queue-wrap">{cards}</div>'
        + section_close()
    )


def render_top(
    on_simulation_progress: Callable[[dict[str, Any]], Any] | None = None,
) -> None:
    left, right = st.columns([0.37, 0.63], gap="small")
    with left:
        render_controls(on_simulation_progress)
    with right:
        render_main_queue()
    note = str(st.session_state.get("sim_note", "")).strip()
    if note:
        st.caption(note)


# ====================== ALGORITHM PANELS ======================
def panel_state(key: str, result: Any, info: dict[str, Any], now: int, max_time: int) -> dict[str, Any]:
    gantt = result_gantt(result)
    end_time = to_int(val(gantt[-1], "end_time", 0), 0) if gantt else 0
    local_now = min(now, end_time)
    current_block = find_current_block(gantt, local_now)
    display_block = get_display_block(gantt, local_now)
    running_id = None

    if display_block is None:
        if local_now >= end_time and end_time > 0:
            current_text = "Hoàn thành tất cả tác vụ"
            task_percent = 100
        else:
            current_text = "Chưa chạy mô phỏng"
            task_percent = 0
    else:
        task_id = str(val(display_block, "task_id", ""))
        if task_id == "IDLE":
            current_text = "IDLE - Chưa có tác vụ đến"
            task_percent = 0
        else:
            running_id = task_id if current_block is not None and str(val(current_block, "task_id", "")) == task_id else None
            task = next((t for t in result_tasks(result) if str(val(t, "task_id", "")) == task_id), None)
            task_type = display_task_type(val(task, "task_type", "Tác vụ"))
            current_text = f"{task_id} - {task_type}"
            if key == "ROUND ROBIN":
                current_text += " (lượt RR)"
            start = to_int(val(display_block, "start_time", 0), 0)
            end = to_int(val(display_block, "end_time", start), start)
            duration = max(1, end - start)
            if local_now >= end:
                task_percent = 100
            else:
                task_percent = int(((local_now - start) / duration) * 100)
            task_percent = max(0, min(100, task_percent))

    completed = completed_tasks_until(result, local_now)
    total_tasks = len(result_tasks(result))
    remaining = max(0, total_tasks - len(completed))
    waiting = count_waiting_tasks(result, local_now, running_id)
    avg_wait, avg_turn = calculate_live_metrics(result, local_now)

    total_burst = sum(max(0, to_int(val(task, "burst_time", 0), 0)) for task in result_tasks(result))
    executed = calculate_executed_service(result, local_now)
    overall_percent = int((executed / total_burst) * 100) if total_burst else 0
    overall_percent = max(0, min(100, overall_percent))

    if max_time > 0 and now >= max_time:
        final_wait, final_turn = final_avg_metrics(result)
        avg_wait, avg_turn = final_wait, final_turn

    return {
        "current_text": current_text,
        "task_percent": task_percent,
        "overall_percent": overall_percent,
        "completed": len(completed),
        "remaining": remaining,
        "waiting": waiting,
        "avg_wait": avg_wait,
        "avg_turn": avg_turn,
        "running_id": running_id,
    }


def algorithm_queue_cards(result: Any, color_map: dict[str, str], now: int) -> str:
    current = find_current_block(result_gantt(result), now)
    running_id = str(val(current, "task_id", "")) if current is not None else ""
    cards = ""
    for task in result_tasks(result):
        tid = str(val(task, "task_id", ""))
        completion = to_int(val(task, "completion_time", 999999), 999999)
        if running_id == tid:
            status = "RUNNING"
        elif completion <= now:
            status = "COMPLETED"
        else:
            status = "WAITING"
        cards += make_task_card(task, color_map, status, small=True)
    return cards


def algorithm_panel_html(key: str, result: Any, info: dict[str, Any], now: int, max_time: int, color_map: dict[str, str]) -> str:
    state = panel_state(key, result, info, now, max_time)
    color = info["color"]
    bg = info["bg"]
    printer = printer_line_icon(color, 58)
    queue = algorithm_queue_cards(result, color_map, min(now, max_time))

    return html_block(f"""
    <div class="algo-card">
        <div class="algo-head" style="color:{color}">
            <div class="algo-index" style="background:{color}">{html.escape(info['index'])}</div>
            <div class="algo-title">{html.escape(info['title'])}</div>
        </div>

        <div class="algo-body">
            <div class="printer-box">{printer}</div>

            <div class="algo-center">
                <div class="progress-outer">
                    <div class="progress-fill" style="background:{color};width:{state['task_percent']}%"></div>
                    <div class="progress-text">{html.escape(state['current_text'])}</div>
                </div>

                <div class="progress-caption" style="color:{color}">
                    Tiến độ tác vụ: {state['task_percent']}% | Tổng: {state['overall_percent']}%
                </div>

                <div class="small-stats">
                    <div class="small-stat">
                        <div class="small-stat-title">Tác vụ đã chạy</div>
                        <div class="small-stat-value">{state['completed']}</div>
                    </div>
                    <div class="small-stat">
                        <div class="small-stat-title">Tác vụ còn lại</div>
                        <div class="small-stat-value">{state['remaining']}</div>
                    </div>
                    <div class="small-stat">
                        <div class="small-stat-title">Tác vụ đang đợi</div>
                        <div class="small-stat-value">{state['waiting']}</div>
                    </div>
                </div>
            </div>

            <div class="metric-box" style="background:{bg};border-color:{color};color:{color}">
                <div class="metric-line">
                    <span>Avg Waiting Time</span>
                    <b>{fmt(state['avg_wait'])}</b>
                </div>
                <div class="metric-line">
                    <span>Avg Turnaround Time</span>
                    <b>{fmt(state['avg_turn'])}</b>
                </div>
            </div>
        </div>

        <div class="algo-queue">{queue}</div>
    </div>
    """)


def render_algorithm_panels() -> None:
    results: OrderedDict[str, Any] = st.session_state.get("sim_results", OrderedDict())
    normalized = st.session_state.get("sim_normalized_tasks") or prepare_simulation_tasks()[0]
    quantum = max(1, to_int(st.session_state.get("sim_quantum", DEFAULT_QUANTUM), DEFAULT_QUANTUM))
    infos = algorithm_infos(normalized, quantum)
    color_map = st.session_state.get("sim_task_color_map") or build_task_color_map(normalized)
    now = to_int(st.session_state.get("sim_current_time", 0), 0)
    max_time = to_int(st.session_state.get("sim_max_time", 0), 0)

    panel_items: list[tuple[str, Any, dict[str, Any]]] = []
    for key, info in infos.items():
        if key in results:
            panel_items.append((key, results[key], info))
        else:
            fake_result = SimpleNamespace(tasks=normalized, gantt_chart=[])
            panel_items.append((key, fake_result, info))

    for row_start in range(0, len(panel_items), 2):
        row_items = panel_items[row_start:row_start + 2]
        cols = st.columns(2, gap="small")
        for col, (key, result, info) in zip(cols, row_items):
            with col:
                render_html(algorithm_panel_html(key, result, info, now, max_time, color_map))


# ====================== GANTT ======================
def choose_tick_step(total: int) -> int:
    if total <= 24:
        return 2
    if total <= 60:
        return 4
    if total <= 120:
        return 8
    if total <= 240:
        return 20
    return max(50, total // 8)


def gantt_svg() -> str:
    results: OrderedDict[str, Any] = st.session_state.get("sim_results", OrderedDict())
    if not results:
        return html_block(f'<div class="empty-box">Chưa chạy mô phỏng. Nhấn “Chạy mô phỏng” để tạo biểu đồ Gantt.</div>')

    normalized = st.session_state.get("sim_normalized_tasks") or []
    quantum = max(1, to_int(st.session_state.get("sim_quantum", DEFAULT_QUANTUM), DEFAULT_QUANTUM))
    infos = algorithm_infos(normalized, quantum)
    color_map = st.session_state.get("sim_task_color_map") or build_task_color_map(normalized)
    now = to_int(st.session_state.get("sim_current_time", 0), 0)
    total = max(1, to_int(st.session_state.get("sim_max_time", 0), 0))

    left = 92
    top = 34
    row_h = 38
    bar_h = 22
    gantt_w = max(980, total * 28)
    width = left + gantt_w + 52
    height = top + len(results) * row_h + 40
    scale = gantt_w / total
    tick = choose_tick_step(total)
    parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">']

    for t in range(0, total + 1, tick):
        x = left + t * scale
        parts.append(f'<line x1="{x:.2f}" y1="{top-15}" x2="{x:.2f}" y2="{height-22}" stroke="#F1F5F9"/>')
        parts.append(f'<text x="{x:.2f}" y="{top-21}" fill="{TEXT}" font-size="10" text-anchor="middle" font-family="Arial" font-weight="700">{t}</text>')
    if total % tick != 0:
        x = left + total * scale
        parts.append(f'<text x="{x:.2f}" y="{top-21}" fill="{TEXT}" font-size="10" text-anchor="middle" font-family="Arial" font-weight="700">{total}</text>')

    current_x = left + min(now, total) * scale
    parts.append(f'<line x1="{current_x:.2f}" y1="{top-9}" x2="{current_x:.2f}" y2="{height-22}" stroke="{RED}" stroke-width="2" stroke-dasharray="5 4"/>')
    parts.append(f'<text x="{current_x+5:.2f}" y="{top-8}" fill="{RED}" font-size="11" font-family="Arial" font-weight="900">t={min(now,total)}</text>')

    for r, (key, result) in enumerate(results.items()):
        info = infos[key]
        y = top + r * row_h
        color = info["color"]
        parts.append(f'<rect x="8" y="{y-3}" width="72" height="{bar_h+6}" fill="{color}"/>')
        parts.append(f'<text x="44" y="{y+15}" fill="#fff" font-size="12" text-anchor="middle" font-family="Arial" font-weight="900">{html.escape(info["short"])}</text>')

        for block in result_gantt(result):
            tid = str(val(block, "task_id", ""))
            start = to_int(val(block, "start_time", 0), 0)
            end = to_int(val(block, "end_time", 0), 0)
            if end <= start:
                continue
            x1 = left + start * scale
            x2 = left + end * scale
            fill = "#CBD5E1" if tid == "IDLE" else color_map.get(tid, color)
            parts.append(f'<rect x="{x1:.2f}" y="{y}" width="{x2-x1:.2f}" height="{bar_h}" fill="#F8FAFC" stroke="#CBD5E1"/>')
            visible_end = min(end, now)
            if visible_end > start:
                vx2 = left + visible_end * scale
                parts.append(f'<rect x="{x1:.2f}" y="{y}" width="{vx2-x1:.2f}" height="{bar_h}" fill="{fill}" stroke="#FFFFFF"/>')
                if vx2 - x1 >= 30:
                    label = tid if tid != "IDLE" else "IDLE"
                    text_color = "#FFFFFF" if tid != "IDLE" else TEXT
                    parts.append(f'<text x="{(x1+vx2)/2:.2f}" y="{y+15}" fill="{text_color}" font-size="10" text-anchor="middle" font-family="Arial" font-weight="900">{html.escape(label)}</text>')
            if now >= total and x2 - x1 >= 30:
                label = tid if tid != "IDLE" else "IDLE"
                text_color = "#FFFFFF" if tid != "IDLE" else TEXT
                parts.append(f'<text x="{(x1+x2)/2:.2f}" y="{y+15}" fill="{text_color}" font-size="10" text-anchor="middle" font-family="Arial" font-weight="900">{html.escape(label)}</text>')

    parts.append("</svg>")
    return html_block('<div class="gantt-svg-wrap">' + "".join(parts) + "</div>")


def render_gantt() -> None:
    render_html(
        f"""
        <div class="gantt-wrap">
            <div class="sim-section-head">{icon('Chart', 24)}<span>BIỂU ĐỒ GANTT (THEO TIẾN TRÌNH MÔ PHỎNG)</span></div>
            {gantt_svg()}
        </div>
        """
    )


# ====================== RENDER ENTRYPOINTS ======================
def auto_advance_if_needed(
    on_simulation_progress: Callable[[dict[str, Any]], Any] | None = None,
    on_simulation_finished: Callable[..., Any] | None = None,
) -> None:
    if not st.session_state.get("sim_running", False):
        return

    # Streamlit không có vòng lặp GUI như Tkinter; dùng rerun ngắn nhưng xử lý nhiều nhịp mỗi lần để chạy nhanh hơn.
    time.sleep(EVENT_STEP_SECONDS)
    for _ in range(max(1, AUTO_ADVANCE_STEPS)):
        if not st.session_state.get("sim_running", False):
            break
        advance_tick(on_simulation_progress, on_simulation_finished)
    st.rerun()


def render(
    tasks: list[Any] | None = None,
    on_simulation_progress: Callable[[dict[str, Any]], Any] | None = None,
    on_simulation_finished: Callable[..., Any] | None = None,
    **_: Any,
) -> None:
    init_state()

    # streamlit_app.py truyền tasks/callback vào page. Chỉ nhận context nếu nó có dữ liệu thật.
    # Nếu context rỗng do app vừa reload khi chuyển trang, nạp lại từ JSON dùng chung.
    if tasks:
        st.session_state["tasks"] = tasks
        save_tasks_to_store(tasks)
    else:
        restore_tasks_if_needed()

    restore_simulation_if_needed()
    sync_simulation_input_tasks()
    handle_sim_action_query(on_simulation_progress, on_simulation_finished)
    if st.session_state.get("sim_results"):
        publish_simulation_payload()

    css()

    if not st.session_state.get("sim_task_color_map"):
        st.session_state["sim_task_color_map"] = build_task_color_map(globals()["tasks"]())

    render_top(on_simulation_progress)
    render_algorithm_panels()
    render_gantt()
    auto_advance_if_needed(on_simulation_progress, on_simulation_finished)

def render_simulation_page(**kwargs: Any) -> None:
    render(**kwargs)


def show_simulation_page(**kwargs: Any) -> None:
    render(**kwargs)


def simulation_page(**kwargs: Any) -> None:
    render(**kwargs)


def show(**kwargs: Any) -> None:
    render(**kwargs)


def app(**kwargs: Any) -> None:
    render(**kwargs)
