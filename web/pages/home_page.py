"""Trang chủ bám giao diện desktop cũ cho bản web Streamlit."""

from __future__ import annotations

import html

import streamlit as st

from web.components import ensure_session_state, icon_html, render_html, section_title
from web.styles import PRIMARY_COLOR


def _page_href(page_key: str) -> str:
    return f"?page={page_key}"


def _quick_action_card(
    icon_file: str,
    fallback: str,
    title: str,
    description: str,
    page_key: str,
) -> str:
    icon = icon_html(icon_file, size=54, fallback=fallback)
    return f"""
    <a class="home-quick-link" href="{_page_href(page_key)}" target="_self">
        <div class="home-quick-card">
            <div class="home-quick-icon">{icon}</div>
            <div>
                <div class="home-quick-title">{html.escape(title)}</div>
                <div class="home-quick-desc">{html.escape(description)}</div>
            </div>
        </div>
    </a>
    """


def _info_item(
    icon_file: str,
    fallback: str,
    title: str,
    description: str,
) -> str:
    icon = icon_html(icon_file, size=30, color=PRIMARY_COLOR, fallback=fallback)
    return f"""
    <div class="home-info-item">
        <div class="home-info-icon">{icon}</div>
        <div>
            <div class="home-info-name">{html.escape(title)}</div>
            <div class="home-info-desc">{html.escape(description)}</div>
        </div>
    </div>
    """


def _process_step(
    number: int,
    icon_file: str,
    fallback: str,
    title: str,
    description: str,
) -> str:
    icon = icon_html(icon_file, size=54, fallback=fallback)
    return f"""
    <div class="process-step">
        <div class="process-number">{number}</div>
        <div class="process-icon-circle">{icon}</div>
        <div class="process-title">{html.escape(title)}</div>
        <div class="process-desc">{html.escape(description)}</div>
    </div>
    """


def _algorithm_card(
    icon_file: str,
    fallback: str,
    title: str,
    description: str,
) -> str:
    icon = icon_html(icon_file, size=64, fallback=fallback)
    return f"""
    <div class="home-algo-card">
        <div class="home-algo-icon">{icon}</div>
        <div>
            <div class="home-algo-name">{html.escape(title)}</div>
            <div class="home-algo-desc">{html.escape(description)}</div>
        </div>
    </div>
    """


