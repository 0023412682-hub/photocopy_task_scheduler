from __future__ import annotations

import html
from contextlib import contextmanager
from typing import Any

import pandas as pd
import streamlit as st

try:
    from web.components import icon_html, set_footer_status
except Exception:
    def icon_html(filename=None, size=24, color=None, class_name="", alt="", fallback="●"):
        return f'<span class="{html.escape(class_name)}">{html.escape(fallback)}</span>'

    def set_footer_status(text: str) -> None:
        st.session_state["footer_status"] = text


PRIMARY_COLOR = "#005BAC"
DARK_BLUE = "#004A99"
ACCENT_COLOR = "#D71920"
BACKGROUND_COLOR = "#F4F7FB"
WHITE_COLOR = "#FFFFFF"
TEXT_COLOR = "#1F2937"
MUTED_TEXT = "#64748B"
BORDER_COLOR = "#D9E2EC"

GREEN = "#16A34A"
ORANGE = "#F97316"
RED = "#DC2626"
PURPLE = "#7C3AED"
TEAL = "#0891B2"

ALGORITHMS = ("First Fit", "Best Fit", "Worst Fit")
ALGORITHM_COLORS = {
    "First Fit": PRIMARY_COLOR,
    "Best Fit": GREEN,
    "Worst Fit": PURPLE,
}

MEMORY_BASE_KB = 20
COVER_PAGE_KB = 8
COLOR_PAGE_KB = 5
BW_PAGE_KB = 2


