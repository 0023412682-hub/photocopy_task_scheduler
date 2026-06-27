from __future__ import annotations

import base64
import copy
import html
import mimetypes
import textwrap
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import quote

import streamlit as st

from web.styles import (
    ACCENT_COLOR,
    BORDER_COLOR,
    MUTED_TEXT,
    PRIMARY_COLOR,
    TEXT_COLOR,
    WHITE_COLOR,
)


try:
    from PIL import Image

    PIL_AVAILABLE = True
except Exception:
    Image = None
    PIL_AVAILABLE = False


ALGORITHM_OPTIONS = ["FCFS", "SJF", "Priority", "Round Robin"]


# =========================================================
# PATHS
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]

ICON_DIR_CANDIDATES = [
    PROJECT_ROOT / "assets" / "icons",
    Path.cwd() / "assets" / "icons",
    Path.cwd() / "web_photocopy_task_scheduler" / "assets" / "icons",
    Path("/Users/mac/web_photocopy_task_scheduler/assets/icons"),
]

ICON_DIR = next(
    (path for path in ICON_DIR_CANDIDATES if path.exists()),
    ICON_DIR_CANDIDATES[0],
)


ICON_ALIASES: dict[str, list[str]] = {
    # Sidebar/header
    "Home.png": ["Home.png", "home.png"],
    "Task_List.png": ["Task_List.png", "Task_List.PNG", "Task List.png", "Manager.png"],
    "Simulation_Algorithm.png": [
        "Simulation_Algorithm.png",
        "Simulation_Algorithm.PNG",
        "Simulation.png",
        "Run.png",
    ],
    "Memory.png": ["Memory.png", "Memory.PNG"],
    "Sync.png": ["Sync.png", "Sync.PNG"],
    "Compare_Algorithms.png": [
        "Compare_Algorithms.png",
        "Comparison_Algorithm.png",
        "Compare.png",
        "Compare.PNG",
    ],
    "Report.png": ["Report.png", "Report.PNG", "H_Report.png", "Export PDF.png", "PDF.png"],
    "khoa.jpg": ["khoa.jpg", "khoa.png", "Khoa.jpg", "Khoa.png"],
    "school.png": ["school.png", "school.jpg", "School.png", "School.jpg", "DThU.png"],

    # Home common icons
    "Fast.png": ["Fast.png", "fast.png", "Speed.png", "Action.png"],
    "Process.png": ["Process.png", "process.png", "Workflow.png"],
    "Information.png": ["Information.png", "Information.PNG", "Info.png", "info.png"],
    "Simulation.png": [
        "Simulation.png",
        "Simulation.PNG",
        "Simulation_Algorithm.png",
        "Simulation_Algorithm.PNG",
        "Run.png",
    ],
    "Comparison_Algorithm.png": [
        "Comparison_Algorithm.png",
        "Compare_Algorithms.png",
        "Compare.png",
        "Compare.PNG",
    ],
    "Manager.png": ["Manager.png", "Task_List.png", "Task List.png"],
    "H_Report.png": ["H_Report.png", "Export PDF.png", "Report.png", "PDF.png"],

    # Hero flow
    "Customer.png": ["Customer.png", "Customer.PNG", "Khach_hang.png", "Client.png", "User.png"],
    "HERO_queue.png": ["HERO_queue.png", "Hero_queue.png", "Queue.png", "queue.png", "Hang_doi.png"],
    "Photocopier.png": ["Photocopier.png", "Photocopier.PNG", "Printer.png", "Photocopy.png", "Machine.png"],
    "Done.png": ["Done.png", "Done.PNG", "Complete.png", "Finished.png", "Task_Done.png"],

    # Info / process
    "Topic.png": ["Topic.png", "Report.png", "Document.png", "Information.png"],
    "Field.png": ["Field.png", "Book.png", "Open_Book.png", "Information.png"],
    "Target.png": ["Target.png", "Goal.png", "Objective.png", "Information.png"],
    "Data.png": ["Data.png", "Database.png", "DataBase.png", "Information.png"],
    "Import_task.png": ["Import_task.png", "Task_Add.png", "Add_Task.png", "Task_List.png"],
    "Choose_algorithm.png": ["Choose_algorithm.png", "Algorithm.png", "List.png", "Process.png"],
    "Process_result.png": ["Process_result.png", "Result.png", "Chart.png", "Report.png"],

    # Algorithms
    "FCFS.png": ["FCFS.png", "fcfs.png"],
    "SJF.png": ["SJF.png", "sjf.png"],
    "Priority.png": ["Priority.png", "priority.png"],
    "Round_Robin.png": ["Round_Robin.png", "Round Robin.png", "RR.png", "RoundRobin.png"],
}


