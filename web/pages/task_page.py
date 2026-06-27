from __future__ import annotations

import base64
import html
import io
import json
import math
import re
import sys
import textwrap
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import pandas as pd
import streamlit as st


# =========================================================
# IMPORT COMPATIBILITY
# =========================================================
# Khi chạy bằng `streamlit run streamlit_app.py`, Python có thể không nhìn thấy
# models.py/constants.py nếu trang đang nằm trong web/pages. Thêm các thư mục
# thường gặp vào sys.path để Task page chạy được ở cả cấu trúc web và desktop.
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


def _import_attr(module_names: list[str], attr_name: str) -> Any:
    import importlib

    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
            value = getattr(module, attr_name, None)
            if value is not None:
                return value
        except Exception:
            continue
    return None


Task = _import_attr(["core.models", "models"], "Task")
PROJECT_TASK_TYPES = _import_attr(
    ["assets.constants", "utils.constants", "core.constants", "constants"],
    "TASK_TYPES",
)
if not PROJECT_TASK_TYPES:
    PROJECT_TASK_TYPES = ["In tài liệu", "Sao chép", "Scan"]


PRIMARY = "#005BAC"
PRIMARY_DARK = "#004A99"
ACCENT = "#D71920"
BG = "#F4F7FB"
WHITE = "#FFFFFF"
TEXT = "#1F2937"
MUTED = "#64748B"
BORDER = "#D9E2EC"
LIGHT_BLUE = "#EAF4FF"
GREEN = "#16A34A"
ORANGE = "#F97316"
PURPLE = "#7C3AED"
RED = "#DC2626"
TEAL = "#0891B2"

TASK_TYPES = list(PROJECT_TASK_TYPES) or ["In tài liệu", "Sao chép", "Scan"]
STATUS_OPTIONS = ["Tất cả trạng thái", "Đang chờ", "Đang xử lý", "Hoàn thành"]
BASE_DIR = Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) >= 3 else Path.cwd()


# =========================================================
# SHARED TASK PERSISTENCE
# =========================================================
# Session State có thể bị mất khi chuyển trang bằng link ?page=... vì trình duyệt
# tạo lại websocket. Vì vậy lưu thêm một bản JSON dùng chung để các trang nạp lại
# danh sách tác vụ nếu session hiện tại đang trống.
TASK_STORE_FILE = BASE_DIR / ".photocopy_shared_tasks.json"
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

    # Chuẩn hóa các field số để JSON đọc lại ổn định.
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

    row["status"] = normalize_status(row.get("status", "Đang chờ"))
    return row


def save_tasks_to_store(source: list[Any] | None = None) -> None:
    try:
        data = [task_to_plain_dict(task) for task in (source if source is not None else tasks())]
        TASK_STORE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        # Không làm vỡ giao diện nếu máy không cho ghi file.
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
            cover = to_int(item.get("cover_pages"), 0)
            color = to_int(item.get("color_pages"), 0)
            bw = to_int(item.get("bw_pages"), 0)
            if cover == 0 and color == 0 and bw == 0:
                # Tương thích dữ liệu cũ chỉ có total_pages/priority.
                bw = max(0, to_int(item.get("total_pages", item.get("priority", 0)), 0))
            burst = max(1, to_int(item.get("burst_time"), calculate_burst_time(cover, color, bw)))
            total = calculate_total_pages(cover, color, bw)
            item = dict(item)
            item.update({
                "task_id": task_id,
                "customer_name": str(item.get("customer_name") or "Khách lẻ"),
                "task_type": str(item.get("task_type") or TASK_TYPES[0]),
                "arrival_time": to_int(item.get("arrival_time"), 0),
                "burst_time": burst,
                "priority": max(1, to_int(item.get("priority"), 1)),
                "cover_pages": cover,
                "color_pages": color,
                "bw_pages": bw,
                "total_pages": total,
                "print_option": str(item.get("print_option") or build_print_option_text(cover, color, bw)),
                "status": normalize_status(item.get("status", "Đang chờ")),
                "processing_method": str(item.get("processing_method") or "Tính theo số trang"),
                "completion_time": to_int(item.get("completion_time"), 0),
                "turnaround_time": to_int(item.get("turnaround_time"), 0),
                "waiting_time": to_int(item.get("waiting_time"), 0),
                "response_time": to_int(item.get("response_time"), 0),
                "simulation_algorithm": str(item.get("simulation_algorithm") or ""),
            })
            loaded.append(item)
        return loaded
    except Exception:
        return []