def inject_memory_css() -> None:
    st.markdown(
        f"""
<style>
.memory-page-wrap {{
    width: 100%;
}}

.memory-top-grid {{
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
    margin-bottom: 14px;
}}

.memory-metric-card {{
    min-height: 124px;
    background: {WHITE_COLOR};
    border: 1px solid {BORDER_COLOR};
    display: flex;
    align-items: center;
    box-sizing: border-box;
    padding: 16px 18px;
}}

.memory-metric-icon {{
    width: 92px;
    height: 92px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 92px;
    margin-right: 16px;
}}

.memory-metric-icon img {{
    width: 86px !important;
    height: 86px !important;
    object-fit: contain;
}}

.memory-metric-title {{
    color: {TEXT_COLOR};
    font-size: 13px;
    font-weight: 900;
    text-transform: uppercase;
    line-height: 1.2;
    margin-bottom: 6px;
}}

.memory-metric-value {{
    font-size: 28px;
    line-height: 1.1;
    font-weight: 900;
    margin-bottom: 7px;
}}

.memory-metric-subtitle {{
    color: {MUTED_TEXT};
    font-size: 12px;
    font-weight: 700;
    line-height: 1.25;
}}

.memory-section-head {{
    display: flex;
    align-items: center;
    gap: 10px;
    border-bottom: 1px solid {BORDER_COLOR};
    margin: -8px -8px 14px -8px;
    padding: 10px 12px 12px 12px;
}}

.memory-section-head-icon {{
    width: 26px;
    height: 26px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}}

.memory-section-head-icon img {{
    width: 24px !important;
    height: 24px !important;
    object-fit: contain;
}}

.memory-section-head-title {{
    color: {PRIMARY_COLOR};
    font-size: 16px;
    font-weight: 900;
    text-transform: uppercase;
}}

.memory-formula-note {{
    color: {MUTED_TEXT};
    font-size: 12px;
    font-style: italic;
    font-weight: 700;
    line-height: 2.6;
}}

.memory-algo-card {{
    background: {WHITE_COLOR};
    border: 1px solid {BORDER_COLOR};
    box-sizing: border-box;
    padding: 10px 10px 8px 10px;
    margin-bottom: 12px;
}}

.memory-algo-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 8px;
}}

.memory-algo-title {{
    font-size: 13px;
    font-weight: 900;
    text-transform: uppercase;
}}

.memory-algo-summary {{
    color: {MUTED_TEXT};
    font-size: 11px;
    font-style: italic;
    font-weight: 800;
    text-align: right;
}}

.memory-visual-scroll {{
    overflow-x: auto;
    overflow-y: hidden;
    padding: 4px 2px 8px 2px;
}}

.memory-block-line {{
    min-height: 126px;
    display: flex;
    gap: 24px;
    align-items: flex-start;
}}

.memory-block-box {{
    flex: 0 0 auto;
}}

.memory-block-label {{
    color: {TEXT_COLOR};
    text-align: center;
    font-size: 11px;
    font-weight: 900;
    height: 20px;
    line-height: 20px;
}}

.memory-block-bar {{
    height: 82px;
    border: 1px solid #94A3B8;
    background: #F8FAFC;
    display: flex;
    overflow: hidden;
    box-sizing: border-box;
}}

.memory-segment {{
    height: 100%;
    min-width: 30px;
    border-right: 1px solid #94A3B8;
    display: flex;
    align-items: center;
    justify-content: center;
    color: {TEXT_COLOR};
    font-size: 11px;
    line-height: 1.15;
    font-weight: 900;
    text-align: center;
    box-sizing: border-box;
    padding: 3px;
}}

.memory-remain {{
    height: 100%;
    min-width: 24px;
    background: #F8FAFC;
    display: flex;
    align-items: center;
    justify-content: center;
    color: {TEXT_COLOR};
    font-size: 11px;
    font-weight: 700;
    box-sizing: border-box;
    padding: 3px;
}}

.memory-empty-note {{
    color: {MUTED_TEXT};
    font-size: 12px;
    font-weight: 700;
    padding: 18px 4px;
}}

.memory-legend {{
    display: flex;
    gap: 26px;
    align-items: center;
    flex-wrap: wrap;
    margin-top: 4px;
    padding: 4px 2px 0 2px;
}}

.memory-legend-item {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: {TEXT_COLOR};
    font-size: 12px;
    font-weight: 800;
}}

.memory-legend-box {{
    width: 22px;
    height: 14px;
    border: 1px solid #BDBDBD;
    background: {WHITE_COLOR};
}}

.memory-legend-allocated {{
    background: #7DCE82;
    border-color: #63B96A;
}}

.memory-legend-fragment {{
    border-color: #E29A9A;
    border-style: dashed;
}}

.memory-table-wrap {{
    max-height: 225px;
    overflow: auto;
    border: 1px solid {BORDER_COLOR};
    background: {WHITE_COLOR};
}}

.memory-result-table-wrap {{
    max-height: 302px;
    overflow: auto;
    border: 1px solid {BORDER_COLOR};
    background: {WHITE_COLOR};
}}

.memory-table {{
    width: 100%;
    min-width: 360px;
    border-collapse: collapse;
    background: {WHITE_COLOR};
    font-size: 12px;
}}

.memory-table th {{
    position: sticky;
    top: 0;
    z-index: 2;
    color: {PRIMARY_COLOR};
    background: #EAF4FF;
    border-bottom: 1px solid {BORDER_COLOR};
    font-weight: 900;
    text-align: center;
    white-space: nowrap;
    padding: 8px 10px;
}}

.memory-table td {{
    color: {TEXT_COLOR};
    border-bottom: 1px solid #EEF2F7;
    text-align: center;
    white-space: nowrap;
    padding: 8px 10px;
    font-weight: 700;
}}

.memory-table tr:last-child td {{
    border-bottom: none;
}}

.memory-status-success {{
    color: {GREEN} !important;
    font-weight: 900 !important;
}}

.memory-status-failed {{
    color: {ORANGE} !important;
    font-weight: 900 !important;
}}

.memory-result-title {{
    color: {PRIMARY_COLOR};
    font-size: 13px;
    font-weight: 900;
    text-transform: uppercase;
    margin-bottom: 8px;
}}

.memory-compare-grid {{
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
}}

.memory-compare-card {{
    border: 1px solid {BORDER_COLOR};
    background: {WHITE_COLOR};
    min-height: 220px;
    padding: 12px;
    box-sizing: border-box;
}}

.memory-compare-title {{
    text-align: center;
    font-size: 13px;
    font-weight: 900;
    margin-bottom: 12px;
}}

.memory-bar-area {{
    height: 145px;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    gap: 24px;
    border-bottom: 1px solid #CBD5E1;
    margin: 0 6px 8px 6px;
}}

.memory-bar-group {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-end;
    height: 145px;
}}

.memory-bar-value {{
    font-size: 11px;
    color: {TEXT_COLOR};
    font-weight: 900;
    margin-bottom: 4px;
}}

.memory-bar {{
    width: 34px;
    min-height: 0;
}}

.memory-bar-label {{
    text-align: center;
    color: {TEXT_COLOR};
    font-size: 11px;
    font-weight: 800;
}}

.memory-conclusion-list {{
    display: flex;
    flex-direction: column;
}}

.memory-conclusion-item {{
    display: flex;
    gap: 10px;
    align-items: flex-start;
    padding: 10px 2px;
    border-bottom: 1px solid {BORDER_COLOR};
    color: {TEXT_COLOR};
    font-size: 13px;
    font-weight: 800;
    line-height: 1.45;
}}

.memory-conclusion-item:last-child {{
    border-bottom: none;
}}

.memory-conclusion-check {{
    width: 22px;
    height: 22px;
    flex: 0 0 22px;
    border-radius: 50%;
    background: #EAF7EE;
    color: {GREEN};
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
}}

div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 0 !important;
    border-color: {BORDER_COLOR} !important;
    background: {WHITE_COLOR} !important;
}}

div[data-testid="stVerticalBlockBorderWrapper"] > div {{
    background: {WHITE_COLOR} !important;
}}

.stButton > button {{
    border-radius: 0 !important;
    background: {PRIMARY_COLOR} !important;
    color: {WHITE_COLOR} !important;
    border: 1px solid {PRIMARY_COLOR} !important;
    font-weight: 900 !important;
    min-height: 38px;
}}

.stButton > button:hover {{
    background: {DARK_BLUE} !important;
    border-color: {DARK_BLUE} !important;
    color: {WHITE_COLOR} !important;
}}

div[data-testid="stNumberInput"] input {{
    border-radius: 0 !important;
}}

@media (max-width: 1200px) {{
    .memory-top-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }}

    .memory-compare-grid {{
        grid-template-columns: 1fr;
    }}
}}

@media (max-width: 760px) {{
    .memory-top-grid {{
        grid-template-columns: 1fr;
    }}
}}
</style>
""",
        unsafe_allow_html=True,
    )


