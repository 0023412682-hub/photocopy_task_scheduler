from __future__ import annotations

import html
from contextlib import contextmanager
from datetime import datetime
from io import BytesIO
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
LIGHT_BLUE = "#EAF4FF"
GREEN = "#16A34A"
ORANGE = "#F97316"
RED = "#DC2626"
PURPLE = "#7C3AED"


@contextmanager
def bordered_container():
    try:
        container = st.container(border=True)
    except TypeError:
        container = st.container()
    with container:
        yield


def inject_report_css() -> None:
    st.markdown(
        f"""
<style>
.report-page-wrap {{
    width: 100%;
}}
.report-title-box {{
    text-align: center;
    margin: -4px 0 16px 0;
}}
.report-title {{
    color: {DARK_BLUE};
    font-size: 28px;
    font-weight: 900;
    text-transform: uppercase;
    line-height: 1.15;
}}
.report-subtitle {{
    color: {ACCENT_COLOR};
    font-size: 13px;
    font-weight: 900;
    margin-top: 6px;
}}
.report-section-head {{
    display: flex;
    align-items: center;
    gap: 10px;
    border-bottom: 1px solid {BORDER_COLOR};
    margin: -8px -8px 14px -8px;
    padding: 10px 12px 12px 12px;
}}
.report-section-icon {{
    width: 26px;
    height: 26px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}}
.report-section-icon img {{
    width: 24px !important;
    height: 24px !important;
    object-fit: contain;
}}
.report-section-title {{
    color: {PRIMARY_COLOR};
    font-size: 16px;
    font-weight: 900;
    text-transform: uppercase;
}}
.report-overview-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}}
.report-overview-table td {{
    padding: 9px 6px;
    vertical-align: top;
}}
.report-overview-label {{
    width: 150px;
    color: {TEXT_COLOR};
    font-weight: 900;
    white-space: nowrap;
}}
.report-overview-value {{
    color: {TEXT_COLOR};
    font-weight: 700;
    line-height: 1.45;
}}
.report-kpi-grid {{
    display: grid;
    grid-template-columns: repeat(6, minmax(92px, 1fr));
    gap: 10px;
}}
.report-kpi-card {{
    min-height: 152px;
    background: {WHITE_COLOR};
    border: 1px solid {BORDER_COLOR};
    box-sizing: border-box;
    text-align: center;
    overflow: hidden;
}}
.report-kpi-icon {{
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: {PRIMARY_COLOR};
    color: {WHITE_COLOR};
}}
.report-kpi-icon img {{
    width: 34px !important;
    height: 34px !important;
    object-fit: contain;
}}
.report-kpi-label {{
    color: {TEXT_COLOR};
    font-size: 11px;
    font-weight: 900;
    min-height: 34px;
    padding: 8px 4px 2px 4px;
    line-height: 1.2;
}}
.report-kpi-value {{
    font-size: 24px;
    font-weight: 900;
    padding: 4px 4px 10px 4px;
    line-height: 1.1;
    word-break: break-word;
}}
.report-donut-wrap {{
    min-height: 300px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}}
.report-donut {{
    width: 190px;
    height: 190px;
    border-radius: 50%;
    position: relative;
    background: conic-gradient(var(--cpu-color) 0deg var(--cpu-end), var(--memory-color) var(--cpu-end) var(--memory-end), var(--sync-color) var(--memory-end) 360deg);
}}
.report-donut::after {{
    content: "";
    position: absolute;
    width: 86px;
    height: 86px;
    border-radius: 50%;
    background: {WHITE_COLOR};
    top: 52px;
    left: 52px;
}}
.report-donut-center {{
    position: absolute;
    z-index: 2;
    top: 67px;
    left: 0;
    width: 190px;
    text-align: center;
}}
.report-donut-percent {{
    color: {TEXT_COLOR};
    font-size: 24px;
    font-weight: 900;
    line-height: 1.1;
}}
.report-donut-label {{
    color: {MUTED_TEXT};
    font-size: 11px;
    font-weight: 700;
    margin-top: 6px;
}}
.report-legend {{
    width: 230px;
    margin-top: 18px;
}}
.report-legend-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    justify-content: space-between;
    color: {TEXT_COLOR};
    font-size: 12px;
    font-weight: 800;
    margin: 8px 0;
}}
.report-legend-name {{
    flex: 1;
    text-align: left;
}}
.report-dot {{
    width: 9px;
    height: 9px;
    border-radius: 50%;
    display: inline-block;
}}
.report-table-wrap {{
    width: 100%;
    max-height: 330px;
    overflow: auto;
    border: 1px solid {BORDER_COLOR};
    background: {WHITE_COLOR};
}}
.report-table {{
    width: 100%;
    min-width: 680px;
    border-collapse: collapse;
    font-size: 13px;
}}
.report-table th {{
    position: sticky;
    top: 0;
    z-index: 2;
    color: {PRIMARY_COLOR};
    background: {LIGHT_BLUE};
    border-bottom: 1px solid {BORDER_COLOR};
    padding: 10px 12px;
    text-align: center;
    font-weight: 900;
    white-space: nowrap;
}}
.report-table td {{
    color: {TEXT_COLOR};
    border-bottom: 1px solid #EEF2F7;
    padding: 10px 12px;
    text-align: center;
    font-weight: 700;
    white-space: nowrap;
}}
.report-table tr.best-row td {{
    background: #FFF7ED;
    border-top: 2px solid {ORANGE};
    border-bottom: 2px solid {ORANGE};
    font-weight: 900;
}}
.report-note {{
    background: {LIGHT_BLUE};
    color: {PRIMARY_COLOR};
    font-size: 12px;
    font-weight: 800;
    font-style: italic;
    padding: 10px 12px;
    margin-top: 12px;
}}
.report-sync-grid {{
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
}}
.report-sync-card {{
    background: {WHITE_COLOR};
    border: 1px solid {BORDER_COLOR};
    min-height: 112px;
    text-align: center;
    padding: 12px 8px;
    box-sizing: border-box;
}}
.report-sync-icon {{
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
}}
.report-sync-icon img {{
    width: 32px !important;
    height: 32px !important;
    object-fit: contain;
}}
.report-sync-title {{
    color: {TEXT_COLOR};
    font-size: 11px;
    font-weight: 900;
    margin-top: 8px;
}}
.report-sync-value {{
    color: {PRIMARY_COLOR};
    font-size: 19px;
    font-weight: 900;
    margin-top: 4px;
    word-break: break-word;
}}
.report-conclusion-list {{
    display: flex;
    flex-direction: column;
}}
.report-conclusion-item {{
    display: flex;
    gap: 10px;
    align-items: flex-start;
    padding: 10px 2px;
    border-bottom: 1px solid {BORDER_COLOR};
    color: {TEXT_COLOR};
    font-size: 13px;
    font-weight: 800;
    line-height: 1.48;
}}
.report-conclusion-item:last-child {{
    border-bottom: none;
}}
.report-check {{
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
.report-empty-note {{
    color: {MUTED_TEXT};
    font-size: 13px;
    font-weight: 700;
    padding: 16px 4px;
}}
@media (max-width: 1250px) {{
    .report-kpi-grid {{
        grid-template-columns: repeat(3, minmax(92px, 1fr));
    }}
}}
@media (max-width: 780px) {{
    .report-kpi-grid, .report-sync-grid {{
        grid-template-columns: 1fr;
    }}
}}
</style>
""",
        unsafe_allow_html=True,
    )