def restore_tasks_if_needed() -> None:
    if st.session_state.get("tasks"):
        return
    persisted = load_tasks_from_store()
    if persisted:
        st.session_state["tasks"] = persisted


# =========================================================
# HTML / ICON HELPERS
# =========================================================
def html_block(value: str) -> str:
    return "\n".join(line.lstrip() for line in textwrap.dedent(str(value)).strip().splitlines())


def render_html(value: str) -> None:
    st.markdown(html_block(value), unsafe_allow_html=True)


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
        Path("/Users/mac/web_photocopy_task_scheduler/assets/icons"),
    ]
    out: list[Path] = []
    for path in paths:
        if path not in out:
            out.append(path)
    return out


@st.cache_data(show_spinner=False)
def _icon_path(name: str) -> str:
    if not name:
        return ""

    raw = str(name).strip()
    path = Path(raw)
    if path.is_file():
        return str(path)

    names = [raw]
    if not raw.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".svg")):
        names += [f"{raw}.png", f"{raw}.jpg", f"{raw}.jpeg", f"{raw}.webp", f"{raw}.svg"]

    aliases = {
        "Task_List": ["Task_List", "Task List", "Manager"],
        "AVG_Waiting": ["AVG_Waiting", "Waiting", "Time"],
        "Processing": ["Processing", "Process"],
        "Complete": ["Complete", "Done"],
        "Describe": ["Describe", "Input", "Task"],
        "Filter": ["Filter", "Search"],
        "Import": ["Import", "Import_task"],
        "Save_task": ["Save_task", "Save"],
        "Delete_task": ["Delete_task", "Delete"],
        "Add": ["Add", "Add_task"],
        "Update": ["Update", "Edit"],
        "Reset": ["Reset", "Refresh"],
    }
    for alias in aliases.get(raw, []):
        if alias not in names:
            names.append(alias)
            names.append(f"{alias}.png")

    target = _norm_name(Path(raw).stem)
    for folder in _icon_dirs():
        if not folder.exists():
            continue
        for candidate in names:
            p = folder / candidate
            if p.exists():
                return str(p)
        for item in folder.iterdir():
            if item.is_file() and _norm_name(item.stem) == target:
                return str(item)
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
    cls_part = f' class="{html.escape(cls)}"' if cls else ""
    return f'<img{cls_part} src="{src}" style="width:{size}px;height:{size}px;object-fit:contain;" />'


# =========================================================
# STATE + SHARED DATA FLOW
# =========================================================
def init_state() -> None:
    if "tasks" not in st.session_state:
        st.session_state["tasks"] = []

    defaults = {
        "task_page_selected_id": "",
        "task_page_checked_ids": set(),
        "task_form_id": "",
        "task_form_customer": "",
        "task_form_type": TASK_TYPES[0],
        "task_form_priority": 1,
        "task_form_cover": 0,
        "task_form_color": 0,
        "task_form_bw": 0,
        "task_filter_keyword": "",
        "task_filter_type": "Tất cả loại",
        "task_filter_status": "Tất cả trạng thái",
        "task_import_nonce": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, set) else value

    restore_tasks_if_needed()


def tasks() -> list[Any]:
    return st.session_state.get("tasks", []) or []


def set_tasks(value: list[Any]) -> None:
    st.session_state["tasks"] = value or []
    save_tasks_to_store(st.session_state["tasks"])


def val(task: Any, key: str, default: Any = "") -> Any:
    if task is None:
        return default
    if isinstance(task, dict):
        return task.get(key, default)
    return getattr(task, key, default)


def put(task: Any, key: str, value: Any) -> None:
    if isinstance(task, dict):
        task[key] = value
    else:
        setattr(task, key, value)


def to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(value))
    except Exception:
        return default