@contextmanager
def bordered_container():
    try:
        container = st.container(border=True)
    except TypeError:
        container = st.container()

    with container:
        yield


def ensure_memory_state() -> None:
    st.session_state.setdefault("memory_total_kb", 1024)
    st.session_state.setdefault("memory_block_count", 5)
    st.session_state.setdefault("latest_memory_payload", None)


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def pick_value(source: Any, *names: str, default: Any = None) -> Any:
    if source is None:
        return default

    if isinstance(source, dict):
        lowered = {str(key).lower(): value for key, value in source.items()}

        for name in names:
            if name in source:
                return source[name]

            lowered_name = str(name).lower()
            if lowered_name in lowered:
                return lowered[lowered_name]

        return default

    for name in names:
        if hasattr(source, name):
            return getattr(source, name)

    return default


def build_processes_from_tasks(tasks: list[Any] | None) -> list[dict[str, Any]]:
    processes: list[dict[str, Any]] = []

    for index, task in enumerate(tasks or []):
        task_id = pick_value(
            task,
            "task_id",
            "id",
            "task_code",
            "code",
            "ma_tac_vu",
            "Mã tác vụ",
            default=f"T{index + 1:03d}",
        )

        customer_name = pick_value(
            task,
            "customer_name",
            "customer",
            "customer_id",
            "client",
            "khach_hang",
            "Khách hàng",
            default=f"Khách {index + 1}",
        )

        cover_pages = safe_int(
            pick_value(
                task,
                "cover_pages",
                "covers",
                "cover",
                "bia",
                "in_bia",
                "so_bia",
                "Bìa",
                default=0,
            ),
            0,
        )

        color_pages = safe_int(
            pick_value(
                task,
                "color_pages",
                "color",
                "mau",
                "in_mau",
                "so_mau",
                "Màu",
                default=0,
            ),
            0,
        )

        bw_pages = safe_int(
            pick_value(
                task,
                "bw_pages",
                "black_white_pages",
                "black_pages",
                "white_black_pages",
                "trang_den",
                "den_trang",
                "so_trang_den",
                "Trắng đen",
                default=0,
            ),
            0,
        )

        memory_size = (
            MEMORY_BASE_KB
            + cover_pages * COVER_PAGE_KB
            + color_pages * COLOR_PAGE_KB
            + bw_pages * BW_PAGE_KB
        )

        processes.append(
            {
                "id": str(task_id),
                "customer_name": str(customer_name),
                "cover_pages": cover_pages,
                "color_pages": color_pages,
                "bw_pages": bw_pages,
                "size": memory_size,
            }
        )

    return processes


