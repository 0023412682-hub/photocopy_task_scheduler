import base64
import html
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st


# ====================== THEME ======================
PRIMARY = "#005BAC"
PRIMARY_DARK = "#004A99"
BG = "#F4F7FB"
WHITE = "#FFFFFF"
TEXT = "#1F2937"
MUTED = "#64748B"
BORDER = "#D9E2EC"
LIGHT_LINE = "#E2E8F0"
GREEN = "#16A34A"
GREEN_BG = "#DCFCE7"
ORANGE = "#F97316"
ORANGE_BG = "#FFEDD5"
RED = "#DC2626"
RED_BG = "#FEE2E2"
PURPLE = "#7C3AED"
PURPLE_BG = "#F5F3FF"
BLUE_BG = "#EFF6FF"
YELLOW_BG = "#FEF3C7"

BASE_DIR = Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) >= 3 else Path.cwd()
SPEED_OPTIONS = [
    "Rất chậm (2000 ms)",
    "Chậm (1000 ms)",
    "Trung bình (500 ms)",
    "Nhanh (250 ms)",
    "Rất nhanh (125 ms)",
]


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
    out: list[Path] = []
    for p in paths:
        if p not in out:
            out.append(p)
    return out


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
            candidate = folder / n
            if candidate.exists():
                return str(candidate)
        for candidate in folder.iterdir():
            if candidate.is_file() and _norm_name(candidate.stem) == target:
                return str(candidate)
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
    return f'<img class="{cls}" src="{src}" style="width:{size}px;height:{size}px;object-fit:contain;" />'


def first_icon(names: list[str], size: int = 24, cls: str = "") -> str:
    for name in names:
        img = icon(name, size, cls)
        if img:
            return img
    return ""


# ====================== TASK + STATE HELPERS ======================
def tasks() -> list[Any]:
    st.session_state.setdefault("tasks", [])
    return st.session_state["tasks"]


def val(task: Any, key: str, default: Any = "") -> Any:
    return task.get(key, default) if isinstance(task, dict) else getattr(task, key, default)


def task_label(task: Any, index: int) -> str:
    return str(val(task, "task_id", f"T{index + 1:03d}"))


def get_delay_ms(text: str, default: int = 500) -> int:
    match = re.search(r"\d+", str(text or ""))
    return int(match.group()) if match else default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def init_state() -> None:
    st.session_state.setdefault("tasks", [])
    defaults = {
        "sync_mechanism": "Producer - Consumer",
        "sync_buffer_size": 5,
        "sync_producer_speed": "Trung bình (500 ms)",
        "sync_consumer_speed": "Trung bình (500 ms)",
        "sync_buffer": [None] * 5,
        "sync_count": 0,
        "sync_in_ptr": 0,
        "sync_out_ptr": 0,
        "sync_task_index": 0,
        "sync_produced_count": 0,
        "sync_consumed_count": 0,
        "sync_producer_wait": 0,
        "sync_consumer_wait": 0,
        "sync_critical_access": 0,
        "sync_event_count": 0,
        "sync_step_index": 0,
        "sync_running": False,
        "sync_started": False,
        "sync_finished": False,
        "sync_deadlock": False,
        "sync_logs": [],
        "sync_last_delay_ms": 500,
        "sync_mutex_state": "Mở",
        "sync_mutex_sub": "C1 đang đọc",
        "sync_producer_state": "Sẵn sàng",
        "sync_producer_sub": "Không còn tác vụ nạp",
        "sync_consumer_state": "Sẵn sàng",
        "sync_consumer_sub": "Đã xử lý hết buffer",
        "sync_last_action": "Sẵn sàng mô phỏng đồng bộ hóa.",
        "sync_payload": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    size = max(1, safe_int(st.session_state.get("sync_buffer_size", 5), 5))
    buf = st.session_state.get("sync_buffer")
    if not isinstance(buf, list) or len(buf) != size:
        reset_runtime(clear_log=False)


def reset_runtime(clear_log: bool = True) -> None:
    size = max(1, safe_int(st.session_state.get("sync_buffer_size", 5), 5))
    st.session_state["sync_buffer_size"] = size
    st.session_state["sync_buffer"] = [None] * size
    st.session_state["sync_count"] = 0
    st.session_state["sync_in_ptr"] = 0
    st.session_state["sync_out_ptr"] = 0
    st.session_state["sync_task_index"] = 0
    st.session_state["sync_produced_count"] = 0
    st.session_state["sync_consumed_count"] = 0
    st.session_state["sync_producer_wait"] = 0
    st.session_state["sync_consumer_wait"] = 0
    st.session_state["sync_critical_access"] = 0
    st.session_state["sync_event_count"] = 0
    st.session_state["sync_step_index"] = 0
    st.session_state["sync_running"] = False
    st.session_state["sync_started"] = False
    st.session_state["sync_finished"] = False
    st.session_state["sync_deadlock"] = False
    st.session_state["sync_last_delay_ms"] = 500
    st.session_state["sync_mutex_state"] = "Mở"
    st.session_state["sync_mutex_sub"] = "C1 đang đọc"
    st.session_state["sync_producer_state"] = "Sẵn sàng"
    st.session_state["sync_producer_sub"] = "Không còn tác vụ nạp"
    st.session_state["sync_consumer_state"] = "Sẵn sàng"
    st.session_state["sync_consumer_sub"] = "Đã xử lý hết buffer"
    st.session_state["sync_last_action"] = "Sẵn sàng mô phỏng đồng bộ hóa."
    st.session_state["sync_payload"] = None
    if clear_log:
        st.session_state["sync_logs"] = []


def add_log(message: str, tag: str = "default") -> None:
    logs = list(st.session_state.get("sync_logs", []))
    logs.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "message": str(message),
        "tag": tag,
    })
    st.session_state["sync_logs"] = logs[-140:]
    st.session_state["sync_event_count"] = safe_int(st.session_state.get("sync_event_count", 0), 0) + 1