def normalize_status(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in ("hoàn thành", "hoan thanh", "completed", "complete", "done"):
        return "Hoàn thành"
    if text in ("đang xử lý", "dang xu ly", "processing", "running", "run"):
        return "Đang xử lý"
    return "Đang chờ"


def calculate_burst_time(cover_pages: Any = 0, color_pages: Any = 0, bw_pages: Any = 0) -> int:
    cover = max(0, to_int(cover_pages, 0))
    color = max(0, to_int(color_pages, 0))
    bw = max(0, to_int(bw_pages, 0))
    total_seconds = cover * 2 + color * 1 + bw * 0.3
    return max(1, int(math.ceil(total_seconds)))


def calculate_total_pages(cover_pages: Any = 0, color_pages: Any = 0, bw_pages: Any = 0) -> int:
    return max(0, to_int(cover_pages, 0)) + max(0, to_int(color_pages, 0)) + max(0, to_int(bw_pages, 0))


def build_print_option_text(cover_pages: int, color_pages: int, bw_pages: int) -> str:
    parts = []
    if cover_pages > 0:
        parts.append(f"In bìa: {cover_pages}")
    if color_pages > 0:
        parts.append(f"In màu: {color_pages}")
    if bw_pages > 0:
        parts.append(f"Trắng đen: {bw_pages}")
    return " | ".join(parts) if parts else "Không có"


def page_counts(task: Any) -> tuple[int, int, int]:
    cover = max(0, to_int(val(task, "cover_pages", 0), 0))
    color = max(0, to_int(val(task, "color_pages", 0), 0))
    bw = max(0, to_int(val(task, "bw_pages", 0), 0))
    if cover == 0 and color == 0 and bw == 0:
        legacy_qty = max(0, to_int(val(task, "priority", 0), 0))
        if legacy_qty > 0:
            bw = legacy_qty
    return cover, color, bw


def make_task(
    task_id: str,
    customer_name: str,
    task_type: str,
    arrival_time: int,
    cover_pages: int,
    color_pages: int,
    bw_pages: int,
    priority: int,
    status: str = "Đang chờ",
) -> Any:
    cover_pages = max(0, to_int(cover_pages, 0))
    color_pages = max(0, to_int(color_pages, 0))
    bw_pages = max(0, to_int(bw_pages, 0))
    total_pages = calculate_total_pages(cover_pages, color_pages, bw_pages)
    burst = calculate_burst_time(cover_pages, color_pages, bw_pages)
    print_option = build_print_option_text(cover_pages, color_pages, bw_pages)
    status = normalize_status(status)

    if Task is not None:
        try:
            task = Task(
                task_id,
                customer_name,
                task_type,
                arrival_time,
                burst,
                priority=priority,
                print_option=print_option,
                status=status,
            )
        except TypeError:
            try:
                task = Task(task_id, customer_name, task_type, arrival_time, burst, priority, print_option, status)
            except Exception:
                task = SimpleNamespace()
    else:
        task = SimpleNamespace()

    # Gán lại đầy đủ thuộc tính để dù Task class thiếu field vẫn không mất dữ liệu.
    put(task, "task_id", task_id)
    put(task, "customer_name", customer_name)
    put(task, "task_type", task_type)
    put(task, "arrival_time", arrival_time)
    put(task, "burst_time", burst)
    put(task, "priority", priority)
    put(task, "print_option", print_option)
    put(task, "status", status)
    put(task, "processing_method", "Tính theo số trang")
    put(task, "cover_pages", cover_pages)
    put(task, "color_pages", color_pages)
    put(task, "bw_pages", bw_pages)
    put(task, "total_pages", total_pages)
    return task


def task_number(task_id: Any) -> int:
    match = re.search(r"\d+", str(task_id or ""))
    return int(match.group()) if match else 999999


def sort_tasks(source: list[Any]) -> list[Any]:
    return sorted(source or [], key=lambda item: (task_number(val(item, "task_id", "")), str(val(item, "task_id", ""))))


def find_index(task_id: str) -> int | None:
    for i, task in enumerate(tasks()):
        if str(val(task, "task_id", "")) == str(task_id):
            return i
    return None


def mark_tasks_changed(on_tasks_changed: Callable[[list[Any]], Any] | None = None) -> None:
    """
    Một điểm duy nhất để báo dữ liệu Task đã đổi.

    Quy ước dữ liệu chung của toàn app:
    - Danh sách tác vụ chỉ nằm ở st.session_state["tasks"].
    - Khi task thay đổi, chỉ xóa kết quả mô phỏng cũ vì không còn khớp dữ liệu.
    - Không tự tạo task mẫu, không tách dữ liệu riêng cho từng trang.
    """
    st.session_state["sim_results"] = OrderedDict()
    st.session_state["sim_normalized_tasks"] = []
    st.session_state["sim_task_color_map"] = {}
    st.session_state["sim_current_time"] = 0
    st.session_state["sim_max_time"] = 0
    st.session_state["sim_timeline_points"] = [0]
    st.session_state["sim_timeline_index"] = 0
    st.session_state["sim_running"] = False
    st.session_state["sim_finished"] = False
    st.session_state["sim_note"] = ""
    st.session_state["sim_last_tick"] = 0.0
    st.session_state["sim_task_signature"] = ""
    st.session_state["simulation_results"] = {}
    st.session_state["latest_simulation_payload"] = None

    # Các trang phụ thuộc task cũng không được giữ payload cũ sau khi task đổi.
    st.session_state["memory_payload"] = {}
    st.session_state["sync_payload"] = {}
    st.session_state["latest_memory_payload"] = None
    st.session_state["latest_sync_payload"] = None
    st.session_state["footer_status"] = "Danh sách tác vụ đã được cập nhật"

    if on_tasks_changed:
        try:
            on_tasks_changed(st.session_state.get("tasks", []))
        except Exception:
            pass


# =========================================================
# FORM / IMPORT
# =========================================================
def fill_form(task: Any) -> None:
    cover, color, bw = page_counts(task)
    kind = str(val(task, "task_type", TASK_TYPES[0]))
    st.session_state["task_page_selected_id"] = str(val(task, "task_id", ""))
    st.session_state["task_form_id"] = str(val(task, "task_id", ""))
    st.session_state["task_form_customer"] = str(val(task, "customer_name", ""))
    st.session_state["task_form_type"] = kind if kind in TASK_TYPES else TASK_TYPES[0]
    st.session_state["task_form_priority"] = max(1, to_int(val(task, "priority", 1), 1))
    st.session_state["task_form_cover"] = cover
    st.session_state["task_form_color"] = color
    st.session_state["task_form_bw"] = bw


def clear_form() -> None:
    st.session_state["task_page_selected_id"] = ""
    st.session_state["task_form_id"] = ""
    st.session_state["task_form_customer"] = ""
    st.session_state["task_form_type"] = TASK_TYPES[0]
    st.session_state["task_form_priority"] = 1
    st.session_state["task_form_cover"] = 0
    st.session_state["task_form_color"] = 0
    st.session_state["task_form_bw"] = 0


def form_values() -> tuple[str, str, str, int, int, int, int]:
    return (
        str(st.session_state.get("task_form_id", "")).strip(),
        str(st.session_state.get("task_form_customer", "")).strip(),
        str(st.session_state.get("task_form_type", TASK_TYPES[0])).strip() or TASK_TYPES[0],
        max(1, to_int(st.session_state.get("task_form_priority", 1), 1)),
        max(0, to_int(st.session_state.get("task_form_cover", 0), 0)),
        max(0, to_int(st.session_state.get("task_form_color", 0), 0)),
        max(0, to_int(st.session_state.get("task_form_bw", 0), 0)),
    )


def validate_form(is_update: bool = False) -> tuple[str, str, str, int, int, int, int]:
    task_id, customer, kind, priority, cover, color, bw = form_values()
    if not task_id or not customer:
        raise ValueError("Mã tác vụ và tên khách hàng không được bỏ trống.")
    if cover + color + bw <= 0:
        raise ValueError("Vui lòng nhập ít nhất 1 trang ở một trong ba ô: in bìa, in màu hoặc trắng đen.")
    if priority <= 0:
        raise ValueError("Độ ưu tiên phải lớn hơn 0. Quy ước: số nhỏ hơn thì ưu tiên cao hơn.")
    existing_index = find_index(task_id)
    selected_id = str(st.session_state.get("task_page_selected_id", ""))
    if not is_update and existing_index is not None:
        raise ValueError(f"Mã tác vụ {task_id} đã tồn tại trong hệ thống.")
    if is_update and existing_index is not None and selected_id and task_id != selected_id:
        raise ValueError(f"Mã tác vụ {task_id} đã tồn tại trong hệ thống.")
    return task_id, customer, kind, priority, cover, color, bw


def norm_col(text: Any) -> str:
    s = str(text or "").strip().lower()
    repl = str.maketrans(
        "áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ",
        "aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd",
    )
    s = s.translate(repl)
    return "".join(ch for ch in s if ch.isalnum())


def row_get(row: pd.Series, names: list[str], default: Any = "") -> Any:
    mapping = {norm_col(col): col for col in row.index}
    for name in names:
        real = mapping.get(norm_col(name))
        if real is not None:
            value = row.get(real, default)
            if value is not None and str(value).strip().lower() not in ("", "nan", "none"):
                return value
    return default


def tasks_from_df(df: pd.DataFrame, seen_ids: set[str]) -> tuple[list[Any], int]:
    loaded: list[Any] = []
    skipped = 0

    if df is None or df.empty:
        return loaded, skipped

    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]

    for _, row in df.iterrows():
        try:
            task_id = str(row_get(row, ["Mã tác vụ", "Ma tac vu", "task_id", "id", "Mã", "Ma"])).strip()
            if not task_id or task_id.lower() in ("nan", "none") or task_id in seen_ids:
                skipped += 1
                continue

            customer = str(row_get(row, ["Khách hàng", "Khach hang", "customer_name", "customer", "Tên khách", "Ten khach"], "Khách lẻ")).strip() or "Khách lẻ"
            kind = str(row_get(row, ["Loại tác vụ", "Loai tac vu", "task_type", "type", "Loại", "Loai"], TASK_TYPES[0])).strip() or TASK_TYPES[0]
            arrival = to_int(row_get(row, ["Thời điểm đến", "Thoi diem den", "Đến", "Den", "arrival_time", "arrival", "AT"], 0), 0)
            cover = to_int(row_get(row, ["Số trang bìa", "So trang bia", "In bìa", "In bia", "cover_pages", "bia_pages", "bia"], 0), 0)
            color = to_int(row_get(row, ["Số trang màu", "So trang mau", "In màu", "In mau", "color_pages", "mau_pages", "mau"], 0), 0)
            bw = to_int(row_get(row, ["Số trang trắng đen", "So trang trang den", "Trắng đen", "Trang den", "bw_pages", "black_white_pages", "trang_den_pages"], 0), 0)

            if cover == 0 and color == 0 and bw == 0:
                old_qty = to_int(row_get(row, ["Số lượng", "So luong", "quantity", "qty", "Số tờ", "So to"], 0), 0)
                old_print_option = str(row_get(row, ["Tùy chọn in", "Tuy chon in", "print_option"], "Trắng đen")).lower()
                if old_qty > 0:
                    if "bìa" in old_print_option or "bia" in old_print_option:
                        cover = old_qty
                    elif "màu" in old_print_option or "mau" in old_print_option:
                        color = old_qty
                    else:
                        bw = old_qty

            if cover + color + bw <= 0:
                skipped += 1
                continue

            priority = max(1, to_int(row_get(row, ["Độ ưu tiên", "Do uu tien", "priority", "prio"], 1), 1))
            status = normalize_status(row_get(row, ["Trạng thái", "Trang thai", "status"], "Đang chờ"))
            loaded.append(make_task(task_id, customer, kind, arrival, cover, color, bw, priority, status))
            seen_ids.add(task_id)
        except Exception:
            skipped += 1

    return loaded, skipped