def build_memory_blocks(total_memory: int, block_count: int) -> list[dict[str, Any]]:
    total_memory = max(1, safe_int(total_memory, 1024))
    block_count = max(1, safe_int(block_count, 5))
    block_count = min(block_count, total_memory)

    base_size = total_memory // block_count
    remainder = total_memory % block_count

    return [
        {
            "id": f"B{index + 1}",
            "size": base_size + (1 if index < remainder else 0),
        }
        for index in range(block_count)
    ]


def build_process_color_map(processes: list[dict[str, Any]]) -> dict[str, str]:
    colors = [
        "#A5F3FC",
        "#BFDBFE",
        "#BBF7D0",
        "#FED7AA",
        "#DDD6FE",
        "#FECACA",
        "#C7D2FE",
        "#FDE68A",
        "#99F6E4",
        "#E9D5FF",
        "#FBCFE8",
        "#BAE6FD",
    ]

    return {
        process["id"]: colors[index % len(colors)]
        for index, process in enumerate(processes)
    }


def allocate_memory(
    algorithm: str,
    memory_blocks: list[dict[str, Any]],
    processes: list[dict[str, Any]],
) -> dict[str, Any]:
    blocks = [
        {
            "id": block["id"],
            "size": block["size"],
            "remaining": block["size"],
            "items": [],
        }
        for block in memory_blocks
    ]

    results: list[dict[str, Any]] = []

    for process in processes:
        candidates = [
            index
            for index, block in enumerate(blocks)
            if block["remaining"] >= process["size"]
        ]

        chosen_index: int | None = None

        if candidates:
            if algorithm == "First Fit":
                chosen_index = candidates[0]
            elif algorithm == "Best Fit":
                chosen_index = min(
                    candidates,
                    key=lambda index: blocks[index]["remaining"] - process["size"],
                )
            elif algorithm == "Worst Fit":
                chosen_index = max(
                    candidates,
                    key=lambda index: blocks[index]["remaining"],
                )

        if chosen_index is None:
            results.append(
                {
                    "algorithm": algorithm,
                    "process": process["id"],
                    "size": process["size"],
                    "block": "—",
                    "remain": "—",
                    "status": "Chờ/Thất bại tạm thời",
                }
            )
        else:
            block = blocks[chosen_index]
            block["items"].append(process)
            block["remaining"] -= process["size"]

            results.append(
                {
                    "algorithm": algorithm,
                    "process": process["id"],
                    "size": process["size"],
                    "block": block["id"],
                    "remain": block["remaining"],
                    "status": "Thành công",
                }
            )

    total_memory = sum(block["size"] for block in blocks)
    used_memory = sum(
        item["size"]
        for block in blocks
        for item in block.get("items", [])
    )
    success = sum(1 for item in results if item["status"] == "Thành công")
    failed = len(results) - success
    usage = round(used_memory / total_memory * 100, 1) if total_memory else 0.0
    fragmentation = 0.0 if not processes else round(100 - usage, 1)

    return {
        "algorithm": algorithm,
        "blocks": blocks,
        "results": results,
        "success": success,
        "failed": failed,
        "usage": usage,
        "memory_usage": usage,
        "used_memory": used_memory,
        "total_memory": total_memory,
        "fragmentation": fragmentation,
    }