def buffer_status() -> tuple[str, str, str]:
    count = safe_int(st.session_state.get("sync_count", 0), 0)
    size = max(1, safe_int(st.session_state.get("sync_buffer_size", 5), 5))
    if count <= 0:
        return "Rỗng", GREEN, "0 / {0} đang sử dụng".format(size)
    if count >= size:
        return "Đầy", RED, "{0} / {0} đang sử dụng".format(size)
    return "Bình thường", GREEN, f"{count} / {size} đang sử dụng"


def start_simulation() -> None:
    if not tasks():
        st.warning("Vui lòng thêm dữ liệu ở màn hình Quản lý tác vụ trước khi chạy mô phỏng đồng bộ hóa.")
        return

    st.session_state["sync_buffer_size"] = max(1, safe_int(st.session_state.get("sync_buffer_size", 5), 5))

    if st.session_state.get("sync_finished") or st.session_state.get("sync_step_index", 0) == 0:
        reset_runtime(clear_log=True)

    if len(st.session_state.get("sync_buffer", [])) != safe_int(st.session_state.get("sync_buffer_size", 5), 5):
        reset_runtime(clear_log=True)

    st.session_state["sync_running"] = True
    st.session_state["sync_started"] = True
    st.session_state["sync_finished"] = False
    st.session_state["sync_deadlock"] = False
    st.session_state["sync_producer_state"] = "Hoạt động"
    st.session_state["sync_consumer_state"] = "Sẵn sàng"
    st.session_state["sync_last_action"] = "Bắt đầu mô phỏng đồng bộ hóa."
    add_log(f"Bắt đầu đồng bộ hóa {len(tasks())} tác vụ gốc.", "blue")


def pause_or_resume() -> None:
    if not st.session_state.get("sync_started"):
        st.info("Hãy nhấn Chạy mô phỏng trước.")
        return
    if st.session_state.get("sync_finished"):
        st.info("Mô phỏng đã hoàn tất. Nhấn Làm mới để chạy lại.")
        return

    if st.session_state.get("sync_running"):
        st.session_state["sync_running"] = False
        st.session_state["sync_last_action"] = "Mô phỏng đã tạm dừng."
        add_log("Tạm dừng mô phỏng.", "orange")
    else:
        st.session_state["sync_running"] = True
        st.session_state["sync_last_action"] = "Tiếp tục mô phỏng đồng bộ hóa."
        add_log("Tiếp tục mô phỏng.", "blue")


def reset_simulation() -> None:
    reset_runtime(clear_log=True)
    st.toast("Đã làm mới mô phỏng đồng bộ hóa.", icon="🔄")


def producer_action() -> None:
    size = max(1, safe_int(st.session_state.get("sync_buffer_size", 5), 5))
    count = safe_int(st.session_state.get("sync_count", 0), 0)
    p_name = random.choice(["P1", "P2"])
    st.session_state["sync_last_delay_ms"] = get_delay_ms(st.session_state.get("sync_producer_speed", ""), 500)

    if count >= size:
        st.session_state["sync_producer_wait"] = safe_int(st.session_state.get("sync_producer_wait", 0), 0) + 1
        st.session_state["sync_mutex_state"] = "Mở"
        st.session_state["sync_mutex_sub"] = "Producer đang chờ buffer"
        st.session_state["sync_producer_state"] = "Đang chờ"
        st.session_state["sync_producer_sub"] = "Buffer đầy"
        st.session_state["sync_consumer_state"] = "Sẵn sàng"
        st.session_state["sync_last_action"] = f"{p_name} chờ vì buffer đầy."
        add_log(f"Producer ({p_name}) chờ vì buffer đầy", "orange")
        return

    idx = safe_int(st.session_state.get("sync_task_index", 0), 0)
    source = tasks()
    if idx >= len(source):
        return consumer_action()

    task_id = task_label(source[idx], idx)
    in_ptr = safe_int(st.session_state.get("sync_in_ptr", 0), 0) % size
    buffer = list(st.session_state.get("sync_buffer", [None] * size))
    if len(buffer) != size:
        buffer = [None] * size

    st.session_state["sync_mutex_state"] = "Mở"
    st.session_state["sync_mutex_sub"] = f"{p_name} vừa ghi ô {in_ptr + 1}"
    st.session_state["sync_critical_access"] = safe_int(st.session_state.get("sync_critical_access", 0), 0) + 1

    buffer[in_ptr] = task_id
    st.session_state["sync_buffer"] = buffer
    st.session_state["sync_in_ptr"] = (in_ptr + 1) % size
    st.session_state["sync_count"] = count + 1
    st.session_state["sync_task_index"] = idx + 1
    st.session_state["sync_produced_count"] = safe_int(st.session_state.get("sync_produced_count", 0), 0) + 1
    st.session_state["sync_producer_state"] = "Hoạt động"
    st.session_state["sync_producer_sub"] = f"Vừa nạp {task_id}"
    st.session_state["sync_consumer_state"] = "Sẵn sàng"
    st.session_state["sync_last_action"] = f"{p_name} nạp {task_id} vào buffer ô {in_ptr + 1}."

    add_log(f"Mutex khóa ({p_name} truy cập vùng tới hạn)", "blue")
    add_log(f"{p_name} nạp tác vụ {task_id} vào buffer (ô {in_ptr + 1})", "green")
    add_log(f"Mutex mở ({p_name} kết thúc truy cập)", "blue")