def dataframe_from_tasks(source: list[Any]) -> pd.DataFrame:
    rows = []
    for task in sort_tasks(source):
        cover, color, bw = page_counts(task)
        total = calculate_total_pages(cover, color, bw)
        rows.append({
            "Mã tác vụ": val(task, "task_id", ""),
            "Khách hàng": val(task, "customer_name", ""),
            "Loại tác vụ": val(task, "task_type", ""),
            "Thời điểm đến": to_int(val(task, "arrival_time", 0), 0),
            "In bìa": cover,
            "In màu": color,
            "Trắng đen": bw,
            "Tổng trang": total,
            "Thời gian xử lý": to_int(val(task, "burst_time", calculate_burst_time(cover, color, bw)), 0),
            "Ưu tiên": to_int(val(task, "priority", 1), 1),
            "Trạng thái": normalize_status(val(task, "status", "Đang chờ")),
            "completion_time": val(task, "completion_time", ""),
            "turnaround_time": val(task, "turnaround_time", ""),
            "waiting_time": val(task, "waiting_time", ""),
            "response_time": val(task, "response_time", ""),
            "simulation_algorithm": val(task, "simulation_algorithm", ""),
        })
    return pd.DataFrame(rows)


# =========================================================
# CSS + RENDER HELPERS
# =========================================================
def inject_css() -> None:
    render_html(f"""
    <style>
    .task-page-wrap {{ width:100%; }}
    .task-stats {{ display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:14px; margin-bottom:14px; }}
    .task-stat {{ background:{WHITE}; border:1px solid {BORDER}; min-height:104px; display:flex; align-items:center; padding:12px 18px; box-sizing:border-box; }}
    .task-stat-icon {{ width:82px; height:82px; display:flex; align-items:center; justify-content:center; margin-right:18px; flex-shrink:0; }}
    .task-stat-title {{ color:{TEXT}; font-size:12px; font-weight:900; text-transform:uppercase; }}
    .task-stat-num {{ font-size:30px; font-weight:900; line-height:1.15; margin-top:2px; }}
    .task-stat-sub {{ color:{MUTED}; font-size:12px; margin-top:2px; }}
    .task-section-title {{ display:flex; align-items:center; gap:10px; color:{PRIMARY}; font-size:16px; font-weight:900; text-transform:uppercase; margin-bottom:12px; }}
    .task-panel-note {{ color:{MUTED}; font-size:12px; font-weight:700; }}
    .task-sync-ok {{ background:{LIGHT_BLUE}; border:1px solid {BORDER}; color:{PRIMARY}; padding:10px 14px; font-weight:800; margin-bottom:12px; }}
    .task-table-wrap {{ background:{WHITE}; border:1px solid {BORDER}; padding:14px; margin-top:14px; }}
    @media(max-width:1100px) {{ .task-stats {{ grid-template-columns:repeat(2, minmax(0, 1fr)); }} }}
    </style>
    """)


