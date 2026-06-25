import os
import tkinter as tk

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False

from ui.icon_utils import load_icon, resolve_icon_path as shared_resolve_icon_path, normalize_icon_name as shared_normalize_icon_name


PRIMARY_COLOR = "#005BAC"
PRIMARY_DARK = "#004A99"
ACCENT_COLOR = "#D71920"
BACKGROUND_COLOR = "#F4F7FB"
HERO_BG = "#EAF4FF"
WHITE_COLOR = "#FFFFFF"
TEXT_COLOR = "#1F2937"
BORDER_COLOR = "#D9E2EC"
LIGHT_BLUE = "#EEF6FF"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(BASE_DIR, "utils", "icons")

ICON_FILES = {
    "hero_customer": "Customer.png",
    "hero_queue": "HERO_queue.png",
    "hero_photocopy": "Photocopier.png",
    "hero_done": "Done.png",

    "section_fast": "Fast.png",
    "section_process": "Process.png",
    "section_overview": "Overview.png",
    "section_info": "Information.png",

    "quick_task": "Manager.png",
    "quick_simulation": "Simulation.png",
    "quick_compare": "Compare.png",
    "quick_report": "H_Report.png",

    "process_input": "Import_task.png",
    "process_select": "Choose_algorithm.png",
    "process_run": "Simulation.png",
    "process_result": "Process_result.png",

    "algo_fcfs": "FCFS.png",
    "algo_sjf": "SJF.png",
    "algo_priority": "Priority.png",
    "algo_rr": "Round_Robin.png",

    "info_topic": "_Describe.png",
    "info_field": "Field.png",
    "info_goal": "Target.png",
    "info_data": "Info_data.png",
}

PAGE_ROUTES = {
    "tasks": (
        "task_frame",
        "TaskFrame",
        "tasks_frame",
        "TasksFrame",
        "task_list",
        "TaskListFrame",
        "TaskList",
        "tasks",
        "task",
        "danh_sach_tac_vu",
        "DanhSachTacVu",
        "Danh sách tác vụ",
        "Danh sách",
    ),
    "simulation": (
        "simulation_frame",
        "SimulationFrame",
        "algorithm_frame",
        "AlgorithmFrame",
        "simulation",
        "algorithm",
        "algorithms",
        "mo_phong",
        "mo_phong_thuat_toan",
        "Mô phỏng thuật toán",
    ),
    "comparison": (
        "comparison_frame",
        "ComparisonFrame",
        "compare_frame",
        "CompareFrame",
        "comparison",
        "compare",
        "so_sanh",
        "so_sanh_thuat_toan",
        "So sánh thuật toán",
    ),
}

PAGE_METHODS = {
    "tasks": (
        "show_task_frame",
        "show_tasks_frame",
        "show_task_list",
        "show_tasks",
        "open_task_frame",
        "open_task_list",
    ),
    "simulation": (
        "show_simulation_frame",
        "show_algorithm_frame",
        "show_simulation",
        "open_simulation_frame",
    ),
    "comparison": (
        "show_comparison_frame",
        "show_compare_frame",
        "show_comparison",
        "open_comparison_frame",
    ),
}

FONT_SECTION = ("Arial", 16, "bold")
FONT_HERO_TITLE = ("Arial", 25, "bold")
FONT_HERO_DESC = ("Arial", 13)
FONT_CARD_TITLE = ("Arial", 12, "bold")
FONT_CARD_DESC = ("Arial", 10)
FONT_INFO_TITLE = ("Arial", 11, "bold")
FONT_INFO_DESC = ("Arial", 9)
FONT_SMALL_BOLD = ("Arial", 10, "bold")
FONT_SMALL = ("Arial", 9)


