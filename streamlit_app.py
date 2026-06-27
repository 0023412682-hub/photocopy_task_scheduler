from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path
from typing import Any, Callable

import streamlit as st


# Đảm bảo import được models.py/core.models khi chạy từ Streamlit hoặc từ package web.
PROJECT_ROOT = Path(__file__).resolve().parent
for _path in (PROJECT_ROOT, PROJECT_ROOT / "core", PROJECT_ROOT / "web"):
    _path_text = str(_path)
    if _path_text not in sys.path:
        sys.path.insert(0, _path_text)


# =========================================================
# STREAMLIT CONFIG
# =========================================================
st.set_page_config(
    page_title="Mô phỏng hệ thống xếp hàng Photocopy",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded",
)


try:
    from web.components import (  # noqa: E402
        ensure_session_state as ensure_component_session_state,
        go_to_page,
        render_footer,
        render_header,
        render_html,
        render_sidebar,
        set_footer_status,
    )
except ImportError:  # fallback cho bản components cũ
    from web.components import (  # type: ignore  # noqa: E402
        go_to_page,
        render_footer,
        render_header,
        render_html,
        render_sidebar,
        set_footer_status,
    )

    def ensure_component_session_state() -> None:
        if "tasks" not in st.session_state:
            st.session_state["tasks"] = []

    def render_html(html_text: str, *, sidebar: bool = False) -> None:
        target = st.sidebar if sidebar else st
        target.markdown(str(html_text), unsafe_allow_html=True)

from web.styles import inject_global_css  # noqa: E402


# =========================================================
# PAGE REGISTRY
# =========================================================
PAGES: dict[str, dict[str, Any]] = {
    "home": {
        "label": "Trang chủ",
        "icon": "Home.png",
        "module": "web.pages.home_page",
        "title": "MÔ PHỎNG HỆ THỐNG XẾP HÀNG",
        "subtitle": "XỬ LÝ TÁC VỤ TRONG QUÁN PHOTOCOPY BẰNG CÁC GIẢI THUẬT LẬP LỊCH CPU",
        "status": "Sẵn sàng mô phỏng",
        "renderers": [
            "render_home_page",
            "show_home_page",
            "render_page",
            "render",
            "main",
            "app",
        ],
    },
    "task": {
        "label": "Danh sách tác vụ",
        "icon": "Task_List.png",
        "module": "web.pages.task_page",
        "title": "QUẢN LÝ DANH SÁCH TÁC VỤ",
        "subtitle": "Thêm, sửa, xóa và quản lý yêu cầu in ấn, sao chép, scan",
        "status": "Sẵn sàng quản lý dữ liệu",
        "renderers": [
            "render_task_page",
            "show_task_page",
            "render_page",
            "render",
            "main",
            "app",
        ],
    },
    "simulation": {
        "label": "Mô phỏng thuật toán",
        "icon": "Simulation_Algorithm.png",
        "module": "web.pages.simulation_page",
        "title": "MÔ PHỎNG XỬ LÝ TÁC VỤ",
        "subtitle": "Mô phỏng các giải thuật lập lịch CPU trong quán photocopy",
        "status": "Đang mô phỏng thuật toán",
        "renderers": [
            "render_simulation_page",
            "show_simulation_page",
            "render_page",
            "render",
            "main",
            "app",
        ],
    },
    "memory": {
        "label": "Bộ nhớ",
        "icon": "Memory.png",
        "module": "web.pages.memory_page",
        "title": "QUẢN LÝ BỘ NHỚ",
        "subtitle": "Mô phỏng cấp phát bộ nhớ cho các tác vụ trong hệ thống photocopy",
        "status": "Đang xem mô phỏng bộ nhớ",
        "renderers": [
            "render_memory_page",
            "show_memory_page",
            "render_page",
            "render",
            "main",
            "app",
        ],
    },
    "sync": {
        "label": "Đồng bộ hóa",
        "icon": "Sync.png",
        "module": "web.pages.sync_page",
        "title": "ĐỒNG BỘ HÓA TÁC VỤ",
        "subtitle": "Mô phỏng tranh chấp tài nguyên và đồng bộ hóa trong hệ thống photocopy",
        "status": "Đang xem mô phỏng đồng bộ hóa",
        "renderers": [
            "render_sync_page",
            "show_sync_page",
            "render_page",
            "render",
            "main",
            "app",
        ],
    },
    "comparison": {
        "label": "So sánh thuật toán",
        "icon": "Compare_Algorithms.png",
        "module": "web.pages.comparison_page",
        "title": "SO SÁNH HIỆU QUẢ THUẬT TOÁN",
        "subtitle": "Đánh giá thời gian chờ và thời gian hoàn thành của các giải thuật",
        "status": "Sẵn sàng so sánh thuật toán",
        "renderers": [
            "render_comparison_page",
            "show_comparison_page",
            "render_page",
            "render",
            "main",
            "app",
        ],
    },
    "report": {
        "label": "Báo cáo",
        "icon": "Report.png",
        "module": "web.pages.report_page",
        "title": "BÁO CÁO MÔ PHỎNG",
        "subtitle": "Kết quả xử lý tác vụ của hệ thống photocopy",
        "status": "Sẵn sàng xuất báo cáo",
        "renderers": [
            "render_report_page",
            "show_report_page",
            "render_page",
            "render",
            "main",
            "app",
        ],
    },
}