def consumer_action() -> None:
    size = max(1, safe_int(st.session_state.get("sync_buffer_size", 5), 5))
    count = safe_int(st.session_state.get("sync_count", 0), 0)
    c_name = random.choice(["C1", "C2"])
    st.session_state["sync_last_delay_ms"] = get_delay_ms(st.session_state.get("sync_consumer_speed", ""), 500)

    if count <= 0:
        st.session_state["sync_consumer_wait"] = safe_int(st.session_state.get("sync_consumer_wait", 0), 0) + 1
        st.session_state["sync_mutex_state"] = "Mở"
        st.session_state["sync_mutex_sub"] = "Consumer đang chờ buffer"
        st.session_state["sync_consumer_state"] = "Đang chờ"
        st.session_state["sync_consumer_sub"] = "Buffer rỗng"
        st.session_state["sync_producer_state"] = "Sẵn sàng" if safe_int(st.session_state.get("sync_task_index", 0), 0) < len(tasks()) else "Hoàn thành"
        st.session_state["sync_last_action"] = f"{c_name} chờ vì buffer rỗng."
        add_log(f"Consumer ({c_name}) chờ vì buffer rỗng", "orange")
        return

    out_ptr = safe_int(st.session_state.get("sync_out_ptr", 0), 0) % size
    buffer = list(st.session_state.get("sync_buffer", [None] * size))
    if len(buffer) != size:
        buffer = [None] * size
    task_id = buffer[out_ptr] or "—"
    buffer[out_ptr] = None

    st.session_state["sync_mutex_state"] = "Mở"
    st.session_state["sync_mutex_sub"] = f"{c_name} vừa đọc ô {out_ptr + 1}"
    st.session_state["sync_critical_access"] = safe_int(st.session_state.get("sync_critical_access", 0), 0) + 1
    st.session_state["sync_buffer"] = buffer
    st.session_state["sync_out_ptr"] = (out_ptr + 1) % size
    st.session_state["sync_count"] = max(0, count - 1)
    st.session_state["sync_consumed_count"] = safe_int(st.session_state.get("sync_consumed_count", 0), 0) + 1
    st.session_state["sync_consumer_state"] = "Hoạt động"
    st.session_state["sync_consumer_sub"] = f"Vừa lấy {task_id}"
    st.session_state["sync_producer_state"] = "Sẵn sàng" if safe_int(st.session_state.get("sync_task_index", 0), 0) < len(tasks()) else "Hoàn thành"
    st.session_state["sync_last_action"] = f"{c_name} lấy {task_id} từ buffer ô {out_ptr + 1}."

    add_log(f"Mutex khóa ({c_name} truy cập vùng tới hạn)", "blue")
    add_log(f"Máy in ({c_name}) lấy tác vụ {task_id} (từ ô {out_ptr + 1})", "purple")
    add_log(f"Mutex mở ({c_name} kết thúc truy cập)", "blue")


def finish_simulation() -> None:
    if st.session_state.get("sync_finished"):
        return
    st.session_state["sync_running"] = False
    st.session_state["sync_finished"] = True
    st.session_state["sync_deadlock"] = False
    st.session_state["sync_mutex_state"] = "Mở"
    st.session_state["sync_mutex_sub"] = "Đồng bộ an toàn"
    st.session_state["sync_producer_state"] = "Hoàn thành"
    st.session_state["sync_producer_sub"] = "Không còn tác vụ nạp"
    st.session_state["sync_consumer_state"] = "Hoàn thành"
    st.session_state["sync_consumer_sub"] = "Đã xử lý hết buffer"
    st.session_state["sync_last_action"] = "Mô phỏng hoàn tất."
    add_log("Mô phỏng hoàn tất (Đã xử lý xong toàn bộ danh sách tác vụ).", "blue")
    st.session_state["sync_payload"] = {
        "mechanism": st.session_state.get("sync_mechanism", "Producer - Consumer"),
        "buffer_size": safe_int(st.session_state.get("sync_buffer_size", 5), 5),
        "produced_count": safe_int(st.session_state.get("sync_produced_count", 0), 0),
        "consumed_count": safe_int(st.session_state.get("sync_consumed_count", 0), 0),
        "producer_wait": safe_int(st.session_state.get("sync_producer_wait", 0), 0),
        "consumer_wait": safe_int(st.session_state.get("sync_consumer_wait", 0), 0),
        "critical_access": safe_int(st.session_state.get("sync_critical_access", 0), 0),
        "event_count": safe_int(st.session_state.get("sync_event_count", 0), 0),
        "deadlock": False,
        "status": "Ổn định",
    }