def stat_cards() -> None:
    source = tasks()
    total = len(source)
    waiting = sum(normalize_status(val(t, "status", "Đang chờ")) == "Đang chờ" for t in source)
    running = sum(normalize_status(val(t, "status", "")) == "Đang xử lý" for t in source)
    done = sum(normalize_status(val(t, "status", "")) == "Hoàn thành" for t in source)

    def card(title: str, number: int, icon_name: str, color: str) -> str:
        img = icon(icon_name, 74) or f"<span style='font-size:42px;color:{color}'>●</span>"
        return f"""
        <div class='task-stat'>
            <div class='task-stat-icon'>{img}</div>
            <div>
                <div class='task-stat-title'>{html.escape(title)}</div>
                <div class='task-stat-num' style='color:{color}'>{number}</div>
                <div class='task-stat-sub'>Tác vụ trong hệ thống</div>
            </div>
        </div>
        """

    render_html(
        "<div class='task-stats'>"
        + card("Tổng tác vụ", total, "Comparison_Algorithm", PRIMARY)
        + card("Đang chờ", waiting, "AVG_Waiting", ORANGE)
        + card("Đang xử lý", running, "Processing", PURPLE)
        + card("Hoàn thành", done, "Complete", GREEN)
        + "</div>"
    )


def filtered_tasks() -> list[Any]:
    keyword = str(st.session_state.get("task_filter_keyword", "")).strip().lower()
    f_type = str(st.session_state.get("task_filter_type", "Tất cả loại"))
    f_status = str(st.session_state.get("task_filter_status", "Tất cả trạng thái"))

    result = []
    for task in sort_tasks(tasks()):
        if keyword:
            haystack = " ".join([
                str(val(task, "task_id", "")),
                str(val(task, "customer_name", "")),
                str(val(task, "task_type", "")),
            ]).lower()
            if keyword not in haystack:
                continue
        if f_type != "Tất cả loại" and str(val(task, "task_type", "")) != f_type:
            continue
        if f_status != "Tất cả trạng thái" and normalize_status(val(task, "status", "")) != f_status:
            continue
        result.append(task)
    return result


