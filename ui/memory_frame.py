import os
import tkinter as tk
from tkinter import ttk
from turtle import right

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False

from ui.icon_utils import load_icon

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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(BASE_DIR, "utils", "icons")

ALGORITHMS = ("First Fit", "Best Fit", "Worst Fit")
ALGORITHM_COLORS = {
    "First Fit": PRIMARY_COLOR,
    "Best Fit": GREEN,
    "Worst Fit": PURPLE,
}

MEMORY_BASE_KB = 20
COVER_PAGE_KB = 8      # in bìa
COLOR_PAGE_KB = 5      # in màu
BW_PAGE_KB = 2         # trắng đen

class MemoryFrame(tk.Frame):
    """
    Màn mô phỏng cấp phát bộ nhớ.

    Phiên bản này bỏ khối "Thiết lập mô phỏng" và trực quan hóa đồng thời
    3 thuật toán: First Fit, Best Fit, Worst Fit.
    """

    def __init__(self, parent, tasks=None, on_memory_finished=None):
        super().__init__(parent, bg=BACKGROUND_COLOR)

        self.tasks = tasks or []
        self.on_memory_finished = on_memory_finished

        # Giữ biến cũ để không làm lỗi các đoạn code khác nếu có gọi tới.
        self.algorithm_var = tk.StringVar(value="First Fit")
        self.total_memory_var = tk.StringVar(value="1024")
        self.block_count_var = tk.StringVar(value="5")

        self.memory_blocks = []
        self.processes = []
        self.allocation_results = []
        self.compare_results = {}
        self.best_payload = None
        self.metric_labels = {}
        self.process_color_map = {}
        self.result_trees = {}
        self.algorithm_visuals = {}
        self.images = {}

        self.build_ui()
        self.refresh_data(notify=True)

    # =====================================================
    # UI HELPERS
    # =====================================================
    def section(self, parent, title, icon="▣", icon_file=None):
        box = tk.Frame(
            parent,
            bg=WHITE_COLOR,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
        )

        head = tk.Frame(box, bg=WHITE_COLOR)
        head.pack(fill="x")

        icon_img = self.load_image(icon_file, (22, 22)) if icon_file else None

        if icon_img:
            icon_label = tk.Label(
                head,
                image=icon_img,
                bg=WHITE_COLOR
            )
            icon_label.image = icon_img
            icon_label.pack(side="left", padx=(14, 8), pady=10)
        else:
            tk.Label(
                head,
                text=icon,
                bg=WHITE_COLOR,
                fg=PRIMARY_COLOR,
                font=("Arial", 13, "bold"),
            ).pack(side="left", padx=(14, 8), pady=10)

        tk.Label(
            head,
            text=title,
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 12, "bold"),
        ).pack(side="left", pady=10)

        tk.Frame(box, bg=BORDER_COLOR, height=1).pack(fill="x")
        return box
    
    def lock_frame_size(self, frame, height=None, width=None):
        if height is not None:
            frame.configure(height=height)

        if width is not None:
            frame.configure(width=width)

        frame.grid_propagate(False)
        frame.pack_propagate(False)

    def make_metric_card(
        self,
        parent,
        key,
        title,
        value,
        subtitle,
        icon_file,
        fallback_icon,
        color,
        col
    ):
        card = tk.Frame(
            parent,
            bg=WHITE_COLOR,
            height=125,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
        )
        card.grid(row=0, column=col, sticky="nsew", padx=6)
        card.pack_propagate(False)

        # Khung icon: bỏ nền màu, chỉ giữ nền trắng
        icon_box = tk.Frame(
            card,
            bg=WHITE_COLOR,
            width=92,
            height=92
        )
        icon_box.pack(side="left", padx=(20, 14), pady=16)
        icon_box.pack_propagate(False)

        # Icon to hơn
        icon_img = self.load_image(icon_file, (85, 85))

        if icon_img:
            icon_label = tk.Label(
                icon_box,
                image=icon_img,
                bg=WHITE_COLOR
            )
            icon_label.image = icon_img
            icon_label.pack(expand=True)
        else:
            tk.Label(
                icon_box,
                text=fallback_icon,
                bg=WHITE_COLOR,
                fg=color,
                font=("Arial", 34, "bold")
            ).pack(expand=True)

        # Khối chữ căn giữa theo chiều cao card
        text_box = tk.Frame(card, bg=WHITE_COLOR)
        text_box.pack(side="left", fill="both", expand=True, pady=18)

        tk.Label(
            text_box,
            text=title.upper(),
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 11, "bold"),
        ).pack(anchor="w")

        value_label = tk.Label(
            text_box,
            text=value,
            bg=WHITE_COLOR,
            fg=color,
            font=("Arial", 24, "bold"),
        )
        value_label.pack(anchor="w", pady=(2, 0))

        tk.Label(
            text_box,
            text=subtitle,
            bg=WHITE_COLOR,
            fg=MUTED_TEXT,
            font=("Arial", 10),
        ).pack(anchor="w", pady=(2, 0))

        self.metric_labels[key] = value_label

    def load_image(self, icon_name, size=(22, 22)):
        if not icon_name:
            return None

        return load_icon(
            self,
            ICON_DIR,
            icon_name,
            size=size,
            crop_transparency=True,
            keep_aspect=True
        )

    def make_legend_item(self, parent, text, kind="empty"):
        item = tk.Frame(parent, bg=WHITE_COLOR)
        item.pack(side="left", padx=(0, 26), pady=2)

        icon = tk.Canvas(
            item,
            width=24,
            height=18,
            bg=WHITE_COLOR,
            highlightthickness=0
        )
        icon.pack(side="left", padx=(0, 7))

        if kind == "empty":
            icon.create_rectangle(
                3, 3, 21, 15,
                fill=WHITE_COLOR,
                outline="#BDBDBD",
                width=1
            )

        elif kind == "allocated":
            icon.create_rectangle(
                3, 3, 21, 15,
                fill="#7DCE82",
                outline="#63B96A",
                width=1
            )

        elif kind == "fragment":
            icon.create_rectangle(
                3, 3, 21, 15,
                fill=WHITE_COLOR,
                outline="#E29A9A",
                width=1,
                dash=(4, 2)
            )

        tk.Label(
            item,
            text=text,
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 9, "bold")
        ).pack(side="left")

    def clear_frame(self, frame):
        for child in frame.winfo_children():
            child.destroy()


    def add_conclusion_item(self, parent, text, icon_bg="#EAF7EE", icon_fg=GREEN):
        row = tk.Frame(parent, bg=WHITE_COLOR)
        row.pack(fill="x", padx=12, pady=0)

        icon_canvas = tk.Canvas(
            row,
            width=26,
            height=26,
            bg=WHITE_COLOR,
            highlightthickness=0
        )
        icon_canvas.pack(side="left", pady=10)

        icon_canvas.create_oval(3, 3, 23, 23, fill=icon_bg, outline=icon_bg)
        icon_canvas.create_text(
            13, 13,
            text="✓",
            fill=icon_fg,
            font=("Arial", 11, "bold")
        )

        text_label = tk.Label(
            row,
            text=text,
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 10, "bold"),
            justify="left",
            anchor="w",
            wraplength=620
        )
        text_label.pack(side="left", fill="x", expand=True, padx=(8, 0), pady=10)

        separator = tk.Frame(parent, bg=BORDER_COLOR, height=1)
        separator.pack(fill="x", padx=12)

    def configure_tree(self, tree, columns, headings, widths):
        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(
                col,
                anchor="center",
                width=widths.get(col, 100),
                stretch=True
            )

    def add_tree_scrollbars(self, parent, tree):
        y_scroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        x_scroll = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
    def add_tree_vertical_scrollbar(self, parent, tree):
        y_scroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=y_scroll.set)

        tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")

        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
    # =====================================================
    # BUILD UI
    # =====================================================
    def build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, bg=BACKGROUND_COLOR, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = tk.Frame(self.canvas, bg=BACKGROUND_COLOR)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self.canvas_window, width=e.width),
        )

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.build_top_metrics()
        self.build_memory_config()
        self.build_main_layout()
        self.build_compare_and_conclusion()

    def build_top_metrics(self):
        wrapper = tk.Frame(self.content, bg=BACKGROUND_COLOR)
        wrapper.pack(fill="x", padx=16, pady=(0, 10))

        for i in range(4):
            wrapper.columnconfigure(i, weight=1)

        self.make_metric_card(
            wrapper,
            "total",
            "Tổng tiến trình",
            "0",
            "Tiến trình cần cấp phát",
            "Memory_Total.png",
            "👥",
            PRIMARY_COLOR,
            0
        )

        self.make_metric_card(
            wrapper,
            "success",
            "Cấp phát thành công",
            "0",
            "Theo thuật toán tốt nhất",
            "Memory_Success.png",
            "✓",
            GREEN,
            1
        )

        self.make_metric_card(
            wrapper,
            "failed",
            "Thất bại",
            "0",
            "Tiến trình không cấp được",
            "Memory_Failed.png",
            "×",
            RED,
            2
        )

        self.make_metric_card(
            wrapper,
            "usage",
            "Hiệu suất bộ nhớ",
            "0%",
            "Tỷ lệ bộ nhớ sử dụng",
            "Memory_Usage.png",
            "◔",
            PURPLE,
            3
        )

    def build_memory_config(self):
        config = self.section(
            self.content,
            "CẤU HÌNH BỘ NHỚ",
            "⚙",
            icon_file="Simulation_Setup.png"
        )
        config.pack(fill="x", padx=16, pady=(0, 6))

        body = tk.Frame(config, bg=WHITE_COLOR)
        body.pack(fill="x", padx=14, pady=10)

        tk.Label(
            body,
            text="Tổng bộ nhớ (KB)",
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=(0, 8))

        total_entry = tk.Entry(
            body,
            textvariable=self.total_memory_var,
            width=12,
            font=("Arial", 10)
        )
        total_entry.pack(side="left", padx=(0, 18), ipady=4)

        tk.Label(
            body,
            text="Số khối nhớ",
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=(0, 8))

        block_entry = tk.Entry(
            body,
            textvariable=self.block_count_var,
            width=10,
            font=("Arial", 10)
        )
        block_entry.pack(side="left", padx=(0, 18), ipady=4)

        tk.Button(
            body,
            text="Áp dụng",
            command=lambda: self.refresh_data(notify=True),
            bg=PRIMARY_COLOR,
            fg=WHITE_COLOR,
            activebackground=PRIMARY_COLOR,
            activeforeground=WHITE_COLOR,
            relief=tk.FLAT,
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=14,
            pady=6
        ).pack(side="left")

        tk.Label(
            body,
            text="Công thức: 20 KB + in bìa × 8 + in màu × 5 + trắng đen × 2",
            bg=WHITE_COLOR,
            fg=MUTED_TEXT,
            font=("Arial", 9, "italic")
        ).pack(side="left", padx=(18, 0))

    def build_main_layout(self):
        row = tk.Frame(self.content, bg=BACKGROUND_COLOR)
        row.pack(fill="both", expand=True, padx=16, pady=6)
        row.columnconfigure(0, weight=40)
        row.columnconfigure(1, weight=60)

        visual = self.section(
            row,
            "TRỰC QUAN CẤP PHÁT BỘ NHỚ",
            "▥",
            icon_file="Memory_Visualization.png"
        )
        visual.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.lock_frame_size(visual, height=710)
        self.build_visual_content(visual)

        right = tk.Frame(row, bg=BACKGROUND_COLOR)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.rowconfigure(0, weight=0)
        right.rowconfigure(1, weight=0)
        right.columnconfigure(0, weight=1)

        data_box = self.section(
            right,
            "DANH SÁCH KHỐI NHỚ & TIẾN TRÌNH",
            "▤",
            icon_file="Choose_algorithm.png"
        )
        data_box.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.lock_frame_size(data_box, height=297)
        self.build_data_tables(data_box)

        result_box = self.section(
            right,
            "KẾT QUẢ CẤP PHÁT",
            "▦",
            icon_file="Describe.png"
        )
        result_box.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self.lock_frame_size(result_box, height=390)
        self.build_result_table(result_box)

    def build_visual_content(self, parent):
        wrap = tk.Frame(parent, bg=WHITE_COLOR)
        wrap.pack(fill="both", expand=True, padx=14, pady=12)
        wrap.columnconfigure(0, weight=1)

        self.algorithm_visuals = {}

        for row_index, algorithm in enumerate(ALGORITHMS):
            block = tk.Frame(
                wrap,
                bg=WHITE_COLOR,
                highlightbackground=BORDER_COLOR,
                highlightthickness=1
            )
            block.grid(
                row=row_index,
                column=0,
                sticky="nsew",
                pady=(0, 10 if row_index < len(ALGORITHMS) - 1 else 6)
            )
            block.columnconfigure(0, weight=1)

            header = tk.Frame(block, bg=WHITE_COLOR)
            header.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
            header.columnconfigure(0, weight=1)
            header.columnconfigure(1, weight=1)

            title_label = tk.Label(
                header,
                text=algorithm.upper(),
                bg=WHITE_COLOR,
                fg=ALGORITHM_COLORS.get(algorithm, PRIMARY_COLOR),
                font=("Arial", 11, "bold"),
                anchor="w",
            )
            title_label.grid(row=0, column=0, sticky="w")

            summary_label = tk.Label(
                header,
                text="",
                bg=WHITE_COLOR,
                fg=MUTED_TEXT,
                font=("Arial", 9, "italic"),
                anchor="e",
            )
            summary_label.grid(row=0, column=1, sticky="e")

            canvas_wrap = tk.Frame(block, bg=WHITE_COLOR)
            canvas_wrap.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))
            canvas_wrap.rowconfigure(0, weight=1)
            canvas_wrap.columnconfigure(0, weight=1)

            canvas = tk.Canvas(
                canvas_wrap,
                height=130,
                bg=WHITE_COLOR,
                highlightthickness=0,
            )

            xscroll = ttk.Scrollbar(
                canvas_wrap,
                orient="horizontal",
                command=canvas.xview
            )

            canvas.configure(xscrollcommand=xscroll.set)

            canvas.grid(row=0, column=0, sticky="nsew")
            xscroll.grid(row=1, column=0, sticky="ew")

            self.algorithm_visuals[algorithm] = {
                "canvas": canvas,
                "scrollbar": xscroll,
                "summary_label": summary_label,
                "title_label": title_label,
            }

            canvas.bind(
                "<Configure>",
                lambda event, algo=algorithm: self.draw_algorithm_visual(algo)
            )

        legend_wrap = tk.Frame(wrap, bg=WHITE_COLOR)
        legend_wrap.grid(
            row=len(ALGORITHMS),
            column=0,
            sticky="w",
            padx=10,
            pady=(9, 10)
        )

        self.make_legend_item(legend_wrap, "Trống (Hole)", "empty")
        self.make_legend_item(legend_wrap, "Đã cấp phát", "allocated")
        self.make_legend_item(legend_wrap, "Phân mảnh (Fragmentation)", "fragment")

    def build_data_tables(self, parent):
        inner = tk.Frame(parent, bg=WHITE_COLOR)
        inner.pack(fill="both", expand=True, padx=14, pady=12)
        inner.columnconfigure(0, weight=1)
        inner.columnconfigure(1, weight=1)
        inner.rowconfigure(0, weight=1)

        block_wrap = tk.Frame(inner, bg=WHITE_COLOR)
        block_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        process_wrap = tk.Frame(inner, bg=WHITE_COLOR)
        process_wrap.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self.block_tree = ttk.Treeview(
            block_wrap,
            columns=("block", "size", "status"),
            show="headings",
            height=6,
        )
        self.configure_tree(
            self.block_tree,
            ("block", "size", "status"),
            {"block": "Khối", "size": "Kích thước", "status": "Trạng thái"},
            {"block": 70, "size": 100, "status": 100},
        )
        self.add_tree_vertical_scrollbar(block_wrap, self.block_tree)

        self.process_tree = ttk.Treeview(
            process_wrap,
            columns=("process", "customer", "cover", "color", "bw", "size"),
            show="headings",
            height=6,
        )

        self.configure_tree(
            self.process_tree,
            ("process", "customer", "cover", "color", "bw", "size"),
            {
                "process": "Tác vụ",
                "customer": "Khách",
                "cover": "Bìa",
                "color": "Màu",
                "bw": "Trắng đen",
                "size": "Bộ nhớ KB",
            },
            {
                "process": 80,
                "customer": 120,
                "cover": 60,
                "color": 60,
                "bw": 80,
                "size": 95,
            },
        )
        self.add_tree_vertical_scrollbar(process_wrap, self.process_tree)

    def build_result_table(self, parent):
        wrap = tk.Frame(parent, bg=WHITE_COLOR)
        wrap.pack(fill="both", expand=True, padx=14, pady=12)

        for i in range(3):
            wrap.columnconfigure(i, weight=1, uniform="result_col")
        wrap.rowconfigure(0, weight=1)

        self.result_trees = {}

        for col, algorithm in enumerate(ALGORITHMS):
            box = tk.Frame(
                wrap,
                bg=WHITE_COLOR,
                highlightbackground=BORDER_COLOR,
                highlightthickness=1
            )
            box.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 6, 0), pady=0)
            box.rowconfigure(1, weight=1)
            box.columnconfigure(0, weight=1)

            header = tk.Frame(box, bg=WHITE_COLOR)
            header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))

            tk.Label(
                header,
                text=algorithm.upper(),
                bg=WHITE_COLOR,
                fg=ALGORITHM_COLORS.get(algorithm, PRIMARY_COLOR),
                font=("Arial", 10, "bold")
            ).pack(anchor="w")

            table_wrap = tk.Frame(box, bg=WHITE_COLOR)
            table_wrap.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
            table_wrap.rowconfigure(0, weight=1)
            table_wrap.columnconfigure(0, weight=1)

            tree = ttk.Treeview(
                table_wrap,
                columns=("pid", "size", "block", "remain", "status"),
                show="headings",
                height=10,
            )

            tree.tag_configure("success", foreground=GREEN)
            tree.tag_configure("waiting", foreground=ORANGE)

            self.configure_tree(
                tree,
                ("pid", "size", "block", "remain", "status"),
                {
                    "pid": "Tiến trình",
                    "size": "Kích thước",
                    "block": "Khối cấp",
                    "remain": "Còn dư",
                    "status": "Trạng thái",
                },
                {
                    "pid": 72,
                    "size": 72,
                    "block": 78,
                    "remain": 65,
                    "status": 110,
                },
            )

            self.add_tree_scrollbars(table_wrap, tree)
            self.result_trees[algorithm] = tree

    def build_compare_and_conclusion(self):
        row = tk.Frame(self.content, bg=BACKGROUND_COLOR)
        row.pack(fill="x", padx=16, pady=(6, 16))

        # Tăng chiều ngang phần so sánh để 3 biểu đồ nằm song song đẹp hơn.
        row.columnconfigure(0, weight=6)
        row.columnconfigure(1, weight=4)

        compare = self.section(
            row,
            "SO SÁNH THUẬT TOÁN CẤP PHÁT",
            "▥",
            icon_file="Chart.png"
        )
        compare.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.compare_canvas = tk.Canvas(
            compare,
            height=220,
            bg=WHITE_COLOR,
            highlightthickness=0,
        )
        self.compare_canvas.pack(fill="both", expand=True, padx=14, pady=12)
        self.compare_canvas.bind("<Configure>", lambda event: self.draw_compare_bar_chart())

        conclusion = self.section(
            row,
            "NHẬN XÉT & KẾT LUẬN",
            "●",
            icon_file="Comment.png"
        )
        conclusion.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        conclusion_body = tk.Frame(conclusion, bg=WHITE_COLOR)
        conclusion_body.pack(fill="both", expand=True, padx=10, pady=10)

        self.conclusion_items_frame = tk.Frame(conclusion_body, bg=WHITE_COLOR)
        self.conclusion_items_frame.pack(fill="both", expand=True)

    # =====================================================
    # DATA + LOGIC
    # =====================================================
    def to_int(self, value, default=0):
        try:
            return int(float(value))
        except Exception:
            return default
        
    def prepare_default_data(self):
        self.processes = self.build_processes_from_tasks()
        self.memory_blocks = self.build_memory_blocks_from_input()
        self.build_process_color_map()
    
    def build_memory_blocks_from_input(self):
        total_memory = max(1, self.to_int(self.total_memory_var.get(), 1024))
        block_count = max(1, self.to_int(self.block_count_var.get(), 5))

        # Nếu nhập số khối lớn hơn tổng KB thì giới hạn lại để tránh khối 0 KB.
        block_count = min(block_count, total_memory)

        base_size = total_memory // block_count
        remainder = total_memory % block_count

        blocks = []
        for index in range(block_count):
            size = base_size + (1 if index < remainder else 0)
            blocks.append({
                "id": f"B{index + 1}",
                "size": size
            })

        return blocks

    def build_processes_from_tasks(self):
        processes = []

        # Không còn tự tạo P1, P2 mẫu nữa.
        # Nếu chưa có khách trong Danh sách tác vụ thì màn Bộ nhớ sẽ rỗng.
        if not self.tasks:
            return processes

        for index, task in enumerate(self.tasks):
            task_id = getattr(task, "task_id", f"T{index + 1:03d}")
            customer_name = getattr(task, "customer_name", "")

            cover_pages = self.to_int(getattr(task, "cover_pages", 0), 0)
            color_pages = self.to_int(getattr(task, "color_pages", 0), 0)
            bw_pages = self.to_int(getattr(task, "bw_pages", 0), 0)

            memory_size = (
                MEMORY_BASE_KB
                + cover_pages * COVER_PAGE_KB
                + color_pages * COLOR_PAGE_KB
                + bw_pages * BW_PAGE_KB
            )

            processes.append({
                "id": task_id,
                "customer_name": customer_name,
                "cover_pages": cover_pages,
                "color_pages": color_pages,
                "bw_pages": bw_pages,
                "size": memory_size,
            })

        return processes

    def build_process_color_map(self):
        colors = [
            "#A5F3FC", "#BFDBFE", "#BBF7D0", "#FED7AA",
            "#DDD6FE", "#FECACA", "#C7D2FE", "#FDE68A",
            "#99F6E4", "#E9D5FF", "#FBCFE8", "#BAE6FD",
        ]
        self.process_color_map = {
            process["id"]: colors[index % len(colors)]
            for index, process in enumerate(self.processes)
        }

    def refresh_tables(self):
        for tree in (self.block_tree, self.process_tree):
            for item in tree.get_children():
                tree.delete(item)

        for block in self.memory_blocks:
            self.block_tree.insert("", "end", values=(block["id"], block["size"], "Đã tạo"))

        for process in self.processes:
            self.process_tree.insert(
                "",
                "end",
                values=(
                    process["id"],
                    process.get("customer_name", ""),
                    process.get("cover_pages", 0),
                    process.get("color_pages", 0),
                    process.get("bw_pages", 0),
                    process["size"],
                )
            )

    def allocate(self, algorithm):
        blocks = [
            {
                "id": block["id"],
                "size": block["size"],
                "remaining": block["size"],
                "items": [],
            }
            for block in self.memory_blocks
        ]

        results = []

        for process in self.processes:
            candidates = [
                index for index, block in enumerate(blocks)
                if block["remaining"] >= process["size"]
            ]

            chosen_index = None
            if candidates:
                if algorithm == "First Fit":
                    chosen_index = candidates[0]
                elif algorithm == "Best Fit":
                    chosen_index = min(
                        candidates,
                        key=lambda i: blocks[i]["remaining"] - process["size"],
                    )
                elif algorithm == "Worst Fit":
                    chosen_index = max(candidates, key=lambda i: blocks[i]["remaining"])

            if chosen_index is None:
                results.append({
                    "algorithm": algorithm,
                    "process": process["id"],
                    "size": process["size"],
                    "block": "—",
                    "remain": "—",
                    "status": "Chờ/Thất bại tạm thời",
                })
            else:
                block = blocks[chosen_index]
                block["items"].append(process)
                block["remaining"] -= process["size"]

                results.append({
                    "algorithm": algorithm,
                    "process": process["id"],
                    "size": process["size"],
                    "block": block["id"],
                    "remain": block["remaining"],
                    "status": "Thành công",
                })

        total_memory = sum(block["size"] for block in blocks)
        used_memory = sum(
            item["size"]
            for block in blocks
            for item in block["items"]
        )
        success = sum(1 for item in results if item["status"] == "Thành công")
        failed = len(results) - success
        usage = round(used_memory / total_memory * 100, 1) if total_memory else 0

        # Khi chưa có tiến trình/tác vụ nào để cấp phát thì biểu đồ so sánh
        # phải bắt đầu từ 0% cho cả hiệu suất và phân mảnh.
        # Không xem toàn bộ bộ nhớ trống là 100% phân mảnh.
        if not self.processes:
            fragmentation = 0
        else:
            fragmentation = round(100 - usage, 1)

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

    def run_allocation(self, notify=False):
        self.compare_results = {algorithm: self.allocate(algorithm) for algorithm in ALGORITHMS}

        self.best_payload = max(
            self.compare_results.values(),
            key=lambda item: (item["success"], item["usage"], -item["fragmentation"]),
        ) if self.compare_results else None

        if self.best_payload:
            self.allocation_results = self.best_payload["results"]
        else:
            self.allocation_results = []

        self.refresh_result_table()
        self.update_metrics()
        self.draw_all_memory_visuals()
        self.update_compare()
        self.update_conclusion()

        if notify and self.best_payload:
            self.emit_memory_payload()

    def refresh_result_table(self):
        for tree in self.result_trees.values():
            for item in tree.get_children():
                tree.delete(item)

        for algorithm in ALGORITHMS:
            tree = self.result_trees.get(algorithm)
            if not tree:
                continue

            payload = self.compare_results.get(algorithm, {})
            results = payload.get("results", [])

            for result in results:
                tag = "success" if result["status"] == "Thành công" else "waiting"
                tree.insert(
                    "",
                    "end",
                    values=(
                        result["process"],
                        result["size"],
                        result["block"],
                        result["remain"],
                        result["status"],
                    ),
                    tags=(tag,),
                )

    def update_metrics(self):
        best = self.best_payload or {}
        self.metric_labels["total"].config(text=str(len(self.processes)))
        self.metric_labels["success"].config(text=str(best.get("success", 0)))
        self.metric_labels["failed"].config(text=str(best.get("failed", 0)))
        self.metric_labels["usage"].config(text=f"{best.get('usage', 0)}%")

    def update_compare(self):
        self.draw_compare_bar_chart()

    def draw_compare_bar_chart(self):
        if not hasattr(self, "compare_canvas"):
            return

        canvas = self.compare_canvas
        canvas.delete("all")

        width = max(canvas.winfo_width(), 520)
        height = max(canvas.winfo_height(), 210)

        if not self.compare_results:
            canvas.create_text(
                18,
                42,
                anchor="w",
                text="Chưa có dữ liệu so sánh cấp phát bộ nhớ.",
                fill=MUTED_TEXT,
                font=("Arial", 10, "bold"),
            )
            return

        card_gap = 10
        left_pad = 6
        top_pad = 6
        card_count = len(ALGORITHMS)
        card_width = max(150, int((width - left_pad * 2 - card_gap * (card_count - 1)) / card_count))
        card_height = height - top_pad * 2

        red = "#EF4444"
        axis_color = "#CBD5E1"
        light_bg = "#F8FAFC"
        max_bar_height = max(70, card_height - 105)

        for index, algorithm in enumerate(ALGORITHMS):
            payload = self.compare_results.get(algorithm, {})

            # Nếu chưa có tác vụ hoặc thuật toán chưa phát sinh dòng kết quả,
            # hai cột đều hiển thị 0 thay vì phân mảnh 100%.
            if not self.processes or not payload.get("results"):
                usage = 0.0
                fragmentation = 0.0
            else:
                usage = float(payload.get("usage", 0) or 0)
                fragmentation = float(payload.get("fragmentation", 0) or 0)

            color = ALGORITHM_COLORS.get(algorithm, PRIMARY_COLOR)

            x1 = left_pad + index * (card_width + card_gap)
            y1 = top_pad
            x2 = x1 + card_width
            y2 = y1 + card_height

            canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=WHITE_COLOR,
                outline=BORDER_COLOR,
                width=1,
            )

            canvas.create_text(
                x1 + card_width / 2,
                y1 + 20,
                text=algorithm,
                fill=color,
                font=("Arial", 10, "bold"),
                anchor="center",
            )

            # Legend: ô màu + tên chỉ số.
            legend_y = y1 + 45
            legend_x = x1 + max(12, card_width * 0.16)

            canvas.create_rectangle(legend_x, legend_y - 5, legend_x + 10, legend_y + 5, fill=color, outline=color)
            canvas.create_text(
                legend_x + 15,
                legend_y,
                text="Hiệu suất",
                fill=TEXT_COLOR,
                font=("Arial", 8, "bold"),
                anchor="w",
            )

            frag_x = legend_x + max(78, card_width * 0.45)
            canvas.create_rectangle(frag_x, legend_y - 5, frag_x + 10, legend_y + 5, fill=red, outline=red)
            canvas.create_text(
                frag_x + 15,
                legend_y,
                text="Phân mảnh",
                fill=TEXT_COLOR,
                font=("Arial", 8, "bold"),
                anchor="w",
            )

            base_y = y2 - 28
            canvas.create_line(x1 + 22, base_y, x2 - 22, base_y, fill=axis_color)

            bar_width = min(36, max(24, int(card_width * 0.16)))
            center_x = x1 + card_width / 2
            usage_x = center_x - bar_width - 15
            frag_bar_x = center_x + 15

            usage_height = 0 if usage <= 0 else max(2, int(max_bar_height * usage / 100))
            frag_height = 0 if fragmentation <= 0 else max(2, int(max_bar_height * fragmentation / 100))

            # Hiệu suất
            canvas.create_rectangle(
                usage_x,
                base_y - usage_height,
                usage_x + bar_width,
                base_y,
                fill=color,
                outline=color,
            )
            canvas.create_text(
                usage_x + bar_width / 2,
                base_y - usage_height - 10,
                text=f"{usage:.1f}%",
                fill=TEXT_COLOR,
                font=("Arial", 8, "bold"),
                anchor="center",
            )

            # Phân mảnh
            canvas.create_rectangle(
                frag_bar_x,
                base_y - frag_height,
                frag_bar_x + bar_width,
                base_y,
                fill=red,
                outline=red,
            )
            canvas.create_text(
                frag_bar_x + bar_width / 2,
                base_y - frag_height - 10,
                text=f"{fragmentation:.1f}%",
                fill=TEXT_COLOR,
                font=("Arial", 8, "bold"),
                anchor="center",
            )

        canvas.configure(scrollregion=(0, 0, width, height))

    def update_conclusion(self):
        if not hasattr(self, "conclusion_items_frame"):
            return

        self.clear_frame(self.conclusion_items_frame)

        if not self.compare_results or not self.processes:
            self.add_conclusion_item(
                self.conclusion_items_frame,
                "Chưa có dữ liệu mô phỏng. Hãy thêm tác vụ và bấm Áp dụng để xem nhận xét."
            )
            return

        # Lấy payload tốt nhất
        best = self.best_payload
        if not best:
            best = max(
                self.compare_results.values(),
                key=lambda x: x.get("usage", 0)
            )

        best_name = best.get("algorithm", "")
        best_usage = best.get("usage", 0.0)
        best_fragmentation = best.get(
            "fragmentation",
            0.0 if not self.processes else round(100 - best_usage, 1)
        )

        # First Fit
        first_fit = self.compare_results.get("First Fit")
        first_fit_usage = 0.0
        if first_fit:
            first_fit_usage = first_fit.get("usage", 0.0)

        # Worst Fit
        worst_fit = self.compare_results.get("Worst Fit")
        worst_fit_fragmentation = 0.0
        if worst_fit:
            worst_fit_fragmentation = worst_fit.get(
                "fragmentation",
                0.0 if not self.processes else round(100 - worst_fit.get("usage", 0.0), 1)
            )

        # Các tiến trình chưa cấp phát được ở thuật toán tốt nhất
        failed_processes = []
        for item in best.get("results", []):
            if item.get("status") != "Thành công":
                failed_processes.append(item.get("process", ""))

        # Dòng 1
        self.add_conclusion_item(
            self.conclusion_items_frame,
            f"{best_name} đạt hiệu suất sử dụng bộ nhớ cao nhất ({best_usage}%) "
            f"và phân mảnh thấp nhất ({best_fragmentation}%)."
        )

        # Dòng 2
        if first_fit:
            self.add_conclusion_item(
                self.conclusion_items_frame,
                f"First Fit có hiệu suất ổn định ({first_fit_usage}%) và phù hợp khi cần tốc độ cấp phát nhanh."
            )

        # Dòng 3
        if worst_fit:
            self.add_conclusion_item(
                self.conclusion_items_frame,
                f"Worst Fit tạo ra nhiều phân mảnh nhất ({worst_fit_fragmentation}%), "
                f"dẫn đến lãng phí bộ nhớ."
            )

        # Dòng 4
        if failed_processes:
            failed_text = ", ".join(failed_processes)
            self.add_conclusion_item(
                self.conclusion_items_frame,
                f"Tiến trình {failed_text} không được cấp phát do không còn khối nhớ phù hợp."
            )
        else:
            self.add_conclusion_item(
                self.conclusion_items_frame,
                "Tất cả tiến trình hiện tại đều được cấp phát thành công với cấu hình bộ nhớ đang chọn."
            )

        # Dòng 5
        self.add_conclusion_item(
            self.conclusion_items_frame,
            "Để cải thiện, có thể hợp nhất (coalesce) các khối nhớ trống liền kề khi tiến trình kết thúc."
        )

    def refresh_data(self, notify=True):
        self.prepare_default_data()
        self.refresh_tables()
        self.run_allocation(notify=notify)

    def refresh_memory(self):
        self.refresh_data()

    def reset_data(self):
        self.refresh_data()

    def run_simulation(self):
        """Giữ hàm cũ để app hoặc code khác gọi vẫn chạy được."""
        self.run_allocation(notify=True)

    def emit_memory_payload(self):
        payload = dict(self.best_payload or {})
        payload["compare_results"] = self.compare_results
        payload["best_algorithm"] = payload.get("algorithm", "")

        if self.on_memory_finished:
            try:
                self.on_memory_finished(payload)
            except Exception as error:
                # Không để lỗi refresh báo cáo làm sập màn hình bộ nhớ.
                print("Lỗi gửi payload bộ nhớ:", error)

    # =====================================================
    # DRAWING
    # =====================================================
    def get_block_width(self, block_size):
        return max(130, min(230, int(block_size * 0.8)))

    def draw_algorithm_visual(self, algorithm):
        visual = self.algorithm_visuals.get(algorithm)
        if not visual:
            return

        canvas = visual["canvas"]
        summary_label = visual["summary_label"]

        canvas.delete("all")

        payload = self.compare_results.get(algorithm)

        if not payload:
            canvas.create_text(
                18,
                42,
                anchor="w",
                text="Chưa có dữ liệu cấp phát bộ nhớ.",
                fill=MUTED_TEXT,
                font=("Arial", 10, "bold"),
            )
            summary_label.config(text="")
            canvas.configure(
                scrollregion=(0, 0, max(canvas.winfo_width(), 300), 96),
                height=96
            )
            return

        left = 18
        top = 18
        block_height = 80
        block_gap = 24
        x = left

        for block in payload["blocks"]:
            block_width = self.get_block_width(block["size"])

            canvas.create_text(
                x + block_width / 2,
                top,
                text=f"{block['id']} ({block['size']} KB)",
                fill=TEXT_COLOR,
                font=("Arial", 9, "bold"),
                anchor="center",
                justify="center"
            )

            y = top + 14
            used_x = x

            canvas.create_rectangle(
                x,
                y,
                x + block_width,
                y + block_height,
                fill="#F8FAFC",
                outline="#94A3B8",
            )

            for item in block.get("items", []):
                item_width = max(
                    30,
                    int(item["size"] / block["size"] * block_width)
                )

                if used_x + item_width > x + block_width:
                    item_width = max(12, int(x + block_width - used_x))

                fill = self.process_color_map.get(item["id"], "#BFDBFE")

                canvas.create_rectangle(
                    used_x,
                    y,
                    used_x + item_width,
                    y + block_height,
                    fill=fill,
                    outline="#94A3B8",
                )

                canvas.create_text(
                    used_x + item_width / 2,
                    y + block_height / 2,
                    text=f"{item['id']}\n{item['size']}",
                    fill=TEXT_COLOR,
                    font=("Arial", 9, "bold"),
                    anchor="center",
                    justify="center",
                    width=max(20, item_width - 6)
                )

                used_x += item_width

            if block["remaining"] > 0 and used_x < x + block_width - 4:
                remain_width = x + block_width - used_x

                canvas.create_text(
                    used_x + remain_width / 2,
                    y + block_height / 2,
                    text=f"{block['remaining']}",
                    fill=TEXT_COLOR,
                    font=("Arial", 9),
                    anchor="center",
                    justify="center",
                    width=max(20, remain_width - 6)
                )

            x += block_width + block_gap

        canvas_height = 130

        canvas.configure(
            scrollregion=(0, 0, max(x + 16, canvas.winfo_width()), canvas_height),
            height=canvas_height,
        )

        summary_label.config(
            text=(
                f"Thành công: {payload['success']}/{len(self.processes)} | "
                f"Chờ/tạm thất bại: {payload['failed']} | "
                f"Hiệu suất: {payload['usage']}%"
            )
        )


    def draw_all_memory_visuals(self):
        if not getattr(self, "algorithm_visuals", None):
            return

        for algorithm in ALGORITHMS:
            self.draw_algorithm_visual(algorithm)

    # Giữ tên hàm cũ để không lỗi nếu nơi khác gọi.
    def draw_memory_blocks(self, blocks=None):
        if blocks is not None:
            # Nếu code cũ truyền 1 bộ blocks, tạm hiển thị như First Fit để tương thích.
            self.compare_results["First Fit"] = {
                "algorithm": "First Fit",
                "blocks": blocks,
                "results": self.allocation_results,
                "success": sum(1 for r in self.allocation_results if r.get("status") == "Thành công"),
                "failed": sum(1 for r in self.allocation_results if r.get("status") != "Thành công"),
                "usage": 0,
                "fragmentation": 0,
            }
        self.draw_all_memory_visuals()

    def on_page_show(self):
        self.draw_all_memory_visuals()

    def on_page_hide(self):
        pass
