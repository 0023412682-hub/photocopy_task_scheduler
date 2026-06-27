from __future__ import annotations

import streamlit as st


# =========================================================
# THEME CONSTANTS
# =========================================================
PRIMARY_COLOR = "#005BAC"
DARK_BLUE = "#004A99"
ACCENT_COLOR = "#D71920"

BACKGROUND_COLOR = "#F4F7FB"
WHITE_COLOR = "#FFFFFF"
TEXT_COLOR = "#1F2937"
MUTED_TEXT = "#64748B"
BORDER_COLOR = "#D9E2EC"
LIGHT_BLUE = "#EAF4FF"

# Các màu bổ sung để các page khác import không bị lỗi
GREEN = "#16A34A"
ORANGE = "#F97316"
RED = "#DC2626"
PURPLE = "#7C3AED"
TEAL = "#0891B2"

SUCCESS_COLOR = GREEN
WARNING_COLOR = ORANGE
ERROR_COLOR = RED
INFO_COLOR = TEAL

HEADER_HEIGHT = 122
FOOTER_HEIGHT = 34
SIDEBAR_WIDTH = 260


# =========================================================
# GLOBAL CSS
# =========================================================
def get_global_css() -> str:
    return f"""
<style>
:root {{
    --primary-color: {PRIMARY_COLOR};
    --dark-blue: {DARK_BLUE};
    --accent-color: {ACCENT_COLOR};
    --background-color: {BACKGROUND_COLOR};
    --white-color: {WHITE_COLOR};
    --text-color: {TEXT_COLOR};
    --muted-text: {MUTED_TEXT};
    --border-color: {BORDER_COLOR};
    --light-blue: {LIGHT_BLUE};

    --green: {GREEN};
    --orange: {ORANGE};
    --red: {RED};
    --purple: {PURPLE};
    --teal: {TEAL};

    --header-height: {HEADER_HEIGHT}px;
    --footer-height: {FOOTER_HEIGHT}px;
    --sidebar-width: {SIDEBAR_WIDTH}px;
}}

html,
body,
.stApp {{
    background: var(--background-color) !important;
    color: var(--text-color);
    font-family: Arial, Helvetica, sans-serif;
}}

#MainMenu,
footer,
header[data-testid="stHeader"],
div[data-testid="stToolbar"],
div[data-testid="stDecoration"] {{
    display: none !important;
    visibility: hidden !important;
}}

div[data-testid="stAppViewContainer"] {{
    background: var(--background-color) !important;
}}

/* ======================================================
   MAIN CONTENT - FORCE FULL WIDTH
   ====================================================== */
.main .block-container,
.block-container,
div.block-container,
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"],
section[data-testid="stMain"] > div,
main > div {{
    max-width: none !important;
    width: 100% !important;
    padding-top: 80px !important;
    padding-left: 0px !important;
    padding-right: 0px !important;
    padding-bottom: calc(var(--footer-height) + 12px) !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    box-sizing: border-box !important;
}}

section[data-testid="stMain"],
div[data-testid="stMain"],
main,
.main {{
    max-width: none !important;
    width: 100% !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}}

div[data-testid="stAppViewContainer"],
div[data-testid="stAppViewBlockContainer"],
div[data-testid="stMainBlockContainer"] {{
    max-width: none !important;
    width: 100% !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    overflow-x: hidden !important;
}}

[data-testid="stVerticalBlock"] {{
    gap: 0.75rem;
}}

[data-testid="stMarkdownContainer"] p {{
    margin-bottom: 0;
}}


/* ======================================================
   HEADER
   ====================================================== */
.app-header {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: var(--header-height);
    z-index: 9999;
    background: var(--white-color);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    box-sizing: border-box;
    padding: 12px 28px;
}}

.app-header-left {{
    display: flex;
    align-items: center;
    min-width: 430px;
    flex-shrink: 0;
}}

.app-logo-group {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-right: 18px;
}}

.app-header-logo {{
    width: 72px !important;
    height: 72px !important;
    object-fit: contain;
    display: block;
}}

.app-school-text {{
    line-height: 1.15;
}}

.app-school-name {{
    font-size: 18px;
    font-weight: 900;
    color: var(--primary-color);
    letter-spacing: 0.2px;
    margin-bottom: 4px;
    text-transform: uppercase;
}}

.app-faculty-name {{
    font-size: 17px;
    font-weight: 900;
    color: var(--primary-color);
    letter-spacing: 0.2px;
    margin-bottom: 3px;
    text-transform: uppercase;
}}

.app-school-subtitle {{
    font-size: 7.3px;
    font-weight: 900;
    color: var(--primary-color);
    letter-spacing: 0.1px;
    text-transform: uppercase;
}}

.app-header-divider {{
    width: 2px;
    height: 76px;
    background: var(--border-color);
    margin: 0 28px;
    flex-shrink: 0;
}}

.app-header-title-area {{
    flex: 1;
    text-align: center;
    padding-right: 18px;
}}

.app-header-title {{
    margin: 0;
    color: var(--primary-color);
    font-size: clamp(24px, 2vw, 34px);
    font-weight: 900;
    line-height: 1.12;
    letter-spacing: 0.2px;
    text-transform: uppercase;
}}

.app-header-subtitle {{
    margin-top: 8px;
    color: var(--accent-color);
    font-size: clamp(10px, 0.82vw, 13px);
    font-weight: 900;
    line-height: 1.2;
    text-transform: uppercase;
}}


/* ======================================================
   SIDEBAR
   ====================================================== */
section[data-testid="stSidebar"] {{
    width: var(--sidebar-width) !important;
    min-width: var(--sidebar-width) !important;
    max-width: var(--sidebar-width) !important;
    background: var(--primary-color) !important;
    border-right: none !important;
}}

section[data-testid="stSidebar"] > div {{
    width: var(--sidebar-width) !important;
    background: var(--primary-color) !important;
}}

div[data-testid="stSidebarContent"] {{
    background: var(--primary-color) !important;
    padding-top: calc(var(--header-height) + 14px) !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    padding-bottom: calc(var(--footer-height) + 14px) !important;
}}

button[kind="header"] {{
    display: none !important;
}}

.web-sidebar {{
    width: 100%;
    min-height: calc(100vh - var(--header-height) - var(--footer-height) - 34px);
    display: flex;
    flex-direction: column;
}}

.web-sidebar-menu {{
    width: 100%;
}}

.web-sidebar-menu a {{
    text-decoration: none !important;
}}

.web-menu-item {{
    display: flex;
    align-items: center;
    min-height: 56px;
    box-sizing: border-box;
    margin: 0 12px 10px 12px;
    padding: 0 14px;
    background: var(--primary-color);
    color: var(--white-color);
    border: 1px solid transparent;
    border-radius: 0;
    transition: all 0.15s ease;
}}

.web-menu-item:hover {{
    background: var(--dark-blue);
    color: var(--white-color);
}}

.web-menu-item.active {{
    background: var(--white-color);
    color: var(--primary-color);
    border-color: var(--white-color);
}}

.web-menu-icon {{
    width: 34px;
    height: 34px;
    margin-right: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}}

.web-menu-icon img {{
    width: 28px !important;
    height: 28px !important;
    object-fit: contain;
    display: block;
}}

.web-menu-text {{
    font-size: 13px;
    font-weight: 800;
    line-height: 1.25;
    white-space: normal;
}}

.icon-fallback {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    font-weight: 800;
    line-height: 1;
}}


/* ======================================================
   SIDEBAR SYSTEM INFO
   ====================================================== */
.system-info-card {{
    background: var(--light-blue);
    margin: auto 14px 10px 14px;
    padding: 14px 14px 12px 14px;
    box-sizing: border-box;
    border: 1px solid rgba(255, 255, 255, 0.36);
}}

.system-info-title {{
    color: var(--primary-color);
    font-size: 12px;
    font-weight: 900;
    text-align: center;
    margin-bottom: 12px;
    text-transform: uppercase;
}}

.system-info-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 8px 0;
    color: var(--text-color);
    font-size: 11px;
}}

.system-info-row .sys-icon {{
    width: 18px;
    color: var(--primary-color);
    text-align: center;
    flex-shrink: 0;
}}

.system-info-row .sys-label {{
    flex: 1;
    color: var(--text-color);
    font-weight: 600;
}}

.system-info-row .sys-value {{
    color: var(--text-color);
    font-weight: 700;
    text-align: right;
}}


/* ======================================================
   FOOTER
   ====================================================== */
.app-footer {{
    position: relative !important;
    left: auto !important;
    right: auto !important;
    bottom: auto !important;
    height: var(--footer-height);
    z-index: 1 !important;
    background: var(--primary-color);
    color: var(--white-color);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    box-sizing: border-box;
    font-size: 12px;
    font-weight: 700;
    margin-top: 10px !important;
}}

.app-footer-left,
.app-footer-right {{
    color: var(--white-color);
    line-height: var(--footer-height);
}}

.app-footer-status-dot {{
    font-size: 10px;
    margin-right: 6px;
}}


/* ======================================================
   COMMON PAGE ELEMENTS
   ====================================================== */
.web-card,
.section-card {{
    background: var(--white-color);
    border: 1px solid var(--border-color);
    padding: 18px;
    box-sizing: border-box;
    margin-bottom: 14px;
    color: var(--text-color);
}}

.web-card-title {{
    color: var(--primary-color);
    font-size: 18px;
    font-weight: 900;
    margin-bottom: 12px;
    text-transform: uppercase;
}}

.web-section-title {{
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--primary-color);
    font-size: 18px;
    font-weight: 900;
    text-transform: uppercase;
    margin: 2px 0 14px 0;
}}

.web-section-title img {{
    width: 26px !important;
    height: 26px !important;
    object-fit: contain;
    display: inline-block;
}}

.web-section-subtitle {{
    color: var(--muted-text);
    font-size: 13px;
    margin-top: -8px;
    margin-bottom: 14px;
}}

.web-muted {{
    color: var(--muted-text);
}}

.web-primary {{
    color: var(--primary-color);
}}

.web-accent {{
    color: var(--accent-color);
}}


/* ======================================================
   HOME PAGE - DESKTOP STYLE
   ====================================================== */
.home-desktop {{
    width: 100%;
}}

.home-hero {{
    background: var(--light-blue);
    border: 1px solid var(--border-color);
    min-height: 180px;
    padding: 24px 34px;
    box-sizing: border-box;
    display: grid;
    grid-template-columns: minmax(300px, 0.92fr) minmax(520px, 1.55fr);
    gap: 30px;
    align-items: center;
    margin-bottom: 12px;
}}

.home-hero-title {{
    color: var(--primary-color);
    font-size: clamp(26px, 2.35vw, 34px);
    font-weight: 900;
    line-height: 1.16;
    text-transform: uppercase;
    margin: 0;
}}

.red-line {{
    width: 54px;
    height: 4px;
    background: var(--accent-color);
    margin: 14px 0 14px 0;
}}

.home-hero-desc {{
    color: var(--text-color);
    font-size: 14px;
    font-weight: 600;
    line-height: 1.45;
    max-width: 430px;
}}

.home-flow {{
    display: grid;
    grid-template-columns: 1fr 34px 1.2fr 34px 1fr 34px 1fr;
    align-items: center;
    gap: 10px;
}}

.home-flow-node {{
    text-align: center;
    color: var(--text-color);
    font-size: 11px;
    font-weight: 800;
}}

.home-flow-icon {{
    min-height: 88px;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.home-flow-icon img {{
    max-width: 100%;
    object-fit: contain;
}}

.home-flow-label {{
    margin-top: 6px;
}}

.home-flow-arrow {{
    color: var(--text-color);
    text-align: center;
    font-size: 30px;
    font-weight: 800;
    margin-top: -4px;
}}

.home-main-grid {{
    display: grid;
    grid-template-columns: minmax(0, 4.6fr) minmax(210px, 0.9fr);
    gap: 12px;
    align-items: stretch;
}}

.home-left-stack {{
    display: flex;
    flex-direction: column;
    gap: 12px;
}}

.home-panel {{
    background: var(--white-color);
    border: 1px solid var(--border-color);
    padding: 18px 20px 18px 20px;
    box-sizing: border-box;
}}

.home-quick-grid {{
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
}}

.home-quick-link {{
    text-decoration: none !important;
    color: inherit !important;
}}

.home-quick-card {{
    min-height: 102px;
    background: var(--white-color);
    border: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    padding: 14px 16px;
    box-sizing: border-box;
    transition: all 0.15s ease;
}}

.home-quick-card:hover {{
    border-color: var(--primary-color);
    box-shadow: 0 4px 12px rgba(0, 91, 172, 0.12);
    transform: translateY(-1px);
}}

.home-quick-icon {{
    width: 72px;
    height: 72px;
    border-radius: 50%;
    background: var(--light-blue);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-right: 16px;
}}

.home-quick-icon img {{
    width: 54px !important;
    height: 54px !important;
    object-fit: contain;
}}

.home-quick-title {{
    color: var(--primary-color);
    font-size: 13px;
    font-weight: 900;
    margin-bottom: 8px;
    line-height: 1.2;
}}

.home-quick-desc {{
    color: var(--text-color);
    font-size: 11px;
    font-weight: 600;
    line-height: 1.35;
}}

.home-info-panel {{
    background: var(--white-color);
    border: 1px solid var(--border-color);
    padding: 18px 18px;
    box-sizing: border-box;
    min-height: 100%;
}}

.home-info-title {{
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--primary-color);
    font-size: 15px;
    font-weight: 900;
    text-transform: uppercase;
    margin-bottom: 16px;
}}

.home-info-title img {{
    width: 30px !important;
    height: 30px !important;
}}

.home-info-item {{
    display: grid;
    grid-template-columns: 38px minmax(0, 1fr);
    gap: 12px;
    padding: 13px 0;
    border-bottom: 1px solid var(--border-color);
}}

.home-info-item:last-child {{
    border-bottom: none;
}}

.home-info-icon {{
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding-top: 2px;
}}

.home-info-icon img {{
    width: 30px !important;
    height: 30px !important;
    object-fit: contain;
}}

.home-info-name {{
    color: var(--primary-color);
    font-size: 12px;
    font-weight: 900;
    margin-bottom: 5px;
}}

.home-info-desc {{
    color: var(--text-color);
    font-size: 10.5px;
    font-weight: 600;
    line-height: 1.35;
}}

.home-process {{
    display: grid;
    grid-template-columns: 1fr 0.55fr 1fr 0.55fr 1fr 0.55fr 1fr;
    align-items: start;
    gap: 8px;
    padding: 4px 10px 0 10px;
}}

.process-step {{
    text-align: center;
    position: relative;
}}

.process-number {{
    position: absolute;
    top: 0;
    left: calc(50% - 46px);
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: var(--primary-color);
    color: var(--white-color);
    font-size: 13px;
    font-weight: 900;
    line-height: 28px;
    z-index: 2;
}}

.process-icon-circle {{
    width: 86px;
    height: 86px;
    border-radius: 50%;
    border: 1.5px dashed #A9C8E8;
    margin: 15px auto 13px auto;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--white-color);
}}

.process-icon-circle img {{
    width: 54px !important;
    height: 54px !important;
    object-fit: contain;
}}

.process-title {{
    color: var(--primary-color);
    font-size: 12px;
    font-weight: 900;
    margin-bottom: 8px;
}}

.process-desc {{
    color: var(--text-color);
    font-size: 10.5px;
    font-weight: 600;
    line-height: 1.35;
}}

.process-arrow {{
    color: var(--primary-color);
    font-size: 46px;
    font-weight: 400;
    text-align: center;
    padding-top: 50px;
}}

.home-algo-grid {{
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
}}

.home-algo-card {{
    background: var(--white-color);
    border: 1px solid var(--border-color);
    min-height: 84px;
    padding: 10px 14px;
    box-sizing: border-box;
    display: flex;
    align-items: center;
}}

.home-algo-icon {{
    width: 68px;
    height: 68px;
    flex-shrink: 0;
    margin-right: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.home-algo-icon img {{
    width: 64px !important;
    height: 64px !important;
    object-fit: contain;
}}

.home-algo-name {{
    color: var(--primary-color);
    font-size: 13px;
    font-weight: 900;
    margin-bottom: 8px;
}}

.home-algo-desc {{
    color: var(--text-color);
    font-size: 10.5px;
    font-weight: 600;
    line-height: 1.35;
}}


/* ======================================================
   COMPATIBLE CARDS FOR OTHER PAGES
   ====================================================== */
.quick-card {{
    background: var(--white-color);
    border: 1px solid var(--border-color);
    padding: 16px;
    min-height: 126px;
    box-sizing: border-box;
}}

.quick-card-title {{
    color: var(--primary-color);
    font-weight: 900;
}}

.quick-card-desc {{
    color: var(--muted-text);
}}

.home-metric-card,
.web-metric-card {{
    background: var(--white-color);
    border: 1px solid var(--border-color);
    padding: 16px;
    box-sizing: border-box;
}}

.web-metric-label {{
    color: var(--muted-text);
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 6px;
}}

.web-metric-value {{
    color: var(--primary-color);
    font-size: 24px;
    font-weight: 900;
}}

.web-grid {{
    display: grid;
    gap: 14px;
}}

.web-grid-2 {{
    grid-template-columns: repeat(2, minmax(0, 1fr));
}}

.web-grid-3 {{
    grid-template-columns: repeat(3, minmax(0, 1fr));
}}

.web-grid-4 {{
    grid-template-columns: repeat(4, minmax(0, 1fr));
}}


/* ======================================================
   STREAMLIT WIDGET POLISH
   ====================================================== */
.stButton > button {{
    border-radius: 0 !important;
    border: 1px solid var(--border-color) !important;
    font-weight: 700 !important;
}}

.stButton > button:hover {{
    border-color: var(--primary-color) !important;
    color: var(--primary-color) !important;
}}

div[data-testid="stMetric"],
div[data-testid="stDataFrame"] {{
    border: 1px solid var(--border-color);
}}

hr {{
    border-color: var(--border-color);
}}


/* ======================================================
   RESPONSIVE
   ====================================================== */
@media (max-width: 1280px) {{
    .home-hero {{
        grid-template-columns: 1fr;
    }}

    .home-flow {{
        max-width: 920px;
    }}

    .home-main-grid {{
        grid-template-columns: 1fr;
    }}
}}

@media (max-width: 1100px) {{
    .app-header {{
        padding-left: 18px;
        padding-right: 18px;
    }}

    .app-header-left {{
        min-width: 360px;
    }}

    .app-header-logo {{
        width: 58px !important;
        height: 58px !important;
    }}

    .app-school-name {{
        font-size: 15px;
    }}

    .app-faculty-name {{
        font-size: 14px;
    }}

    .app-school-subtitle {{
        font-size: 6.5px;
    }}

    .app-header-divider {{
        margin: 0 18px;
    }}

    .home-quick-grid,
    .home-algo-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }}
}}

@media (max-width: 820px) {{
    :root {{
        --sidebar-width: 230px;
    }}

    .app-header-left {{
        min-width: 250px;
    }}

    .app-header-title {{
        font-size: 19px;
    }}

    .app-header-subtitle {{
        font-size: 9px;
    }}

    .app-header-divider {{
        display: none;
    }}

    .home-flow,
    .home-process {{
        grid-template-columns: 1fr;
    }}

    .home-flow-arrow,
    .process-arrow {{
        padding-top: 0;
        transform: rotate(90deg);
    }}

    .home-quick-grid,
    .home-algo-grid,
    .web-grid-2,
    .web-grid-3,
    .web-grid-4 {{
        grid-template-columns: 1fr;
    }}
}}
/* ======================================================
   FINAL OVERRIDE - SAME TOP GAP FOR ALL PAGES
   ====================================================== */
:root {{
    --content-top-offset: 84px;
    --page-x-gap: 5px;
}}

html,
body,
.stApp,
div[data-testid="stAppViewContainer"] {{
    width: 100% !important;
    max-width: 100% !important;
    overflow-x: hidden !important;
}}

section[data-testid="stMain"],
div[data-testid="stMain"],
main,
.main {{
    width: 100% !important;
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
    flex: 1 1 auto !important;
}}

.main .block-container,
.block-container,
div.block-container,
section[data-testid="stMain"] .block-container,
section[data-testid="stMain"] > div,
div[data-testid="stMainBlockContainer"],
div[data-testid="stAppViewBlockContainer"],
main > div {{
    width: 100% !important;
    max-width: none !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    padding-top: var(--content-top-offset) !important;
    padding-left: var(--page-x-gap) !important;
    padding-right: var(--page-x-gap) !important;
    padding-bottom: calc(var(--footer-height) + 12px) !important;
    box-sizing: border-box !important;
}}

.home-desktop,
.task-page-wrap,
.sim-page-wrap,
.simulation-page-wrap,
.memory-page-wrap,
.sync-page-wrap,
.comparison-page-wrap,
.report-page-wrap {{
    width: 100% !important;
    max-width: 100% !important;
    margin-top: 0 !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    padding-left: var(--page-x-gap) !important;
    padding-right: var(--page-x-gap) !important;
    box-sizing: border-box !important;
}}

/* Xóa khoảng hở tự sinh ở phần tử đầu tiên của từng trang */
div[data-testid="stVerticalBlock"] {{
    gap: 0.75rem !important;
}}

div[data-testid="stVerticalBlock"] > div:first-child,
div[data-testid="element-container"]:first-child,
div[data-testid="stHorizontalBlock"]:first-child {{
    margin-top: 0 !important;
    padding-top: 0 !important;
}}

/* Đồng bộ riêng các khối đầu trang hay dùng */
.memory-top-grid,
.task-stats,
.sync-stats,
.comparison-title-box,
.report-title-box,
.sim-grid-top {{
    margin-top: 0 !important;
}}
[data-testid="stAppViewContainer"] {{
    min-height: 100vh !important;
}}

.app-footer {{
    width: 100% !important;
}}
</style>
"""


def inject_global_css() -> None:
    st.markdown(get_global_css(), unsafe_allow_html=True)


# Alias để tránh lỗi nếu file cũ đang gọi tên khác
apply_global_styles = inject_global_css
load_css = inject_global_css