def choose_best_payload(compare_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not compare_results:
        return {}

    return max(
        compare_results.values(),
        key=lambda item: (
            item.get("success", 0),
            item.get("usage", 0),
            -item.get("fragmentation", 0),
        ),
    )


def build_payload(
    best_payload: dict[str, Any],
    compare_results: dict[str, dict[str, Any]],
    memory_blocks: list[dict[str, Any]],
    processes: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = dict(best_payload or {})
    payload["compare_results"] = compare_results
    payload["best_algorithm"] = payload.get("algorithm", "")
    payload["memory_blocks"] = memory_blocks
    payload["processes"] = processes
    payload["formula"] = "20 KB + in bìa × 8 + in màu × 5 + trắng đen × 2"
    return payload


def format_percent(value: Any) -> str:
    number = float(value or 0)
    if number.is_integer():
        return f"{int(number)}%"
    return f"{number:.1f}%"


def render_section_head(title: str, icon_file: str, fallback: str = "▣") -> None:
    icon = icon_html(
        icon_file,
        size=26,
        color=PRIMARY_COLOR,
        class_name="memory-section-head-icon-img",
        fallback=fallback,
    )

    st.markdown(
        f"""
<div class="memory-section-head">
    <span class="memory-section-head-icon">{icon}</span>
    <span class="memory-section-head-title">{html.escape(title)}</span>
</div>
""",
        unsafe_allow_html=True,
    )


def render_metric_card(
    title: str,
    value: str,
    subtitle: str,
    icon_file: str,
    color: str,
    fallback: str,
) -> str:
    icon = icon_html(
        icon_file,
        size=86,
        color=None,
        class_name="memory-metric-icon-img",
        fallback=fallback,
    )

    return f"""
<div class="memory-metric-card">
    <div class="memory-metric-icon">{icon}</div>
    <div>
        <div class="memory-metric-title">{html.escape(title)}</div>
        <div class="memory-metric-value" style="color:{color};">{html.escape(value)}</div>
        <div class="memory-metric-subtitle">{html.escape(subtitle)}</div>
    </div>
</div>
"""


def render_top_metrics(
    processes: list[dict[str, Any]],
    best_payload: dict[str, Any],
) -> None:
    cards = [
        render_metric_card(
            "Tổng tiến trình",
            str(len(processes)),
            "Tiến trình cần cấp phát",
            "Memory_Total.png",
            PRIMARY_COLOR,
            "👥",
        ),
        render_metric_card(
            "Cấp phát thành công",
            str(best_payload.get("success", 0)),
            "Theo thuật toán tốt nhất",
            "Memory_Success.png",
            GREEN,
            "✓",
        ),
        render_metric_card(
            "Thất bại",
            str(best_payload.get("failed", 0)),
            "Tiến trình không cấp được",
            "Memory_Failed.png",
            RED,
            "×",
        ),
        render_metric_card(
            "Hiệu suất bộ nhớ",
            format_percent(best_payload.get("usage", 0)),
            "Tỷ lệ bộ nhớ sử dụng",
            "Memory_Usage.png",
            PURPLE,
            "◔",
        ),
    ]

    st.markdown(
        '<div class="memory-top-grid">' + "\n".join(cards) + "</div>",
        unsafe_allow_html=True,
    )


def get_block_width(block_size: int) -> int:
    return max(130, min(230, int(block_size * 0.8)))


def render_algorithm_visual(
    algorithm: str,
    payload: dict[str, Any],
    processes: list[dict[str, Any]],
    process_color_map: dict[str, str],
) -> str:
    color = ALGORITHM_COLORS.get(algorithm, PRIMARY_COLOR)

    if not payload:
        return f"""
<div class="memory-algo-card">
    <div class="memory-algo-row">
        <div class="memory-algo-title" style="color:{color};">{html.escape(algorithm.upper())}</div>
        <div class="memory-algo-summary"></div>
    </div>
    <div class="memory-empty-note">Chưa có dữ liệu cấp phát bộ nhớ.</div>
</div>
"""

    block_html_parts: list[str] = []

    for block in payload.get("blocks", []):
        block_size = max(1, int(block.get("size", 1)))
        block_width = get_block_width(block_size)
        segment_parts: list[str] = []

        for item in block.get("items", []):
            item_size = max(0, int(item.get("size", 0)))
            width_percent = max(6.0, item_size / block_size * 100)
            fill = process_color_map.get(item.get("id", ""), "#BFDBFE")
            segment_parts.append(
                f"""
<div class="memory-segment" style="flex-basis:{width_percent:.3f}%; background:{fill};">
    {html.escape(str(item.get('id', '')))}<br>{html.escape(str(item_size))}
</div>
"""
            )

        remaining = max(0, int(block.get("remaining", 0)))
        if remaining > 0:
            remain_percent = max(6.0, remaining / block_size * 100)
            segment_parts.append(
                f"""
<div class="memory-remain" style="flex-basis:{remain_percent:.3f}%;">
    {html.escape(str(remaining))}
</div>
"""
            )

        if not segment_parts:
            segment_parts.append(
                f"""
<div class="memory-remain" style="flex-basis:100%;">
    {html.escape(str(block_size))}
</div>
"""
            )

        block_html_parts.append(
            f"""
<div class="memory-block-box" style="width:{block_width}px;">
    <div class="memory-block-label">{html.escape(str(block.get('id', '')))} ({block_size} KB)</div>
    <div class="memory-block-bar">{''.join(segment_parts)}</div>
</div>
"""
        )

    summary = (
        f"Thành công: {payload.get('success', 0)}/{len(processes)} | "
        f"Chờ/tạm thất bại: {payload.get('failed', 0)} | "
        f"Hiệu suất: {format_percent(payload.get('usage', 0))}"
    )

    return f"""
<div class="memory-algo-card">
    <div class="memory-algo-row">
        <div class="memory-algo-title" style="color:{color};">{html.escape(algorithm.upper())}</div>
        <div class="memory-algo-summary">{html.escape(summary)}</div>
    </div>
    <div class="memory-visual-scroll">
        <div class="memory-block-line">
            {''.join(block_html_parts)}
        </div>
    </div>
</div>
"""


def render_visual_panel(
    compare_results: dict[str, dict[str, Any]],
    processes: list[dict[str, Any]],
    process_color_map: dict[str, str],
) -> None:
    with bordered_container():
        render_section_head(
            "TRỰC QUAN CẤP PHÁT BỘ NHỚ",
            "Memory_Visualization.png",
            "▥",
        )

        for algorithm in ALGORITHMS:
            st.markdown(
                render_algorithm_visual(
                    algorithm,
                    compare_results.get(algorithm, {}),
                    processes,
                    process_color_map,
                ),
                unsafe_allow_html=True,
            )

        st.markdown(
            f"""
<div class="memory-legend">
    <span class="memory-legend-item"><span class="memory-legend-box"></span>Trống (Hole)</span>
    <span class="memory-legend-item"><span class="memory-legend-box memory-legend-allocated"></span>Đã cấp phát</span>
    <span class="memory-legend-item"><span class="memory-legend-box memory-legend-fragment"></span>Phân mảnh (Fragmentation)</span>
</div>
""",
            unsafe_allow_html=True,
        )


def render_table_html(
    headers: list[str],
    rows: list[list[Any]],
    max_height_class: str = "memory-table-wrap",
    status_col_index: int | None = None,
) -> str:
    header_html = "".join(f"<th>{html.escape(str(header))}</th>" for header in headers)

    if not rows:
        body_html = (
            f'<tr><td colspan="{len(headers)}" style="color:{MUTED_TEXT};">'
            "Chưa có dữ liệu"
            "</td></tr>"
        )
    else:
        body_parts: list[str] = []

        for row in rows:
            cell_parts: list[str] = []
            for index, cell in enumerate(row):
                cell_class = ""

                if status_col_index is not None and index == status_col_index:
                    cell_text = str(cell)
                    if cell_text == "Thành công":
                        cell_class = ' class="memory-status-success"'
                    else:
                        cell_class = ' class="memory-status-failed"'

                cell_parts.append(
                    f"<td{cell_class}>{html.escape(str(cell))}</td>"
                )

            body_parts.append(f"<tr>{''.join(cell_parts)}</tr>")

        body_html = "".join(body_parts)

    return f"""
<div class="{max_height_class}">
    <table class="memory-table">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{body_html}</tbody>
    </table>
</div>
"""


def render_data_tables(
    memory_blocks: list[dict[str, Any]],
    processes: list[dict[str, Any]],
) -> None:
    with bordered_container():
        render_section_head(
            "DANH SÁCH KHỐI NHỚ & TIẾN TRÌNH",
            "Choose_algorithm.png",
            "▤",
        )

        left, right = st.columns([0.32, 0.68], gap="medium")

        block_rows = [
            [block["id"], block["size"], "Đã tạo"]
            for block in memory_blocks
        ]

        process_rows = [
            [
                process["id"],
                process.get("customer_name", ""),
                process.get("cover_pages", 0),
                process.get("color_pages", 0),
                process.get("bw_pages", 0),
                process.get("size", 0),
            ]
            for process in processes
        ]

        with left:
            st.markdown(
                render_table_html(
                    ["Khối", "Kích thước", "Trạng thái"],
                    block_rows,
                    "memory-table-wrap",
                ),
                unsafe_allow_html=True,
            )

        with right:
            st.markdown(
                render_table_html(
                    ["Tác vụ", "Khách", "Bìa", "Màu", "Trắng đen", "Bộ nhớ KB"],
                    process_rows,
                    "memory-table-wrap",
                ),
                unsafe_allow_html=True,
            )


def render_result_tables(compare_results: dict[str, dict[str, Any]]) -> None:
    with bordered_container():
        render_section_head("KẾT QUẢ CẤP PHÁT", "Describe.png", "▦")

        cols = st.columns(3, gap="small")

        for col, algorithm in zip(cols, ALGORITHMS):
            payload = compare_results.get(algorithm, {})
            rows = [
                [
                    result.get("process", ""),
                    result.get("size", ""),
                    result.get("block", ""),
                    result.get("remain", ""),
                    result.get("status", ""),
                ]
                for result in payload.get("results", [])
            ]
            color = ALGORITHM_COLORS.get(algorithm, PRIMARY_COLOR)

            with col:
                st.markdown(
                    f'<div class="memory-result-title" style="color:{color};">{html.escape(algorithm.upper())}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    render_table_html(
                        ["Tiến trình", "Kích thước", "Khối cấp", "Còn dư", "Trạng thái"],
                        rows,
                        "memory-result-table-wrap",
                        status_col_index=4,
                    ),
                    unsafe_allow_html=True,
                )


def render_memory_config() -> bool:
    with bordered_container():
        render_section_head("CẤU HÌNH BỘ NHỚ", "Simulation_Setup.png", "⚙")

        c1, c2, c3, c4 = st.columns([1.25, 1.0, 0.9, 4.3], gap="medium")

        with c1:
            st.number_input(
                "Tổng bộ nhớ (KB)",
                min_value=1,
                max_value=100000,
                step=64,
                key="memory_total_kb",
            )

        with c2:
            st.number_input(
                "Số khối nhớ",
                min_value=1,
                max_value=100,
                step=1,
                key="memory_block_count",
            )

        with c3:
            st.write("")
            apply_clicked = st.button("Áp dụng", use_container_width=True)

        with c4:
            st.markdown(
                '<div class="memory-formula-note">'
                'Công thức: 20 KB + in bìa × 8 + in màu × 5 + trắng đen × 2'
                '</div>',
                unsafe_allow_html=True,
            )

    return apply_clicked


def render_compare_chart(compare_results: dict[str, dict[str, Any]], has_processes: bool) -> None:
    with bordered_container():
        render_section_head("SO SÁNH THUẬT TOÁN CẤP PHÁT", "Chart.png", "▥")

        card_parts: list[str] = []

        for algorithm in ALGORITHMS:
            payload = compare_results.get(algorithm, {})
            color = ALGORITHM_COLORS.get(algorithm, PRIMARY_COLOR)

            if not has_processes or not payload.get("results"):
                usage = 0.0
                fragmentation = 0.0
            else:
                usage = float(payload.get("usage", 0) or 0)
                fragmentation = float(payload.get("fragmentation", 0) or 0)

            usage_height = max(0, min(100, usage))
            frag_height = max(0, min(100, fragmentation))

            card_parts.append(
                f"""
<div class="memory-compare-card">
    <div class="memory-compare-title" style="color:{color};">{html.escape(algorithm)}</div>
    <div class="memory-bar-area">
        <div class="memory-bar-group">
            <div class="memory-bar-value">{format_percent(usage)}</div>
            <div class="memory-bar" style="height:{usage_height}%; background:{color};"></div>
        </div>
        <div class="memory-bar-group">
            <div class="memory-bar-value">{format_percent(fragmentation)}</div>
            <div class="memory-bar" style="height:{frag_height}%; background:{RED};"></div>
        </div>
    </div>
    <div style="display:flex;justify-content:center;gap:22px;">
        <div class="memory-bar-label">Hiệu suất</div>
        <div class="memory-bar-label">Phân mảnh</div>
    </div>
</div>
"""
            )

        st.markdown(
            '<div class="memory-compare-grid">' + "\n".join(card_parts) + "</div>",
            unsafe_allow_html=True,
        )


def build_conclusions(
    compare_results: dict[str, dict[str, Any]],
    best_payload: dict[str, Any],
    processes: list[dict[str, Any]],
) -> list[str]:
    if not compare_results or not processes:
        return [
            "Chưa có dữ liệu mô phỏng. Hãy thêm tác vụ trong Danh sách tác vụ và bấm Áp dụng để xem nhận xét."
        ]

    best_name = best_payload.get("algorithm", "")
    best_usage = best_payload.get("usage", 0)
    best_fragmentation = best_payload.get("fragmentation", 0)

    conclusions = [
        f"{best_name} đạt hiệu suất sử dụng bộ nhớ cao nhất ({format_percent(best_usage)}) và phân mảnh thấp nhất ({format_percent(best_fragmentation)})."
    ]

    first_fit = compare_results.get("First Fit")
    if first_fit:
        conclusions.append(
            f"First Fit có hiệu suất ổn định ({format_percent(first_fit.get('usage', 0))}) và phù hợp khi cần tốc độ cấp phát nhanh."
        )

    worst_fit = compare_results.get("Worst Fit")
    if worst_fit:
        conclusions.append(
            f"Worst Fit có mức phân mảnh {format_percent(worst_fit.get('fragmentation', 0))}, cần cân nhắc khi bộ nhớ bị chia nhỏ."
        )

    failed_processes = [
        item.get("process", "")
        for item in best_payload.get("results", [])
        if item.get("status") != "Thành công"
    ]

    if failed_processes:
        conclusions.append(
            "Tiến trình " + ", ".join(failed_processes) + " chưa được cấp phát do không còn khối nhớ phù hợp."
        )
    else:
        conclusions.append(
            "Tất cả tiến trình hiện tại đều được cấp phát thành công với cấu hình bộ nhớ đang chọn."
        )

    conclusions.append(
        "Có thể cải thiện bằng cách tăng tổng bộ nhớ, giảm số trang của tác vụ quá lớn hoặc hợp nhất các vùng nhớ trống liền kề khi tiến trình kết thúc."
    )

    return conclusions


def render_conclusion_panel(
    compare_results: dict[str, dict[str, Any]],
    best_payload: dict[str, Any],
    processes: list[dict[str, Any]],
) -> None:
    with bordered_container():
        render_section_head("NHẬN XÉT & KẾT LUẬN", "Comment.png", "●")
        items = build_conclusions(compare_results, best_payload, processes)

        item_html = "".join(
            f"""
<div class="memory-conclusion-item">
    <span class="memory-conclusion-check">✓</span>
    <span>{html.escape(item)}</span>
</div>
"""
            for item in items
        )

        st.markdown(
            f'<div class="memory-conclusion-list">{item_html}</div>',
            unsafe_allow_html=True,
        )


def emit_payload_if_needed(
    payload: dict[str, Any],
    apply_clicked: bool,
    on_memory_finished: Any = None,
) -> None:
    st.session_state["latest_memory_payload"] = payload

    if not apply_clicked:
        return

    set_footer_status("Mô phỏng bộ nhớ đã cập nhật")

    if callable(on_memory_finished):
        try:
            on_memory_finished(payload)
        except Exception as error:
            st.warning(f"Đã cập nhật mô phỏng bộ nhớ nhưng chưa gửi được payload báo cáo: {error}")


def render_memory_page(
    tasks: list[Any] | None = None,
    on_memory_finished: Any = None,
    **_: Any,
) -> None:
    inject_memory_css()
    ensure_memory_state()

    current_tasks = tasks if tasks is not None else st.session_state.get("tasks", [])

    total_memory = safe_int(st.session_state.get("memory_total_kb", 1024), 1024)
    block_count = safe_int(st.session_state.get("memory_block_count", 5), 5)

    processes = build_processes_from_tasks(current_tasks)
    memory_blocks = build_memory_blocks(total_memory, block_count)
    process_color_map = build_process_color_map(processes)

    compare_results = {
        algorithm: allocate_memory(algorithm, memory_blocks, processes)
        for algorithm in ALGORITHMS
    }
    best_payload = choose_best_payload(compare_results)
    payload = build_payload(best_payload, compare_results, memory_blocks, processes)

    st.markdown('<div class="memory-page-wrap">', unsafe_allow_html=True)

    render_top_metrics(processes, best_payload)
    apply_clicked = render_memory_config()

    if not processes:
        st.info(
            "Chưa có tác vụ để cấp phát bộ nhớ. Hãy thêm dữ liệu ở trang Danh sách tác vụ, sau đó quay lại trang Bộ nhớ."
        )

    left_col, right_col = st.columns([0.40, 0.60], gap="medium")

    with left_col:
        render_visual_panel(compare_results, processes, process_color_map)

    with right_col:
        render_data_tables(memory_blocks, processes)
        render_result_tables(compare_results)

    compare_col, conclusion_col = st.columns([0.60, 0.40], gap="medium")

    with compare_col:
        render_compare_chart(compare_results, bool(processes))

    with conclusion_col:
        render_conclusion_panel(compare_results, best_payload, processes)

    st.markdown("</div>", unsafe_allow_html=True)

    emit_payload_if_needed(payload, apply_clicked, on_memory_finished)


# Các alias để streamlit_app.py có thể tự nhận diện renderer.
def render_page(**kwargs: Any) -> None:
    render_memory_page(**kwargs)


def show_memory_page(**kwargs: Any) -> None:
    render_memory_page(**kwargs)


def render(**kwargs: Any) -> None:
    render_memory_page(**kwargs)


def main() -> None:
    render_memory_page()


app = render_memory_page


if __name__ == "__main__":
    main()