# =========================================================
# ACTIONS
# =========================================================
def add_task(on_tasks_changed: Callable[[list[Any]], Any] | None = None) -> None:
    try:
        task_id, customer, kind, priority, cover, color, bw = validate_form(is_update=False)
        updated = list(tasks())
        updated.append(make_task(task_id, customer, kind, 0, cover, color, bw, priority, "Đang chờ"))
        set_tasks(updated)
        clear_form()
        mark_tasks_changed(on_tasks_changed)
        st.success(f"Đã thêm tác vụ {task_id}.")
    except Exception as exc:
        st.error(str(exc))


def update_task(on_tasks_changed: Callable[[list[Any]], Any] | None = None) -> None:
    selected_id = str(st.session_state.get("task_page_selected_id", "")).strip()
    if not selected_id:
        st.warning("Vui lòng chọn một tác vụ trong bảng trước khi cập nhật.")
        return
    try:
        task_id, customer, kind, priority, cover, color, bw = validate_form(is_update=True)
        updated = list(tasks())
        old_index = find_index(selected_id)
        if old_index is None:
            st.warning("Không tìm thấy tác vụ đang chọn.")
            return
        old_task = updated[old_index]
        status = normalize_status(val(old_task, "status", "Đang chờ"))
        updated[old_index] = make_task(task_id, customer, kind, to_int(val(old_task, "arrival_time", 0), 0), cover, color, bw, priority, status)
        set_tasks(updated)
        clear_form()
        mark_tasks_changed(on_tasks_changed)
        st.success(f"Đã cập nhật tác vụ {task_id}.")
    except Exception as exc:
        st.error(str(exc))


