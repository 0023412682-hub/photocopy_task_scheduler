import os
import math
import tkinter as tk
from tkinter import ttk, messagebox

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False

from ui.icon_utils import load_icon, resolve_icon_path as shared_resolve_icon_path, normalize_icon_name as shared_normalize_icon_name

from models import Task
from utils.constants import TASK_TYPES

PRIMARY_COLOR = "#005BAC"
PRIMARY_DARK = "#004A99"
SECONDARY_COLOR = "#EAF4FF"
ACCENT_COLOR = "#D71920"
BACKGROUND_COLOR = "#F4F7FB"
WHITE_COLOR = "#FFFFFF"
TEXT_COLOR = "#1F2937"
PLACEHOLDER_COLOR = "#9CA3AF"
BORDER_COLOR = "#D9E2EC"
GREEN = "#16A34A"
ORANGE = "#F59E0B"
GRAY = "#6B7280"
LIGHT_GRAY = "#F1F5F9"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ICON_DIR = os.path.join(BASE_DIR, "utils", "icons")

# Cấu hình hằng số quy đổi thời gian cho Phương thức
METHOD_TIME_MAP = {
    "Online": 7,
    "Offline": 5
}


class PlaceholderEntry(tk.Entry):
    def __init__(self, parent, placeholder="", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.placeholder = placeholder
        self.placeholder_active = False
        self.bind("<FocusIn>", self.clear_placeholder)
        self.bind("<FocusOut>", self.show_placeholder)
        self.show_placeholder()

    def show_placeholder(self, event=None):
        if self.get().strip() == "":
            self.placeholder_active = True
            self.delete(0, tk.END)
            self.insert(0, self.placeholder)
            self.config(fg=PLACEHOLDER_COLOR)

    def clear_placeholder(self, event=None):
        if self.placeholder_active:
            self.placeholder_active = False
            self.delete(0, tk.END)
            self.config(fg=TEXT_COLOR)

    def get_real_value(self):
        if self.placeholder_active:
            return ""
        return self.get().strip()

    def set_real_value(self, value):
        self.placeholder_active = False
        self.config(fg=TEXT_COLOR)
        self.delete(0, tk.END)
        self.insert(0, str(value))

    def reset_placeholder(self):
        self.placeholder_active = False
        self.delete(0, tk.END)
        self.show_placeholder()


class TaskFrame(tk.Frame):
    def __init__(self, parent, tasks, on_tasks_changed=None):
        super().__init__(parent, bg=BACKGROUND_COLOR)

        self.tasks = tasks
        self.on_tasks_changed = on_tasks_changed
        self.selected_task_id = None
        self.checked_task_ids = set()
        self.images = {}

        self.task_type_var = tk.StringVar(value=TASK_TYPES[0] if TASK_TYPES else "")
        self.print_option_var = tk.StringVar(value="Trắng đen")
        
        # Thêm biến quản lý Phương thức (Online/Offline)
        self.method_var = tk.StringVar(value="Offline")
        self.cover_pages_entry = None
        self.color_pages_entry = None
        self.bw_pages_entry = None
        self.priority_entry = None

        self.filter_type_var = tk.StringVar(value="Tất cả loại")
        self.filter_status_var = tk.StringVar(value="Tất cả trạng thái")

        self.configure_styles()
        self.create_widgets()
        self.refresh_task_table()

    def configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Treeview",
            font=("Arial", 10),
            rowheight=34,
            background=WHITE_COLOR,
            fieldbackground=WHITE_COLOR,
            foreground=TEXT_COLOR,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            font=("Arial", 10, "bold"),
            background="#EAF4FF",
            foreground=PRIMARY_COLOR,
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", "#DBEAFE")],
            foreground=[("selected", TEXT_COLOR)],
        )

    def normalize_icon_name(self, value):
        return shared_normalize_icon_name(value)

    def resolve_icon_path(self, filename):
        return shared_resolve_icon_path(ICON_DIR, filename)

    def load_image(self, filename, size=(40, 40)):
        return load_icon(self, ICON_DIR, filename, size=size, crop_transparency=True, keep_aspect=True)

    def load_button_image(self, filename, size=(132, 33)):
        # Dùng cho ảnh button hoàn chỉnh tỉ lệ 1000x250 = 4:1.
        # Không crop và vẫn giữ tỉ lệ để ảnh không bị kéo ngang/dọc.
        return load_icon(self, ICON_DIR, filename, size=size, crop_transparency=False, keep_aspect=True)

    def load_toolbar_icon(self, filename, size=(32, 32)):
        # Dùng cho icon rời ở thanh công cụ bảng, không ép thành button dài.
        return load_icon(self, ICON_DIR, filename, size=size, crop_transparency=True, keep_aspect=True)

    def create_widgets(self):
        self.create_summary_cards()
        self.create_body()
        self.create_task_table_section()

    def make_section(self, parent, title, icon_file=None, height=None, show_border=True, show_divider=True):
        if show_border:
            section = tk.Frame(parent, bg=WHITE_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
        else:
            section = tk.Frame(parent, bg=WHITE_COLOR, bd=0, highlightthickness=0)

        if height:
            section.configure(height=height)
            section.grid_propagate(False)
            section.pack_propagate(False)

        header = tk.Frame(section, bg=WHITE_COLOR, height=44)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        icon_img = self.load_image(icon_file, (20, 20))
        if icon_img:
            tk.Label(header, image=icon_img, bg=WHITE_COLOR).pack(side=tk.LEFT, padx=(18, 10))
        else:
            tk.Label(header, text="▣", bg=WHITE_COLOR, fg=PRIMARY_COLOR, font=("Arial", 13, "bold")).pack(side=tk.LEFT, padx=(18, 10))

        tk.Label(header, text=title, bg=WHITE_COLOR, fg=PRIMARY_COLOR, font=("Arial", 14, "bold")).pack(side=tk.LEFT)
        if show_divider:
            tk.Frame(section, bg=BORDER_COLOR, height=1).pack(fill=tk.X)
        return section

    def make_label_button(self, parent, text, bg, fg, command):
        btn = tk.Label(parent, text=text, bg=bg, fg=fg, font=("Arial", 10, "bold"), padx=10, pady=10, cursor="hand2")
        btn.bind("<Button-1>", lambda event: command())

        def on_enter(event): btn.configure(bg=self.darken_color(bg))
        def on_leave(event): btn.configure(bg=bg)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def make_image_button(self, parent, image_name, fallback_text, command, size=(178, 42), button_size=None, fallback_bg=PRIMARY_COLOR, fallback_fg=WHITE_COLOR):
        photo = self.load_button_image(image_name, size)
        bg = parent.cget("bg") if hasattr(parent, "cget") else WHITE_COLOR

        if photo:
            btn = tk.Label(parent, image=photo, bg=bg, bd=0, borderwidth=0, highlightthickness=0, cursor="hand2")
            btn.image = photo
            btn.bind("<Button-1>", lambda event: command())
            return btn

        btn = tk.Label(parent, text=fallback_text, bg=fallback_bg, fg=fallback_fg, font=("Arial", 10, "bold"), padx=10, pady=8, bd=0, borderwidth=0, highlightthickness=0, cursor="hand2")
        btn.bind("<Button-1>", lambda event: command())
        btn.bind("<Enter>", lambda event: btn.configure(bg=self.darken_color(fallback_bg)))
        btn.bind("<Leave>", lambda event: btn.configure(bg=fallback_bg))
        return btn

    def make_toolbar_button(self, parent, image_name, fallback_text, command, icon_size=(30, 30), box_size=(116, 40)):
        box = tk.Frame(parent, bg=WHITE_COLOR, width=box_size[0], height=box_size[1], highlightbackground=BORDER_COLOR, highlightthickness=1, cursor="hand2")
        box.pack_propagate(False)
        photo = self.load_toolbar_icon(image_name, icon_size)
        child = tk.Label(box, image=photo, text="" if photo else fallback_text, bg=WHITE_COLOR, fg=PRIMARY_COLOR, font=("Arial", 18, "bold"), cursor="hand2")
        if photo:
            child.image = photo
        child.pack(expand=True)
        box.bind("<Button-1>", lambda event: command())
        child.bind("<Button-1>", lambda event: command())
        box.bind("<Enter>", lambda event: box.configure(bg="#F8FAFC"))
        box.bind("<Leave>", lambda event: box.configure(bg=WHITE_COLOR))
        child.bind("<Enter>", lambda event: box.configure(bg="#F8FAFC"))
        child.bind("<Leave>", lambda event: box.configure(bg=WHITE_COLOR))
        return box

    def darken_color(self, color):
        hover_map = {
            PRIMARY_COLOR: PRIMARY_DARK, GREEN: "#15803D", ACCENT_COLOR: "#B91C1C",
            ORANGE: "#D97706", "#0D9488": "#0F766E", "#EEF6FF": "#DBEAFE", WHITE_COLOR: "#F8FAFC",
        }
        return hover_map.get(color, color)

    def make_input(self, parent, label, row, col, placeholder):
        tk.Label(parent, text=label, bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 10, "bold")).grid(row=row, column=col, sticky="w", padx=(0, 8), pady=6)
        entry = PlaceholderEntry(
            parent, placeholder=placeholder, font=("Arial", 10), bg=WHITE_COLOR, fg=TEXT_COLOR,
            relief=tk.SOLID, bd=1, highlightthickness=1, highlightbackground=BORDER_COLOR,
            highlightcolor=PRIMARY_COLOR, insertbackground=TEXT_COLOR,
        )
        entry.grid(row=row, column=col + 1, sticky="ew", pady=6, ipady=5)
        return entry

    def make_small_count_entry(self, parent, label, placeholder="0"):
        box = tk.Frame(parent, bg=WHITE_COLOR)

        entry = PlaceholderEntry(
            box,
            placeholder=placeholder,
            font=("Arial", 11, "bold"),
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            width=6,
            justify="center",
            relief=tk.SOLID,
            bd=1,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=PRIMARY_COLOR,
            insertbackground=TEXT_COLOR,
        )
        entry.pack(side=tk.LEFT, ipady=5)

        tk.Label(
            box,
            text=label,
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=(6, 14))

        return box, entry

    def make_option_menu(self, parent, variable, values):
        menu = tk.OptionMenu(parent, variable, *(values or [""]))
        menu.configure(bg=LIGHT_GRAY, fg=TEXT_COLOR, activebackground=SECONDARY_COLOR, activeforeground=PRIMARY_COLOR, font=("Arial", 10), relief=tk.FLAT, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, cursor="hand2", anchor="w")
        menu["menu"].configure(bg=WHITE_COLOR, fg=TEXT_COLOR, activebackground=SECONDARY_COLOR, activeforeground=PRIMARY_COLOR, font=("Arial", 10))
        return menu

    def normalize_method(self, value):
        text = str(value).strip().lower()
        if text in ("offline", "off", "truc tiep", "trực tiếp", "tai quay", "tại quầy"):
            return "Offline"
        return "Online"

    def get_base_processing_time(self, task_type, print_option=""):
        """Giữ hàm cũ để không làm hỏng các đoạn code khác đang gọi."""
        task_type = str(task_type or "").strip()
        print_option = str(print_option or "").strip()

        if task_type == "In tài liệu":
            if print_option in ("In màu", "Màu"):
                return 1
            if print_option in ("In bìa", "Bìa"):
                return 2
            return 0.3

        return 1

    def calculate_processing_time(self, cover_pages=0, color_pages=0, bw_pages=0):
        """
        Công thức tính burst_time mới theo số trang:
            - In bìa:     2 giây / trang
            - In màu:     1 giây / trang
            - Trắng đen:  0.3 giây / trang

        Vì thuật toán mô phỏng/Gantt nên dùng thời gian nguyên,
        tổng thời gian được làm tròn lên bằng math.ceil().
        """
        cover = max(0, self.to_int(cover_pages, 0))
        color = max(0, self.to_int(color_pages, 0))
        bw = max(0, self.to_int(bw_pages, 0))

        total_seconds = cover * 2 + color * 1 + bw * 0.3
        return max(1, int(math.ceil(total_seconds)))

    def calculate_total_pages(self, cover_pages=0, color_pages=0, bw_pages=0):
        return (
            max(0, self.to_int(cover_pages, 0))
            + max(0, self.to_int(color_pages, 0))
            + max(0, self.to_int(bw_pages, 0))
        )

    def get_task_page_counts(self, task):
        cover = self.to_int(getattr(task, "cover_pages", 0), 0)
        color = self.to_int(getattr(task, "color_pages", 0), 0)
        bw = self.to_int(getattr(task, "bw_pages", 0), 0)

        # Tương thích dữ liệu cũ: nếu chưa có 3 thuộc tính trang,
        # dùng priority như tổng số lượng và xem là trắng đen.
        if cover == 0 and color == 0 and bw == 0:
            legacy_qty = self.to_int(getattr(task, "priority", 0), 0)
            if legacy_qty > 0:
                bw = legacy_qty

        return cover, color, bw

    def build_print_option_text(self, cover_pages, color_pages, bw_pages):
        parts = []
        if self.to_int(cover_pages, 0) > 0:
            parts.append(f"In bìa: {self.to_int(cover_pages, 0)}")
        if self.to_int(color_pages, 0) > 0:
            parts.append(f"In màu: {self.to_int(color_pages, 0)}")
        if self.to_int(bw_pages, 0) > 0:
            parts.append(f"Trắng đen: {self.to_int(bw_pages, 0)}")
        return " | ".join(parts) if parts else "Không có"

    def get_method_time(self, task):
        # Giữ hàm cũ để các chức năng xuất file không bị lỗi.
        return 0

    def create_summary_cards(self):
        stats = tk.Frame(self, bg=BACKGROUND_COLOR)
        stats.pack(fill=tk.X, padx=10, pady=(4, 10))
        for i in range(4): stats.columnconfigure(i, weight=1)

        self.total_lbl = self.stat_card(stats, "Tổng tác vụ", "0", "Comparison_Algorithm", "☷", 0)
        self.wait_lbl = self.stat_card(stats, "Đang chờ", "0", "AVG_Waiting", "◷", 1)
        self.run_lbl = self.stat_card(stats, "Đang xử lý", "0", "Processing", "⚙", 2)
        self.done_lbl = self.stat_card(stats, "Hoàn thành", "0", "Complete", "✓", 3)

    def stat_card(self, parent, title, value, icon_file, fallback_icon, col):
        card = tk.Frame(parent, bg=WHITE_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1, height=112)
        card.grid(row=0, column=col, sticky="nsew", padx=7, pady=4)
        card.grid_propagate(False)

        icon_img = self.load_image(icon_file, (74, 74))
        icon_holder = tk.Frame(card, bg=WHITE_COLOR, width=88, height=88)
        icon_holder.pack(side=tk.LEFT, padx=(24, 18), pady=12)
        icon_holder.pack_propagate(False)

        if icon_img:
            tk.Label(icon_holder, image=icon_img, bg=WHITE_COLOR).pack(expand=True)
        else:
            tk.Label(icon_holder, text=fallback_icon, bg=WHITE_COLOR, fg=PRIMARY_COLOR, font=("Arial", 38, "bold")).pack(expand=True)

        info = tk.Frame(card, bg=WHITE_COLOR)
        info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(12, 10))
        tk.Label(info, text=title.upper(), bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 11, "bold")).pack(anchor="w")
        
        value_label = tk.Label(info, text=value, bg=WHITE_COLOR, fg=PRIMARY_COLOR, font=("Arial", 32, "bold"))
        value_label.pack(anchor="w", pady=(1, 0))
        tk.Label(info, text="Tác vụ trong hệ thống", bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 10)).pack(anchor="w")
        return value_label

    def create_body(self):
        body = tk.Frame(self, bg=BACKGROUND_COLOR)
        body.pack(fill=tk.X, padx=10, pady=(0, 6))
        body.columnconfigure(0, weight=6)
        body.columnconfigure(1, weight=4)

        form = self.make_section(body, "NHẬP THÔNG TIN TÁC VỤ", icon_file="Describe", height=235, show_border=False, show_divider=False)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        filter_box = self.make_section(body, "BỘ LỌC & TÌM KIẾM", icon_file="Time", height=235, show_border=False, show_divider=False)
        filter_box.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self.build_form(form)
        self.build_filter(filter_box)

    def build_form(self, parent):
        inner = tk.Frame(parent, bg=WHITE_COLOR)
        inner.pack(fill=tk.BOTH, expand=True, padx=18, pady=(2, 6))
        for i in range(4):
            inner.columnconfigure(i, weight=1)

        self.task_id_entry = self.make_input(inner, "Mã tác vụ", 0, 0, "Nhập mã tác vụ (vd: T001)")
        self.customer_name_entry = self.make_input(inner, "Khách hàng", 0, 2, "Nhập tên khách hàng")

        tk.Label(inner, text="Loại tác vụ", bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=6)
        self.task_type_var.trace_add("write", lambda *args: self.toggle_print_options())
        self.task_type_menu = self.make_option_menu(inner, self.task_type_var, TASK_TYPES)
        self.task_type_menu.grid(row=1, column=1, sticky="ew", pady=6, ipady=3)
        self.priority_entry = self.make_input(inner, "Độ ưu tiên", 1, 2, "1 = ưu tiên cao")

        tk.Label(inner, text="Số trang in", bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=6)
        page_box = tk.Frame(inner, bg=WHITE_COLOR)
        page_box.grid(row=2, column=1, columnspan=3, sticky="w", pady=6)

        cover_box, self.cover_pages_entry = self.make_small_count_entry(page_box, "in bìa", "0")
        color_box, self.color_pages_entry = self.make_small_count_entry(page_box, "in màu", "0")
        bw_box, self.bw_pages_entry = self.make_small_count_entry(page_box, "trắng đen", "0")
        cover_box.pack(side=tk.LEFT)
        color_box.pack(side=tk.LEFT)
        bw_box.pack(side=tk.LEFT)

        button_area = tk.Frame(inner, bg=WHITE_COLOR)
        button_area.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        for i in range(4):
            button_area.columnconfigure(i, weight=1)

        btns = [
            ("Add", "＋ Thêm tác vụ", self.add_task, PRIMARY_COLOR, WHITE_COLOR),
            ("Update", "✎ Cập nhật", self.update_task, GREEN, WHITE_COLOR),
            ("Delete", "🗑 Xóa", self.delete_selected_task, ACCENT_COLOR, WHITE_COLOR),
            ("Reset", "⟳ Làm mới", self.clear_form, "#EEF6FF", PRIMARY_COLOR),
        ]
        for idx, (icon_name, text, cmd, bg, fg) in enumerate(btns):
            self.make_image_button(button_area, icon_name, text, cmd, size=(144, 36), fallback_bg=bg, fallback_fg=fg).grid(row=0, column=idx, padx=5)

        self.toggle_print_options()

    def toggle_print_options(self):
        # Phiên bản mới không dùng radio tùy chọn in nữa.
        # Burst time được tính trực tiếp từ 3 ô: in bìa, in màu, trắng đen.
        return

    def build_filter(self, parent):
        f = tk.Frame(parent, bg=WHITE_COLOR)
        f.pack(fill=tk.BOTH, expand=True, padx=18, pady=(2, 6))
        f.columnconfigure(1, weight=1)

        tk.Label(f, text="Từ khóa tìm", bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 12), pady=6)
        self.search_entry = PlaceholderEntry(f, placeholder="Nhập mã hoặc tên khách", font=("Arial", 10), bg=WHITE_COLOR, fg=TEXT_COLOR, relief=tk.SOLID, bd=1, highlightthickness=1, highlightbackground=BORDER_COLOR, highlightcolor=PRIMARY_COLOR, insertbackground=TEXT_COLOR)
        self.search_entry.grid(row=0, column=1, sticky="ew", pady=6, ipady=5)

        tk.Label(f, text="Loại tác vụ", bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", padx=(0, 12), pady=6)
        self.filter_type_menu = self.make_option_menu(f, self.filter_type_var, ["Tất cả loại"] + TASK_TYPES)
        self.filter_type_menu.grid(row=1, column=1, sticky="ew", pady=6, ipady=3)

        tk.Label(f, text="Trạng thái", bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", padx=(0, 12), pady=6)
        self.filter_status_menu = self.make_option_menu(f, self.filter_status_var, ["Tất cả trạng thái", "Đang chờ", "Đang xử lý", "Hoàn thành"])
        self.filter_status_menu.grid(row=2, column=1, sticky="ew", pady=6, ipady=3)

        button_area = tk.Frame(f, bg=WHITE_COLOR)
        button_area.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        button_area.columnconfigure(0, weight=1)
        button_area.columnconfigure(1, weight=1)

        self.make_image_button(button_area, "Filter", "▽  Áp dụng bộ lọc", self.search_tasks, size=(138, 34), fallback_bg=PRIMARY_COLOR, fallback_fg=WHITE_COLOR).grid(row=0, column=0, padx=(0, 5), pady=4)
        self.make_image_button(button_area, "Import", "📁 Nạp từ Excel/CSV", self.load_tasks_from_excel, size=(138, 34), fallback_bg="#0D9488", fallback_fg=WHITE_COLOR).grid(row=0, column=1, padx=(5, 0), pady=4)

    def create_task_table_section(self):
        table_box = self.make_section(self, "DANH SÁCH TÁC VỤ TRONG HỆ THỐNG", icon_file="Task_List")
        table_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))
        self.build_table(table_box)

    def build_table(self, parent):
        outer = tk.Frame(parent, bg=WHITE_COLOR)
        outer.pack(fill=tk.BOTH, expand=True, padx=14, pady=12)

        action_bar = tk.Frame(outer, bg=WHITE_COLOR)
        action_bar.pack(fill=tk.X, pady=(0, 8))

        self.make_image_button(action_bar, "Save_task", "💾 Lưu tác vụ", self.save_tasks, size=(132, 33), fallback_bg="#0D9488", fallback_fg=WHITE_COLOR).pack(side=tk.RIGHT, padx=(6, 0))
        self.make_image_button(action_bar, "Delete_task", "🗑 Xóa tác vụ đã tick", self.delete_checked_tasks, size=(132, 33), fallback_bg=ACCENT_COLOR, fallback_fg=WHITE_COLOR).pack(side=tk.RIGHT, padx=(6, 0))

        tk.Label(
            action_bar,
            text="Mẹo: burst_time được tính tự động theo số trang in bìa / in màu / trắng đen.",
            bg=WHITE_COLOR,
            fg=GRAY,
            font=("Arial", 9)
        ).pack(side=tk.LEFT)

        table_frame = tk.Frame(outer, bg=WHITE_COLOR)
        table_frame.pack(fill=tk.BOTH, expand=True)

        cols = (
            "checked",
            "task_id",
            "customer_name",
            "task_type",
            "arrival_time",
            "cover_pages",
            "color_pages",
            "bw_pages",
            "burst_time",
            "priority",
            "status",
        )
        self.task_table = ttk.Treeview(table_frame, columns=cols, show="headings", height=10)

        heads = [
            "Chọn",
            "Mã tác vụ",
            "Khách hàng",
            "Loại tác vụ",
            "Thời điểm đến",
            "In bìa",
            "In màu",
            "Trắng đen",
            "Thời gian xử lý",
            "Ưu tiên",
            "Trạng thái",
        ]
        widths = [60, 100, 150, 165, 110, 80, 80, 95, 130, 90, 120]

        for col, head, width in zip(cols, heads, widths):
            self.task_table.heading(col, text=head)
            self.task_table.column(col, anchor="center", width=width, minwidth=width, stretch=False)

        vertical_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.task_table.yview)
        horizontal_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.task_table.xview)
        self.task_table.configure(yscrollcommand=vertical_scroll.set, xscrollcommand=horizontal_scroll.set)

        self.task_table.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.task_table.bind("<<TreeviewSelect>>", self.on_table_select)
        self.task_table.bind("<Button-1>", self.on_table_click)

    def validate_task_input(self, is_update=False):
        task_id = self.task_id_entry.get_real_value()
        name = self.customer_name_entry.get_real_value()

        cover_pages = self.cover_pages_entry.get_real_value() if self.cover_pages_entry else "0"
        color_pages = self.color_pages_entry.get_real_value() if self.color_pages_entry else "0"
        bw_pages = self.bw_pages_entry.get_real_value() if self.bw_pages_entry else "0"
        priority_value = self.priority_entry.get_real_value() if self.priority_entry else "1"

        if not task_id or not name:
            raise ValueError("Mã tác vụ và tên khách hàng không được bỏ trống.")

        try:
            arrival_seconds = 0
            cover_pages = self.to_int(cover_pages, 0)
            color_pages = self.to_int(color_pages, 0)
            bw_pages = self.to_int(bw_pages, 0)
            priority_value = self.to_int(priority_value, 1)
        except Exception:
            raise ValueError("Các ô số trang và độ ưu tiên phải là số nguyên.")

        if cover_pages < 0 or color_pages < 0 or bw_pages < 0:
            raise ValueError("Số trang không được nhỏ hơn 0.")

        total_pages = self.calculate_total_pages(cover_pages, color_pages, bw_pages)
        if total_pages <= 0:
            raise ValueError("Vui lòng nhập ít nhất 1 trang ở một trong ba ô: in bìa, in màu hoặc trắng đen.")

        if priority_value <= 0:
            raise ValueError("Độ ưu tiên phải là số nguyên lớn hơn 0. Quy ước: số nhỏ hơn thì ưu tiên cao hơn.")

        calculated_burst = self.calculate_processing_time(cover_pages, color_pages, bw_pages)

        if not is_update and any(t.task_id == task_id for t in self.tasks):
            raise ValueError(f"Mã tác vụ {task_id} đã tồn tại trong hệ thống.")

        current_status = "Đang chờ"
        if is_update and self.selected_task_id:
            old_task = next((t for t in self.tasks if t.task_id == self.selected_task_id), None)
            if old_task:
                current_status = getattr(old_task, "status", "Đang chờ")

        print_opt = self.build_print_option_text(cover_pages, color_pages, bw_pages)

        task_obj = Task(
            task_id,
            name,
            self.task_type_var.get(),
            arrival_seconds,
            calculated_burst,
            priority=priority_value,
            print_option=print_opt,
            status=current_status,
        )

        setattr(task_obj, "processing_method", "Tính theo số trang")
        setattr(task_obj, "cover_pages", cover_pages)
        setattr(task_obj, "color_pages", color_pages)
        setattr(task_obj, "bw_pages", bw_pages)
        setattr(task_obj, "total_pages", total_pages)

        return task_obj

    def notify(self):
        if self.on_tasks_changed:
            self.on_tasks_changed(self.tasks)

    def add_task(self):
        try:
            task = self.validate_task_input(is_update=False)
            self.tasks.append(task)
            self.refresh_task_table()
            self.clear_form()
            self.notify()
        except Exception as error:
            messagebox.showerror("Lỗi nhập liệu", str(error))

    def update_task(self):
        if not self.selected_task_id:
            return messagebox.showwarning("Chưa chọn tác vụ", "Vui lòng bấm chọn một dòng tác vụ dưới bảng để cập nhật.")
        try:
            new_task = self.validate_task_input(is_update=True)
            for index, task in enumerate(self.tasks):
                if task.task_id == self.selected_task_id:
                    self.tasks[index] = new_task
                    break
            self.selected_task_id = None
            self.refresh_task_table()
            self.clear_form()
            self.notify()
        except Exception as error:
            messagebox.showerror("Lỗi cập nhật", str(error))

    def delete_selected_task(self):
        if not self.selected_task_id:
            return messagebox.showwarning("Chưa chọn tác vụ", "Vui lòng bấm chọn dòng tác vụ cần xóa.")
        if not messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc chắn muốn xóa tác vụ {self.selected_task_id} không?"):
            return
        self.tasks[:] = [t for t in self.tasks if t.task_id != self.selected_task_id]
        self.checked_task_ids.discard(self.selected_task_id)
        self.selected_task_id = None
        self.refresh_task_table()
        self.clear_form()
        self.notify()

    def delete_checked_tasks(self):
        if not self.checked_task_ids:
            return messagebox.showwarning("Chưa chọn tác vụ", "Vui lòng tick vào ô đầu dòng của tác vụ cần xóa.")
        if not messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc chắn muốn xóa {len(self.checked_task_ids)} tác vụ đã chọn không?"):
            return
        self.tasks[:] = [t for t in self.tasks if t.task_id not in self.checked_task_ids]
        self.checked_task_ids.clear()
        self.selected_task_id = None
        self.refresh_task_table()
        self.clear_form()
        self.notify()

    def refresh_after_simulation(self, tasks=None, payload=None, notify=True):
        if tasks is not None:
            self.tasks = tasks

        self.apply_simulation_payload(payload)
        self.refresh_task_table()

        if notify:
            self.notify()

    def refresh_data(self):
        self.refresh_task_table()

    def apply_simulation_payload(self, payload=None):
        if not payload:
            return

        result_map = payload.get("result_map") or {}
        results = payload.get("results") or []

        preferred_result = None

        if isinstance(result_map, dict) and result_map:
            values = list(result_map.values())
            preferred_result = (
                result_map.get("ROUND ROBIN")
                or result_map.get("Round Robin")
                or values[-1]
            )

        if preferred_result is None and results:
            preferred_result = results[-1]

        if preferred_result is None:
            return

        simulated_by_id = {
            str(getattr(task, "task_id", "")): task
            for task in getattr(preferred_result, "tasks", []) or []
        }

        algorithm_name = getattr(preferred_result, "algorithm_name", "Simulation")

        for task in self.tasks:
            task_id = str(getattr(task, "task_id", ""))
            simulated = simulated_by_id.get(task_id)

            if simulated is None:
                continue

            setattr(task, "status", "Hoàn thành")
            setattr(task, "completion_time", getattr(simulated, "completion_time", 0))
            setattr(task, "turnaround_time", getattr(simulated, "turnaround_time", 0))
            setattr(task, "waiting_time", getattr(simulated, "waiting_time", 0))
            setattr(task, "response_time", getattr(simulated, "response_time", 0))
            setattr(task, "simulation_algorithm", algorithm_name)

    def load_tasks_from_excel(self):
        try:
            import pandas as pd
        except ImportError:
            messagebox.showerror(
                "Thiếu thư viện",
                "Vui lòng cài đặt thư viện bằng lệnh:\npip install pandas openpyxl"
            )
            return

        os.makedirs(DATA_DIR, exist_ok=True)
        data_files = [
            os.path.join(DATA_DIR, name)
            for name in os.listdir(DATA_DIR)
            if name.lower().endswith((".xlsx", ".xls", ".csv"))
            and not name.startswith("~$")
        ]

        ignored_prefixes = (
            "danh_sach_dang_cho",
            "danh_sach_hoan_thanh",
            "simulation_result",
            "ket_qua_mo_phong",
        )
        data_files = [
            path for path in data_files
            if not os.path.basename(path).lower().startswith(ignored_prefixes)
        ]

        if not data_files:
            messagebox.showwarning(
                "Chưa có file dữ liệu",
                f"Không tìm thấy file Excel/CSV nào trong thư mục:\n{DATA_DIR}"
            )
            return

        loaded_tasks = []
        skipped_rows = 0
        errors = []
        seen_ids = set()

        for file_path in sorted(data_files):
            try:
                if file_path.lower().endswith(".csv"):
                    df = pd.read_csv(file_path)
                    loaded, skipped = self.tasks_from_dataframe(df, seen_ids)
                    loaded_tasks.extend(loaded)
                    skipped_rows += skipped
                else:
                    sheets = pd.read_excel(file_path, sheet_name=None)
                    for _, df in sheets.items():
                        loaded, skipped = self.tasks_from_dataframe(df, seen_ids)
                        loaded_tasks.extend(loaded)
                        skipped_rows += skipped
            except Exception as error:
                errors.append(f"{os.path.basename(file_path)}: {error}")

        if not loaded_tasks:
            detail = "\n".join(errors[:5]) if errors else "Không có dòng hợp lệ trong các file."
            messagebox.showerror("Không nạp được dữ liệu", detail)
            return

        self.tasks.clear()
        self.tasks.extend(loaded_tasks)
        self.checked_task_ids.clear()
        self.selected_task_id = None
        self.refresh_task_table()
        self.clear_form()
        self.notify()

        msg = f"Đã nạp {len(loaded_tasks)} tác vụ từ {len(data_files)} file trong thư mục data."
        if skipped_rows:
            msg += f"\nBỏ qua {skipped_rows} dòng không hợp lệ/trùng mã."
        if errors:
            msg += "\n\nMột số file bị lỗi:\n" + "\n".join(errors[:5])
        messagebox.showinfo("Thành công", msg)

    def tasks_from_dataframe(self, df, seen_ids):
        tasks = []
        skipped = 0
        if df is None or df.empty:
            return tasks, skipped

        df = df.copy()
        df.columns = [str(col).strip() for col in df.columns]

        for _, row in df.iterrows():
            try:
                task_id = self.get_row_value(row, ["Mã tác vụ", "Ma tac vu", "task_id", "id", "Mã", "Ma"])
                customer_name = self.get_row_value(row, ["Khách hàng", "Khach hang", "customer_name", "customer", "Tên khách", "Ten khach"])
                task_type = self.get_row_value(row, ["Loại tác vụ", "Loai tac vu", "task_type", "type", "Loại", "Loai"], default="In tài liệu")
                arrival = self.get_row_value(row, ["Thời điểm đến", "Thoi diem den", "Đến", "Den", "arrival_time", "arrival", "AT"], default="0")
                status = self.get_row_value(row, ["Trạng thái", "Trang thai", "status"], default="Đang chờ")

                cover_pages = self.get_row_value(
                    row,
                    ["Số trang bìa", "So trang bia", "In bìa", "In bia", "cover_pages", "bia_pages", "bia"],
                    default=0,
                )
                color_pages = self.get_row_value(
                    row,
                    ["Số trang màu", "So trang mau", "In màu", "In mau", "color_pages", "mau_pages", "mau"],
                    default=0,
                )
                bw_pages = self.get_row_value(
                    row,
                    [
                        "Số trang trắng đen", "So trang trang den", "Trắng đen", "Trang den",
                        "bw_pages", "black_white_pages", "trang_den_pages", "den_trang"
                    ],
                    default=0,
                )

                priority_value = self.get_row_value(
                    row,
                    ["Độ ưu tiên", "Do uu tien", "Mức độ ưu tiên", "Muc do uu tien", "priority", "prio"],
                    default="",
                )

                # Tương thích dữ liệu cũ: nếu chưa có 3 cột số trang riêng,
                # dùng cột Số lượng + Tùy chọn in để tự đưa vào đúng loại trang.
                if self.to_int(cover_pages, 0) == 0 and self.to_int(color_pages, 0) == 0 and self.to_int(bw_pages, 0) == 0:
                    old_qty = self.get_row_value(row, ["Số lượng", "So luong", "quantity", "qty", "Số tờ", "So to"], default=0)
                    old_print_option = self.get_row_value(row, ["Tùy chọn in", "Tuy chon in", "print_option"], default="Trắng đen")
                    old_qty = self.to_int(old_qty, 0)
                    old_print_text = str(old_print_option).strip().lower()

                    if old_qty > 0:
                        if "bìa" in old_print_text or "bia" in old_print_text:
                            cover_pages = old_qty
                        elif "màu" in old_print_text or "mau" in old_print_text:
                            color_pages = old_qty
                        else:
                            bw_pages = old_qty

                task_id = str(task_id).strip()
                if not task_id or task_id.lower() in ("nan", "none") or task_id in seen_ids:
                    skipped += 1
                    continue

                customer_name = str(customer_name).strip()
                if not customer_name or customer_name.lower() in ("nan", "none"):
                    customer_name = "Khách lẻ"

                task_type = str(task_type).strip()
                if not task_type or task_type.lower() in ("nan", "none"):
                    task_type = "In tài liệu"

                cover_val = max(0, self.to_int(cover_pages, 0))
                color_val = max(0, self.to_int(color_pages, 0))
                bw_val = max(0, self.to_int(bw_pages, 0))
                total_pages = self.calculate_total_pages(cover_val, color_val, bw_val)

                if total_pages <= 0:
                    skipped += 1
                    continue

                calculated_burst = self.calculate_processing_time(cover_val, color_val, bw_val)
                priority_int = self.to_int(priority_value, total_pages)
                if priority_int <= 0:
                    priority_int = total_pages

                arrival_seconds = self.to_int(str(arrival).strip(), 0)
                print_opt_str = self.build_print_option_text(cover_val, color_val, bw_val)

                task = Task(
                    task_id=task_id,
                    customer_name=customer_name,
                    task_type=task_type,
                    arrival_time=arrival_seconds,
                    burst_time=calculated_burst,
                    priority=priority_int,
                    print_option=print_opt_str,
                    status=self.normalize_status(status),
                )

                setattr(task, "processing_method", "Tính theo số trang")
                setattr(task, "cover_pages", cover_val)
                setattr(task, "color_pages", color_val)
                setattr(task, "bw_pages", bw_val)
                setattr(task, "total_pages", total_pages)

                seen_ids.add(task_id)
                tasks.append(task)
            except Exception:
                skipped += 1
        return tasks, skipped

    def get_row_value(self, row, names, default=""):
        normalized_map = {self.normalize_column_name(col): col for col in row.index}
        for name in names:
            real_col = normalized_map.get(self.normalize_column_name(name))
            if real_col is not None:
                value = row.get(real_col, default)
                if value is not None and str(value).strip().lower() != "nan":
                    return value
        return default

    def normalize_column_name(self, text):
        text = str(text).strip().lower()
        replacements = {
            "á": "a", "à": "a", "ả": "a", "ã": "a", "ạ": "a",
            "ă": "a", "ắ": "a", "ằ": "a", "ẳ": "a", "ẵ": "a", "ặ": "a",
            "â": "a", "ấ": "a", "ầ": "a", "ẩ": "a", "ẫ": "a", "ậ": "a",
            "é": "e", "è": "e", "ẻ": "e", "ẽ": "e", "ẹ": "e",
            "ê": "e", "ế": "e", "ề": "e", "ể": "e", "ễ": "e", "ệ": "e",
            "í": "i", "ì": "i", "ỉ": "i", "ĩ": "i", "ị": "i",
            "ó": "o", "ò": "o", "ỏ": "o", "õ": "o", "ọ": "o",
            "ô": "o", "ố": "o", "ồ": "o", "ổ": "o", "ỗ": "o", "ộ": "o",
            "ơ": "o", "ớ": "o", "ờ": "o", "ở": "o", "ỡ": "o", "ợ": "o",
            "ú": "u", "ù": "u", "ủ": "u", "ũ": "u", "ụ": "u",
            "ư": "u", "ứ": "u", "ừ": "u", "ử": "u", "ữ": "u", "ự": "u",
            "ý": "y", "ỳ": "y", "ỷ": "y", "ỹ": "y", "ỵ": "y",
            "đ": "d",
        }
        for src, dst in replacements.items():
            text = text.replace(src, dst)
        return "".join(ch for ch in text if ch.isalnum())

    def normalize_status(self, value):
        text = str(value).strip().lower()
        if text in ("hoàn thành", "hoan thanh", "completed", "complete", "done"):
            return "Hoàn thành"
        if text in ("đang xử lý", "dang xu ly", "processing", "running", "run"):
            return "Đang xử lý"
        return "Đang chờ"

    def to_int(self, value, default=0):
        try:
            if isinstance(value, str) and ":" in value:
                return self.time_str_to_seconds(value)
            return int(float(value))
        except Exception:
            return default

    def save_tasks(self):
        if not self.tasks:
            return messagebox.showwarning("Trống", "Hệ thống chưa có tác vụ nào để lưu.")
        try:
            import pandas as pd
            rows = []
            for t in self.tasks:
                cover_pages, color_pages, bw_pages = self.get_task_page_counts(t)
                rows.append({
                    "Mã tác vụ": t.task_id,
                    "Khách hàng": t.customer_name,
                    "Loại tác vụ": t.task_type,
                    "Số trang bìa": cover_pages,
                    "Số trang màu": color_pages,
                    "Số trang trắng đen": bw_pages,
                    "Thời gian xử lý": t.burst_time,
                    "Độ ưu tiên": t.priority,
                    "Thời điểm đến": t.arrival_time,
                    "Tùy chọn in": getattr(t, "print_option", ""),
                    "Trạng thái": getattr(t, "status", "Đang chờ"),
                    "Hoàn thành (CT)": getattr(t, "completion_time", ""),
                    "Lưu lại (TAT)": getattr(t, "turnaround_time", ""),
                    "Thời gian chờ (WT)": getattr(t, "waiting_time", ""),
                    "Phản hồi (RT)": getattr(t, "response_time", ""),
                })
            os.makedirs(DATA_DIR, exist_ok=True)
            output_path = os.path.join(DATA_DIR, "Danh_sach_Tac_vu.xlsx")
            pd.DataFrame(rows).to_excel(output_path, index=False, engine='openpyxl')
            messagebox.showinfo("Thành công", f"Đã lưu danh sách tác vụ vào:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu file: {str(e)}")

    def export_waiting_tasks(self):
        if not self.tasks:
            return messagebox.showwarning("Trống", "Hệ thống chưa có tác vụ nào để xuất.")
        try:
            import pandas as pd
            waiting_list = [t for t in self.tasks if t.status == "Đang chờ"]
            if not waiting_list:
                return messagebox.showinfo("Thông báo", "Hiện tại không có tác vụ nào ở trạng thái 'Đang chờ'.")
            
            rows = []
            for t in waiting_list:
                cover_pages, color_pages, bw_pages = self.get_task_page_counts(t)
                rows.append({
                    "Mã tác vụ": t.task_id,
                    "Khách hàng": t.customer_name,
                    "Loại tác vụ": t.task_type,
                    "Số trang bìa": cover_pages,
                    "Số trang màu": color_pages,
                    "Số trang trắng đen": bw_pages,
                    "Thời gian xử lý": t.burst_time,
                    "Độ ưu tiên": t.priority,
                    "Đến": t.arrival_time,
                    "Tùy chọn in": t.print_option,
                })
            
            df = pd.DataFrame(rows)
            output_path = os.path.join(DATA_DIR, "Danh_sach_Dang_cho.xlsx")
            df.to_excel(output_path, index=False, engine='openpyxl')
            messagebox.showinfo("Thành công", f"Đã lưu danh sách tác vụ đang chờ xử lý vào:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất file: {str(e)}")

    def export_completed_tasks(self):
        if not self.tasks:
            return messagebox.showwarning("Trống", "Hệ thống chưa có tác vụ nào để xuất.")
        try:
            import pandas as pd
            completed_list = [t for t in self.tasks if t.status == "Hoàn thành"]
            if not completed_list:
                return messagebox.showinfo("Thông báo", "Chưa có tác vụ nào 'Hoàn thành'. Vui lòng chạy Mô phỏng trước.")
            
            rows = []
            for t in completed_list:
                cover_pages, color_pages, bw_pages = self.get_task_page_counts(t)
                rows.append({
                    "Mã tác vụ": t.task_id,
                    "Khách hàng": t.customer_name,
                    "Loại tác vụ": t.task_type,
                    "Số trang bìa": cover_pages,
                    "Số trang màu": color_pages,
                    "Số trang trắng đen": bw_pages,
                    "Thời gian xử lý": t.burst_time,
                    "Độ ưu tiên": t.priority,
                    "Thời điểm đến": t.arrival_time,
                    "Tùy chọn in": t.print_option,
                    "Hoàn thành (CT)": t.completion_time,
                    "Lưu lại (TAT)": t.turnaround_time,
                    "Thời gian chờ (WT)": t.waiting_time,
                    "Phản hồi (RT)": t.response_time,
                })
            
            df = pd.DataFrame(rows)
            output_path = os.path.join(DATA_DIR, "Danh_sach_Hoan_thanh.xlsx")
            df.to_excel(output_path, index=False, engine='openpyxl')
            messagebox.showinfo("Thành công", f"Đã xuất lịch sử tác vụ đã hoàn tất vào:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất file: {str(e)}")

    def search_tasks(self):
        keyword = self.search_entry.get_real_value().lower().strip()
        selected_type = self.filter_type_var.get()
        selected_status = self.filter_status_var.get()

        filtered_data = []
        for task in self.tasks:
            match_keyword = (keyword == "" or keyword in task.task_id.lower() or keyword in task.customer_name.lower() or keyword in task.task_type.lower())
            match_type = (selected_type == "Tất cả loại" or selected_type in task.task_type)
            match_status = (selected_status == "Tất cả trạng thái" or task.status == selected_status)

            if match_keyword and match_type and match_status:
                filtered_data.append(task)

        self.search_tasks_display(filtered_data)

    def search_tasks_display(self, filtered_data):
        for row in self.task_table.get_children():
            self.task_table.delete(row)
        for task in filtered_data:
            self.insert_task_row(task)

    def refresh_task_table(self, tasks_to_display=None):
        for row in self.task_table.get_children():
            self.task_table.delete(row)

        display_list = tasks_to_display if tasks_to_display is not None else self.tasks
        for task in display_list:
            self.insert_task_row(task)
        self.update_stat_cards()

    def insert_task_row(self, task):
        checked_text = "☑" if task.task_id in self.checked_task_ids else "☐"

        cover_pages, color_pages, bw_pages = self.get_task_page_counts(task)
        burst_time = getattr(task, "burst_time", 0)
        priority_value = getattr(task, "priority", 1)

        self.task_table.insert(
            "",
            tk.END,
            values=(
                checked_text,
                task.task_id,
                task.customer_name,
                task.task_type,
                task.arrival_time,
                cover_pages,
                color_pages,
                bw_pages,
                f"{burst_time} giây",
                priority_value,
                task.status,
            ),
        )

    def update_stat_cards(self):
        total = len(self.tasks)
        waiting = sum(1 for t in self.tasks if t.status == "Đang chờ")
        processing = sum(1 for t in self.tasks if t.status == "Đang xử lý")
        completed = sum(1 for t in self.tasks if t.status == "Hoàn thành")

        self.total_lbl.config(text=str(total))
        self.wait_lbl.config(text=str(waiting))
        self.run_lbl.config(text=str(processing))
        self.done_lbl.config(text=str(completed))

    def on_table_click(self, event):
        region = self.task_table.identify("region", event.x, event.y)
        column = self.task_table.identify_column(event.x)
        row_id = self.task_table.identify_row(event.y)

        if region != "cell" or not row_id: return
        if column == "#1":
            values = self.task_table.item(row_id, "values")
            task_id = values[1]
            if task_id in self.checked_task_ids:
                self.checked_task_ids.remove(task_id)
            else:
                self.checked_task_ids.add(task_id)
            self.refresh_task_table()
            return "break"

    def on_table_select(self, event):
        selected = self.task_table.selection()
        if not selected:
            return

        values = self.task_table.item(selected[0], "values")
        self.selected_task_id = values[1]

        self.task_id_entry.set_real_value(values[1])
        self.customer_name_entry.set_real_value(values[2])
        self.task_type_var.set(values[3])

        if self.cover_pages_entry:
            self.cover_pages_entry.set_real_value(values[5])
        if self.color_pages_entry:
            self.color_pages_entry.set_real_value(values[6])
        if self.bw_pages_entry:
            self.bw_pages_entry.set_real_value(values[7])
        if self.priority_entry:
            self.priority_entry.set_real_value(values[9])

    def clear_form(self):
        self.selected_task_id = None
        self.task_id_entry.reset_placeholder()
        self.customer_name_entry.reset_placeholder()

        if self.cover_pages_entry:
            self.cover_pages_entry.set_real_value("0")
        if self.color_pages_entry:
            self.color_pages_entry.set_real_value("0")
        if self.bw_pages_entry:
            self.bw_pages_entry.set_real_value("0")
        if self.priority_entry:
            self.priority_entry.set_real_value("1")

        if TASK_TYPES:
            self.task_type_var.set(TASK_TYPES[0])
        self.print_option_var.set("Trắng đen")

    def time_str_to_seconds(self, time_str):
        try:
            parts = str(time_str).strip().split(":")
            if len(parts) == 3: return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            if len(parts) == 2: return int(parts[0]) * 3600 + int(parts[1]) * 60
            return int(time_str)
        except Exception: return 0