def render() -> None:
    ensure_session_state()

    # Trang Home không render header/sidebar/footer ở đây.
    # Các phần đó được streamlit_app.py render một lần duy nhất để tránh chồng layout và tránh lộ HTML thô.

    customer_icon = icon_html("Customer.png", size=(96, 96), fallback="👤")
    queue_icon = icon_html("HERO_queue.png", size=(132, 92), fallback="1 2 ... n")
    photocopier_icon = icon_html("Photocopier.png", size=(108, 96), fallback="🖨️")
    done_icon = icon_html("Done.png", size=(92, 96), fallback="✅")

    quick_cards = "\n".join(
        [
            _quick_action_card(
                "Manager.png",
                "📋",
                "Quản lý tác vụ",
                "Thêm, sửa, nhập danh sách tác vụ",
                "task",
            ),
            _quick_action_card(
                "Simulation.png",
                "▶",
                "Chạy mô phỏng",
                "Mô phỏng FCFS, SJF, Priority, Round Robin",
                "simulation",
            ),
            _quick_action_card(
                "Compare_Algorithms.png",
                "⚖",
                "So sánh thuật toán",
                "Đánh giá thời gian chờ và hoàn thành",
                "comparison",
            ),
            _quick_action_card(
                "H_Report.png",
                "PDF",
                "Xuất tác vụ",
                "Mở danh sách tác vụ để xuất PDF/CSV",
                "report",
            ),
        ]
    )

    info_items = "\n".join(
        [
            _info_item(
                "Topic.png",
                "▣",
                "Đề tài",
                "Mô phỏng xử lý tác vụ photocopy",
            ),
            _info_item(
                "Field.png",
                "□",
                "Lĩnh vực",
                "Hệ điều hành",
            ),
            _info_item(
                "Target.png",
                "◎",
                "Mục tiêu",
                "So sánh hiệu quả các giải thuật lập lịch",
            ),
            _info_item(
                "Data.png",
                "▤",
                "Dữ liệu",
                "Tác vụ in, sao chép, scan",
            ),
        ]
    )

    process_steps = "\n".join(
        [
            _process_step(
                1,
                "Import_task.png",
                "➕",
                "Nhập tác vụ",
                "Thêm và cấu hình danh sách tác vụ",
            ),
            '<div class="process-arrow">→</div>',
            _process_step(
                2,
                "Choose_algorithm.png",
                "☷",
                "Chọn thuật toán",
                "Chọn giải thuật lập lịch",
            ),
            '<div class="process-arrow">→</div>',
            _process_step(
                3,
                "Simulation.png",
                "▶",
                "Chạy mô phỏng",
                "Tiến hành mô phỏng",
            ),
            '<div class="process-arrow">→</div>',
            _process_step(
                4,
                "Process_result.png",
                "▴",
                "Xem kết quả",
                "Xem thời gian chờ",
            ),
        ]
    )

    algorithm_cards = "\n".join(
        [
            _algorithm_card(
                "FCFS.png",
                "1",
                "FCFS",
                "Xử lý theo thứ tự đến trước",
            ),
            _algorithm_card(
                "SJF.png",
                "2",
                "SJF",
                "Ưu tiên tác vụ có thời gian xử lý ngắn",
            ),
            _algorithm_card(
                "Priority.png",
                "3",
                "Priority",
                "Ưu tiên theo mức độ quan trọng",
            ),
            _algorithm_card(
                "Round_Robin.png",
                "4",
                "Round Robin",
                "Chia thời gian xử lý theo quantum",
            ),
        ]
    )

    info_title_icon = icon_html("Data.png", size=30, color=PRIMARY_COLOR, fallback="▤")
    fast_icon = icon_html("Fast.png", size=26, color=PRIMARY_COLOR, fallback="⚡")
    process_icon = icon_html("Process.png", size=26, color=PRIMARY_COLOR, fallback="▥")
    algo_icon = icon_html("Comparison_Algorithm.png", size=26, color=PRIMARY_COLOR, fallback="⌘")

    render_html(
        f"""
        <div class="home-desktop">
            <div class="home-hero">
                <div class="home-hero-left">
                    <h2 class="home-hero-title">
                        MÔ PHỎNG HỆ THỐNG<br>
                        XẾP HÀNG PHOTOCOPY
                    </h2>
                    <div class="red-line"></div>
                    <div class="home-hero-desc">
                        Ứng dụng mô phỏng và so sánh các giải thuật lập lịch CPU
                        trong xử lý tác vụ photocopy
                    </div>
                </div>

                <div class="home-flow">
                    <div class="home-flow-node">
                        <div class="home-flow-icon">{customer_icon}</div>
                        <div class="home-flow-label">Khách hàng</div>
                    </div>
                    <div class="home-flow-arrow">→</div>
                    <div class="home-flow-node">
                        <div class="home-flow-icon">{queue_icon}</div>
                        <div class="home-flow-label">Hàng đợi</div>
                    </div>
                    <div class="home-flow-arrow">→</div>
                    <div class="home-flow-node">
                        <div class="home-flow-icon">{photocopier_icon}</div>
                        <div class="home-flow-label">Máy photocopy</div>
                    </div>
                    <div class="home-flow-arrow">→</div>
                    <div class="home-flow-node">
                        <div class="home-flow-icon">{done_icon}</div>
                        <div class="home-flow-label">Tác vụ hoàn thành</div>
                    </div>
                </div>
            </div>

            <div class="home-main-grid">
                <div class="home-left-stack">
                    <div class="home-panel">
                        <div class="web-section-title">
                            {fast_icon}
                            <span>THAO TÁC NHANH</span>
                        </div>

                        <div class="home-quick-grid">
                            {quick_cards}
                        </div>
                    </div>

                    <div class="home-panel">
                        <div class="web-section-title">
                            {process_icon}
                            <span>QUY TRÌNH MÔ PHỎNG</span>
                        </div>

                        <div class="home-process">
                            {process_steps}
                        </div>
                    </div>

                    <div class="home-panel">
                        <div class="web-section-title">
                            {algo_icon}
                            <span>TỔNG QUAN GIẢI THUẬT</span>
                        </div>

                        <div class="home-algo-grid">
                            {algorithm_cards}
                        </div>
                    </div>
                </div>

                <div class="home-info-panel">
                    <div class="home-info-title">
                        {info_title_icon}
                        <span>THÔNG TIN ĐỀ TÀI</span>
                    </div>

                    {info_items}
                </div>
            </div>
        </div>
        """
    )


# Alias để streamlit_app.py có thể gọi linh hoạt
render_home_page = render
show_home_page = render
render_page = render
main = render
app = render