PAGE_KEY_ALIASES = {
    "home": "home",
    "trang chủ": "home",
    "trang chu": "home",
    "task": "task",
    "tasks": "task",
    "danh sách tác vụ": "task",
    "danh sach tac vu": "task",
    "mô phỏng thuật toán": "simulation",
    "mo phong thuat toan": "simulation",
    "simulation": "simulation",
    "bộ nhớ": "memory",
    "bo nho": "memory",
    "memory": "memory",
    "đồng bộ hóa": "sync",
    "dong bo hoa": "sync",
    "sync": "sync",
    "so sánh thuật toán": "comparison",
    "so sanh thuat toan": "comparison",
    "comparison": "comparison",
    "compare": "comparison",
    "báo cáo": "report",
    "bao cao": "report",
    "report": "report",
}


# =========================================================
# HTML RENDER HELPER
# =========================================================
def _clean_html(html_text: str) -> str:
    """
    Làm sạch HTML trước khi đưa vào st.markdown.

    Lỗi đang gặp là do nhiều chuỗi HTML trong f-string còn thụt đầu dòng >= 4 dấu cách.
    Markdown xem các dòng đó là code block nên Streamlit hiện nguyên <div> ra màn hình.
    Vì vậy ngoài textwrap.dedent, cần lstrip từng dòng để không dòng HTML nào
    bị Markdown hiểu nhầm là code.
    """
    dedented = textwrap.dedent(str(html_text)).strip()
    return "\n".join(line.lstrip() for line in dedented.splitlines())


def render_html(html_text: str, *, sidebar: bool = False) -> None:
    """
    Render HTML an toàn cho Streamlit.
    Dùng hàm này để tránh lỗi HTML bị hiện thô do Markdown nhận nhầm khối code.
    """
    target = st.sidebar if sidebar else st
    target.markdown(_clean_html(html_text), unsafe_allow_html=True)


# =========================================================
# ICON HELPERS
# =========================================================
def normalize_icon_name(value: str | Path | None) -> str:
    if value is None:
        return ""

    text = str(value).strip().replace("\\", "/")
    return text.split("/")[-1]


def resolve_icon_path(filename: str | Path | None) -> Path | None:
    """
    Tìm icon trong assets/icons.

    Có hỗ trợ:
    - tên file trực tiếp;
    - đường dẫn tuyệt đối;
    - thiếu đuôi .png/.jpg;
    - alias một số icon hay đổi tên;
    - tìm không phân biệt hoa thường.
    """
    if filename is None:
        return None

    raw = Path(str(filename))

    if raw.is_absolute() and raw.exists():
        return raw

    name = normalize_icon_name(filename)
    if not name:
        return None

    candidates: list[str] = [name]

    if name in ICON_ALIASES:
        candidates.extend(ICON_ALIASES[name])

    stem = Path(name).stem
    suffix = Path(name).suffix

    if not suffix:
        for ext in [".png", ".jpg", ".jpeg", ".webp"]:
            candidates.append(stem + ext)

    for icon_dir in ICON_DIR_CANDIDATES:
        if not icon_dir.exists():
            continue

        for candidate in candidates:
            direct_path = icon_dir / candidate
            if direct_path.exists():
                return direct_path

        lower_map = {
            item.name.lower(): item
            for item in icon_dir.iterdir()
            if item.is_file()
        }

        for candidate in candidates:
            matched = lower_map.get(candidate.lower())
            if matched and matched.exists():
                return matched

    return None