class HomeFrame(tk.Frame):
    def __init__(self, parent, navigate_callback=None, tasks=None):
        super().__init__(parent, bg=BACKGROUND_COLOR)
        self.navigate_callback = navigate_callback
        self.tasks = tasks or []
        self.images = {}
        self.create_widgets()

    def normalize_icon_name(self, value):
        return shared_normalize_icon_name(value)

    def get_icon_path(self, icon_key):
        filename = ICON_FILES.get(icon_key, icon_key)
        return shared_resolve_icon_path(ICON_DIR, filename)

    def load_image(self, icon_key, size=(48, 48)):
        filename = ICON_FILES.get(icon_key, icon_key)
        return load_icon(self, ICON_DIR, filename, size=size, crop_transparency=True, keep_aspect=True)

    def normalize_name(self, value):
        return str(value).lower().replace(" ", "_").replace("-", "_")

    def find_route_from_app(self, page_key):
        app = getattr(self.navigate_callback, "__self__", None)
        candidates = PAGE_ROUTES.get(page_key, (page_key,))
        normalized_candidates = [self.normalize_name(item) for item in candidates]
        if not app:
            return None

        for attr in ("frames", "pages", "screens", "frame_map", "page_frames"):
            mapping = getattr(app, attr, None)
            if isinstance(mapping, dict):
                keys = list(mapping.keys())
                for candidate, normalized in zip(candidates, normalized_candidates):
                    for key in keys:
                        key_name = self.normalize_name(key)
                        if key_name == normalized or normalized in key_name or key_name in normalized:
                            return key

        for method_name in PAGE_METHODS.get(page_key, ()): 
            method = getattr(app, method_name, None)
            if callable(method):
                return method
        return None

    def navigate_to(self, page_key):
        if not self.navigate_callback:
            return

        route_or_method = self.find_route_from_app(page_key)
        if callable(route_or_method):
            try:
                route_or_method()
                return
            except TypeError:
                pass
        elif route_or_method is not None:
            try:
                self.navigate_callback(route_or_method)
                return
            except TypeError:
                pass

        for route_name in PAGE_ROUTES.get(page_key, (page_key,)):
            try:
                self.navigate_callback(route_name)
                return
            except TypeError:
                continue
            except Exception:
                continue

    def bind_click_recursive(self, widget, command):
        widget.bind("<Button-1>", lambda event: command(), add="+")
        try:
            widget.configure(cursor="hand2")
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self.bind_click_recursive(child, command)

    def create_widgets(self):
        wrapper = tk.Frame(self, bg=BACKGROUND_COLOR)
        wrapper.pack(fill=tk.BOTH, expand=True, padx=22, pady=(14, 10))
        self.create_hero_section(wrapper)
        self.create_body_layout(wrapper)

    def make_box(self, parent, bg=WHITE_COLOR, height=None):
        box = tk.Frame(parent, bg=bg, highlightbackground=BORDER_COLOR, highlightthickness=1)
        if height:
            box.configure(height=height)
            box.pack_propagate(False)
            box.grid_propagate(False)
        return box

    def make_section(self, parent, title, icon_text="▣", height=None, title_font=FONT_SECTION, icon_key=None):
        section = self.make_box(parent, WHITE_COLOR, height=height)
        header = tk.Frame(section, bg=WHITE_COLOR, height=42)
        header.pack(fill=tk.X, padx=20, pady=(6, 0))
        header.pack_propagate(False)

        icon_img = self.load_image(icon_key, (22, 22)) if icon_key else None
        if icon_img:
            tk.Label(header, image=icon_img, bg=WHITE_COLOR).pack(side=tk.LEFT, padx=(0, 10))
        else:
            tk.Label(header, text=icon_text, bg=WHITE_COLOR, fg=PRIMARY_COLOR, font=("Arial", 14, "bold")).pack(
                side=tk.LEFT, padx=(0, 10)
            )
        tk.Label(header, text=title, bg=WHITE_COLOR, fg=PRIMARY_COLOR, font=title_font).pack(side=tk.LEFT)

        content = tk.Frame(section, bg=WHITE_COLOR)
        content.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))
        return section, content

    def make_icon_circle(
        self,
        parent,
        icon_key,
        fallback_text,
        circle_size=58,
        icon_size=(34, 34),
        circle_color=LIGHT_BLUE,
        fg=PRIMARY_COLOR,
        bg=WHITE_COLOR,
        draw_circle=True,
    ):
        canvas = tk.Canvas(parent, width=circle_size, height=circle_size, bg=bg, highlightthickness=0)
        pad = 4
        if draw_circle:
            canvas.create_oval(pad, pad, circle_size - pad, circle_size - pad, fill=circle_color, outline=circle_color)
        icon_img = self.load_image(icon_key, icon_size)
        if icon_img:
            canvas.create_image(circle_size // 2, circle_size // 2, image=icon_img)
        else:
            canvas.create_text(
                circle_size // 2,
                circle_size // 2,
                text=fallback_text,
                fill=fg,
                font=("Arial", 20, "bold"),
            )
        return canvas

    def create_hero_section(self, parent):
        hero = self.make_box(parent, HERO_BG, height=180)
        hero.pack(fill=tk.X, pady=(0, 12))

        left = tk.Frame(hero, bg=HERO_BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(42, 24), pady=28)

        tk.Label(
            left,
            text="MÔ PHỎNG HỆ THỐNG\nXẾP HÀNG PHOTOCOPY",
            bg=HERO_BG,
            fg=PRIMARY_COLOR,
            justify=tk.LEFT,
            font=FONT_HERO_TITLE,
        ).pack(anchor="w")

        tk.Frame(left, bg=ACCENT_COLOR, width=52, height=4).pack(anchor="w", pady=(10, 12))

        tk.Label(
            left,
            text="Ứng dụng mô phỏng và so sánh các giải thuật\nlập lịch CPU trong xử lý tác vụ photocopy",
            bg=HERO_BG,
            fg=TEXT_COLOR,
            justify=tk.LEFT,
            font=FONT_HERO_DESC,
        ).pack(anchor="w")

        process = tk.Frame(hero, bg=HERO_BG)
        process.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(26, 38), pady=(18, 14))
        self.create_hero_flow(process)

    def create_hero_flow(self, parent):
        parent.rowconfigure(0, weight=1)
        for col in range(7):
            parent.columnconfigure(col, weight=1 if col % 2 == 0 else 0)

        nodes = [
            (0, "hero_customer", "👤", "Khách hàng"),
            (2, "hero_queue", "1  2  ...  n", "Hàng đợi"),
            (4, "hero_photocopy", "▤", "Máy photocopy"),
            (6, "hero_done", "✓", "Tác vụ hoàn thành"),
        ]

        for col, icon_key, fallback, label in nodes:
            node = tk.Frame(parent, bg=HERO_BG)
            node.grid(row=0, column=col, sticky="nsew")
            if icon_key == "hero_queue":
                self.make_queue_visual(node).pack(pady=(4, 2))
            else:
                img = self.load_image(icon_key, (112, 112))
                if img:
                    tk.Label(node, image=img, bg=HERO_BG).pack(pady=(0, 4))
                else:
                    self.make_icon_circle(
                        node,
                        icon_key,
                        fallback,
                        circle_size=112,
                        icon_size=(82, 82),
                        circle_color=HERO_BG,
                        bg=HERO_BG,
                    ).pack(pady=(0, 2))
            tk.Label(node, text=label, bg=HERO_BG, fg=TEXT_COLOR, font=("Arial", 11, "bold")).pack()

        for col in (1, 3, 5):
            tk.Label(parent, text="→", bg=HERO_BG, fg=TEXT_COLOR, font=("Arial", 30, "bold")).grid(
                row=0, column=col, padx=8, sticky="ns"
            )

    def make_queue_visual(self, parent):
        canvas = tk.Canvas(parent, width=220, height=112, bg=HERO_BG, highlightthickness=0)
        icon_img = self.load_image("hero_queue", (210, 96))
        if icon_img:
            canvas.create_image(110, 56, image=icon_img)
            return canvas

        x, y, cell_w, cell_h = 22, 28, 44, 50
        labels = ["1", "2", "...", "n"]
        for i, text in enumerate(labels):
            x1 = x + i * cell_w
            x2 = x1 + cell_w
            canvas.create_rectangle(x1, y, x2, y + cell_h, fill=PRIMARY_COLOR, outline=WHITE_COLOR, width=1)
            canvas.create_text((x1 + x2) // 2, y + cell_h // 2, text=text, fill=WHITE_COLOR, font=("Arial", 14, "bold"))
        return canvas

    def create_body_layout(self, parent):
        body = tk.Frame(parent, bg=BACKGROUND_COLOR)
        body.pack(fill=tk.BOTH, expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=0)
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=BACKGROUND_COLOR)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        right = tk.Frame(body, bg=BACKGROUND_COLOR, width=360)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_propagate(False)

        self.create_quick_actions(left)
        self.create_process_section(left)
        self.create_algorithm_overview(left)
        self.create_info_panel(right)

    def create_quick_actions(self, parent):
        section, content = self.make_section(parent, "THAO TÁC NHANH", icon_text="⚡", height=168, icon_key="section_fast")
        section.pack(fill=tk.X, pady=(0, 12))

        for i in range(4):
            content.columnconfigure(i, weight=1, uniform="quick")
        content.rowconfigure(0, weight=1)

        actions = [
            ("quick_task", "📋", "Quản lý tác vụ", "Thêm, sửa, nhập\ndanh sách tác vụ", "tasks"),
            ("quick_simulation", "▶", "Chạy mô phỏng", "Mô phỏng FCFS, SJF,\nPriority, Round Robin", "simulation"),
            ("quick_compare", "⚖", "So sánh thuật toán", "Đánh giá thời gian chờ\nvà hoàn thành", "comparison"),
            ("quick_report", "PDF", "Xuất tác vụ", "Mở danh sách tác vụ\nđể xuất PDF/CSV", "tasks"),
        ]

        for col, item in enumerate(actions):
            self.make_quick_card(content, *item).grid(row=0, column=col, sticky="nsew", padx=6, pady=4)

    def make_quick_card(self, parent, icon_key, fallback, title, desc, page_key):
        card = self.make_box(parent, WHITE_COLOR, height=106)

        icon_area = tk.Frame(card, bg=WHITE_COLOR, width=88)
        icon_area.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 4), pady=8)
        icon_area.pack_propagate(False)

        self.make_icon_circle(
            icon_area,
            icon_key,
            fallback,
            circle_size=70,
            icon_size=(44, 44),
            circle_color=LIGHT_BLUE,
            bg=WHITE_COLOR,
        ).pack(expand=True)

        text_area = tk.Frame(card, bg=WHITE_COLOR)
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(14, 8), padx=(0, 6))

        tk.Label(
            text_area,
            text=title,
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=FONT_CARD_TITLE,
            justify=tk.LEFT,
            anchor="w",
            wraplength=180,
        ).pack(anchor="w")

        tk.Label(
            text_area,
            text=desc,
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            font=FONT_CARD_DESC,
            justify=tk.LEFT,
            anchor="w",
            wraplength=180,
        ).pack(anchor="w", pady=(4, 0))

        self.bind_click_recursive(card, lambda key=page_key: self.navigate_to(key))
        return card

    def create_process_section(self, parent):
        section, content = self.make_section(parent, "QUY TRÌNH MÔ PHỎNG", icon_text="♙", height=226, icon_key="section_process")
        section.pack(fill=tk.X, pady=(0, 12))

        canvas = tk.Canvas(content, bg=WHITE_COLOR, highlightthickness=0, height=162)
        canvas.pack(fill=tk.BOTH, expand=True)

        def draw(event=None):
            canvas.delete("all")
            w = canvas.winfo_width()
            if w <= 10:
                return

            steps = [
                ("process_input", "＋", "Nhập tác vụ", "Thêm và cấu hình\ndanh sách tác vụ"),
                ("process_select", "☷", "Chọn thuật toán", "Chọn giải thuật lập lịch"),
                ("process_run", "▶", "Chạy mô phỏng", "Tiến hành mô phỏng"),
                ("process_result", "↗", "Xem kết quả", "Xem thời gian chờ"),
            ]

            xs = [int(w * 0.10), int(w * 0.37), int(w * 0.64), int(w * 0.90)]
            cy = 58
            r = 44

            for i in range(3):
                canvas.create_line(xs[i] + r + 22, cy, xs[i + 1] - r - 22, cy, fill=PRIMARY_COLOR, width=3, arrow=tk.LAST)

            for idx, (icon_key, fallback, title, desc) in enumerate(steps):
                x = xs[idx]
                canvas.create_oval(x - r, cy - r, x + r, cy + r, outline="#AFC7DD", width=1, dash=(2, 2))
                canvas.create_oval(x - r - 14, cy - r - 14, x - r + 14, cy - r + 14, fill=PRIMARY_COLOR, outline=PRIMARY_COLOR)
                canvas.create_text(x - r, cy - r, text=str(idx + 1), fill=WHITE_COLOR, font=FONT_SMALL_BOLD)

                icon_img = self.load_image(icon_key, (42, 42))
                if icon_img:
                    canvas.create_image(x, cy - (2 if icon_key == "process_run" else 0), image=icon_img)
                else:
                    canvas.create_text(x, cy, text=fallback, fill=PRIMARY_COLOR, font=("Arial", 23, "bold"))

                canvas.create_text(x, cy + 66, text=title, fill=PRIMARY_COLOR, font=("Arial", 11, "bold"))
                canvas.create_text(x, cy + 94, text=desc, fill=TEXT_COLOR, font=FONT_SMALL, justify=tk.CENTER)

        canvas.bind("<Configure>", draw)

    def create_algorithm_overview(self, parent):
        section, content = self.make_section(parent, "TỔNG QUAN GIẢI THUẬT", icon_text="▣", height=150, icon_key="section_overview")
        section.pack(fill=tk.BOTH, expand=True)

        for i in range(4):
            content.columnconfigure(i, weight=1, uniform="algo")
        content.rowconfigure(0, weight=1)

        algorithms = [
            ("algo_fcfs", "♛", "FCFS", "Xử lý theo thứ tự\nđến trước", PRIMARY_COLOR),
            ("algo_sjf", "◷", "SJF", "Ưu tiên tác vụ có\nthời gian xử lý ngắn", "#00A86B"),
            ("algo_priority", "★", "Priority", "Ưu tiên theo mức độ\nquan trọng", "#F59E0B"),
            ("algo_rr", "↻", "Round Robin", "Chia thời gian xử lý\ntheo quantum", "#7C3AED"),
        ]

        for col, item in enumerate(algorithms):
            self.make_algorithm_card(content, *item).grid(row=0, column=col, sticky="nsew", padx=6, pady=4)

    def make_algorithm_card(self, parent, icon_key, fallback, title, desc, color):
        card = self.make_box(parent, WHITE_COLOR, height=92)

        icon_area = tk.Frame(card, bg=WHITE_COLOR, width=88)
        icon_area.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 4), pady=6)
        icon_area.pack_propagate(False)

        # Dùng icon PNG hoàn chỉnh trực tiếp, không vẽ hình tròn lên trên/trùng với icon.
        icon_img = self.load_image(icon_key, (68, 68))
        if icon_img:
            tk.Label(icon_area, image=icon_img, bg=WHITE_COLOR).pack(expand=True)
        else:
            self.make_icon_circle(
                icon_area,
                icon_key,
                fallback,
                circle_size=68,
                icon_size=(46, 46),
                circle_color=color,
                fg=WHITE_COLOR,
                bg=WHITE_COLOR,
                draw_circle=True,
            ).pack(expand=True)

        text_area = tk.Frame(card, bg=WHITE_COLOR)
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(12, 6), padx=(0, 6))

        tk.Label(
            text_area,
            text=title,
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=FONT_CARD_TITLE,
            anchor="w",
            justify=tk.LEFT,
            wraplength=180,
        ).pack(anchor="w")

        tk.Label(
            text_area,
            text=desc,
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            font=FONT_SMALL,
            justify=tk.LEFT,
            anchor="w",
            wraplength=180,
        ).pack(anchor="w", pady=(3, 0))

        return card

    def create_info_panel(self, parent):
        panel, content = self.make_section(parent, "THÔNG TIN ĐỀ TÀI", icon_text="ⓘ", title_font=("Arial", 13, "bold"), icon_key="section_info")
        panel.pack(fill=tk.BOTH, expand=True)

        rows = [
            ("info_topic", "▤", "Đề tài", "Mô phỏng xử lý tác vụ photocopy"),
            ("info_field", "▱", "Lĩnh vực", "Hệ điều hành"),
            ("info_goal", "◎", "Mục tiêu", "So sánh hiệu quả các giải thuật\nlập lịch"),
            ("info_data", "▰", "Dữ liệu", "Tác vụ in, sao chép, scan"),
        ]

        for i, row in enumerate(rows):
            self.make_info_row(content, *row)
            if i < len(rows) - 1:
                tk.Frame(content, bg=BORDER_COLOR, height=1).pack(fill=tk.X, padx=4, pady=8)

    def make_info_row(self, parent, icon_key, fallback, title, desc):
        row = tk.Frame(parent, bg=WHITE_COLOR)
        row.pack(fill=tk.X, padx=4, pady=(6, 3))

        icon_box = tk.Frame(row, bg=WHITE_COLOR, width=44)
        icon_box.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        icon_box.pack_propagate(False)

        icon_img = self.load_image(icon_key, (30, 30))
        if icon_img:
            tk.Label(icon_box, image=icon_img, bg=WHITE_COLOR).pack(anchor="n")
        else:
            tk.Label(icon_box, text=fallback, bg=WHITE_COLOR, fg=PRIMARY_COLOR, font=("Arial", 20, "bold")).pack(anchor="n")

        text_box = tk.Frame(row, bg=WHITE_COLOR)
        text_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(
            text_box,
            text=title,
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=FONT_INFO_TITLE,
            anchor="w",
            wraplength=145,
        ).pack(anchor="w")

        tk.Label(
            text_box,
            text=desc,
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            font=FONT_INFO_DESC,
            justify=tk.LEFT,
            anchor="w",
            wraplength=210,
        ).pack(anchor="w", pady=(5, 0))