def get_value(obj: Any, names: list[str] | tuple[str, ...], default: Any = None) -> Any:
    if obj is None:
        return default

    if isinstance(obj, dict):
        lowered = {str(k).lower(): v for k, v in obj.items()}
        for name in names:
            if name in obj:
                return obj[name]
            lower = str(name).lower()
            if lower in lowered:
                return lowered[lower]
        return default

    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)

    return default


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def fmt_number(value: Any) -> str:
    number = to_float(value, 0.0)
    if number.is_integer():
        return str(int(number))
    return f"{number:.2f}"


def fmt_percent(value: Any) -> str:
    number = to_float(value, 0.0)
    if number.is_integer():
        return f"{int(number)}%"
    return f"{number:.1f}%"


def normalize_algorithm_name(name: Any) -> str:
    text = str(name or "Chưa có").strip()
    lower = text.lower().replace("_", " ").replace("-", " ")

    if "fcfs" in lower:
        return "FCFS"
    if "sjf" in lower or "shortest" in lower:
        return "SJF"
    if "priority" in lower or "ưu tiên" in lower:
        return "Priority"
    if "round" in lower or lower == "rr":
        return "Round Robin"
    return text


def normalize_payload(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}

    cpu = source.get("cpu") if isinstance(source.get("cpu"), dict) else None
    memory = source.get("memory") if isinstance(source.get("memory"), dict) else None
    sync = source.get("sync") if isinstance(source.get("sync"), dict) else None

    if cpu is None and any(key in source for key in ("result_map", "results", "preferred_result")):
        cpu = source

    return {
        "cpu": cpu or st.session_state.get("latest_simulation_payload") or {},
        "memory": memory or st.session_state.get("latest_memory_payload") or {},
        "sync": sync or st.session_state.get("latest_sync_payload") or {},
    }