def delete_selected(on_tasks_changed: Callable[[list[Any]], Any] | None = None) -> None:
    selected_id = str(st.session_state.get("task_page_selected_id", "")).strip()
    if not selected_id:
        st.warning("Vui lòng chọn một tác vụ cần xóa.")
        return
    updated = [task for task in tasks() if str(val(task, "task_id", "")) != selected_id]
    set_tasks(updated)
    clear_form()
    checked = set(st.session_state.get("task_page_checked_ids", set()))
    checked.discard(selected_id)
    st.session_state["task_page_checked_ids"] = checked
    mark_tasks_changed(on_tasks_changed)
    st.success(f"Đã xóa tác vụ {selected_id}.")


def delete_checked(on_tasks_changed: Callable[[list[Any]], Any] | None = None) -> None:
    checked = set(st.session_state.get("task_page_checked_ids", set()))
    if not checked:
        st.warning("Chưa tick tác vụ nào để xóa.")
        return
    updated = [task for task in tasks() if str(val(task, "task_id", "")) not in checked]
    set_tasks(updated)
    st.session_state["task_page_checked_ids"] = set()
    clear_form()
    mark_tasks_changed(on_tasks_changed)
    st.success(f"Đã xóa {len(checked)} tác vụ đã tick.")


def reset_all(on_tasks_changed: Callable[[list[Any]], Any] | None = None) -> None:
    set_tasks([])
    st.session_state["task_page_checked_ids"] = set()
    clear_form()
    mark_tasks_changed(on_tasks_changed)
    st.success("Đã xóa toàn bộ danh sách tác vụ.")


# =========================================================
# UI SECTIONS
# =========================================================
def render_form(on_tasks_changed: Callable[[list[Any]], Any] | None = None) -> None:
    render_html(f"<div class='task-section-title'>{icon('Describe', 24)}<span>NHẬP THÔNG TIN TÁC VỤ</span></div>")

    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Mã tác vụ", key="task_form_id", placeholder="Ví dụ: T001")
    with c2:
        st.text_input("Khách hàng", key="task_form_customer", placeholder="Nhập tên khách hàng")

    c3, c4 = st.columns(2)
    with c3:
        st.selectbox("Loại tác vụ", TASK_TYPES, key="task_form_type")
    with c4:
        st.number_input("Độ ưu tiên", min_value=1, step=1, key="task_form_priority")

    st.caption("Số trang in")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.number_input("In bìa", min_value=0, step=1, key="task_form_cover")
    with p2:
        st.number_input("In màu", min_value=0, step=1, key="task_form_color")
    with p3:
        st.number_input("Trắng đen", min_value=0, step=1, key="task_form_bw")

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("＋ Thêm tác vụ", type="primary", use_container_width=True):
            add_task(on_tasks_changed)
            st.rerun()
    with b2:
        if st.button("✎ Cập nhật", use_container_width=True):
            update_task(on_tasks_changed)
            st.rerun()
    with b3:
        if st.button("🗑 Xóa", use_container_width=True):
            delete_selected(on_tasks_changed)
            st.rerun()
    with b4:
        if st.button("⟳ Làm mới form", use_container_width=True):
            clear_form()
            st.rerun()


def render_filter_import(on_tasks_changed: Callable[[list[Any]], Any] | None = None) -> None:
    render_html(f"<div class='task-section-title'>{icon('Filter', 24)}<span>BỘ LỌC & TÌM KIẾM</span></div>")

    st.text_input("Từ khóa tìm", key="task_filter_keyword", placeholder="Nhập mã hoặc tên khách")
    st.selectbox("Loại tác vụ", ["Tất cả loại"] + TASK_TYPES, key="task_filter_type")
    st.selectbox("Trạng thái", STATUS_OPTIONS, key="task_filter_status")

    uploaded = st.file_uploader(
        "Nạp từ Excel/CSV",
        type=["xlsx", "xls", "csv"],
        key=f"task_uploader_{st.session_state.get('task_import_nonce', 0)}",
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📁 Import", use_container_width=True, disabled=uploaded is None):
            if uploaded is not None:
                try:
                    if uploaded.name.lower().endswith(".csv"):
                        df = pd.read_csv(uploaded)
                    else:
                        df = pd.read_excel(uploaded)
                    seen = {str(val(task, "task_id", "")) for task in tasks()}
                    loaded, skipped = tasks_from_df(df, seen)
                    if loaded:
                        set_tasks(list(tasks()) + loaded)
                        st.session_state["task_import_nonce"] = st.session_state.get("task_import_nonce", 0) + 1
                        mark_tasks_changed(on_tasks_changed)
                        st.success(f"Đã import {len(loaded)} tác vụ. Bỏ qua {skipped} dòng.")
                        st.rerun()
                    else:
                        st.warning(f"Không có tác vụ hợp lệ để import. Bỏ qua {skipped} dòng.")
                except Exception as exc:
                    st.error(f"Không đọc được file: {exc}")
    with c2:
        df = dataframe_from_tasks(tasks())
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "💾 Tải CSV",
            data=csv,
            file_name="danh_sach_tac_vu.csv",
            mime="text/csv",
            use_container_width=True,
            disabled=df.empty,
        )


