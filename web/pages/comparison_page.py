from __future__ import annotations

import base64
import csv
import html
from contextlib import contextmanager
from datetime import datetime
from io import BytesIO, StringIO
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

ALGORITHM_COLORS = {
    "FCFS": PRIMARY_COLOR,
    "SJF": GREEN,
    "Priority": ORANGE,
    "Round Robin": PURPLE,
    "Round Robin q=3": PURPLE,
}


@contextmanager
def bordered_container():
    try:
        container = st.container(border=True)
    except TypeError:
        container = st.container()
    with container:
        yield


def inject_comparison_css() -> None:
    st.markdown(
        f"""
<style>
.comparison-page-wrap {{
    width: 100%;
}}
.comparison-title-box {{
    text-align: center;
    margin: -4px 0 14px 0;
}}
.comparison-title {{
    color: {DARK_BLUE};
    font-size: 26px;
    font-weight: 900;
    text-transform: uppercase;
    line-height: 1.15;
}}
.comparison-subtitle {{
    color: {ACCENT_COLOR};
    font-size: 13px;
    font-weight: 900;
    margin-top: 5px;
}}
.comparison-section-head {{
    display: flex;
    align-items: center;
    gap: 10px;
    border-bottom: 1px solid {BORDER_COLOR};
    margin: -8px -8px 14px -8px;
    padding: 10px 12px 12px 12px;
}}
.comparison-section-icon {{
    width: 26px;
    height: 26px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}}
.comparison-section-icon img {{
    width: 24px !important;
    height: 24px !important;
    object-fit: contain;
}}
.comparison-section-title {{
    color: {PRIMARY_COLOR};
    font-size: 16px;
    font-weight: 900;
    text-transform: uppercase;
}}
.comparison-control-grid {{
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
}}
.comparison-control-card {{
    background: {WHITE_COLOR};
    border: 1px solid {BORDER_COLOR};
    min-height: 82px;
    padding: 12px;
    box-sizing: border-box;
    display: flex;
    gap: 10px;
    align-items: center;
}}
.comparison-control-icon {{
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    display: flex;
    align-items: center;
    justify-content: center;
}}
.comparison-control-icon img {{
    width: 40px !important;
    height: 40px !important;
    object-fit: contain;
}}
.comparison-control-label {{
    color: {MUTED_TEXT};
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
}}
.comparison-control-value {{
    color: {PRIMARY_COLOR};
    font-size: 18px;
    font-weight: 900;
    margin-top: 3px;
}}
.comparison-table-wrap {{
    width: 100%;
    overflow: auto;
    border: 1px solid {BORDER_COLOR};
    background: {WHITE_COLOR};
}}
.comparison-table {{
    width: 100%;
    min-width: 760px;
    border-collapse: collapse;
    background: {WHITE_COLOR};
    font-size: 13px;
}}
.comparison-table th {{
    position: sticky;
    top: 0;
    background: {LIGHT_BLUE};
    color: {PRIMARY_COLOR};
    border-bottom: 1px solid {BORDER_COLOR};
    padding: 10px 12px;
    text-align: center;
    font-weight: 900;
    white-space: nowrap;
}}
.comparison-table td {{
    color: {TEXT_COLOR};
    border-bottom: 1px solid #EEF2F7;
    padding: 10px 12px;
    text-align: center;
    font-weight: 700;
    white-space: nowrap;
}}
.comparison-table tr.best-row td {{
    background: #FFF7ED;
    color: {TEXT_COLOR};
    font-weight: 900;
    border-top: 2px solid {ORANGE};
    border-bottom: 2px solid {ORANGE};
}}
.comparison-badge-best {{
    display: inline-block;
    background: {ORANGE};
    color: {WHITE_COLOR};
    font-size: 11px;
    font-weight: 900;
    padding: 3px 8px;
    margin-left: 6px;
}}
.comparison-chart-card {{
    border: 1px solid {BORDER_COLOR};
    background: {WHITE_COLOR};
    padding: 12px;
    box-sizing: border-box;
    min-height: 360px;
}}
.comparison-chart-title {{
    color: {PRIMARY_COLOR};
    font-size: 14px;
    font-weight: 900;
    margin-bottom: 12px;
    text-transform: uppercase;
}}
.comparison-chart-area {{
    height: 260px;
    display: flex;
    align-items: flex-end;
    gap: 18px;
    overflow-x: auto;
    padding: 10px 8px 0 8px;
    border-left: 1px solid #CBD5E1;
    border-bottom: 1px solid #CBD5E1;
}}
.comparison-chart-group {{
    min-width: 116px;
    height: 240px;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    align-items: center;
}}
.comparison-bars {{
    height: 200px;
    display: flex;
    align-items: flex-end;
    gap: 10px;
}}
.comparison-bar-item {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-end;
    height: 200px;
}}
.comparison-bar-value {{
    color: {TEXT_COLOR};
    font-size: 10px;
    font-weight: 900;
    margin-bottom: 4px;
}}
.comparison-bar {{
    width: 28px;
    min-height: 2px;
}}
.comparison-algo-label {{
    color: {TEXT_COLOR};
    font-size: 11px;
    font-weight: 900;
    text-align: center;
    margin-top: 8px;
    min-height: 28px;
}}
.comparison-chart-legend {{
    display: flex;
    gap: 20px;
    justify-content: center;
    align-items: center;
    margin-top: 12px;
    color: {TEXT_COLOR};
    font-size: 12px;
    font-weight: 800;
}}
.comparison-legend-item {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
}}
.comparison-legend-box {{
    width: 16px;
    height: 12px;
    display: inline-block;
}}
.comparison-conclusion-list {{
    display: flex;
    flex-direction: column;
}}
.comparison-conclusion-item {{
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
.comparison-conclusion-item:last-child {{
    border-bottom: none;
}}
.comparison-check {{
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
.comparison-export-grid {{
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
}}
.comparison-print-button {{
    display: block;
    width: 100%;
    box-sizing: border-box;
    min-height: 38px;
    line-height: 38px;
    text-align: center;
    background: {PRIMARY_COLOR};
    color: {WHITE_COLOR} !important;
    text-decoration: none !important;
    font-weight: 900;
    border: 1px solid {PRIMARY_COLOR};
}}
.comparison-empty-note {{
    color: {MUTED_TEXT};
    font-size: 13px;
    font-weight: 700;
    padding: 16px 4px;
}}
.stButton > button {{
    border-radius: 0 !important;
    background: {PRIMARY_COLOR} !important;
    color: {WHITE_COLOR} !important;
    border: 1px solid {PRIMARY_COLOR} !important;
    font-weight: 900 !important;
}}
div[data-testid="stDownloadButton"] > button {{
    border-radius: 0 !important;
    background: {PRIMARY_COLOR} !important;
    color: {WHITE_COLOR} !important;
    border: 1px solid {PRIMARY_COLOR} !important;
    font-weight: 900 !important;
}}
@media print {{
    section[data-testid="stSidebar"], .app-header, .app-footer, div[data-testid="stToolbar"] {{
        display: none !important;
    }}
    .main .block-container {{
        padding: 12px !important;
    }}
}}
@media (max-width: 1100px) {{
    .comparison-control-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }}
    .comparison-export-grid {{
        grid-template-columns: 1fr;
    }}
}}
@media (max-width: 720px) {{
    .comparison-control-grid {{
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


def get_cpu_payload(cpu_payload: Any = None, payload: Any = None, **_: Any) -> dict[str, Any]:
    if isinstance(cpu_payload, dict) and cpu_payload:
        return cpu_payload

    if isinstance(payload, dict):
        if isinstance(payload.get("cpu"), dict):
            return payload.get("cpu") or {}
        if any(key in payload for key in ("result_map", "results", "preferred_result")):
            return payload

    session_payload = st.session_state.get("latest_simulation_payload")
    if isinstance(session_payload, dict):
        return session_payload

    return {}


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


def normalize_algorithm_name(name: Any) -> str:
    text = str(name or "Chưa có").strip()
    lower = text.lower().replace("_", " ").replace("-", " ")

    if "fcfs" in lower:
        return "FCFS"
    if "sjf" in lower or "shortest" in lower:
        return "SJF"
    if "priority" in lower or "ưu tiên" in lower:
        return "Priority"
    if "round" in lower or "rr" == lower:
        return "Round Robin"

    return text


def get_algorithm_name(result: Any) -> str:
    return normalize_algorithm_name(
        get_value(result, ["algorithm_name", "algorithm", "name", "label"], "Chưa có")
    )


def get_avg_waiting(result: Any) -> float:
    return to_float(
        get_value(result, ["average_waiting_time", "avg_waiting_time", "avg_waiting", "waiting"], 0),
        0,
    )


def get_avg_turnaround(result: Any) -> float:
    return to_float(
        get_value(result, ["average_turnaround_time", "avg_turnaround_time", "avg_turnaround", "turnaround"], 0),
        0,
    )


def get_avg_response(result: Any) -> float:
    return to_float(
        get_value(result, ["average_response_time", "avg_response_time", "avg_response", "response"], 0),
        0,
    )


def calculate_cpu_utilization(result: Any) -> float | None:
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


def build_comparison_rows(cpu_results: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sorted_results = sorted(cpu_results, key=lambda item: get_avg_waiting(item))

    for rank, result in enumerate(sorted_results, start=1):
        algorithm = get_algorithm_name(result)
        rows.append(
            {
                "rank": rank,
                "algorithm": algorithm,
                "avg_waiting": get_avg_waiting(result),
                "avg_turnaround": get_avg_turnaround(result),
                "avg_response": get_avg_response(result),
                "cpu_utilization": calculate_cpu_utilization(result),
                "note": cpu_note(algorithm, rank),
                "raw": result,
            }
        )

    return rows


def get_best_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    return rows[0] if rows else None


def render_section_head(title: str, icon_file: str, fallback: str = "▣") -> None:
    icon = icon_html(
        icon_file,
        size=26,
        color=PRIMARY_COLOR,
        class_name="comparison-section-icon-img",
        fallback=fallback,
    )
    st.markdown(
        f"""
<div class="comparison-section-head">
    <span class="comparison-section-icon">{icon}</span>
    <span class="comparison-section-title">{html.escape(title)}</span>
</div>
""",
        unsafe_allow_html=True,
    )


def render_page_title() -> None:
    st.markdown(
        """
<div class="comparison-title-box">
    <div class="comparison-title">SO SÁNH HIỆU QUẢ THUẬT TOÁN</div>
    <div class="comparison-subtitle">Đánh giá thời gian chờ và thời gian hoàn thành của các giải thuật lập lịch CPU</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_control_card(label: str, value: str, icon_file: str, color: str, fallback: str) -> str:
    icon = icon_html(icon_file, size=40, color=None, class_name="comparison-control-icon-img", fallback=fallback)
    return f"""
<div class="comparison-control-card">
    <div class="comparison-control-icon">{icon}</div>
    <div>
        <div class="comparison-control-label">{html.escape(label)}</div>
        <div class="comparison-control-value" style="color:{color};">{html.escape(value)}</div>
    </div>
</div>
"""


def render_control_panel(rows: list[dict[str, Any]], tasks: list[Any]) -> None:
    best = get_best_row(rows)
    best_name = best["algorithm"] if best else "---"
    best_wait = fmt_number(best["avg_waiting"]) if best else "---"
    now = datetime.now().strftime("%H:%M:%S")

    with bordered_container():
        render_section_head("ĐIỀU KHIỂN SO SÁNH REALTIME", "Comparison_Algorithm.png", "▥")
        cards = [
            render_control_card("Số thuật toán", str(len(rows)), "Choose_algorithm.png", PRIMARY_COLOR, "▤"),
            render_control_card("Thuật toán tốt nhất", best_name, "Best_Algorithm.png", ORANGE, "🏆"),
            render_control_card("Avg Waiting thấp nhất", best_wait, "AVG_Waiting.png", GREEN, "◷"),
            render_control_card("Cập nhật lúc", now, "Refresh.png", PRIMARY_COLOR, "↻"),
        ]
        st.markdown('<div class="comparison-control-grid">' + "\n".join(cards) + "</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 5])
        with c1:
            if st.button("Làm mới", use_container_width=True):
                set_footer_status("Đã làm mới dữ liệu so sánh thuật toán")
                st.rerun()
        with c2:
            st.toggle("Realtime", value=True, key="comparison_realtime_enabled")
        with c3:
            st.caption(f"Dữ liệu đang lấy từ kết quả mô phỏng mới nhất trong session_state. Tổng tác vụ hiện có: {len(tasks or [])}.")


def render_summary_table(rows: list[dict[str, Any]]) -> None:
    with bordered_container():
        render_section_head("BẢNG SO SÁNH TỔNG HỢP REALTIME", "Compare.png", "▤")

        if not rows:
            st.markdown('<div class="comparison-empty-note">Chưa có kết quả mô phỏng. Hãy chạy mô phỏng CPU trước khi so sánh.</div>', unsafe_allow_html=True)
            return

        body_parts: list[str] = []
        for row in rows:
            is_best = row["rank"] == 1
            badge = '<span class="comparison-badge-best">TỐT NHẤT</span>' if is_best else ""
            css_class = ' class="best-row"' if is_best else ""
            body_parts.append(
                f"""
<tr{css_class}>
    <td>{html.escape(str(row['rank']))}</td>
    <td>{html.escape(row['algorithm'])}{badge}</td>
    <td>{html.escape(fmt_number(row['avg_waiting']))}</td>
    <td>{html.escape(fmt_number(row['avg_turnaround']))}</td>
    <td>{html.escape(fmt_number(row['avg_response']))}</td>
    <td>{html.escape(row['note'])}</td>
</tr>
"""
            )

        table_html = f"""
<div class="comparison-table-wrap">
    <table class="comparison-table">
        <thead>
            <tr>
                <th>Xếp hạng</th>
                <th>Thuật toán</th>
                <th>Avg Waiting Time</th>
                <th>Avg Turnaround Time</th>
                <th>Avg Response Time</th>
                <th>Nhận xét</th>
            </tr>
        </thead>
        <tbody>{''.join(body_parts)}</tbody>
    </table>
</div>
"""
        st.markdown(table_html, unsafe_allow_html=True)


def render_chart(rows: list[dict[str, Any]]) -> None:
    with bordered_container():
        render_section_head("BIỂU ĐỒ SO SÁNH AVG WAITING & AVG TURNAROUND", "Chart.png", "▥")

        if not rows:
            st.markdown('<div class="comparison-empty-note">Chưa có dữ liệu để vẽ biểu đồ.</div>', unsafe_allow_html=True)
            return

        max_value = max(
            max(row["avg_waiting"], row["avg_turnaround"])
            for row in rows
        ) or 1

        groups: list[str] = []
        for row in rows:
            algorithm = row["algorithm"]
            color = ALGORITHM_COLORS.get(algorithm, PRIMARY_COLOR)
            waiting_height = max(2, row["avg_waiting"] / max_value * 190)
            turnaround_height = max(2, row["avg_turnaround"] / max_value * 190)
            groups.append(
                f"""
<div class="comparison-chart-group">
    <div class="comparison-bars">
        <div class="comparison-bar-item">
            <div class="comparison-bar-value">{html.escape(fmt_number(row['avg_waiting']))}</div>
            <div class="comparison-bar" style="height:{waiting_height:.1f}px;background:{color};"></div>
        </div>
        <div class="comparison-bar-item">
            <div class="comparison-bar-value">{html.escape(fmt_number(row['avg_turnaround']))}</div>
            <div class="comparison-bar" style="height:{turnaround_height:.1f}px;background:{RED};"></div>
        </div>
    </div>
    <div class="comparison-algo-label">{html.escape(algorithm)}</div>
</div>
"""
            )

        st.markdown(
            f"""
<div class="comparison-chart-card" id="comparison-chart-print-area">
    <div class="comparison-chart-title">Thời gian trung bình theo thuật toán</div>
    <div class="comparison-chart-area">{''.join(groups)}</div>
    <div class="comparison-chart-legend">
        <span class="comparison-legend-item"><span class="comparison-legend-box" style="background:{PRIMARY_COLOR};"></span>Avg Waiting Time</span>
        <span class="comparison-legend-item"><span class="comparison-legend-box" style="background:{RED};"></span>Avg Turnaround Time</span>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )


def build_conclusions(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return ["Chưa có dữ liệu so sánh. Hãy chạy mô phỏng CPU để hệ thống tự đánh giá thuật toán phù hợp."]

    best = rows[0]
    worst = max(rows, key=lambda row: row["avg_waiting"])
    response_best = min(rows, key=lambda row: row["avg_response"])

    lines = [
        f"{best['algorithm']} đang là thuật toán tốt nhất theo Avg Waiting Time ({fmt_number(best['avg_waiting'])}).",
        f"{best['algorithm']} cũng có Avg Turnaround Time là {fmt_number(best['avg_turnaround'])}, phù hợp để giảm thời gian lưu lại trong hệ thống.",
        f"{response_best['algorithm']} có Avg Response Time tốt nhất ({fmt_number(response_best['avg_response'])}), hữu ích khi cần phản hồi nhanh cho tác vụ đầu tiên.",
        f"{worst['algorithm']} có Avg Waiting Time cao nhất ({fmt_number(worst['avg_waiting'])}), nên cân nhắc khi số lượng tác vụ tăng.",
        "Kết quả có thể thay đổi khi danh sách tác vụ, burst time, độ ưu tiên hoặc quantum thay đổi.",
    ]
    return lines


def render_conclusion(rows: list[dict[str, Any]]) -> None:
    with bordered_container():
        render_section_head("NHẬN XÉT & KẾT LUẬN", "Comment.png", "●")
        item_html = "".join(
            f"""
<div class="comparison-conclusion-item">
    <span class="comparison-check">✓</span>
    <span>{html.escape(item)}</span>
</div>
"""
            for item in build_conclusions(rows)
        )
        st.markdown(f'<div class="comparison-conclusion-list">{item_html}</div>', unsafe_allow_html=True)


def rows_to_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Thuật toán": row["algorithm"],
                "Avg Waiting Time": row["avg_waiting"],
                "Avg Turnaround Time": row["avg_turnaround"],
                "Avg Response Time": row["avg_response"],
                "Nhận xét": row["note"],
            }
            for row in rows
        ]
    )


def build_pdf_bytes(rows: list[dict[str, Any]]) -> bytes | None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except Exception:
        return None

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="Bao cao so sanh thuat toan")
    styles = getSampleStyleSheet()
    story = [
        Paragraph("BAO CAO SO SANH HIEU QUA THUAT TOAN", styles["Title"]),
        Spacer(1, 12),
        Paragraph("Danh gia Avg Waiting Time, Avg Turnaround Time va Avg Response Time.", styles["Normal"]),
        Spacer(1, 12),
    ]

    data = [["Thuat toan", "Avg Waiting", "Avg Turnaround", "Avg Response", "Nhan xet"]]
    for row in rows:
        data.append([
            row["algorithm"],
            fmt_number(row["avg_waiting"]),
            fmt_number(row["avg_turnaround"]),
            fmt_number(row["avg_response"]),
            row["note"],
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PRIMARY_COLOR)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER_COLOR)),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    return buffer.getvalue()


def render_export_panel(rows: list[dict[str, Any]]) -> None:
    with bordered_container():
        render_section_head("XUẤT BÁO CÁO", "Export_Report.png", "▣")

        if not rows:
            st.markdown('<div class="comparison-empty-note">Chưa có dữ liệu để xuất báo cáo.</div>', unsafe_allow_html=True)
            return

        df = rows_to_dataframe(rows)
        csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
        pdf_bytes = build_pdf_bytes(rows)

        col1, col2, col3 = st.columns(3, gap="medium")
        with col1:
            st.download_button(
                "Xuất CSV",
                data=csv_bytes,
                file_name="so_sanh_thuat_toan.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with col2:
            if pdf_bytes:
                st.download_button(
                    "Xuất PDF",
                    data=pdf_bytes,
                    file_name="so_sanh_thuat_toan.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.button("Xuất PDF", disabled=True, use_container_width=True)
                st.caption("Cài thêm reportlab để bật xuất PDF.")
        with col3:
            st.markdown(
                '<a class="comparison-print-button" href="javascript:window.print()">In biểu đồ</a>',
                unsafe_allow_html=True,
            )


def render_comparison_page(
    tasks: list[Any] | None = None,
    cpu_payload: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    **kwargs: Any,
) -> None:
    inject_comparison_css()

    current_tasks = tasks if tasks is not None else st.session_state.get("tasks", [])
    cpu_data = get_cpu_payload(cpu_payload=cpu_payload, payload=payload, **kwargs)
    results = get_cpu_results(cpu_data)
    rows = build_comparison_rows(results)
    st.session_state["latest_comparison_rows"] = rows

    st.markdown('<div class="comparison-page-wrap">', unsafe_allow_html=True)
    render_page_title()
    render_control_panel(rows, current_tasks)
    render_summary_table(rows)

    chart_col, conclusion_col = st.columns([0.62, 0.38], gap="medium")
    with chart_col:
        render_chart(rows)
    with conclusion_col:
        render_conclusion(rows)

    render_export_panel(rows)
    st.markdown("</div>", unsafe_allow_html=True)

    if rows:
        best = rows[0]
        set_footer_status(f"So sánh hoàn tất - thuật toán đề xuất: {best['algorithm']}")


# Aliases để streamlit_app.py tự nhận diện renderer.
def render_page(**kwargs: Any) -> None:
    render_comparison_page(**kwargs)


def show_comparison_page(**kwargs: Any) -> None:
    render_comparison_page(**kwargs)


def render(**kwargs: Any) -> None:
    render_comparison_page(**kwargs)


def main() -> None:
    render_comparison_page()


app = render_comparison_page


if __name__ == "__main__":
    main()