def get_cpu_results(cpu_payload: dict[str, Any]) -> list[Any]:
    result_map = get_value(cpu_payload, ["result_map", "algorithm_results"], None)
    if isinstance(result_map, dict) and result_map:
        return list(result_map.values())

    results = get_value(cpu_payload, ["results", "comparison_results"], None)
    if isinstance(results, list) and results:
        return results

    preferred = get_value(cpu_payload, ["preferred_result", "best_result"], None)
    if preferred:
        return [preferred]

    return []


def get_algorithm_name(result: Any) -> str:
    return normalize_algorithm_name(get_value(result, ["algorithm_name", "algorithm", "name", "label"], "Chưa có"))


def get_avg_waiting(result: Any) -> float:
    return to_float(get_value(result, ["average_waiting_time", "avg_waiting_time", "avg_waiting", "waiting"], 0), 0)


def get_avg_turnaround(result: Any) -> float:
    return to_float(get_value(result, ["average_turnaround_time", "avg_turnaround_time", "avg_turnaround", "turnaround"], 0), 0)


def get_avg_response(result: Any) -> float:
    return to_float(get_value(result, ["average_response_time", "avg_response_time", "avg_response", "response"], 0), 0)


def get_best_cpu_result(cpu_payload: dict[str, Any]) -> Any | None:
    results = get_cpu_results(cpu_payload)
    if not results:
        return None
    return min(results, key=lambda result: get_avg_waiting(result))


def calculate_cpu_utilization(result: Any) -> float | None:
    if result is None:
        return None

    gantt = get_value(result, ["gantt_chart", "gantt", "timeline"], [])
    if not gantt:
        return None

    starts: list[float] = []
    ends: list[float] = []
    busy = 0.0

    for block in gantt:
        start = to_float(get_value(block, ["start_time", "start"], 0), 0)
        end = to_float(get_value(block, ["end_time", "end"], 0), 0)
        task_id = str(get_value(block, ["task_id", "pid", "id"], ""))
        starts.append(start)
        ends.append(end)
        if task_id.upper() != "IDLE":
            busy += max(0.0, end - start)

    total = max(ends) - min(starts) if starts and ends else 0
    if total <= 0:
        return None
    return round(busy / total * 100, 1)


def cpu_note(algorithm: str, rank: int) -> str:
    lower = algorithm.lower()
    if rank == 1:
        return "Tốt nhất theo Avg Waiting"
    if "fcfs" in lower:
        return "Đơn giản, dễ triển khai"
    if "sjf" in lower:
        return "Tối ưu thời gian chờ"
    if "priority" in lower:
        return "Phù hợp tác vụ ưu tiên"
    if "round" in lower:
        return "Công bằng, phản hồi tốt"
    return "Đã mô phỏng"