def render_table(on_tasks_changed: Callable[[list[Any]], Any] | None = None) -> None:
    render_html(f"""
    <div class='task-table-wrap'>
        <div class='task-section-title'>{icon('Task_List', 24)}<span>DANH SÁCH TÁC VỤ TRONG HỆ THỐNG</span></div>
        <div class='task-panel-note'>Dữ liệu trong bảng này được lưu trực tiếp vào <b>st.session_state["tasks"]</b> và được trang Simulation đọc lại ngay.</div>
    </div>
    """)

    source = filtered_tasks()
    if not source:
        st.info("Chưa có tác vụ phù hợp bộ lọc. Hãy thêm hoặc import dữ liệu tác vụ.")
        return

    selected_options = [str(val(task, "task_id", "")) for task in sort_tasks(source)]
    selected_id = st.selectbox(
        "Chọn tác vụ để sửa/xóa",
        [""] + selected_options,
        index=0,
        format_func=lambda x: "-- Chọn tác vụ --" if not x else x,
    )
    if selected_id:
        idx = find_index(selected_id)
        if idx is not None and st.button(f"Đưa {selected_id} lên form", use_container_width=False):
            fill_form(tasks()[idx])
            st.rerun()

    df = dataframe_from_tasks(source)
    st.dataframe(df, use_container_width=True, hide_index=True)

    with st.expander("Tick nhiều tác vụ để xóa", expanded=False):
        checked = set(st.session_state.get("task_page_checked_ids", set()))
        cols = st.columns(4)
        for i, task_id in enumerate(selected_options):
            with cols[i % 4]:
                is_checked = st.checkbox(task_id, value=task_id in checked, key=f"task_check_{task_id}")
                if is_checked:
                    checked.add(task_id)
                else:
                    checked.discard(task_id)
        st.session_state["task_page_checked_ids"] = checked
        if st.button("🗑 Xóa tác vụ đã tick", type="secondary", use_container_width=True):
            delete_checked(on_tasks_changed)
            st.rerun()

    if st.button("🧹 Xóa toàn bộ danh sách", type="secondary"):
        reset_all(on_tasks_changed)
        st.rerun()


# =========================================================
# ENTRYPOINTS
# =========================================================
def render_task_page(
    tasks: list[Any] | None = None,
    on_tasks_changed: Callable[[list[Any]], Any] | None = None,
    **_: Any,
) -> None:
    init_state()

    # Nhận tasks từ streamlit_app.py chỉ khi session chưa có dữ liệu và context có dữ liệu thật.
    # Không nhận list rỗng từ streamlit_app sau khi trình duyệt reload, vì list rỗng đó
    # sẽ che mất dữ liệu vừa được restore từ file JSON dùng chung.
    if tasks:
        st.session_state["tasks"] = tasks
        save_tasks_to_store(tasks)
    else:
        restore_tasks_if_needed()

    inject_css()
    render_html("<div class='task-page-wrap'>")
    render_html("<div class='task-sync-ok'>Dữ liệu tác vụ đang dùng chung với trang Mô phỏng thuật toán.</div>")
    stat_cards()

    left, right = st.columns([0.6, 0.4], gap="medium")
    with left:
        render_form(on_tasks_changed)
    with right:
        render_filter_import(on_tasks_changed)

    render_table(on_tasks_changed)
    render_html("</div>")


def render_page(**kwargs: Any) -> None:
    render_task_page(**kwargs)


def show_task_page(**kwargs: Any) -> None:
    render_task_page(**kwargs)


def render(**kwargs: Any) -> None:
    render_task_page(**kwargs)


def main() -> None:
    render_task_page()


app = render_task_page


if __name__ == "__main__":
    main()