MENU_ITEMS = [
    {
        "key": key,
        "label": page["label"],
        "icon": page["icon"],
    }
    for key, page in PAGES.items()
]


# =========================================================
# SESSION STATE
# =========================================================
def ensure_session_state() -> None:
    """
    Chỉ tạo state mặc định nếu chưa có.
    Không clear, không ghi đè dữ liệu hiện tại của các trang.
    """
    ensure_component_session_state()

    defaults = {
        "current_page": "home",
        "tasks": [],
        "simulation_results": {},
        "memory_payload": {},
        "sync_payload": {},
        "latest_simulation_payload": None,
        "latest_memory_payload": None,
        "latest_sync_payload": None,
        "sim_results": {},
        "sim_normalized_tasks": [],
        "sim_task_color_map": {},
        "sim_current_time": 0,
        "sim_max_time": 0,
        "sim_timeline_points": [0],
        "sim_timeline_index": 0,
        "sim_running": False,
        "sim_finished": False,
        "sim_task_signature": "",
        "footer_status": "Sẵn sàng mô phỏng",
        "_last_page": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, (list, dict)) else value


def read_page_from_query_params() -> str | None:
    """
    Đọc ?page=... khi người dùng bấm menu HTML.
    Có fallback cho Streamlit cũ.
    """
    value = None

    try:
        value = st.query_params.get("page", None)
    except Exception:
        try:
            params = st.experimental_get_query_params()
            raw_value = params.get("page")
            if isinstance(raw_value, list):
                value = raw_value[0] if raw_value else None
            else:
                value = raw_value
        except Exception:
            value = None

    if isinstance(value, list):
        value = value[0] if value else None

    if value in PAGES:
        return value

    return None


def resolve_current_page() -> str:
    """
    Ưu tiên:
    1. navigation pending do các page set;
    2. query param ?page=...;
    3. current_page đang có trong session_state.
    """
    pending_page = st.session_state.pop("_navigate_to_page", None)
    if pending_page in PAGES:
        st.session_state["current_page"] = pending_page
        return pending_page

    query_page = read_page_from_query_params()
    if query_page in PAGES:
        st.session_state["current_page"] = query_page
        return query_page

    current_page = st.session_state.get("current_page", "home")
    if current_page not in PAGES:
        current_page = "home"

    st.session_state["current_page"] = current_page
    return current_page


# =========================================================
# APP CALLBACKS
# =========================================================
def build_report_payload() -> dict[str, Any]:
    return {
        "cpu": st.session_state.get("latest_simulation_payload")
        or st.session_state.get("simulation_results")
        or {},
        "memory": st.session_state.get("latest_memory_payload")
        or st.session_state.get("memory_payload")
        or {},
        "sync": st.session_state.get("latest_sync_payload")
        or st.session_state.get("sync_payload")
        or {},
    }


def reset_simulation_state_for_task_change() -> None:
    """Reset toàn bộ trạng thái mô phỏng khi danh sách task đầu vào thay đổi."""
    from collections import OrderedDict

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
    st.session_state["latest_simulation_payload"] = None
    st.session_state["simulation_results"] = {}


def on_tasks_changed(tasks: list[dict[str, Any]]) -> None:
    # Một nguồn dữ liệu duy nhất cho toàn app: st.session_state["tasks"].
    st.session_state["tasks"] = tasks or []

    # Task thay đổi thì kết quả mô phỏng cũ không còn hợp lệ.
    reset_simulation_state_for_task_change()

    # Các payload phụ thuộc task cũng được xóa để tránh trang khác đọc dữ liệu cũ.
    st.session_state["latest_memory_payload"] = None
    st.session_state["latest_sync_payload"] = None
    st.session_state["memory_payload"] = {}
    st.session_state["sync_payload"] = {}

    set_footer_status("Danh sách tác vụ đã được cập nhật")


def on_simulation_progress(payload: dict[str, Any]) -> None:
    st.session_state["latest_simulation_payload"] = payload
    st.session_state["simulation_results"] = payload
    set_footer_status("Đang cập nhật tiến trình mô phỏng")