def build_cpu_rows(cpu_payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = get_cpu_results(cpu_payload)
    sorted_results = sorted(results, key=lambda result: get_avg_waiting(result))
    rows: list[dict[str, Any]] = []

    for rank, result in enumerate(sorted_results, start=1):
        algorithm = get_algorithm_name(result)
        rows.append(
            {
                "rank": rank,
                "algorithm": algorithm,
                "avg_waiting": get_avg_waiting(result),
                "avg_turnaround": get_avg_turnaround(result),
                "avg_response": get_avg_response(result),
                "note": cpu_note(algorithm, rank),
            }
        )

    return rows


def build_memory_rows(memory_payload: dict[str, Any]) -> list[dict[str, Any]]:
    compare = get_value(memory_payload, ["compare_results"], None)
    rows: list[dict[str, Any]] = []

    if isinstance(compare, dict) and compare:
        for algorithm, data in compare.items():
            rows.append(
                {
                    "algorithm": str(algorithm),
                    "success": get_value(data, ["success"], 0),
                    "usage": get_value(data, ["usage", "memory_usage"], 0),
                    "fragmentation": get_value(data, ["fragmentation"], 0),
                }
            )
    elif memory_payload:
        rows.append(
            {
                "algorithm": get_value(memory_payload, ["algorithm", "best_algorithm"], "Đã chạy"),
                "success": get_value(memory_payload, ["success"], 0),
                "usage": get_value(memory_payload, ["usage", "memory_usage"], 0),
                "fragmentation": get_value(memory_payload, ["fragmentation"], 0),
            }
        )

    if rows:
        best_usage = max(to_float(row["usage"], 0) for row in rows)
        for row in rows:
            row["note"] = "Khuyến nghị" if to_float(row["usage"], 0) == best_usage else ""

    return rows


def module_statuses(cpu_payload: dict[str, Any], memory_payload: dict[str, Any], sync_payload: dict[str, Any]) -> list[tuple[str, bool, str]]:
    return [
        ("Lập lịch CPU", bool(get_cpu_results(cpu_payload)), "#0B63CE"),
        ("Cấp phát bộ nhớ", bool(memory_payload), "#16A34A"),
        ("Đồng bộ hóa", bool(sync_payload), "#F97316"),
    ]


def render_title() -> None:
    st.markdown(
        """
<div class="report-title-box">
    <div class="report-title">BÁO CÁO TỔNG HỢP HỆ THỐNG</div>
    <div class="report-subtitle">Đánh giá lập lịch CPU, cấp phát bộ nhớ và đồng bộ hóa tiến trình</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_section_head(title: str, icon_file: str, fallback: str = "▣") -> None:
    icon = icon_html(icon_file, size=26, color=PRIMARY_COLOR, class_name="report-section-icon-img", fallback=fallback)
    st.markdown(
        f"""
<div class="report-section-head">
    <span class="report-section-icon">{icon}</span>
    <span class="report-section-title">{html.escape(title)}</span>
</div>
""",
        unsafe_allow_html=True,
    )


def render_overview(tasks: list[Any], cpu_payload: dict[str, Any], memory_payload: dict[str, Any], sync_payload: dict[str, Any]) -> None:
    statuses = module_statuses(cpu_payload, memory_payload, sync_payload)
    done_modules = [name for name, done, _ in statuses if done]
    modules_text = ", ".join(done_modules) if done_modules else "Chưa chạy module nào"

    rows = [
        ("Mô hình:", "Một máy xử lý chung"),
        ("Số tác vụ:", str(len(tasks or []))),
        ("Module đã chạy:", modules_text),
        ("Dữ liệu:", "Dữ liệu mô phỏng hiện tại"),
        ("Ghi chú:", "Báo cáo tổng hợp dùng để đánh giá kết quả cuối cùng, không lặp lại Gantt hoặc bảng tác vụ chi tiết."),
    ]

    body = "".join(
        f"""
<tr>
    <td class="report-overview-label">{html.escape(label)}</td>
    <td class="report-overview-value">{html.escape(value)}</td>
</tr>
"""
        for label, value in rows
    )

    with bordered_container():
        render_section_head("A. TỔNG QUAN MÔ PHỎNG", "Information.png", "ⓘ")
        st.markdown(f'<table class="report-overview-table"><tbody>{body}</tbody></table>', unsafe_allow_html=True)


def render_kpi_card(title: str, value: str, icon_file: str, color: str, fallback: str) -> str:
    icon = icon_html(icon_file, size=34, color=WHITE_COLOR, class_name="report-kpi-icon-img", fallback=fallback)
    return f"""
<div class="report-kpi-card">
    <div class="report-kpi-icon" style="background:{color};">{icon}</div>
    <div class="report-kpi-label">{html.escape(title)}</div>
    <div class="report-kpi-value" style="color:{color};">{html.escape(value)}</div>
</div>
"""


def render_kpis(tasks: list[Any], cpu_payload: dict[str, Any], memory_payload: dict[str, Any], sync_payload: dict[str, Any]) -> None:
    best_cpu = get_best_cpu_result(cpu_payload)
    best_cpu_name = get_algorithm_name(best_cpu) if best_cpu else "---"
    best_wait = fmt_number(get_avg_waiting(best_cpu)) if best_cpu else "---"
    memory_usage = get_value(memory_payload, ["usage", "memory_usage"], "---")
    memory_usage_text = fmt_percent(memory_usage) if isinstance(memory_usage, (int, float)) else str(memory_usage)
    deadlock = bool(get_value(sync_payload, ["deadlock"], False))
    cpu_util = calculate_cpu_utilization(best_cpu)

    cards = [
        render_kpi_card("Tổng tác vụ", str(len(tasks or [])), "Comparison_Algorithm.png", PRIMARY_COLOR, "▤"),
        render_kpi_card("Thuật toán CPU đề xuất", best_cpu_name, "Best_Algorithm.png", PRIMARY_COLOR, "🏆"),
        render_kpi_card("Hiệu suất bộ nhớ", memory_usage_text, "Selected.png", GREEN, "▣"),
        render_kpi_card("Deadlock", "Có" if deadlock else "Không", "Deadlock.png", RED if deadlock else GREEN, "!"),
        render_kpi_card("Avg Waiting tốt nhất", best_wait, "AVG_Waiting.png", PRIMARY_COLOR, "◷"),
        render_kpi_card("CPU Utilization", fmt_percent(cpu_util) if cpu_util is not None else "---", "Processing.png", PRIMARY_COLOR, "▣"),
    ]

    with bordered_container():
        render_section_head("B. KẾT QUẢ HIỆU NĂNG CHÍNH", "Queue.png", "▥")
        st.markdown('<div class="report-kpi-grid">' + "\n".join(cards) + "</div>", unsafe_allow_html=True)


def render_system_overview(cpu_payload: dict[str, Any], memory_payload: dict[str, Any], sync_payload: dict[str, Any]) -> None:
    statuses = module_statuses(cpu_payload, memory_payload, sync_payload)
    completed = sum(1 for _, done, _ in statuses if done)
    overall = round(completed / len(statuses) * 100) if statuses else 0

    active_colors = [color if done else "#CBD5E1" for _, done, color in statuses]
    cpu_end = "120deg"
    memory_end = "240deg"

    legend = "".join(
        f"""
<div class="report-legend-row">
    <span class="report-dot" style="background:{color if done else '#CBD5E1'};"></span>
    <span class="report-legend-name">{html.escape(name)}</span>
    <span>{'100%' if done else '0%'}</span>
</div>
"""
        for name, done, color in statuses
    )

    with bordered_container():
        render_section_head("TỔNG QUAN HỆ THỐNG", "Target.png", "◉")
        st.markdown(
            f"""
<div class="report-donut-wrap">
    <div class="report-donut" style="--cpu-color:{active_colors[0]};--memory-color:{active_colors[1]};--sync-color:{active_colors[2]};--cpu-end:{cpu_end};--memory-end:{memory_end};">
        <div class="report-donut-center">
            <div class="report-donut-percent">{overall}%</div>
            <div class="report-donut-label">Hoàn thành</div>
        </div>
    </div>
    <div class="report-legend">{legend}</div>
</div>
""",
            unsafe_allow_html=True,
        )


def render_table(headers: list[str], rows: list[list[Any]], best_row_index: int | None = None) -> str:
    header_html = "".join(f"<th>{html.escape(str(header))}</th>" for header in headers)

    if not rows:
        body_html = f'<tr><td colspan="{len(headers)}" style="color:{MUTED_TEXT};">Chưa có dữ liệu</td></tr>'
    else:
        body_parts: list[str] = []
        for index, row in enumerate(rows):
            css = ' class="best-row"' if best_row_index is not None and index == best_row_index else ""
            cells = "".join(f"<td>{html.escape(str(cell))}</td>" for cell in row)
            body_parts.append(f"<tr{css}>{cells}</tr>")
        body_html = "".join(body_parts)

    return f"""
<div class="report-table-wrap">
    <table class="report-table">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{body_html}</tbody>
    </table>
</div>
"""


def render_cpu_summary(cpu_payload: dict[str, Any]) -> None:
    cpu_rows = build_cpu_rows(cpu_payload)
    rows = [
        [
            row["rank"],
            row["algorithm"],
            fmt_number(row["avg_waiting"]),
            fmt_number(row["avg_turnaround"]),
            fmt_number(row["avg_response"]),
            row["note"],
        ]
        for row in cpu_rows
    ]
    note = (
        f"{cpu_rows[0]['algorithm']} cho kết quả tốt nhất theo Avg Waiting trong bộ dữ liệu hiện tại."
        if cpu_rows
        else "Chưa có kết quả lập lịch CPU. Hãy chạy mô phỏng trước khi xem báo cáo."
    )

    with bordered_container():
        render_section_head("C. TÓM TẮT LẬP LỊCH CPU", "Process_result.png", "▥")
        st.markdown(
            render_table(
                ["Xếp hạng", "Thuật toán", "Avg Waiting", "Avg Turnaround", "Avg Response", "Nhận xét ngắn"],
                rows,
                best_row_index=0 if rows else None,
            ),
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="report-note">{html.escape(note)}</div>', unsafe_allow_html=True)


def render_memory_summary(memory_payload: dict[str, Any]) -> None:
    memory_rows = build_memory_rows(memory_payload)
    rows = [
        [
            row["algorithm"],
            row["success"],
            fmt_percent(row["usage"]),
            fmt_percent(row["fragmentation"]),
            row.get("note", ""),
        ]
        for row in memory_rows
    ]
    best_index = 0
    if memory_rows:
        best_index = max(range(len(memory_rows)), key=lambda i: to_float(memory_rows[i]["usage"], 0))
        note = f"{memory_rows[best_index]['algorithm']} có hiệu suất sử dụng bộ nhớ cao nhất trong bộ dữ liệu hiện tại."
    else:
        note = "Chưa có kết quả cấp phát bộ nhớ."

    with bordered_container():
        render_section_head("D. KẾT QUẢ CẤP PHÁT BỘ NHỚ", "Memory_Visualization.png", "▦")
        st.markdown(
            render_table(
                ["Thuật toán", "Thành công", "Hiệu suất", "Phân mảnh", "Khuyến nghị"],
                rows,
                best_row_index=best_index if rows else None,
            ),
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="report-note">{html.escape(note)}</div>', unsafe_allow_html=True)


def render_sync_summary(sync_payload: dict[str, Any]) -> None:
    deadlock = bool(get_value(sync_payload, ["deadlock"], False))
    items = [
        ("Cơ chế", get_value(sync_payload, ["mechanism"], "---"), "Producer-Consumer.png", PRIMARY_COLOR),
        ("Dung lượng buffer", get_value(sync_payload, ["buffer_size", "buffer"], "---"), "Buffer.png", PRIMARY_COLOR),
        ("Producer chờ", f"{get_value(sync_payload, ['producer_wait'], 0)} lần" if sync_payload else "---", "Producer.png", ORANGE),
        ("Consumer chờ", f"{get_value(sync_payload, ['consumer_wait'], 0)} lần" if sync_payload else "---", "Consumer.png", ORANGE),
        ("Deadlock", "Có" if deadlock else "Không", "Complete.png", RED if deadlock else GREEN),
        ("Trạng thái", get_value(sync_payload, ["status"], "Ổn định" if sync_payload else "---"), "Status.png", GREEN if sync_payload and not deadlock else PRIMARY_COLOR),
    ]

    card_parts: list[str] = []
    for title, value, icon_file, color in items:
        icon = icon_html(icon_file, size=32, color=None, class_name="report-sync-icon-img", fallback="▣")
        card_parts.append(
            f"""
<div class="report-sync-card">
    <div class="report-sync-icon">{icon}</div>
    <div class="report-sync-title">{html.escape(str(title))}</div>
    <div class="report-sync-value" style="color:{color};">{html.escape(str(value))}</div>
</div>
"""
        )

    with bordered_container():
        render_section_head("E. KẾT QUẢ ĐỒNG BỘ HÓA", "Sync.png", "●")
        st.markdown('<div class="report-sync-grid">' + "\n".join(card_parts) + "</div>", unsafe_allow_html=True)


def build_conclusions(cpu_payload: dict[str, Any], memory_payload: dict[str, Any], sync_payload: dict[str, Any]) -> list[str]:
    best_cpu = get_best_cpu_result(cpu_payload)
    best_cpu_name = get_algorithm_name(best_cpu) if best_cpu else "chưa có dữ liệu"

    memory_algo = get_value(memory_payload, ["algorithm", "best_algorithm"], "chưa có dữ liệu")
    memory_usage = get_value(memory_payload, ["usage", "memory_usage"], "---")
    memory_usage_text = fmt_percent(memory_usage) if isinstance(memory_usage, (int, float)) else str(memory_usage)

    deadlock = bool(get_value(sync_payload, ["deadlock"], False))
    sync_status = "không xảy ra deadlock" if not deadlock else "có dấu hiệu deadlock"

    return [
        f"Thuật toán CPU đề xuất: {best_cpu_name}. Kết quả được chọn dựa trên Avg Waiting Time thấp nhất trong các thuật toán đã chạy.",
        f"Cấp phát bộ nhớ: thuật toán {memory_algo} đạt hiệu suất {memory_usage_text} trong phiên mô phỏng hiện tại.",
        f"Đồng bộ hóa: hệ thống {sync_status}, buffer được kiểm soát bằng cơ chế Producer - Consumer/Mutex.",
        "Hạn chế hiện tại: mô hình đang giả định một máy xử lý chung, chưa mô phỏng nhiều máy in, máy scan hoặc nhiều CPU chạy song song.",
        "Hướng phát triển: bổ sung mô hình nhiều máy, thuật toán quản lý bộ nhớ nâng cao như phân trang/thay thế trang, và các bài toán đồng bộ hóa phức tạp hơn như deadlock hoặc dining philosophers.",
    ]


def render_conclusion(cpu_payload: dict[str, Any], memory_payload: dict[str, Any], sync_payload: dict[str, Any]) -> None:
    item_html = "".join(
        f"""
<div class="report-conclusion-item">
    <span class="report-check">✓</span>
    <span>{html.escape(line)}</span>
</div>
"""
        for line in build_conclusions(cpu_payload, memory_payload, sync_payload)
    )

    with bordered_container():
        render_section_head("F. KẾT LUẬN & HƯỚNG PHÁT TRIỂN", "Comment.png", "✓")
        st.markdown(f'<div class="report-conclusion-list">{item_html}</div>', unsafe_allow_html=True)


def render_report_page(
    tasks: list[Any] | None = None,
    payload: dict[str, Any] | None = None,
    report_payload: dict[str, Any] | None = None,
    cpu_payload: dict[str, Any] | None = None,
    memory_payload: dict[str, Any] | None = None,
    sync_payload: dict[str, Any] | None = None,
    **_: Any,
) -> None:
    inject_report_css()

    current_tasks = tasks if tasks is not None else st.session_state.get("tasks", [])
    normalized = normalize_payload(report_payload or payload)

    cpu_data = cpu_payload if isinstance(cpu_payload, dict) and cpu_payload else normalized["cpu"]
    memory_data = memory_payload if isinstance(memory_payload, dict) and memory_payload else normalized["memory"]
    sync_data = sync_payload if isinstance(sync_payload, dict) and sync_payload else normalized["sync"]

    st.markdown('<div class="report-page-wrap">', unsafe_allow_html=True)
    render_title()

    top_left, top_mid, top_right = st.columns([0.42, 0.30, 0.28], gap="medium")
    with top_left:
        render_overview(current_tasks, cpu_data, memory_data, sync_data)
    with top_mid:
        render_kpis(current_tasks, cpu_data, memory_data, sync_data)
    with top_right:
        render_system_overview(cpu_data, memory_data, sync_data)

    cpu_col, mem_col = st.columns(2, gap="medium")
    with cpu_col:
        render_cpu_summary(cpu_data)
    with mem_col:
        render_memory_summary(memory_data)

    sync_col, conclusion_col = st.columns([0.40, 0.60], gap="medium")
    with sync_col:
        render_sync_summary(sync_data)
    with conclusion_col:
        render_conclusion(cpu_data, memory_data, sync_data)

    st.markdown("</div>", unsafe_allow_html=True)
    set_footer_status("Sẵn sàng xuất báo cáo")


# Aliases để streamlit_app.py tự nhận diện renderer.
def render_page(**kwargs: Any) -> None:
    render_report_page(**kwargs)


def show_report_page(**kwargs: Any) -> None:
    render_report_page(**kwargs)


def render(**kwargs: Any) -> None:
    render_report_page(**kwargs)


def main() -> None:
    render_report_page()


app = render_report_page


if __name__ == "__main__":
    main()