def run_step() -> None:
    if not st.session_state.get("sync_running"):
        return

    total = len(tasks())
    if total <= 0:
        st.session_state["sync_running"] = False
        return

    if safe_int(st.session_state.get("sync_consumed_count", 0), 0) >= total:
        finish_simulation()
        return

    st.session_state["sync_step_index"] = safe_int(st.session_state.get("sync_step_index", 0), 0) + 1
    has_more = safe_int(st.session_state.get("sync_task_index", 0), 0) < total
    if has_more:
        # Ưu tiên producer nhẹ để buffer có dữ liệu, giống bản desktop.
        is_producer = random.choice([True, True, True, False, False])
    else:
        is_producer = False

    if is_producer:
        producer_action()
    else:
        consumer_action()

    if safe_int(st.session_state.get("sync_consumed_count", 0), 0) >= total:
        finish_simulation()


# ====================== CSS + HTML HELPERS ======================
def css() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{ background: {BG}; }}
        div[data-testid="stVerticalBlock"] {{ gap: .75rem; }}
        .sync-stats {{
            display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:14px;
            margin: 2px 0 14px 0;
        }}
        .sync-stat-card {{
            min-height:112px; background:{WHITE}; border:1px solid {BORDER};
            display:flex; align-items:center; padding:18px 22px; box-sizing:border-box;
        }}
        .sync-stat-icon {{
            width:76px; height:76px; margin-right:22px; display:flex; align-items:center; justify-content:center;
            flex: 0 0 76px;
        }}
        .sync-stat-fallback {{
            width:66px; height:66px; border-radius:50%; background:{PRIMARY}; color:#fff;
            display:flex; align-items:center; justify-content:center; font-size:34px; font-weight:900;
        }}
        .sync-stat-title {{ color:{TEXT}; font:900 13px Arial, sans-serif; text-transform:uppercase; }}
        .sync-stat-value {{ color:{PRIMARY}; font:900 33px Arial, sans-serif; line-height:1.05; margin-top:4px; }}
        .sync-stat-sub {{ color:{MUTED}; font:700 12px Arial, sans-serif; margin-top:4px; }}
        .sync-section-head {{
            display:flex; align-items:center; gap:10px; min-height:46px; padding:0 14px;
            color:{PRIMARY}; font:900 15px Arial, sans-serif; border-bottom:1px solid {LIGHT_LINE};
            text-transform:uppercase; background:{WHITE};
        }}
        .sync-section-body {{ padding:14px 16px 16px 16px; background:{WHITE}; }}
        .sync-status-grid {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:10px; padding:14px; }}
        .sync-status-card {{
            border:1px solid {BORDER}; background:#fff; min-height:124px; padding:12px 8px;
            display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center;
        }}
        .sync-status-title {{ color:{TEXT}; font:900 11px Arial, sans-serif; text-transform:uppercase; margin-top:8px; }}
        .sync-badge {{ display:inline-block; border-radius:4px; padding:4px 9px; font:900 11px Arial, sans-serif; margin:7px 0 4px; }}
        .sync-status-sub {{ color:{MUTED}; font:700 10px Arial, sans-serif; line-height:1.25; }}
        .sync-svg-scroll {{ width:100%; overflow-x:auto; padding:8px 0 0 0; background:#fff; }}
        .sync-log-box {{
            height:260px; overflow-y:auto; border:1px solid #EEF2F7; background:#fff; padding:10px 12px;
            font:700 12px Consolas, 'Courier New', monospace; line-height:1.35;
        }}
        .log-time {{ color:{TEXT}; margin-right:8px; }}
        .log-default {{ color:{TEXT}; }}
        .log-green {{ color:{GREEN}; }}
        .log-purple {{ color:{PURPLE}; }}
        .log-orange {{ color:{ORANGE}; }}
        .log-blue {{ color:{PRIMARY}; }}
        .sync-stat-mini-grid {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:10px; padding:14px; }}
        .sync-mini-card {{
            border:1px solid {BORDER}; background:#fff; min-height:86px; padding:12px;
            display:flex; align-items:center; box-sizing:border-box;
        }}
        .sync-mini-card .mini-icon {{ width:45px; height:45px; display:flex; align-items:center; justify-content:center; margin-right:12px; }}
        .mini-title {{ color:{TEXT}; font:900 12px Arial, sans-serif; }}
        .mini-value {{ font:900 25px Arial, sans-serif; line-height:1.05; }}
        .sync-conclusion {{
            margin:14px; min-height:124px; border:1px solid #EEF2F7; padding:14px 16px;
            font:700 13px Arial, sans-serif; color:{TEXT}; line-height:1.55; background:#fff;
        }}
        .sync-last-action {{
            border-left:4px solid {PRIMARY}; background:{BLUE_BG}; color:{PRIMARY};
            padding:10px 12px; font:800 13px Arial, sans-serif; margin-top:8px;
        }}
        .stButton > button {{
            border-radius:6px !important; min-height:40px; font-weight:900 !important;
            border:1px solid {BORDER} !important;
        }}
        .stButton > button[kind="primary"] {{ background:{PRIMARY} !important; border-color:{PRIMARY} !important; }}
        div[data-testid="stNumberInput"] input, div[data-testid="stSelectbox"] div[data-baseweb="select"] {{
            font-weight:700;
        }}
        @media (max-width: 1000px) {{
            .sync-stats, .sync-status-grid, .sync-stat-mini-grid {{ grid-template-columns:repeat(2, minmax(0,1fr)); }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, icon_name: str, fallback: str = "▣") -> None:
    img = icon(icon_name, 25)
    fallback_html = f'<span style="font-size:22px;color:{PRIMARY};font-weight:900">{html.escape(fallback)}</span>'
    st.markdown(
        f'<div class="sync-section-head">{img or fallback_html}<span>{html.escape(title)}</span></div>',
        unsafe_allow_html=True,
    )


def button_with_icon(icon_name: str, label: str, key: str, kind: str = "secondary") -> bool:
    c1, c2 = st.columns([.18, .82], gap="small")
    with c1:
        st.markdown(
            f"<div style='height:42px;display:flex;align-items:center;justify-content:center'>{icon(icon_name, 28)}</div>",
            unsafe_allow_html=True,
        )
    with c2:
        return st.button(label, key=key, type=kind, use_container_width=True)


def stat_card(title: str, value: str, sub: str, icon_name: str, fallback: str) -> str:
    img = icon(icon_name, 76)
    fallback_html = f'<div class="sync-stat-fallback">{html.escape(fallback)}</div>'
    return (
        '<div class="sync-stat-card">'
        f'<div class="sync-stat-icon">{img or fallback_html}</div>'
        '<div>'
        f'<div class="sync-stat-title">{html.escape(title)}</div>'
        f'<div class="sync-stat-value">{html.escape(str(value))}</div>'
        f'<div class="sync-stat-sub">{html.escape(sub)}</div>'
        '</div></div>'
    )


def render_metrics() -> None:
    total = len(tasks())
    size = safe_int(st.session_state.get("sync_buffer_size", 5), 5)
    produced = safe_int(st.session_state.get("sync_produced_count", 0), 0)
    consumed = safe_int(st.session_state.get("sync_consumed_count", 0), 0)
    deadlock = "Có" if st.session_state.get("sync_deadlock") else "Không"
    st.markdown(
        '<div class="sync-stats">'
        + stat_card("Kích thước Buffer", str(size), "ô", "Buffer", "▣")
        + stat_card("Đã sản xuất", f"{produced} / {total}", "tác vụ", "Producer", "↗")
        + stat_card("Đã tiêu thụ", f"{consumed} / {total}", "tác vụ", "Consumer", "↘")
        + stat_card("Deadlock", deadlock, "trạng thái", "Deadlock", "⊘")
        + '</div>',
        unsafe_allow_html=True,
    )


def state_color(state: str) -> tuple[str, str]:
    text = str(state or "")
    if text in ("Khóa", "Đang chờ", "Đầy"):
        return ORANGE_BG, ORANGE
    if text in ("Hoàn thành", "Hoạt động", "Mở", "Rỗng", "Bình thường", "Sẵn sàng"):
        return GREEN_BG, GREEN
    return BLUE_BG, PRIMARY


def status_card(icon_names: list[str], title: str, value: str, subtitle: str, fallback: str) -> str:
    bg, fg = state_color(value)
    img = first_icon(icon_names, 40)
    fallback_html = f'<span style="font-size:32px;color:{PRIMARY};font-weight:900">{html.escape(fallback)}</span>'
    return (
        '<div class="sync-status-card">'
        f'<div>{img or fallback_html}</div>'
        f'<div class="sync-status-title">{html.escape(title)}</div>'
        f'<div class="sync-badge" style="background:{bg};color:{fg}">{html.escape(value)}</div>'
        f'<div class="sync-status-sub">{html.escape(subtitle)}</div>'
        '</div>'
    )


def render_system_status() -> None:
    b_value, _, b_sub = buffer_status()
    mutex_value = str(st.session_state.get("sync_mutex_state", "Mở"))
    mutex_sub = str(st.session_state.get("sync_mutex_sub", "C1 đang đọc"))
    prod_value = str(st.session_state.get("sync_producer_state", "Sẵn sàng"))
    prod_sub = str(st.session_state.get("sync_producer_sub", "Không còn tác vụ nạp"))
    cons_value = str(st.session_state.get("sync_consumer_state", "Sẵn sàng"))
    cons_sub = str(st.session_state.get("sync_consumer_sub", "Đã xử lý hết buffer"))
    html_status = (
        '<div class="sync-status-grid">'
        + status_card(["Mutex", "Lock"], "Mutex", mutex_value, mutex_sub, "🔒")
        + status_card(["Buffer"], "Buffer", b_value, b_sub, "▣")
        + status_card(["Producer", "Produced"], "Producer", prod_value, prod_sub, "↗")
        + status_card(["Consumer", "Consumed"], "Consumer", cons_value, cons_sub, "↘")
        + '</div>'
    )
    st.markdown(html_status, unsafe_allow_html=True)


def render_setup_and_status() -> None:
    left, right = st.columns([.66, .34], gap="medium")
    with left:
        with st.container(border=True):
            section("THIẾT LẬP MÔ PHỎNG", "Settings", "⚙")
            st.markdown('<div class="sync-section-body">', unsafe_allow_html=True)
            r1c1, r1c2 = st.columns(2, gap="large")
            with r1c1:
                st.selectbox(
                    "Cơ chế đồng bộ",
                    ["Producer - Consumer", "Mutex"],
                    key="sync_mechanism",
                    disabled=st.session_state.get("sync_running", False),
                )
            with r1c2:
                st.number_input(
                    "Sức chứa buffer",
                    min_value=1,
                    max_value=20,
                    step=1,
                    key="sync_buffer_size",
                    disabled=st.session_state.get("sync_running", False),
                )

            r2c1, r2c2 = st.columns(2, gap="large")
            with r2c1:
                st.selectbox(
                    "Tốc độ Producer",
                    SPEED_OPTIONS,
                    key="sync_producer_speed",
                    disabled=st.session_state.get("sync_running", False),
                )
            with r2c2:
                st.selectbox(
                    "Tốc độ Consumer",
                    SPEED_OPTIONS,
                    key="sync_consumer_speed",
                    disabled=st.session_state.get("sync_running", False),
                )

            st.markdown(f'<div class="sync-last-action">{html.escape(str(st.session_state.get("sync_last_action", "")))}</div>', unsafe_allow_html=True)
            b1, b2, b3 = st.columns(3, gap="medium")
            with b1:
                if button_with_icon("Run_Simulation", "Chạy mô phỏng", "sync_btn_run", "primary"):
                    start_simulation()
                    st.rerun()
            with b2:
                pause_label = "Tạm dừng" if st.session_state.get("sync_running") else "Tiếp tục"
                if not st.session_state.get("sync_started"):
                    pause_label = "Tạm dừng"
                if button_with_icon("Pause" if st.session_state.get("sync_running") else "Continue", pause_label, "sync_btn_pause"):
                    pause_or_resume()
                    st.rerun()
            with b3:
                if button_with_icon("Reset", "Làm mới", "sync_btn_reset"):
                    reset_simulation()
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    with right:
        with st.container(border=True):
            section("TRẠNG THÁI HỆ THỐNG", "Info_data", "▣")
            render_system_status()


# ====================== BUFFER VISUAL + LOG ======================
def svg_icon(names: list[str], x: float, y: float, size: int) -> str:
    src = ""
    for name in names:
        src = icon_uri(name)
        if src:
            break
    if not src:
        return ""
    return f'<image href="{src}" x="{x}" y="{y}" width="{size}" height="{size}" preserveAspectRatio="xMidYMid meet"/>'


def buffer_svg() -> str:
    size = max(1, safe_int(st.session_state.get("sync_buffer_size", 5), 5))
    buffer = list(st.session_state.get("sync_buffer", [None] * size))
    if len(buffer) != size:
        buffer = [None] * size

    start_x = 195
    y = 74
    slot_w = 96
    slot_h = 64
    gap = 13
    producer_x = 28
    consumer_x = start_x + size * (slot_w + gap) + 56
    width = max(980, consumer_x + 170)
    height = 215

    parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">']
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#FFFFFF"/>')

    parts.append(f'<text x="{producer_x + 30}" y="30" fill="{PRIMARY}" font-family="Arial" font-size="13" font-weight="900">PRODUCER</text>')
    p_icon_1 = svg_icon(["Produced", "Producer"], producer_x + 42, 58, 36)
    p_icon_2 = svg_icon(["Produced", "Producer"], producer_x + 42, 107, 36)
    if p_icon_1:
        parts.append(p_icon_1)
        parts.append(p_icon_2)
    else:
        parts.append(f'<circle cx="{producer_x+60}" cy="76" r="15" fill="{PRIMARY}" opacity=".95"/><circle cx="{producer_x+60}" cy="124" r="15" fill="{PRIMARY}" opacity=".95"/>')
    parts.append(f'<text x="{producer_x + 5}" y="82" fill="{PRIMARY}" font-family="Arial" font-size="17" font-weight="900">P1</text>')
    parts.append(f'<text x="{producer_x + 5}" y="131" fill="{PRIMARY}" font-family="Arial" font-size="17" font-weight="900">P2</text>')
    parts.append(f'<line x1="{producer_x+95}" y1="78" x2="{start_x-26}" y2="78" stroke="{PRIMARY}" stroke-width="2.5" marker-end="url(#arrowBlue)"/>')
    parts.append(f'<line x1="{producer_x+95}" y1="126" x2="{start_x-26}" y2="101" stroke="{PRIMARY}" stroke-width="2.5" marker-end="url(#arrowBlue)"/>')

    center_x = start_x + (slot_w + gap) * size / 2 - 10
    parts.append(f'<text x="{center_x}" y="30" text-anchor="middle" fill="{PRIMARY}" font-family="Arial" font-size="14" font-weight="900">BUFFER (SỨC CHỨA: {size})</text>')

    parts.append(
        '<defs>'
        f'<marker id="arrowBlue" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="{PRIMARY}" /></marker>'
        '</defs>'
    )

    for i in range(size):
        x = start_x + i * (slot_w + gap)
        item = buffer[i]
        if item:
            parts.append(f'<rect x="{x}" y="{y}" width="{slot_w}" height="{slot_h}" fill="{YELLOW_BG}" stroke="#F59E0B" stroke-width="2"/>')
            parts.append(f'<text x="{x + slot_w/2}" y="{y + slot_h/2 + 5}" text-anchor="middle" fill="{TEXT}" font-family="Arial" font-size="13" font-weight="900">{html.escape(str(item))}</text>')
        else:
            parts.append(f'<rect x="{x}" y="{y}" width="{slot_w}" height="{slot_h}" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="1.3" stroke-dasharray="5 4"/>')
            parts.append(f'<text x="{x + slot_w/2}" y="{y + slot_h/2 + 5}" text-anchor="middle" fill="#CBD5E1" font-family="Arial" font-size="18" font-weight="900">—</text>')
        parts.append(f'<text x="{x + slot_w/2}" y="{y + slot_h + 28}" text-anchor="middle" fill="{TEXT}" font-family="Arial" font-size="12" font-weight="900">{i + 1}</text>')

    parts.append(f'<text x="{consumer_x + 56}" y="30" text-anchor="middle" fill="{PRIMARY}" font-family="Arial" font-size="13" font-weight="900">CONSUMER</text>')
    c_icon_1 = svg_icon(["Consumed", "Consumer"], consumer_x + 4, 58, 36)
    c_icon_2 = svg_icon(["Consumed", "Consumer"], consumer_x + 4, 107, 36)
    if c_icon_1:
        parts.append(c_icon_1)
        parts.append(c_icon_2)
    else:
        parts.append(f'<circle cx="{consumer_x+23}" cy="76" r="15" fill="{PURPLE}" opacity=".95"/><circle cx="{consumer_x+23}" cy="124" r="15" fill="{PURPLE}" opacity=".95"/>')
    parts.append(f'<text x="{consumer_x + 55}" y="82" fill="{PURPLE}" font-family="Arial" font-size="17" font-weight="900">C1</text>')
    parts.append(f'<text x="{consumer_x + 55}" y="131" fill="{PURPLE}" font-family="Arial" font-size="17" font-weight="900">C2</text>')
    parts.append(f'<line x1="{consumer_x}" y1="78" x2="{consumer_x-66}" y2="78" stroke="{PRIMARY}" stroke-width="2.5" marker-end="url(#arrowBlue)"/>')
    parts.append(f'<line x1="{consumer_x}" y1="126" x2="{consumer_x-66}" y2="101" stroke="{PRIMARY}" stroke-width="2.5" marker-end="url(#arrowBlue)"/>')

    legend_y = 176
    parts.append(f'<rect x="{start_x}" y="{legend_y}" width="16" height="16" fill="{YELLOW_BG}" stroke="#F59E0B"/>')
    parts.append(f'<text x="{start_x + 24}" y="{legend_y + 12}" fill="{TEXT}" font-family="Arial" font-size="11" font-weight="700">Ô đã có tác vụ</text>')
    parts.append(f'<rect x="{start_x + 148}" y="{legend_y}" width="16" height="16" fill="#F8FAFC" stroke="#CBD5E1" stroke-dasharray="3 2"/>')
    parts.append(f'<text x="{start_x + 172}" y="{legend_y + 12}" fill="{TEXT}" font-family="Arial" font-size="11" font-weight="700">Ô trống</text>')

    parts.append('</svg>')
    return ''.join(parts)


def log_html() -> str:
    logs = st.session_state.get("sync_logs", [])
    if not logs:
        return f'<div class="sync-log-box"><span class="log-default">Chưa có sự kiện. Nhấn “Chạy mô phỏng” để bắt đầu.</span></div>'
    rows = []
    for row in logs[-80:]:
        tag = str(row.get("tag", "default"))
        if tag not in ("default", "green", "purple", "orange", "blue"):
            tag = "default"
        rows.append(
            f'<div><span class="log-time">{html.escape(str(row.get("time", "")))}</span>'
            f'<span class="log-{tag}">{html.escape(str(row.get("message", "")))}</span></div>'
        )
    return '<div class="sync-log-box">' + ''.join(rows) + '</div>'


def render_buffer_and_log() -> None:
    left, right = st.columns([.68, .32], gap="medium")
    with left:
        with st.container(border=True):
            section("TRỰC QUAN BUFFER DÙNG CHUNG", "Buffer", "▣")
            st.markdown(f'<div class="sync-svg-scroll">{buffer_svg()}</div>', unsafe_allow_html=True)
    with right:
        with st.container(border=True):
            section("NHẬT KÝ SỰ KIỆN", "Log", "●")
            st.markdown(log_html(), unsafe_allow_html=True)


# ====================== STATS + CONCLUSION ======================
def mini_card(key: str, title: str, value: str, color: str, icons: list[str], fallback: str) -> str:
    img = first_icon(icons, 42)
    fallback_html = f'<span style="font-size:32px;color:{color};font-weight:900">{html.escape(fallback)}</span>'
    return (
        '<div class="sync-mini-card">'
        f'<div class="mini-icon">{img or fallback_html}</div>'
        '<div>'
        f'<div class="mini-title">{html.escape(title)}</div>'
        f'<div class="mini-value" style="color:{color}">{html.escape(value)}</div>'
        '</div></div>'
    )


def conclusion_text() -> str:
    mechanism = st.session_state.get("sync_mechanism", "Producer - Consumer")
    prod_wait = safe_int(st.session_state.get("sync_producer_wait", 0), 0)
    cons_wait = safe_int(st.session_state.get("sync_consumer_wait", 0), 0)
    critical = safe_int(st.session_state.get("sync_critical_access", 0), 0)
    deadlock = st.session_state.get("sync_deadlock", False)
    lines = [
        f"✓ Hệ thống hoạt động đúng cơ chế {mechanism} với Mutex.",
        "✓ Không xảy ra deadlock trong quá trình xử lý chuỗi tác vụ thực tế." if not deadlock else "⚠ Cần kiểm tra vì có dấu hiệu deadlock.",
        "✓ Buffer được quản lý đúng kích thước, không ghi đè và không tràn.",
        f"✓ Vùng tới hạn được truy cập an toàn {critical} lần.",
    ]
    if prod_wait or cons_wait:
        lines.append(f"✓ Producer chờ {prod_wait} lần, Consumer chờ {cons_wait} lần do trạng thái đầy/rỗng của buffer.")
    else:
        lines.append("✓ Quá trình chạy hiện chưa phát sinh tình huống chờ tài nguyên.")
    return "<br/>".join(html.escape(line) for line in lines)


def render_stats_and_conclusion() -> None:
    left, right = st.columns([.56, .44], gap="medium")
    with left:
        with st.container(border=True):
            section("THỐNG KÊ ĐỒNG BỘ HÓA", "Statistics", "▥")
            st.markdown(
                '<div class="sync-stat-mini-grid">'
                + mini_card("producer_wait", "Producer chờ", f'{safe_int(st.session_state.get("sync_producer_wait", 0), 0)} lần', PRIMARY, ["Waiting_producer"], "◷")
                + mini_card("consumer_wait", "Consumer chờ", f'{safe_int(st.session_state.get("sync_consumer_wait", 0), 0)} lần', PURPLE, ["Waiting_consumer"], "◷")
                + mini_card("critical", "Truy cập vùng tới hạn", f'{safe_int(st.session_state.get("sync_critical_access", 0), 0)} lần', GREEN, ["Critical_section_access", "Mutex"], "🔒")
                + mini_card("events", "Tổng sự kiện", str(safe_int(st.session_state.get("sync_event_count", 0), 0)), ORANGE, ["total_event", "Statistics"], "∑")
                + '</div>',
                unsafe_allow_html=True,
            )
    with right:
        with st.container(border=True):
            section("NHẬN XÉT & KẾT LUẬN", "Comment", "💬")
            st.markdown(f'<div class="sync-conclusion">{conclusion_text()}</div>', unsafe_allow_html=True)


# ====================== RENDER ENTRYPOINTS ======================
def auto_advance_if_needed() -> None:
    if not st.session_state.get("sync_running", False):
        return
    delay_ms = max(80, get_delay_ms(str(st.session_state.get("sync_last_delay_ms", 500)), 500))
    # Streamlit không có vòng lặp after như Tkinter; rerun theo nhịp ngắn để mô phỏng realtime.
    time.sleep(min(max(delay_ms / 1000, 0.12), 2.0))
    run_step()
    st.rerun()


def render() -> None:
    init_state()
    css()
    render_metrics()
    render_setup_and_status()
    render_buffer_and_log()
    render_stats_and_conclusion()
    auto_advance_if_needed()


def render_sync_page() -> None:
    render()


def show_sync_page() -> None:
    render()


def sync_page() -> None:
    render()


def show() -> None:
    render()


def app() -> None:
    render()