def on_simulation_finished(
    tasks: list[dict[str, Any]] | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    # Không tự xoá danh sách tác vụ khi callback không truyền tasks.
    if tasks is not None:
        st.session_state["tasks"] = tasks

    if payload is not None:
        st.session_state["latest_simulation_payload"] = payload
        st.session_state["simulation_results"] = payload

    set_footer_status("Mô phỏng hoàn thành, danh sách tác vụ đã cập nhật")


def on_memory_finished(payload: dict[str, Any]) -> None:
    st.session_state["latest_memory_payload"] = payload
    st.session_state["memory_payload"] = payload
    set_footer_status("Mô phỏng bộ nhớ hoàn thành")


def on_sync_finished(payload: dict[str, Any]) -> None:
    st.session_state["latest_sync_payload"] = payload
    st.session_state["sync_payload"] = payload
    set_footer_status("Mô phỏng đồng bộ hóa hoàn thành")


def get_app_context(current_page: str) -> dict[str, Any]:
    """
    Context dùng cho các page nếu page render cần nhận tham số.
    Nếu page cũ không cần tham số thì vẫn chạy bình thường.
    """
    return {
        "current_page": current_page,
        "tasks": st.session_state.get("tasks", []),
        "payload": build_report_payload(),
        "report_payload": build_report_payload(),
        "cpu_payload": st.session_state.get("latest_simulation_payload")
        or st.session_state.get("simulation_results"),
        "memory_payload": st.session_state.get("latest_memory_payload")
        or st.session_state.get("memory_payload"),
        "sync_payload": st.session_state.get("latest_sync_payload")
        or st.session_state.get("sync_payload"),
        "state": st.session_state,
        "session_state": st.session_state,
        "go_to_page": go_to_page,
        "navigate": go_to_page,
        "on_tasks_changed": on_tasks_changed,
        "on_simulation_progress": on_simulation_progress,
        "on_simulation_finished": on_simulation_finished,
        "on_memory_finished": on_memory_finished,
        "on_sync_finished": on_sync_finished,
        "build_report_payload": build_report_payload,
    }


# =========================================================
# PAGE RENDER LOADER
# =========================================================
def load_page_renderer(page_key: str) -> Callable[..., Any] | None:
    page = PAGES[page_key]
    module_name = page["module"]

    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        st.error(f"Không import được module `{module_name}`.")
        st.exception(exc)
        return None

    for renderer_name in page["renderers"]:
        renderer = getattr(module, renderer_name, None)
        if callable(renderer):
            return renderer

    st.warning(
        f"Module `{module_name}` chưa có hàm render phù hợp. "
        f"Hãy tạo một trong các hàm: {', '.join(page['renderers'])}."
    )
    return None


def call_page_renderer(
    renderer: Callable[..., Any],
    page_key: str,
) -> Any:
    """
    Gọi page render theo kiểu linh hoạt:
    - Nếu page không nhận tham số: gọi bình thường.
    - Nếu page nhận tasks/callback/state: tự truyền đúng tên tham số.
    """
    context = get_app_context(page_key)

    try:
        signature = inspect.signature(renderer)
    except Exception:
        return renderer()

    params = signature.parameters

    has_var_kwargs = any(
        param.kind == inspect.Parameter.VAR_KEYWORD
        for param in params.values()
    )

    if has_var_kwargs:
        return renderer(**context)

    kwargs: dict[str, Any] = {}

    for name in params:
        if name in context:
            kwargs[name] = context[name]

    try:
        return renderer(**kwargs)
    except TypeError as exc:
        try:
            return renderer()
        except TypeError:
            raise exc


# =========================================================
# MAIN APP
# =========================================================
def main() -> None:
    inject_global_css()
    ensure_session_state()

    current_page = resolve_current_page()
    page_config = PAGES[current_page]

    if st.session_state.get("_last_page") != current_page:
        st.session_state["footer_status"] = page_config["status"]
        st.session_state["_last_page"] = current_page

    # Header/sidebar/footer chỉ render tại đây một lần.
    # Không dùng st.write cho HTML và không mở/đóng <div> qua nhiều st.markdown khác nhau.
    render_header(
        title=page_config["title"],
        subtitle=page_config["subtitle"],
    )

    render_sidebar(
        menu_items=MENU_ITEMS,
        active_key=current_page,
    )

    renderer = load_page_renderer(current_page)
    if renderer is not None:
        result = call_page_renderer(renderer, current_page)

        # Nếu page/component cũ trả về HTML string thì render đúng bằng unsafe_allow_html.
        # Không in HTML bằng hàm ghi văn bản thông thường, vì sẽ làm lộ thẻ ra giao diện.
        if isinstance(result, str) and result.strip():
            render_html(result)

    render_footer(
        status=st.session_state.get("footer_status") or page_config["status"],
    )


if __name__ == "__main__":
    main()
