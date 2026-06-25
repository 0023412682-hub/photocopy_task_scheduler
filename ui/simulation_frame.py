import copy
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox
from collections import OrderedDict

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False

from ui.icon_utils import load_icon, resolve_icon_path as shared_resolve_icon_path, normalize_icon_name as shared_normalize_icon_name


# Import trực tiếp từng file thuật toán.
# Không import qua algorithms/__init__.py để tránh trường hợp __init__.py export nhầm
# làm SJF / Priority / Round Robin cùng trỏ về run_fcfs.
from algorithms.fcfs import run_fcfs
from algorithms.sjf import run_sjf
from algorithms.priority import run_priority
from algorithms.round_robin import run_round_robin
try:
    from utils.constants import (
        DEFAULT_TIME_QUANTUM,
        PRIMARY_COLOR,
        SECONDARY_COLOR,
        ACCENT_COLOR,
        BACKGROUND_COLOR,
        WHITE_COLOR,
        TEXT_COLOR,
    )
except Exception:
    DEFAULT_TIME_QUANTUM = 4
    PRIMARY_COLOR = "#005BAC"
    SECONDARY_COLOR = "#EAF4FF"
    ACCENT_COLOR = "#D71920"
    BACKGROUND_COLOR = "#F4F7FB"
    WHITE_COLOR = "#FFFFFF"
    TEXT_COLOR = "#1F2937"

BORDER_COLOR = "#D9E2EC"
MUTED_TEXT = "#64748B"
GREEN = "#16A34A"
GREEN_DARK = "#15803D"
GREEN_BG = "#F0FDF4"
ORANGE = "#F97316"
ORANGE_DARK = "#C2410C"
ORANGE_BG = "#FFF7ED"
PURPLE = "#7C3AED"
PURPLE_BG = "#F5F3FF"
BLUE_BG = "#EFF6FF"
RED_BG = "#FEF2F2"

# Chạy theo mốc sự kiện, không chạy 1 giây/1 đơn vị thời gian nữa.
# Vì vậy dữ liệu có arrival_time lớn như 30000+ cũng không phải đợi 30000 giây.
EVENT_STEP_MS = 450
# Chỉ làm các thao tác nặng (vẽ Gantt, quét toàn bộ card, gửi payload) mỗi 3 tick.
# Nhãn thời gian, tiến độ và chỉ số vẫn cập nhật ở từng đơn vị thời gian.
HEAVY_REFRESH_EVERY = 3
PX_PER_TIME = 26

# Nếu khoảng arrival_time quá lớn so với tổng burst_time, giao diện sẽ nén arrival_time
# theo thứ tự đến để mô phỏng dễ nhìn hơn. Thứ tự tác vụ vẫn giữ nguyên.
LARGE_ARRIVAL_MIN_SPAN = 120
LARGE_ARRIVAL_BURST_MULTIPLIER = 4

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(BASE_DIR, "utils", "icons")