def _guess_mime_type(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(path.name)
    return mime_type or "image/png"


@st.cache_data(show_spinner=False)
def _file_to_data_uri(path_text: str) -> str:
    path = Path(path_text)
    mime_type = _guess_mime_type(path)
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = str(color).strip()

    if color.startswith("#"):
        color = color[1:]

    if len(color) == 3:
        color = "".join(ch * 2 for ch in color)

    return (
        int(color[0:2], 16),
        int(color[2:4], 16),
        int(color[4:6], 16),
    )


def _normalize_size(size: int | tuple[int, int] | None) -> tuple[int, int] | None:
    if size is None:
        return None

    if isinstance(size, int):
        return size, size

    if len(size) != 2:
        return None

    return int(size[0]), int(size[1])


@st.cache_data(show_spinner=False)
def _processed_icon_to_data_uri(
    path_text: str,
    width: int,
    height: int,
    color: str | None,
) -> str:
    """
    Resize/tint icon bằng alpha channel.
    Dùng cho sidebar để icon active màu xanh, inactive màu trắng.
    """
    path = Path(path_text)

    if not PIL_AVAILABLE:
        return _file_to_data_uri(path_text)

    image = Image.open(path).convert("RGBA")

    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        image = image.crop(bbox)

    try:
        resample_filter = Image.Resampling.LANCZOS
    except AttributeError:
        resample_filter = Image.LANCZOS

    image.thumbnail((width, height), resample_filter)

    canvas = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    x = (width - image.width) // 2
    y = (height - image.height) // 2

    if color:
        r, g, b = _hex_to_rgb(color)
        tinted = Image.new("RGBA", image.size, (r, g, b, 0))
        tinted.putalpha(image.getchannel("A"))
        canvas.paste(tinted, (x, y), tinted)
    else:
        canvas.paste(image, (x, y), image)

    buffer = BytesIO()
    canvas.save(buffer, format="PNG")

    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def load_icon(
    filename: str | Path | None,
    size: int | tuple[int, int] | None = None,
    color: str | None = None,
) -> str | None:
    path = resolve_icon_path(filename)
    if path is None:
        return None

    normalized_size = _normalize_size(size)

    if normalized_size:
        width, height = normalized_size
        if color or PIL_AVAILABLE:
            return _processed_icon_to_data_uri(str(path), width, height, color)

    return _file_to_data_uri(str(path))


def icon_html(
    filename: str | Path | None,
    size: int | tuple[int, int] = 24,
    color: str | None = None,
    class_name: str = "",
    alt: str = "",
    fallback: str = "●",
) -> str:
    """
    Trả về thẻ <img> dùng được trong st.markdown(..., unsafe_allow_html=True).

    Cách gọi đúng:
        icon_html("Fast.png", size=24, fallback="⚡")
    """
    normalized_size = _normalize_size(size) or (24, 24)
    width, height = normalized_size

    uri = load_icon(
        filename=filename,
        size=(width, height),
        color=color,
    )

    safe_class = html.escape(class_name or "")
    safe_alt = html.escape(alt or normalize_icon_name(filename))
    safe_fallback = html.escape(str(fallback))

    if uri is None:
        return (
            f'<span class="{safe_class} icon-fallback" '
            f'style="width:{width}px;height:{height}px;">'
            f"{safe_fallback}</span>"
        )

    return (
        f'<img src="{uri}" alt="{safe_alt}" class="{safe_class}" '
        f'style="width:{width}px;height:{height}px;object-fit:contain;" />'
    )


get_icon_uri = load_icon
image_to_base64 = load_icon


# =========================================================
# NAVIGATION HELPERS
# =========================================================
def _safe_rerun() -> None:
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def normalize_page_key(page_key: str) -> str:
    raw = str(page_key or "").strip()
    normalized = raw.lower()
    return PAGE_KEY_ALIASES.get(normalized, raw)


def go_to_page(page_key: str) -> None:
    page = normalize_page_key(page_key)
    st.session_state["current_page"] = page
    st.session_state["_navigate_to_page"] = page

    try:
        st.query_params["page"] = page
    except Exception:
        try:
            st.experimental_set_query_params(page=page)
        except Exception:
            pass

    _safe_rerun()


def set_footer_status(text: str) -> None:
    st.session_state["footer_status"] = str(text)


def ensure_session_state() -> None:
    """
    Khởi tạo các khóa session_state dùng chung cho toàn bộ app.
    Không ghi đè dữ liệu đã có.
    """
    defaults: dict[str, Any] = {
        "tasks": [],
        "simulation_results": {},
        "memory_payload": {},
        "sync_payload": {},
        "latest_simulation_payload": None,
        "latest_memory_payload": None,
        "latest_sync_payload": None,
        "current_page": "home",
        "footer_status": "Sẵn sàng mô phỏng",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = copy.deepcopy(value)


# =========================================================
# LAYOUT COMPONENTS
# =========================================================
def render_header(
    title: str,
    subtitle: str,
) -> None:
    khoa_logo = icon_html(
        "khoa.jpg",
        size=72,
        class_name="app-header-logo",
        fallback="KHOA",
    )

    school_logo = icon_html(
        "school.png",
        size=72,
        class_name="app-header-logo",
        fallback="DThU",
    )

    safe_title = html.escape(str(title))
    safe_subtitle = html.escape(str(subtitle))

    render_html(
        f"""
        <div class="app-header">
            <div class="app-header-left">
                <div class="app-logo-group">
                    {khoa_logo}
                    {school_logo}
                </div>

                <div class="app-school-text">
                    <div class="app-school-name">ĐẠI HỌC ĐỒNG THÁP</div>
                    <div class="app-faculty-name">KHOA SƯ PHẠM TOÁN - TIN</div>
                    <div class="app-school-subtitle">
                        FACULTY OF MATHEMATICS - INFORMATICS TEACHER EDUCATION
                    </div>
                </div>
            </div>

            <div class="app-header-divider"></div>

            <div class="app-header-title-area">
                <h1 class="app-header-title">{safe_title}</h1>
                <div class="app-header-subtitle">{safe_subtitle}</div>
            </div>
        </div>
        """
    )


def render_sidebar(
    menu_items: list[dict[str, Any]],
    active_key: str,
) -> None:
    now = datetime.now()
    menu_html_parts: list[str] = []

    for item in menu_items:
        key = str(item.get("key", ""))
        label = str(item.get("label", key))
        icon_name = item.get("icon")

        is_active = key == active_key
        active_class = "active" if is_active else ""
        icon_color = PRIMARY_COLOR if is_active else WHITE_COLOR

        icon = icon_html(
            filename=icon_name,
            size=28,
            color=icon_color,
            class_name="web-menu-icon-img",
            fallback="●",
        )

        safe_label = html.escape(label)
        safe_href = f"?page={quote(key)}"

        menu_html_parts.append(
            f"""
            <a href="{safe_href}" target="_self">
                <div class="web-menu-item {active_class}">
                    <span class="web-menu-icon">{icon}</span>
                    <span class="web-menu-text">{safe_label}</span>
                </div>
            </a>
            """
        )

    menu_html = "\n".join(menu_html_parts)

    render_html(
        f"""
        <div class="web-sidebar">
            <div class="web-sidebar-menu">
                {menu_html}
            </div>

            <div class="system-info-card">
                <div class="system-info-title">THÔNG TIN HỆ THỐNG</div>

                <div class="system-info-row">
                    <span class="sys-icon">📅</span>
                    <span class="sys-label">Ngày</span>
                    <span class="sys-value">{now.strftime("%d/%m/%Y")}</span>
                </div>

                <div class="system-info-row">
                    <span class="sys-icon">◷</span>
                    <span class="sys-label">Giờ</span>
                    <span class="sys-value">{now.strftime("%H:%M:%S")}</span>
                </div>

                <div class="system-info-row">
                    <span class="sys-icon">👤</span>
                    <span class="sys-label">Người dùng</span>
                    <span class="sys-value">Sinh viên</span>
                </div>

                <div class="system-info-row">
                    <span class="sys-icon">ⓘ</span>
                    <span class="sys-label">Phiên bản</span>
                    <span class="sys-value">1.0.0</span>
                </div>
            </div>
        </div>
        """,
        sidebar=True,
    )


def render_footer(
    status: str = "Sẵn sàng mô phỏng",
    copyright_text: str = "© 2025 - Khoa Sư phạm Toán - Tin, Trường Đại học Đồng Tháp",
) -> None:
    safe_status = html.escape(str(status))
    safe_copyright = html.escape(str(copyright_text))

    render_html(
        f"""
        <div class="app-footer">
            <div class="app-footer-left">
                <span class="app-footer-status-dot">●</span>
                {safe_status}
            </div>

            <div class="app-footer-right">
                {safe_copyright}
            </div>
        </div>
        """
    )


# =========================================================
# COMMON UI HELPERS CHO CÁC TRANG GỌI LẠI
# =========================================================
def _looks_like_html_fragment(value: str | None) -> bool:
    if not value:
        return False

    stripped = str(value).strip().lower()
    return stripped.startswith("<img") or stripped.startswith("<span") or stripped.startswith("<div")


def _safe_color(value: str | None, fallback: str = PRIMARY_COLOR) -> str:
    if not value:
        return fallback

    text = str(value).strip()
    if text.startswith("#") and len(text) in {4, 7}:
        return html.escape(text)

    return fallback


def section_title(
    title: str,
    icon: str | None = None,
    subtitle: str | None = None,
) -> None:
    """
    Render tiêu đề section.

    Cách dùng khuyến nghị:
        section_title("THAO TÁC NHANH", "Fast.png")
    """
    icon_part = ""

    if icon:
        if _looks_like_html_fragment(str(icon)):
            icon_part = str(icon)
        else:
            icon_part = icon_html(
                filename=icon,
                size=26,
                color=PRIMARY_COLOR,
                class_name="web-section-icon",
                fallback="",
            )

    safe_title = html.escape(str(title))
    subtitle_part = ""

    if subtitle:
        subtitle_part = f'<div class="web-section-subtitle">{html.escape(str(subtitle))}</div>'

    render_html(
        f"""
        <div class="web-section-title">
            {icon_part}
            <span>{safe_title}</span>
        </div>
        {subtitle_part}
        """
    )


def card(
    title: str | None = None,
    body: str | None = None,
    icon: str | None = None,
) -> None:
    title_html = ""

    if title:
        icon_part = ""
        if icon:
            icon_part = icon_html(
                filename=icon,
                size=24,
                color=PRIMARY_COLOR,
                class_name="web-card-title-icon",
                fallback="",
            )

        title_html = f'<div class="web-card-title">{icon_part} {html.escape(str(title))}</div>'

    render_html(
        f"""
        <div class="web-card">
            {title_html}
            {body or ""}
        </div>
        """
    )


def metric_card(
    label: str,
    value: str | int | float,
    icon: str | None = None,
) -> None:
    icon_part = ""

    if icon:
        icon_part = icon_html(
            filename=icon,
            size=28,
            color=PRIMARY_COLOR,
            class_name="web-metric-icon",
            fallback="",
        )

    render_html(
        f"""
        <div class="web-metric-card">
            {icon_part}
            <div class="web-metric-label">{html.escape(str(label))}</div>
            <div class="web-metric-value">{html.escape(str(value))}</div>
        </div>
        """
    )


def info_text(text: str) -> None:
    render_html(f'<div class="web-muted">{html.escape(str(text))}</div>')


def quick_card(
    icon: str | None,
    title: str,
    description: str,
    color: str = PRIMARY_COLOR,
    href: str | None = None,
) -> str:
    """
    Trả về HTML card thao tác nhanh.

    icon có thể là:
    - HTML trả về từ icon_html(...)
    - hoặc tên file trong assets/icons.
    Nơi gọi phải dùng:
        st.markdown(quick_card(...), unsafe_allow_html=True)
    """
    safe_color = _safe_color(color)

    if icon:
        if _looks_like_html_fragment(str(icon)):
            icon_part = str(icon)
        else:
            icon_part = icon_html(
                filename=icon,
                size=42,
                class_name="quick-card-icon-img",
                fallback="●",
            )
    else:
        icon_part = ""

    safe_title = html.escape(str(title))
    safe_description = html.escape(str(description))

    inner = f"""
    <div class="quick-card">
        <div class="quick-card-icon">{icon_part}</div>
        <div class="quick-card-title" style="color:{safe_color};">{safe_title}</div>
        <div class="quick-card-desc">{safe_description}</div>
    </div>
    """

    if href:
        return f'<a class="home-quick-link" href="{html.escape(href)}" target="_self">{inner}</a>'

    return inner


def render_metric_cards(
    metrics: list[tuple[str, Any, str, str]],
    columns: int = 4,
) -> None:
    """
    Render nhóm card thống kê.
    metrics dạng:
        [(title, value, subtitle, color), ...]
    """
    if not metrics:
        return

    column_count = max(1, min(int(columns or len(metrics)), len(metrics)))

    for start in range(0, len(metrics), column_count):
        row_metrics = metrics[start : start + column_count]
        cols = st.columns(column_count)

        for col, metric in zip(cols, row_metrics):
            title, value, subtitle, color = metric
            safe_color = _safe_color(color)
            safe_title = html.escape(str(title))
            safe_value = html.escape(str(value))
            safe_subtitle = html.escape(str(subtitle))

            with col:
                render_html(
                    f"""
                    <div class="home-metric-card" style="border-top:5px solid {safe_color};">
                        <div class="home-metric-label">{safe_title}</div>
                        <div class="home-metric-value">{safe_value}</div>
                        <div class="home-metric-subtitle">{safe_subtitle}</div>
                    </div>
                    """
                )


# Alias tên cũ/tên mới để tránh lỗi ImportError giữa các page
app_header = render_header
go_to = go_to_page
render_section_title = section_title
render_card = card
render_metric_card = metric_card