class SimulationFrame(tk.Frame):
    """Màn mô phỏng xử lý tác vụ cho 4 giải thuật.

    Bản này dùng kết quả thật từ 4 hàm thuật toán:
    - run_fcfs
    - run_sjf
    - run_priority
    - run_round_robin

    Sửa tối ưu:
    - Không reset khi chuyển giao diện.
    - Khi đã mô phỏng xong, quay lại trang không render lại toàn bộ.
    - Hạn chế draw_gantt() khi resize hoặc khi trang đã có kết quả.
    """

    def __init__(self, parent, tasks, on_simulation_finished=None, on_simulation_progress=None):
        super().__init__(parent, bg=BACKGROUND_COLOR)

        self.tasks = tasks or []
        self.on_simulation_finished = on_simulation_finished
        self.on_simulation_progress = on_simulation_progress

        self.normalized_tasks = []
        self.arrival_note = ""

        self.results = OrderedDict()
        self.current_time = 0
        self.max_time = 0
        self.timeline_points = [0]
        self.timeline_index = 0

        self.is_running = False
        self.after_id = None
        self.is_visible = True

        # Đánh dấu đã render xong lần cuối để khi quay lại trang không vẽ lại nặng
        self.is_finished_rendered = False

        self.algo_panels = {}
        self.task_lookup = {}
        self.task_color_map = {}
        self.original_arrival_map = {}

        # Cache widget để khi mô phỏng chỉ cập nhật text/trạng thái,
        # không destroy và tạo lại card liên tục gây giật.
        self.queue_card_widgets = {}
        self.algo_queue_card_widgets = {}
        self.mousewheel_bound = False
        self.images = {}

        self.task_colors = [
            "#0B63CE", "#16A34A", "#F97316", "#7C3AED",
            "#DC2626", "#0891B2", "#2563EB", "#9333EA",
            "#EA580C", "#059669", "#BE123C", "#0F766E",
        ]

        self.algorithm_var = tk.StringVar(value="Tất cả")
        self.quantum_var = tk.StringVar(value="3")
        self.time_var = tk.StringVar(value="Thời gian mô phỏng: 0")
        self.note_var = tk.StringVar(value="")

        self.configure_styles()
        self.prepare_display_task_maps()
        self.create_widgets()
        self.render_queue()
        self.render_algorithm_panels()
        self.draw_gantt()

        self.bind("<Destroy>", self._on_destroy, add="+")

    # =========================================================
    # PAGE LIFECYCLE
    # =========================================================
    def on_page_hide(self):
        """Khi chuyển sang trang khác: không reset, không destroy, không render nặng."""
        self.is_visible = False
        self.unbind_mousewheel_events()
    def on_page_show(self):
        """Khi quay lại trang mô phỏng: chỉ cập nhật giao diện 1 lần theo trạng thái hiện tại."""
        self.is_visible = True
        self.bind_mousewheel_events()

        if not self.results:
            if hasattr(self, "queue_frame"):
                self.render_queue()

            if hasattr(self, "algorithm_area"):
                self.render_algorithm_panels()

            self.draw_gantt()
            return

        # Khi quay lại giữa lúc đang chạy, cập nhật 1 lần để giao diện bắt kịp thời gian hiện tại.
        self.refresh_realtime_ui(force=True)

        if hasattr(self, "status_label"):
            if self.is_running:
                self.status_label.config(text="● Đang mô phỏng...", fg="#16A34A")
            elif self.timeline_index >= len(self.timeline_points) - 1:
                self.status_label.config(text="● Đã hoàn thành mô phỏng", fg="#2563EB")
            else:
                self.status_label.config(text="● Đã tạm dừng", fg="#F97316")
    def _on_destroy(self, event):
        """Hủy after khi frame bị destroy thật sự."""
        if event.widget is self:
            self.stop_after_job()

    def refresh_data(self):
        """Được app.py gọi khi danh sách tác vụ thay đổi.

        Tối ưu:
        - Nếu đang chạy hoặc đã có kết quả mô phỏng thì không reset.
        - Tránh trường hợp chuyển trang quay lại bị render lại rất lâu.
        """
        if self.is_running or self.results:
            return

        self.stop_after_job()
        self.current_time = 0
        self.max_time = 0
        self.timeline_points = [0]
        self.timeline_index = 0
        self.results.clear()
        self.normalized_tasks = []
        self.task_lookup = {}
        self.arrival_note = ""
        self.is_finished_rendered = False

        self.time_var.set("Thời gian mô phỏng: 0")
        self.note_var.set("")

        self.prepare_display_task_maps()

        if hasattr(self, "task_count_label"):
            self.task_count_label.config(text=str(len(self.tasks)))

        if hasattr(self, "queue_title_label"):
            self.queue_title_label.config(text=f"DANH SÁCH TÁC VỤ ({len(self.tasks)})")

        if hasattr(self, "status_label"):
            self.status_label.config(
                text="● Sẵn sàng mô phỏng",
                fg="#64748B"
            )

        if hasattr(self, "run_button"):
            self.run_button.config(state=tk.NORMAL)

        if hasattr(self, "pause_button"):
            self.update_button_image(self.pause_button, "Pause", "Ⅱ  Tạm dừng", "#F97316", WHITE_COLOR)

        if hasattr(self, "queue_frame"):
            self.render_queue()

        if hasattr(self, "algorithm_area"):
            self.render_algorithm_panels()

        self.draw_gantt()

    # =========================================================
    # UI SETUP
    # =========================================================
    def configure_styles(self):
        style = ttk.Style()
        style.configure("Scheduler.TCombobox", font=("Arial", 10), padding=6)
        style.configure("Horizontal.TScrollbar", background="#CBD5E1")

    def normalize_icon_name(self, value):
        return shared_normalize_icon_name(value)

    def resolve_icon_path(self, filename):
        return shared_resolve_icon_path(ICON_DIR, filename)

    def load_image(self, filename, size=(40, 40)):
        return load_icon(self, ICON_DIR, filename, size=size, crop_transparency=True, keep_aspect=True)

    def make_image_button(
        self,
        parent,
        image_name,
        fallback_text,
        command,
        size=(136, 36),
        button_size=None,
        fallback_bg=PRIMARY_COLOR,
        fallback_fg=WHITE_COLOR,
    ):
        """Tạo nút bằng Label để không xuất hiện khung mặc định của tk.Button.
        Tất cả ảnh nút dùng cùng size để 3 nút bằng nhau.
        """
        button_size = button_size or size
        photo = self.load_image(image_name, size)
        bg = parent.cget("bg") if hasattr(parent, "cget") else WHITE_COLOR

        if photo:
            btn = tk.Label(
                parent,
                image=photo,
                bg=bg,
                relief=tk.FLAT,
                bd=0,
                borderwidth=0,
                highlightthickness=0,
                cursor="hand2",
                padx=0,
                pady=0,
            )
            btn.image = photo
        else:
            btn = tk.Label(
                parent,
                text=fallback_text,
                bg=fallback_bg,
                fg=fallback_fg,
                font=("Arial", 11, "bold"),
                relief=tk.FLAT,
                bd=0,
                borderwidth=0,
                highlightthickness=0,
                cursor="hand2",
                padx=14,
                pady=7,
            )

        btn._image_size = size
        btn._button_size = button_size
        btn._button_command = command

        def on_click(event, widget=btn):
            if str(widget.cget("state")) == str(tk.DISABLED):
                return
            widget._button_command()

        btn.bind("<Button-1>", on_click)
        return btn

    def update_button_image(self, button, image_name, fallback_text=None, fallback_bg=None, fallback_fg=None):
        size = getattr(button, "_image_size", (136, 36))
        photo = self.load_image(image_name, size)
        if photo:
            bg = button.master.cget("bg") if getattr(button, "master", None) else WHITE_COLOR
            button.config(image=photo, text="", bg=bg)
            button.image = photo
        elif fallback_text is not None:
            button.config(text=fallback_text, image="")
            if fallback_bg:
                button.config(bg=fallback_bg)
            if fallback_fg:
                button.config(fg=fallback_fg)

    def section(self, parent, title, icon_file=None):
        box = tk.Frame(
            parent,
            bg=WHITE_COLOR,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )

        head = tk.Frame(box, bg=WHITE_COLOR)
        head.pack(fill=tk.X)

        icon_photo = self.load_image(icon_file, (20, 20)) if icon_file else None
        if icon_photo:
            tk.Label(head, image=icon_photo, bg=WHITE_COLOR).pack(side=tk.LEFT, padx=(14, 8), pady=9)
        else:
            tk.Label(
                head,
                text="▣",
                bg=WHITE_COLOR,
                fg=PRIMARY_COLOR,
                font=("Arial", 11, "bold")
            ).pack(side=tk.LEFT, padx=(14, 8), pady=9)

        title_label = tk.Label(
            head,
            text=title,
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 12, "bold")
        )
        title_label.pack(side=tk.LEFT, pady=9)

        box.title_label = title_label

        tk.Frame(box, bg="#E2E8F0", height=1).pack(fill=tk.X)

        return box

    def create_widgets(self):
        self.canvas = tk.Canvas(self, bg=BACKGROUND_COLOR, highlightthickness=0)
        self.scrollbar_y = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = tk.Frame(self.canvas, bg=BACKGROUND_COLOR)

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.content,
            anchor="nw"
        )

        self.canvas.configure(yscrollcommand=self.scrollbar_y.set)

        self.content.bind(
            "<Configure>",
            lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(self.canvas_window, width=event.width)
        )

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.bind_mousewheel_events()

        self.build_top_section()
        self.build_algorithm_section()
        self.build_gantt_section()

    def bind_mousewheel_events(self):
        """Chỉ bind mousewheel khi trang mô phỏng đang hiển thị.

        Dùng bind_all quá lâu có thể làm trang khác bị ảnh hưởng khi đã chuyển giao diện.
        """
        if self.mousewheel_bound or not hasattr(self, "canvas"):
            return

        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind_all("<Button-4>", self.on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self.on_mousewheel_linux)
        self.mousewheel_bound = True

    def unbind_mousewheel_events(self):
        if not self.mousewheel_bound or not hasattr(self, "canvas"):
            return

        try:
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        except Exception:
            pass

        self.mousewheel_bound = False

    def build_top_section(self):
        top = tk.Frame(
            self.content,
            bg=BACKGROUND_COLOR
        )

        top.pack(
            fill=tk.X,
            padx=8,
            pady=(0, 8)
        )

        self.control_card = self.section(
            top,
            "THIẾT LẬP MÔ PHỎNG",
            icon_file="Simulation_Setup"
        )

        self.control_card.pack(
            side=tk.LEFT,
            fill=tk.Y,
            padx=(0, 6)
        )

        self.control_card.pack_propagate(False)
        self.control_card.config(width=450, height=220)

        self.queue_section = self.section(
            top,
            f"DANH SÁCH TÁC VỤ ({len(self.tasks)})",
            icon_file="Info_data"
        )

        self.queue_title_label = self.queue_section.title_label

        self.queue_section.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        self.build_control_content()
        self.build_queue_content()

    def on_mousewheel(self, event):
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def on_mousewheel_linux(self, event):
        try:
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")
        except Exception:
            pass

    def build_control_content(self):
        ctrl = self.control_card

        body = tk.Frame(
            ctrl,
            bg=WHITE_COLOR
        )

        body.pack(fill=tk.X, padx=12, pady=10)

        tk.Label(
            body,
            text="📋 Số tác vụ đang chờ",
            bg=WHITE_COLOR,
            fg=MUTED_TEXT,
            font=("Arial", 13, "bold")
        ).pack()

        self.task_count_label = tk.Label(
            body,
            text=str(len(self.tasks)),
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 23, "bold")
        )

        self.task_count_label.pack(pady=(2, 8))

        self.status_label = tk.Label(
            body,
            text="● Sẵn sàng mô phỏng",
            bg=WHITE_COLOR,
            fg="#64748B",
            font=("Arial", 12, "bold")
        )

        self.status_label.pack(pady=(0, 8))

        btn_frame = tk.Frame(
            body,
            bg=WHITE_COLOR
        )

        btn_frame.pack()

        control_button_size = (136, 36)

        self.run_button = self.make_image_button(
            btn_frame,
            "Run_Simulation",
            "▶ Chạy mô phỏng",
            self.run_simulation,
            size=control_button_size,
            button_size=control_button_size,
            fallback_bg="#16A34A",
            fallback_fg=WHITE_COLOR
        )

        self.run_button.pack(side=tk.LEFT, padx=(0, 6))

        self.pause_button = self.make_image_button(
            btn_frame,
            "Pause",
            "Ⅱ  Tạm dừng",
            self.pause_or_resume,
            size=control_button_size,
            button_size=control_button_size,
            fallback_bg="#F97316",
            fallback_fg=WHITE_COLOR
        )

        self.pause_button.pack(side=tk.LEFT, padx=(0, 6))

        self.reset_button = self.make_image_button(
            btn_frame,
            "Reset",
            "↺ Đặt lại",
            self.reset_simulation,
            size=control_button_size,
            button_size=control_button_size,
            fallback_bg="#DC2626",
            fallback_fg=WHITE_COLOR
        )

        self.reset_button.pack(side=tk.LEFT, padx=0)

    def info_label(self, parent, title, value, row):
        tk.Label(
            parent,
            text=title,
            bg=WHITE_COLOR,
            fg=MUTED_TEXT,
            font=("Arial", 10, "bold")
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=(0 if row == 0 else 8, 0)
        )

        tk.Label(
            parent,
            text=value,
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 10, "bold")
        ).grid(
            row=row,
            column=1,
            sticky="w",
            padx=(6, 0),
            pady=(0 if row == 0 else 8, 0)
        )

    def vertical_divider(self, parent):
        tk.Frame(
            parent,
            bg="#E2E8F0",
            width=1,
            height=48
        ).pack(side=tk.LEFT, padx=(0, 22), fill=tk.Y)

    def build_queue_content(self):
        queue_wrap = tk.Frame(self.queue_section, bg=WHITE_COLOR)
        queue_wrap.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        self.queue_canvas = tk.Canvas(
            queue_wrap,
            bg=WHITE_COLOR,
            height=82,
            highlightthickness=0
        )

        self.queue_scroll = ttk.Scrollbar(
            queue_wrap,
            orient="horizontal",
            command=self.queue_canvas.xview
        )

        self.queue_canvas.configure(xscrollcommand=self.queue_scroll.set)

        self.queue_frame = tk.Frame(self.queue_canvas, bg=WHITE_COLOR)

        self.queue_canvas.create_window(
            (0, 0),
            window=self.queue_frame,
            anchor="nw"
        )

        self.queue_frame.bind(
            "<Configure>",
            lambda event: self.queue_canvas.configure(scrollregion=self.queue_canvas.bbox("all"))
        )

        self.queue_canvas.pack(fill=tk.BOTH, expand=True)
        self.queue_scroll.pack(fill=tk.X)

    def build_algorithm_section(self):
        self.algorithm_area = tk.Frame(self.content, bg=BACKGROUND_COLOR)
        self.algorithm_area.pack(fill=tk.X, padx=8, pady=0)
        self.algorithm_area.grid_columnconfigure(0, weight=1)
        self.algorithm_area.grid_columnconfigure(1, weight=1)

    def build_gantt_section(self):
        gantt = self.section(
            self.content,
            "BIỂU ĐỒ GANTT (THEO TIẾN TRÌNH MÔ PHỎNG)",
            icon_file="Chart"
        )

        gantt.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        wrap = tk.Frame(gantt, bg=WHITE_COLOR)
        wrap.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        self.gantt_canvas = tk.Canvas(
            wrap,
            height=205,
            bg=WHITE_COLOR,
            highlightthickness=0
        )

        self.gantt_scroll = ttk.Scrollbar(
            wrap,
            orient="horizontal",
            command=self.gantt_canvas.xview
        )

        self.gantt_canvas.configure(xscrollcommand=self.gantt_scroll.set)

        self.gantt_canvas.pack(fill=tk.BOTH, expand=True)
        self.gantt_scroll.pack(fill=tk.X)

        # Tối ưu: không gọi draw_gantt trực tiếp liên tục khi resize
        self.gantt_canvas.bind(
            "<Configure>",
            self.on_gantt_resize
        )

    def on_gantt_resize(self, event=None):
        """Hạn chế vẽ lại Gantt khi chuyển trang hoặc resize."""
        if not self.is_visible:
            return

        if not self.results:
            self.draw_gantt()
            return

        if self.is_running:
            self.draw_gantt()
            return

        if self.timeline_index >= len(self.timeline_points) - 1:
            return

        self.draw_gantt()
    def get_task_number(self, task_id):
        """Lấy phần số trong task_id để sắp xếp T001, T002, ..., T010 đúng thứ tự."""
        match = re.search(r"\d+", str(task_id))
        if match:
            return int(match.group())

        return 999999

    def sort_tasks_by_task_id(self, tasks):
        """Sắp xếp theo mã tác vụ để giao diện luôn hiển thị từ T001."""
        return sorted(
            tasks or [],
            key=lambda task: (
                self.get_task_number(self.safe_attr(task, "task_id", "")),
                str(self.safe_attr(task, "task_id", ""))
            )
        )

    def prepare_sequence_algorithm_tasks(self, tasks):
        """
        Tạo nguồn dữ liệu riêng cho FCFS và Round Robin.

        Hai thuật toán này trong file algorithm đang sort theo arrival_time.
        Nếu dữ liệu Excel có T005 đến trước T001 thì màn mô phỏng sẽ bắt đầu từ T005.
        Để phần demo chạy đúng thứ tự mã tác vụ, ta copy riêng danh sách, sắp xếp T001 -> T002
        và gán lại arrival_time tăng dần 0, 1, 2... Chỉ áp dụng cho FCFS/RR, không ảnh hưởng
        dữ liệu gốc hay SJF/Priority.
        """
        ordered_tasks = self.sort_tasks_by_task_id(copy.deepcopy(tasks or []))

        for index, task in enumerate(ordered_tasks):
            setattr(task, "arrival_time", index)

        return ordered_tasks

    def get_algorithm_infos(self):
        q = self.get_quantum(show_error=False)
        task_source = self.normalized_tasks if self.normalized_tasks else self.prepare_simulation_tasks()[0]

        # Quan trọng:
        # 4 thuật toán phải nhận CÙNG một bộ dữ liệu đầu vào đã chuẩn hoá.
        # Không được gán lại arrival_time riêng cho FCFS/RR thành 0,1,2...
        # vì như vậy các thuật toán rất dễ nhìn giống FCFS và làm sai bản chất mô phỏng.
        def clone_source():
            return copy.deepcopy(task_source)

        return OrderedDict([
            ("FCFS", {
                "index": "1",
                "title": "FCFS (First Come First Serve)",
                "short": "FCFS",
                "color": PRIMARY_COLOR,
                "bg": BLUE_BG,
                "printer_icon": "B_Printer",
                "runner": lambda: run_fcfs(clone_source()),
            }),
            ("SJF", {
                "index": "2",
                "title": "SJF (Shortest Job First)",
                "short": "SJF",
                "color": GREEN_DARK,
                "bg": GREEN_BG,
                "printer_icon": "G_Printer",
                "runner": lambda: run_sjf(clone_source()),
            }),
            ("PRIORITY", {
                "index": "3",
                "title": "PRIORITY (Có ưu tiên)",
                "short": "Prio",
                "color": ORANGE_DARK,
                "bg": ORANGE_BG,
                "printer_icon": "R_Printer",
                "runner": lambda: run_priority(clone_source()),
            }),
            ("ROUND ROBIN", {
                "index": "4",
                "title": f"ROUND ROBIN (Quantum = {q})",
                "short": f"RR q={q}",
                "color": PURPLE,
                "bg": PURPLE_BG,
                "printer_icon": "P_Printer",
                "runner": lambda quantum=q: run_round_robin(clone_source(), quantum),
            }),
        ])

    def selected_algorithm_keys(self):
        selected = self.algorithm_var.get()

        if selected == "Tất cả":
            return ["FCFS", "SJF", "PRIORITY", "ROUND ROBIN"]

        return [selected]

    def render_algorithm_panels(self):
        for widget in self.algorithm_area.winfo_children():
            widget.destroy()

        self.algo_panels.clear()
        self.algo_queue_card_widgets.clear()

        keys = self.selected_algorithm_keys()

        for index, key in enumerate(keys):
            row = index // 2
            col = index % 2

            card = self.create_algorithm_card(self.algorithm_area, key)

            card.grid(
                row=row,
                column=col,
                sticky="nsew",
                padx=(0 if col == 0 else 6, 6 if col == 0 else 0),
                pady=6
            )

        self.algorithm_area.grid_columnconfigure(0, weight=1)
        self.algorithm_area.grid_columnconfigure(1, weight=1 if len(keys) > 1 else 0)
    def create_algorithm_card(self, parent, key):
        info = self.get_algorithm_infos()[key]
        color = info["color"]
        bg = info["bg"]

        card = tk.Frame(
            parent,
            bg=WHITE_COLOR,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )

        header = tk.Frame(card, bg=WHITE_COLOR)
        header.pack(fill=tk.X, padx=10, pady=(8, 4))

        tk.Label(
            header,
            text=info["index"],
            bg=color,
            fg=WHITE_COLOR,
            width=2,
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(
            header,
            text=info["title"],
            bg=WHITE_COLOR,
            fg=color,
            font=("Arial", 11, "bold")
        ).pack(side=tk.LEFT)

        body = tk.Frame(card, bg=WHITE_COLOR)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # ==========================
        # Queue hiển thị của thuật toán
        # ==========================
        queue_container = tk.Frame(
            card,
            bg="#F8FAFC",
            height=110,
            highlightbackground="#CBD5E1",
            highlightthickness=1
        )

        queue_container.pack(
            fill=tk.X,
            padx=10,
            pady=(0, 8)
        )

        queue_container.pack_propagate(False)

        queue_canvas = tk.Canvas(
            queue_container,
            bg="#F8FAFC",
            height=65,
            highlightthickness=0
        )

        queue_scroll = ttk.Scrollbar(
            queue_container,
            orient="horizontal",
            command=queue_canvas.xview
        )

        queue_canvas.configure(
            xscrollcommand=queue_scroll.set
        )

        queue_canvas.pack(
            fill=tk.BOTH,
            expand=True
        )

        queue_scroll.pack(
            fill=tk.X
        )

        queue_frame = tk.Frame(
            queue_canvas,
            bg="#F8FAFC"
        )

        queue_canvas.create_window(
            (0, 0),
            window=queue_frame,
            anchor="nw"
        )

        queue_frame.bind(
            "<Configure>",
            lambda e, c=queue_canvas:
                c.configure(scrollregion=c.bbox("all"))
        )

        printer_icon = self.load_image(info.get("printer_icon", "Printer"), (54, 54))
        printer_box = tk.Frame(body, bg=WHITE_COLOR, width=58, height=58)
        printer_box.grid(row=0, column=0, rowspan=4, sticky="n", padx=(0, 10), pady=(0, 2))
        printer_box.grid_propagate(False)
        printer_box.pack_propagate(False)
        if printer_icon:
            tk.Label(printer_box, image=printer_icon, bg=WHITE_COLOR).pack(expand=True)
        else:
            tk.Label(
                printer_box,
                text="🖨",
                bg=WHITE_COLOR,
                fg=color,
                font=("Arial", 34)
            ).pack(expand=True)

        progress_canvas = tk.Canvas(
            body,
            height=24,
            bg=WHITE_COLOR,
            highlightthickness=0,
            bd=0,
        )

        progress_canvas._progress_text = "Chưa chạy mô phỏng"
        progress_canvas._progress_percent = 0
        progress_canvas._progress_color = color

        progress_canvas.grid(row=0, column=1, sticky="ew", pady=(0, 6))

        progress_canvas.bind(
            "<Configure>",
            lambda event, canvas=progress_canvas: self.draw_progress_bar(canvas)
        )

        progress_label = tk.Label(
            body,
            text="Tiến độ: 0%",
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 9, "bold"),
            anchor="w",
        )

        progress_label.grid(row=1, column=1, sticky="ew")

        stat_row = tk.Frame(body, bg=WHITE_COLOR)
        stat_row.grid(row=2, column=1, sticky="ew", pady=(7, 0))

        elapsed_label = self.small_stat(stat_row, "◷  Tác vụ đã chạy", "0")
        remain_label = self.small_stat(stat_row, "⌛  Tác vụ còn lại", "0")
        waiting_label = self.small_stat(stat_row, "♟  Tác vụ đang đợi", "0")

        metric = tk.Frame(
            body,
            bg=bg,
            highlightbackground=self.lighten_border(color),
            highlightthickness=1
        )

        metric.grid(row=0, column=2, rowspan=3, sticky="nsew", padx=(12, 0))

        avg_wait_label = tk.Label(
            metric,
            text="Avg Waiting Time\n0.00",
            bg=bg,
            fg=color,
            font=("Arial", 10, "bold"),
            justify="center"
        )

        avg_wait_label.pack(fill=tk.X, padx=14, pady=(12, 6))

        avg_turn_label = tk.Label(
            metric,
            text="Avg Turnaround Time\n0.00",
            bg=bg,
            fg=color,
            font=("Arial", 10, "bold"),
            justify="center"
        )

        avg_turn_label.pack(fill=tk.X, padx=14, pady=(0, 12))

        body.grid_columnconfigure(1, weight=1)
        body.grid_columnconfigure(2, minsize=145)
        self.algo_panels[key] = {
            "queue_frame": queue_frame,
            "queue_canvas": queue_canvas,
            "progress_canvas": progress_canvas,
            "progress_label": progress_label,
            "elapsed_label": elapsed_label,
            "remain_label": remain_label,
            "waiting_label": waiting_label,
            "avg_wait_label": avg_wait_label,
            "avg_turn_label": avg_turn_label,
            "color": color,
            "bg": bg,
        }

        return card

    def render_algorithm_queue(self, key, result, force_rebuild=False):
        """Render queue riêng của từng thuật toán nhưng có cache widget.

        Bản cũ xoá toàn bộ card rồi tạo lại ở mỗi tick nên rất giật, đặc biệt khi có nhiều tác vụ.
        Bản này chỉ tạo card khi cần, còn mỗi tick chỉ đổi trạng thái RUNNING / WAITING / COMPLETED.
        """
        if key not in self.algo_panels:
            return

        panel = self.algo_panels[key]
        frame = panel["queue_frame"]

        if force_rebuild or key not in self.algo_queue_card_widgets:
            for w in frame.winfo_children():
                w.destroy()

            self.algo_queue_card_widgets[key] = {}

            for task in result.tasks:
                task_id = str(self.safe_attr(task, "task_id", ""))
                color = self.task_color_map.get(task_id, PRIMARY_COLOR)

                card = tk.Frame(
                    frame,
                    bg=WHITE_COLOR,
                    highlightbackground=BORDER_COLOR,
                    highlightthickness=1,
                    width=240,
                    height=120
                )

                card.pack(side=tk.LEFT, padx=(0, 8), pady=(2, 2))
                card.pack_propagate(False)

                card.grid_columnconfigure(0, weight=0, minsize=70)
                card.grid_columnconfigure(1, weight=1)

                tk.Label(
                    card,
                    text=self.icon_for_task(self.safe_attr(task, "task_type", "")),
                    bg=WHITE_COLOR,
                    font=("Arial", 28)
                ).grid(
                    row=0,
                    column=0,
                    rowspan=3,
                    padx=(8, 4),
                    pady=6,
                    sticky="n"
                )

                info_frame = tk.Frame(card, bg=WHITE_COLOR)
                info_frame.grid(
                    row=0,
                    column=1,
                    sticky="nsew",
                    padx=(0, 8),
                    pady=8
                )

                id_label = tk.Label(
                    info_frame,
                    text=task_id,
                    bg=WHITE_COLOR,
                    fg=color,
                    font=("Arial", 11, "bold"),
                    anchor="w"
                )
                id_label.pack(fill="x")

                type_label = tk.Label(
                    info_frame,
                    text=self.safe_attr(task, "task_type", ""),
                    bg=WHITE_COLOR,
                    fg=TEXT_COLOR,
                    font=("Arial", 10, "bold"),
                    anchor="w"
                )
                type_label.pack(fill="x", pady=(3, 0))

                status_label = tk.Label(
                    info_frame,
                    text="WAITING",
                    bg=WHITE_COLOR,
                    fg="#F97316",
                    font=("Arial", 9, "bold"),
                    anchor="w"
                )
                status_label.pack(fill="x", pady=(5, 0))

                self.algo_queue_card_widgets[key][task_id] = {
                    "status_label": status_label,
                    "last_status": None,
                    "last_color": None,
                }

            panel["queue_canvas"].after_idle(
                lambda c=panel["queue_canvas"]: (
                    c.configure(scrollregion=c.bbox("all")),
                    c.xview_moveto(0)
                )
            )

        self.update_algorithm_queue_statuses(key, result)

    def update_algorithm_queue_statuses(self, key, result):
        if key not in self.algo_panels or key not in self.algo_queue_card_widgets:
            return

        current_block = self.find_current_block(result.gantt_chart, self.current_time)
        running_id = None

        if current_block:
            running_id = str(self.safe_attr(current_block, "task_id", ""))

        cache = self.algo_queue_card_widgets[key]

        for task in result.tasks:
            task_id = str(self.safe_attr(task, "task_id", ""))
            widget_info = cache.get(task_id)

            if not widget_info:
                continue

            completion = self.to_int(
                self.safe_attr(task, "completion_time", 999999),
                999999
            )

            if running_id == task_id:
                status = "RUNNING"
                status_color = "#16A34A"
            elif completion <= self.current_time:
                status = "COMPLETED"
                status_color = "#2563EB"
            else:
                status = "WAITING"
                status_color = "#F97316"

            if (
                widget_info.get("last_status") != status
                or widget_info.get("last_color") != status_color
            ):
                widget_info["status_label"].config(text=status, fg=status_color)
                widget_info["last_status"] = status
                widget_info["last_color"] = status_color
    def update_task_card_status(self, algorithm_key, result):
        self.update_algorithm_queue_statuses(algorithm_key, result)

    def update_algorithm_task_cards(self):
        for key in self.selected_algorithm_keys():
            if key in self.results:
                self.update_algorithm_queue_statuses(key, self.results[key])

    def refresh_algorithm_panels(self):
        self.render_algorithm_panels()
        for key in self.selected_algorithm_keys():
            if key in self.results:
                self.render_algorithm_queue(key, self.results[key], force_rebuild=True)

    def small_stat(self, parent, title, value):
        box = tk.Frame(parent, bg=WHITE_COLOR)
        box.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(
            box,
            text=title,
            bg=WHITE_COLOR,
            fg=MUTED_TEXT,
            font=("Arial", 8, "bold")
        ).pack()

        label = tk.Label(
            box,
            text=value,
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 9, "bold")
        )

        label.pack()

        tk.Frame(
            parent,
            bg="#E2E8F0",
            width=1
        ).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        return label

    def lighten_border(self, color):
        return {
            PRIMARY_COLOR: "#BFDBFE",
            GREEN_DARK: "#BBF7D0",
            ORANGE_DARK: "#FED7AA",
            PURPLE: "#DDD6FE",
        }.get(color, BORDER_COLOR)

    # =========================================================
    # QUEUE AND GANTT
    # =========================================================
    def prepare_display_task_maps(self):
        self.task_color_map.clear()
        self.original_arrival_map.clear()

        sorted_tasks = self.sort_tasks_by_task_id(self.tasks)

        for index, task in enumerate(sorted_tasks):
            task_id = str(self.safe_attr(task, "task_id", f"T{index + 1:03d}"))
            self.task_color_map[task_id] = self.task_colors[index % len(self.task_colors)]
            self.original_arrival_map[task_id] = self.to_int(
                self.safe_attr(task, "arrival_time", 0),
                0
            )

    def render_queue(self):
        for widget in self.queue_frame.winfo_children():
            widget.destroy()

        self.queue_card_widgets.clear()

        display_tasks = self.normalized_tasks if self.normalized_tasks else self.prepare_simulation_tasks()[0]

        if not display_tasks:
            tk.Label(
                self.queue_frame,
                text="Chưa có dữ liệu tác vụ. Hãy import Excel ở mục Danh sách tác vụ trước.",
                bg=WHITE_COLOR,
                fg=MUTED_TEXT,
                font=("Arial", 11, "bold"),
            ).pack(padx=16, pady=20)
            return

        sorted_tasks = self.sort_tasks_by_task_id(display_tasks)

        for index, task in enumerate(sorted_tasks):
            task_id = str(self.safe_attr(task, "task_id", f"T{index + 1:03d}"))
            color = self.task_color_map.get(task_id, self.task_colors[index % len(self.task_colors)])
            task_type = str(self.safe_attr(task, "task_type", "In tài liệu"))

            card = tk.Frame(
                self.queue_frame,
                bg=WHITE_COLOR,
                highlightbackground=BORDER_COLOR,
                highlightthickness=1,
                width=240,
                height=120
            )

            card.pack(side=tk.LEFT, padx=(0, 10), pady=(10, 2))
            card.pack_propagate(False)

            card.grid_columnconfigure(0, weight=0, minsize=80)
            card.grid_columnconfigure(1, weight=1)

            icon_label = tk.Label(
                card,
                text=self.icon_for_task(task_type),
                bg=WHITE_COLOR,
                font=("Arial", 40)
            )

            icon_label.grid(
                row=0,
                column=0,
                rowspan=3,
                sticky="nsew",
                padx=(10, 5),
                pady=10
            )

            text_box = tk.Frame(card, bg=WHITE_COLOR)

            text_box.grid(
                row=0,
                column=1,
                sticky="nsew",
                padx=(0, 10),
                pady=12
            )

            tk.Label(
                text_box,
                text=task_id,
                bg=WHITE_COLOR,
                fg=color,
                font=("Arial", 13, "bold"),
                anchor="w"
            ).pack(fill="x")

            tk.Label(
                text_box,
                text=task_type.title(),
                bg=WHITE_COLOR,
                fg=TEXT_COLOR,
                font=("Arial", 12, "bold"),
                anchor="w"
            ).pack(fill="x", pady=(6, 0))

            status = getattr(task, "status", "WAITING")

            if status == "RUNNING":
                status_color = "#16A34A"
            elif status == "COMPLETED" or status == "Hoàn thành":
                status_color = "#2563EB"
            else:
                status_color = "#F97316"

            status_label = tk.Label(
                text_box,
                text=status,
                bg=WHITE_COLOR,
                fg=status_color,
                font=("Arial", 8, "bold"),
                anchor="w"
            )
            status_label.pack(fill="x", pady=(8, 0))

            self.queue_card_widgets[task_id] = {
                "status_label": status_label,
                "last_status": status,
                "last_color": status_color,
            }

        if hasattr(self, "queue_canvas"):
            self.queue_canvas.after_idle(
                lambda c=self.queue_canvas: c.xview_moveto(0)
            )

    def update_main_queue_statuses(self):
        """Chỉ cập nhật label trạng thái của queue tổng, không render lại toàn bộ card."""
        if not self.queue_card_widgets:
            return

        display_tasks = self.normalized_tasks if self.normalized_tasks else self.tasks

        for task in display_tasks:
            task_id = str(self.safe_attr(task, "task_id", ""))
            widget_info = self.queue_card_widgets.get(task_id)

            if not widget_info:
                continue

            status = getattr(task, "status", "WAITING")

            if status == "RUNNING":
                status_color = "#16A34A"
            elif status == "COMPLETED" or status == "Hoàn thành":
                status_color = "#2563EB"
            else:
                status_color = "#F97316"

            if (
                widget_info.get("last_status") != status
                or widget_info.get("last_color") != status_color
            ):
                widget_info["status_label"].config(text=status, fg=status_color)
                widget_info["last_status"] = status
                widget_info["last_color"] = status_color
    def draw_gantt(self):
        if not hasattr(self, "gantt_canvas"):
            return

        self.gantt_canvas.delete("all")

        keys = [
            key for key in self.selected_algorithm_keys()
            if key in self.results
        ]

        if not keys:
            self.gantt_canvas.create_text(
                24,
                45,
                anchor="w",
                text="Chưa chạy mô phỏng. Nhấn ‘Chạy’ để tạo biểu đồ Gantt.",
                fill=MUTED_TEXT,
                font=("Arial", 11, "bold"),
            )

            self.gantt_canvas.configure(scrollregion=self.gantt_canvas.bbox("all"))
            return

        left = 96
        top = 34
        row_height = 34
        bar_height = 20
        total = max(self.max_time, 1)

        canvas_visible_width = max(self.gantt_canvas.winfo_width(), 1100)
        gantt_width = max(canvas_visible_width - left - 50, total * PX_PER_TIME)
        canvas_height = top + len(keys) * row_height + 34

        self.gantt_canvas.configure(height=max(155, canvas_height))

        scale = gantt_width / total
        tick_step = self.choose_tick_step(total)

        for time_value in range(0, total + 1, tick_step):
            x = left + time_value * scale

            self.gantt_canvas.create_line(
                x,
                top - 14,
                x,
                canvas_height - 22,
                fill="#F1F5F9"
            )

            self.gantt_canvas.create_text(
                x,
                top - 21,
                text=str(time_value),
                fill=TEXT_COLOR,
                font=("Arial", 8)
            )

        if total % tick_step != 0:
            x = left + total * scale

            self.gantt_canvas.create_text(
                x,
                top - 21,
                text=str(total),
                fill=TEXT_COLOR,
                font=("Arial", 8)
            )

        current_x = left + min(self.current_time, total) * scale

        self.gantt_canvas.create_line(
            current_x,
            top - 8,
            current_x,
            canvas_height - 22,
            fill=ACCENT_COLOR,
            dash=(4, 3),
            width=2
        )

        self.gantt_canvas.create_text(
            current_x + 4,
            top - 7,
            anchor="w",
            text=f"t={min(self.current_time, total)}",
            fill=ACCENT_COLOR,
            font=("Arial", 8, "bold")
        )

        for row_index, key in enumerate(keys):
            result = self.results[key]
            info = self.get_algorithm_infos()[key]
            y = top + row_index * row_height
            color = info["color"]

            self.gantt_canvas.create_rectangle(
                8,
                y - 3,
                left - 12,
                y + bar_height + 3,
                fill=color,
                outline=""
            )

            self.gantt_canvas.create_text(
                (left - 4) / 2,
                y + bar_height / 2,
                text=info["short"],
                fill=WHITE_COLOR,
                font=("Arial", 9, "bold")
            )

            for block in result.gantt_chart:
                task_id = str(self.safe_attr(block, "task_id", ""))
                start = self.to_int(self.safe_attr(block, "start_time", 0), 0)
                end = self.to_int(self.safe_attr(block, "end_time", 0), 0)

                if end <= start:
                    continue

                x1 = left + start * scale
                x2 = left + end * scale

                block_color = "#CBD5E1" if task_id == "IDLE" else self.task_color_map.get(task_id, color)

                self.gantt_canvas.create_rectangle(
                    x1,
                    y,
                    x2,
                    y + bar_height,
                    fill="#F8FAFC",
                    outline="#CBD5E1"
                )

                visible_end = min(end, self.current_time)

                if visible_end > start:
                    vx2 = left + visible_end * scale

                    self.gantt_canvas.create_rectangle(
                        x1,
                        y,
                        vx2,
                        y + bar_height,
                        fill=block_color,
                        outline=WHITE_COLOR,
                        width=1
                    )

                    if vx2 - x1 >= 28:
                        label = task_id if task_id != "IDLE" else "IDLE"

                        self.gantt_canvas.create_text(
                            (x1 + vx2) / 2,
                            y + bar_height / 2,
                            text=label,
                            fill=WHITE_COLOR if task_id != "IDLE" else TEXT_COLOR,
                            font=("Arial", 8, "bold")
                        )

                if self.current_time >= self.max_time and x2 - x1 >= 28:
                    label = task_id if task_id != "IDLE" else "IDLE"

                    self.gantt_canvas.create_text(
                        (x1 + x2) / 2,
                        y + bar_height / 2,
                        text=label,
                        fill=WHITE_COLOR if task_id != "IDLE" else TEXT_COLOR,
                        font=("Arial", 8, "bold")
                    )

        self.gantt_canvas.configure(
            scrollregion=(0, 0, left + gantt_width + 50, canvas_height)
        )

    def choose_tick_step(self, total):
        if total <= 24:
            return 2
        if total <= 60:
            return 4
        if total <= 120:
            return 8
        if total <= 240:
            return 20

        return max(50, total // 8)

    def normalize_algorithm_name(self, key):
        names = {
            "FCFS": "FCFS",
            "SJF": "SJF",
            "PRIORITY": "Priority",
            "ROUND ROBIN": "Round Robin",
        }
        return names.get(str(key).upper(), str(key))

    def stamp_result_algorithm(self, result, key):
        if result is None:
            return result
        display_name = self.normalize_algorithm_name(key)
        try:
            setattr(result, "algorithm_name", display_name)
            setattr(result, "algorithm_key", key)
        except Exception:
            pass
        return result

    # =========================================================
    # SIMULATION LOGIC
    # =========================================================
    def get_preferred_result_key(self):
        if not self.results:
            return None
        selected_keys = [key for key in self.selected_algorithm_keys() if key in self.results]
        if selected_keys:
            return selected_keys[-1]
        if "ROUND ROBIN" in self.results:
            return "ROUND ROBIN"
        return next(reversed(self.results))

    def build_progress_payload(self, is_finished=False):
        preferred_key = self.get_preferred_result_key()
        preferred_result = self.results.get(preferred_key) if preferred_key else None

        return {
            "tasks": self.tasks,
            "results": list(self.results.values()),
            "result_map": self.results,
            "preferred_result": preferred_result,
            "task_results": getattr(preferred_result, "tasks", []) if preferred_result else [],
            "gantt_blocks": getattr(preferred_result, "gantt_chart", []) if preferred_result else [],
            "algorithm": preferred_key or "Chưa chạy",
            "algorithm_name": self.safe_attr(preferred_result, "algorithm_name", preferred_key or "Chưa chạy") if preferred_result else "Chưa chạy",
            "current_time": self.current_time,
            "max_time": self.max_time,
            "timeline_points": list(self.timeline_points),
            "timeline_index": self.timeline_index,
            "is_running": self.is_running,
            "is_finished": bool(is_finished),
            "selected_keys": self.selected_algorithm_keys() if self.results else [],
        }

    def emit_simulation_progress(self, is_finished=False):
        if not self.on_simulation_progress or not self.results:
            return None

        payload = self.build_progress_payload(is_finished=is_finished)
        try:
            self.on_simulation_progress(payload)
        except Exception as error:
            print("Không gửi được dữ liệu realtime sang ComparisonFrame:", error)

        return payload

    def run_simulation(self):
        if not self.tasks:
            messagebox.showwarning(
                "Chưa có dữ liệu",
                "Hãy import file Excel trước khi chạy mô phỏng."
            )
            return

        quantum = self.get_quantum(show_error=True)

        if quantum is None:
            return

        self.stop_after_job()

        self.current_time = 0
        self.max_time = 0
        self.timeline_points = [0]
        self.timeline_index = 0
        self.results.clear()
        self.is_finished_rendered = False

        self.normalized_tasks, self.arrival_note = self.prepare_simulation_tasks()

        for task in self.normalized_tasks:
            task.status = "WAITING"

        self.task_lookup = {
            str(self.safe_attr(task, "task_id", "")): task
            for task in self.normalized_tasks
        }

        self.note_var.set(self.arrival_note)

        self.render_queue()
        self.render_algorithm_panels()

        infos = self.get_algorithm_infos()

        for key in self.selected_algorithm_keys():
            try:
                result = infos[key]["runner"]()
                self.results[key] = self.stamp_result_algorithm(result, key)
            except Exception as exc:
                messagebox.showerror(
                    "Lỗi mô phỏng",
                    f"Không chạy được thuật toán {key}:\n{exc}"
                )

                self.results.clear()
                self.draw_gantt()
                return

        self.max_time = max([
            self.to_int(self.safe_attr(result.gantt_chart[-1], "end_time", 0), 0)
            for result in self.results.values()
            if result.gantt_chart
        ] or [0])

        if self.max_time <= 0:
            messagebox.showwarning(
                "Không có dữ liệu",
                "Danh sách tác vụ chưa có thời gian xử lý hợp lệ."
            )
            return

        self.timeline_points = self.build_timeline_points()
        self.timeline_index = 0
        self.current_time = self.timeline_points[0]

        self.is_running = True

        self.status_label.config(
            text="● Đang mô phỏng...",
            fg="#16A34A"
        )

        self.run_button.config(state=tk.DISABLED)
        self.update_button_image(self.pause_button, "Pause", "Ⅱ  Tạm dừng", "#F97316", WHITE_COLOR)

        self.refresh_realtime_ui()

        self.after_id = self.after(
            EVENT_STEP_MS,
            self.simulation_tick
        )

    def simulation_tick(self):
        if not self.is_running:
            return

        if self.timeline_index >= len(self.timeline_points) - 1:
            self.finish_simulation()
            return

        self.timeline_index += 1
        self.current_time = self.timeline_points[self.timeline_index]

        # Cập nhật nhẹ mỗi tick; chỉ redraw các phần nặng theo nhịp thưa hơn.
        heavy_refresh = (
            self.timeline_index % HEAVY_REFRESH_EVERY == 0
            or self.timeline_index >= len(self.timeline_points) - 1
        )
        self.refresh_realtime_ui(heavy=heavy_refresh)

        if self.timeline_index >= len(self.timeline_points) - 1:
            self.finish_simulation()
        else:
            self.after_id = self.after(
                EVENT_STEP_MS,
                self.simulation_tick
            )

    def pause_or_resume(self):
        if not self.results:
            return

        if self.is_running:
            self.status_label.config(
                text="● Đã tạm dừng",
                fg="#F97316"
            )

            self.is_running = False
            self.stop_after_job()
            self.update_button_image(self.pause_button, "Continue", "▶  Tiếp tục", "#16A34A", WHITE_COLOR)
            self.run_button.config(state=tk.DISABLED)

        else:
            if self.timeline_index >= len(self.timeline_points) - 1:
                return

            self.status_label.config(
                text="● Đang mô phỏng...",
                fg="#16A34A"
            )

            self.is_running = True
            self.update_button_image(self.pause_button, "Pause", "Ⅱ  Tạm dừng", "#F97316", WHITE_COLOR)
            self.run_button.config(state=tk.DISABLED)

            self.after_id = self.after(
                EVENT_STEP_MS,
                self.simulation_tick
            )

    def finish_simulation(self):
        self.is_running = False
        self.stop_after_job()

        self.timeline_index = len(self.timeline_points) - 1
        self.current_time = self.max_time

        if not self.is_finished_rendered:
            self.refresh_realtime_ui()
            self.is_finished_rendered = True

        self.apply_result_to_source_tasks()
        self.update_task_statuses()
        if self.is_visible:
            self.update_main_queue_statuses()
            for key in self.selected_algorithm_keys():
                if key in self.results and key in self.algo_panels:
                    self.render_algorithm_queue(key, self.results[key])

        self.run_button.config(state=tk.NORMAL)
        self.update_button_image(self.pause_button, "Pause", "Ⅱ  Tạm dừng", "#F97316", WHITE_COLOR)

        self.status_label.config(
            text="● Đã hoàn thành mô phỏng",
            fg="#2563EB"
        )

        final_payload = self.emit_simulation_progress(is_finished=True)

        if self.on_simulation_finished:
            try:
                self.on_simulation_finished(self.tasks, final_payload)
            except TypeError:
                self.on_simulation_finished(self.tasks)

        if self.is_visible:
            messagebox.showinfo(
                "Hoàn tất",
                "Đã mô phỏng xong. Màn Danh sách tác vụ đã được cập nhật trạng thái."
            )

    def apply_result_to_source_tasks(self):
        if not self.results:
            return

        preferred_key = "ROUND ROBIN" if "ROUND ROBIN" in self.results else next(reversed(self.results))
        result = self.results[preferred_key]

        result_task_map = {
            str(self.safe_attr(task, "task_id", "")): task
            for task in getattr(result, "tasks", [])
        }

        for task in self.tasks:
            task_id = str(self.safe_attr(task, "task_id", ""))
            simulated = result_task_map.get(task_id)

            if simulated is None:
                continue

            setattr(task, "status", "Hoàn thành")
            setattr(task, "completion_time", self.safe_attr(simulated, "completion_time", 0))
            setattr(task, "turnaround_time", self.safe_attr(simulated, "turnaround_time", 0))
            setattr(task, "waiting_time", self.safe_attr(simulated, "waiting_time", 0))
            setattr(task, "response_time", self.safe_attr(simulated, "response_time", 0))
            setattr(task, "simulation_algorithm", preferred_key)

    def reset_simulation(self):
        self.status_label.config(
            text="● Sẵn sàng mô phỏng",
            fg="#64748B"
        )

        self.stop_after_job()

        self.is_running = False
        self.current_time = 0
        self.max_time = 0
        self.timeline_points = [0]
        self.timeline_index = 0
        self.results.clear()
        self.normalized_tasks = []
        self.task_lookup = {}
        self.arrival_note = ""
        self.is_finished_rendered = False

        self.time_var.set("Thời gian mô phỏng: 0")
        self.note_var.set("")

        self.run_button.config(state=tk.NORMAL)
        self.update_button_image(self.pause_button, "Pause", "Ⅱ  Tạm dừng", "#F97316", WHITE_COLOR)

        self.render_queue()
        self.render_algorithm_panels()
        self.draw_gantt()

    def change_filter(self):
        self.reset_simulation()

    def stop_after_job(self):
        if self.after_id is not None:
            try:
                self.after_cancel(self.after_id)
            except Exception:
                pass

            self.after_id = None

    def refresh_realtime_ui(self, force=False, heavy=True):
        """Cập nhật realtime theo hai mức.

        - Mức nhẹ: thời gian, tiến độ, Avg Waiting/Turnaround ở từng tick.
        - Mức nặng: trạng thái toàn bộ card, Gantt và payload sang Comparison
          chỉ chạy định kỳ để tránh khóa main thread của Tkinter.
        """
        self.time_var.set(
            f"Thời gian mô phỏng: {min(self.current_time, self.max_time)} / {self.max_time}"
        )

        self.update_task_statuses()

        if not self.is_visible and not force:
            # Khi trang bị ẩn chỉ gửi dữ liệu theo nhịp thưa.
            if heavy:
                self.emit_simulation_progress(is_finished=False)
            return

        # Các nhãn nhỏ vẫn đổi từng đơn vị thời gian nên mô phỏng không bị nhảy cóc.
        for key in self.selected_algorithm_keys():
            if key in self.results and key in self.algo_panels:
                self.update_algorithm_panel(key, self.results[key])

        if heavy or force:
            self.emit_simulation_progress(is_finished=False)
            self.update_main_queue_statuses()

            for key in self.selected_algorithm_keys():
                if key in self.results and key in self.algo_panels:
                    self.render_algorithm_queue(key, self.results[key])

            self.draw_gantt()

    def update_progress_bar(self, canvas, text, percent, color):
        try:
            percent = int(percent)
        except Exception:
            percent = 0

        canvas._progress_text = text
        canvas._progress_percent = max(0, min(100, percent))
        canvas._progress_color = color

        self.draw_progress_bar(canvas)


    def draw_progress_bar(self, canvas):
        width = max(canvas.winfo_width(), 1)
        height = max(canvas.winfo_height(), 24)

        text = getattr(canvas, "_progress_text", "Chưa chạy mô phỏng")
        percent = max(0, min(100, int(getattr(canvas, "_progress_percent", 0))))
        color = getattr(canvas, "_progress_color", PRIMARY_COLOR)

        canvas.delete("all")

        if width <= 2:
            return

        x1, y1 = 1, 1
        x2, y2 = width - 1, height - 1

        fill_width = x1 + int((x2 - x1) * percent / 100)

        # Nền trắng + viền đen
        canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=WHITE_COLOR,
            outline="#111827",
            width=1,
        )

        # Phần màu chạy theo %
        if percent > 0:
            canvas.create_rectangle(
                x1 + 1,
                y1 + 1,
                max(x1 + 1, fill_width),
                y2 - 1,
                fill=color,
                outline="",
            )

        # Vẽ lại viền phía trên để không bị màu che mất
        canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            outline="#111827",
            width=1,
        )

        text_x = width // 2
        text_y = height // 2
        text_font = ("Arial", 11, "bold")

        # Viền đen dày quanh chữ
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue

                canvas.create_text(
                    text_x + dx,
                    text_y + dy,
                    text=text,
                    fill="#000000",
                    font=text_font,
                )

        # Chữ chính màu trắng
        canvas.create_text(
            text_x,
            text_y,
            text=text,
            fill="#FFFFFF",
            font=text_font,
        )
    
    def get_progress_display_block(self, gantt_chart, now):
        """
        Lấy block để hiển thị trên thanh tiến độ.
        Ưu tiên block vừa kết thúc tại đúng thời điểm now để thấy được 100%
        trước khi chuyển sang tác vụ kế tiếp.
        """
        if not gantt_chart:
            return None

        for block in reversed(gantt_chart):
            task_id = str(self.safe_attr(block, "task_id", ""))
            end = self.to_int(self.safe_attr(block, "end_time", 0), 0)

            if task_id != "IDLE" and now == end:
                return block

        return self.find_current_block(gantt_chart, now)


    def get_current_task_progress(self, result, block, now, key):
        if block is None:
            return "Đang chờ tác vụ", 0

        task_id = str(self.safe_attr(block, "task_id", ""))

        if task_id == "IDLE":
            return "IDLE - Chưa có tác vụ đến", 0

        task = next(
            (
                item for item in getattr(result, "tasks", []) or []
                if str(self.safe_attr(item, "task_id", "")) == task_id
            ),
            self.task_lookup.get(task_id)
        )

        task_type = str(self.safe_attr(task, "task_type", "Tác vụ")) if task else "Tác vụ"
        burst_time = max(1, self.to_int(self.safe_attr(task, "burst_time", 1), 1))

        executed_time = self.calculate_task_executed_service(result, task_id, now)
        task_percent = int((executed_time / burst_time) * 100)
        task_percent = max(0, min(100, task_percent))

        if key == "ROUND ROBIN":
            text = f"{task_id} - {task_type} (lượt RR)"
        else:
            text = f"{task_id} - {task_type}"

        return text, task_percent

    def update_algorithm_panel(self, key, result):
        panel = self.algo_panels[key]
        color = panel["color"]
        bg = panel["bg"]

        end_time = self.to_int(
            self.safe_attr(result.gantt_chart[-1], "end_time", 0),
            0
        ) if result.gantt_chart else 0

        now = min(self.current_time, end_time)
        current_block = self.find_current_block(result.gantt_chart, now)
        completed_tasks = self.get_completed_tasks_until(result, now)
        total_tasks = len(getattr(result, "tasks", []) or [])

        # Tiến độ tổng của thuật toán, chỉ để hiện ở dòng chữ bên dưới.
        total_burst = sum(
            max(0, self.to_int(self.safe_attr(task, "burst_time", 0), 0))
            for task in (getattr(result, "tasks", []) or [])
        )
        executed_time = self.calculate_executed_service(result, now)
        overall_percent = int((executed_time / total_burst) * 100) if total_burst else 0
        overall_percent = max(0, min(100, overall_percent))

        completed_count = len(completed_tasks)
        remaining_count = max(total_tasks - completed_count, 0)

        # Lấy block để hiển thị trên thanh.
        # Nếu đúng thời điểm kết thúc 1 tác vụ, vẫn cho tác vụ đó hiện 100%
        # rồi tick sau mới chuyển sang tác vụ tiếp theo.
        display_block = current_block

        if result.gantt_chart:
            for block in reversed(result.gantt_chart):
                task_id_check = str(self.safe_attr(block, "task_id", ""))
                block_end = self.to_int(self.safe_attr(block, "end_time", 0), 0)

                if task_id_check != "IDLE" and now == block_end:
                    display_block = block
                    break

        if display_block is None:
            if now >= end_time and end_time > 0:
                current_text = "Hoàn thành tất cả tác vụ"
                task_percent = 100
            else:
                current_text = "Đang chờ tác vụ"
                task_percent = 0

            running_task_id = None

        else:
            task_id = str(self.safe_attr(display_block, "task_id", ""))

            if task_id == "IDLE":
                current_text = "IDLE - Chưa có tác vụ đến"
                task_percent = 0
                running_task_id = None

            else:
                task = self.task_lookup.get(task_id)

                if task is None:
                    task = next(
                        (
                            item for item in getattr(result, "tasks", []) or []
                            if str(self.safe_attr(item, "task_id", "")) == task_id
                        ),
                        None
                    )

                task_type = str(self.safe_attr(task, "task_type", "Tác vụ")) if task else "Tác vụ"
                running_task_id = task_id

                if key == "ROUND ROBIN":
                    current_text = f"{task_id} - {task_type} (lượt RR)"
                else:
                    current_text = f"{task_id} - {task_type}"

                block_start = self.to_int(self.safe_attr(display_block, "start_time", 0), 0)
                block_end = self.to_int(self.safe_attr(display_block, "end_time", block_start), block_start)
                block_duration = max(1, block_end - block_start)

                if now >= block_end:
                    task_percent = 100
                else:
                    task_percent = int(((now - block_start) / block_duration) * 100)

                task_percent = max(0, min(100, task_percent))

        waiting = self.count_waiting_tasks(result, now, running_task_id)

        avg_wait, avg_turn = self.calculate_live_metrics(result, now)

        # Nếu bạn đã đổi thanh ngang sang Canvas ở bước trước.
        if "progress_canvas" in panel:
            self.update_progress_bar(
                panel["progress_canvas"],
                current_text,
                task_percent,
                color
            )
        else:
            # Fallback nếu máy bạn vẫn còn dùng task_label cũ.
            panel["task_label"].config(text=current_text, bg=bg, fg=color)

        panel["elapsed_label"].config(text=str(completed_count))
        panel["remain_label"].config(text=str(remaining_count))
        panel["waiting_label"].config(text=str(waiting))

        panel["progress_label"].config(
            text=f"Tiến độ tác vụ: {task_percent}% | Tổng: {overall_percent}%",
            fg=color
        )

        panel["avg_wait_label"].config(
            text=f"Avg Waiting Time\n{self.format_number(avg_wait)}"
        )

        panel["avg_turn_label"].config(
            text=f"Avg Turnaround Time\n{self.format_number(avg_turn)}"
        )

        self.update_idletasks()

    def get_completed_tasks_until(self, result, now):
        completed = []

        for task in getattr(result, "tasks", []) or []:
            completion = self.to_int(
                self.safe_attr(task, "completion_time", 999999),
                999999
            )

            if completion <= now:
                completed.append(task)

        return completed

    def calculate_task_executed_service(self, result, task_id, now):
        """Tổng thời gian CPU mà một tác vụ đã thực sự chạy đến thời điểm now."""
        executed = 0

        for block in getattr(result, "gantt_chart", []) or []:
            block_task_id = str(self.safe_attr(block, "task_id", ""))
            if block_task_id != str(task_id):
                continue

            start = self.to_int(self.safe_attr(block, "start_time", 0), 0)
            end = self.to_int(self.safe_attr(block, "end_time", 0), 0)

            if now <= start:
                continue

            executed += max(0, min(now, end) - start)

        return executed

    def calculate_executed_service(self, result, now):
        """Tổng lượng CPU đã xử lý của toàn thuật toán đến thời điểm now."""
        executed = 0

        for block in getattr(result, "gantt_chart", []) or []:
            task_id = str(self.safe_attr(block, "task_id", ""))
            if task_id == "IDLE":
                continue

            start = self.to_int(self.safe_attr(block, "start_time", 0), 0)
            end = self.to_int(self.safe_attr(block, "end_time", 0), 0)

            if now <= start:
                continue

            executed += max(0, min(now, end) - start)

        return executed

    def calculate_live_metrics(self, result, now):
        """Tính chỉ số realtime tại đúng thời điểm now.

        Với tác vụ chưa hoàn thành, turnaround tăng theo thời gian đã ở trong hệ thống;
        waiting bằng turnaround trừ lượng CPU tác vụ đã được cấp. Cách này đặc biệt
        quan trọng với Round Robin vì tác vụ có thể chạy nhiều lượt quantum.
        """
        arrived_tasks = []

        for task in getattr(result, "tasks", []) or []:
            arrival = self.to_int(self.safe_attr(task, "arrival_time", 0), 0)
            if arrival <= now:
                arrived_tasks.append(task)

        if not arrived_tasks:
            return 0, 0

        waiting_values = []
        turnaround_values = []

        for task in arrived_tasks:
            task_id = str(self.safe_attr(task, "task_id", ""))
            arrival = self.to_int(self.safe_attr(task, "arrival_time", 0), 0)
            completion = self.to_int(
                self.safe_attr(task, "completion_time", now),
                now
            )
            observed_end = min(now, completion)
            turnaround = max(0, observed_end - arrival)
            executed = self.calculate_task_executed_service(result, task_id, now)
            waiting = max(0, turnaround - executed)

            turnaround_values.append(turnaround)
            waiting_values.append(waiting)

        return (
            sum(waiting_values) / len(waiting_values),
            sum(turnaround_values) / len(turnaround_values),
        )

    def find_current_block(self, gantt_chart, now):
        for block in gantt_chart:
            start = self.to_int(self.safe_attr(block, "start_time", 0), 0)
            end = self.to_int(self.safe_attr(block, "end_time", 0), 0)

            if start <= now < end:
                return block

        return None

    def count_waiting_tasks(self, result, now, running_task_id):
        count = 0

        for task in result.tasks:
            task_id = str(self.safe_attr(task, "task_id", ""))

            if task_id == running_task_id:
                continue

            arrival = self.to_int(self.safe_attr(task, "arrival_time", 0), 0)
            completion = self.to_int(self.safe_attr(task, "completion_time", 0), 0)

            if arrival <= now < completion:
                count += 1

        return count

    def build_timeline_points(self):
        """Tạo timeline theo từng đơn vị thời gian.

        Bản cũ chỉ lấy đầu/cuối Gantt block nên Round Robin chỉ đổi sau mỗi quantum.
        Bản mới cập nhật t = 0, 1, 2, ... để tiến độ và chỉ số thay đổi liên tục.
        """
        max_time = max(0, self.to_int(self.max_time, 0))
        return list(range(0, max_time + 1))

    def update_task_statuses(self):
        """Giữ toàn bộ hàng đợi ở WAITING trong lúc mô phỏng.

        Khi mô phỏng kết thúc, cập nhật toàn bộ sang COMPLETED cùng một lượt.
        Không còn nhảy RUNNING/COMPLETED từng tác vụ để tránh hiểu nhầm trạng thái nguồn.
        """
        if not self.normalized_tasks:
            return

        final_done = self.max_time > 0 and self.current_time >= self.max_time

        for task in self.normalized_tasks:
            task.status = "COMPLETED" if final_done else "WAITING"

    # =========================================================
    # TASK NORMALIZATION HELPERS
    # =========================================================
    def prepare_simulation_tasks(self):
        """
        Chuẩn hoá dữ liệu trước khi đưa vào 4 thuật toán.

        Với bài toán quán photocopy, tại thời điểm bấm "Chạy" thì các tác vụ đang nằm
        trong danh sách được xem là đã có trong hàng đợi. Vì vậy ta đưa arrival_time
        của tất cả tác vụ về 0 để:
        - FCFS chọn theo thứ tự hàng đợi.
        - SJF có cơ hội chọn tác vụ ngắn nhất.
        - Priority có cơ hội chọn tác vụ ưu tiên cao nhất.
        - Round Robin có nhiều tác vụ trong ready_queue để chia quantum.

        Nếu giữ arrival_time rải quá xa nhau thì tại mỗi thời điểm thường chỉ có 1 tác vụ
        sẵn sàng, khi đó FCFS/SJF/Priority/RR có thể cho ra cùng kết quả. Đó là đúng
        về lý thuyết nhưng không phù hợp để demo so sánh thuật toán trên giao diện này.
        """
        tasks_copy = copy.deepcopy(self.tasks)

        if not tasks_copy:
            return [], ""

        for index, task in enumerate(tasks_copy):
            self.ensure_task_defaults(task, index)

        # Giữ thứ tự hiển thị ổn định T001, T002... cho hàng đợi ban đầu.
        tasks_copy = self.sort_tasks_by_task_id(tasks_copy)

        for task in tasks_copy:
            original_arrival = self.to_int(
                self.safe_attr(task, "arrival_time", 0),
                0
            )

            # Lưu lại arrival_time gốc để khi cần vẫn có thể xem/debug.
            setattr(task, "original_arrival_time", original_arrival)

            # Điểm quan trọng: trong mô phỏng hàng đợi photocopy, tất cả task đã chờ sẵn.
            setattr(task, "arrival_time", 0)

            setattr(
                task,
                "burst_time",
                max(1, self.to_int(self.safe_attr(task, "burst_time", 1), 1))
            )

            setattr(
                task,
                "priority",
                self.to_int(self.safe_attr(task, "priority", 1), 1)
            )

            setattr(task, "status", "WAITING")

        note = (
            "Chế độ hàng đợi: tất cả tác vụ được xem là đã có trong hàng đợi tại t=0 "
            "để các thuật toán FCFS/SJF/Priority/Round Robin thể hiện sự khác nhau."
        )

        return tasks_copy, note

    def ensure_task_defaults(self, task, index):
        if not hasattr(task, "arrival_time") or getattr(task, "arrival_time") is None:
            setattr(task, "arrival_time", 0)

        if not hasattr(task, "burst_time") or getattr(task, "burst_time") is None:
            setattr(task, "burst_time", 1)

        if not hasattr(task, "priority") or getattr(task, "priority") is None:
            setattr(task, "priority", 1)

        if not hasattr(task, "task_id") or getattr(task, "task_id") is None:
            setattr(task, "task_id", f"T{index + 1:03d}")

        if not hasattr(task, "task_type") or getattr(task, "task_type") is None:
            setattr(task, "task_type", "In tài liệu")

    # =========================================================
    # GENERAL HELPERS
    # =========================================================
    def get_quantum(self, show_error=True):
        try:
            q = int(self.quantum_var.get())

            if q <= 0:
                raise ValueError

            return q

        except Exception:
            if show_error:
                messagebox.showwarning(
                    "Quantum không hợp lệ",
                    "Quantum Round Robin phải là số nguyên lớn hơn 0."
                )

            return None if show_error else (DEFAULT_TIME_QUANTUM or 4)

    def icon_for_task(self, task_type):
        text = str(task_type).lower()

        if "sao" in text or "copy" in text or "photo" in text:
            return "📄"

        if "scan" in text:
            return "📠"

        return "🖨"

    def safe_attr(self, obj, attr, default=None):
        if obj is None:
            return default

        return getattr(obj, attr, default)

    def to_int(self, value, default=0):
        try:
            return int(float(value))
        except Exception:
            return default

    def format_number(self, value):
        try:
            return f"{float(value):.2f}"
        except Exception:
            return str(value)

