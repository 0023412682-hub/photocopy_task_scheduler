import os
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False

from ui.icon_utils import (
    load_icon,
    resolve_icon_path as shared_resolve_icon_path,
    normalize_icon_name as shared_normalize_icon_name
)

from ui.home_frame import HomeFrame
from ui.task_frame import TaskFrame
from ui.simulation_frame import SimulationFrame
from ui.comparison_frame import ComparisonFrame
from ui.memory_frame import MemoryFrame
from ui.sync_frame import SyncFrame
from ui.report_frame import ReportFrame


PRIMARY_COLOR = "#005BAC"
DARK_BLUE = "#004A99"
ACCENT_COLOR = "#D71920"
BACKGROUND_COLOR = "#F4F7FB"
WHITE_COLOR = "#FFFFFF"
TEXT_COLOR = "#1F2937"
MUTED_TEXT = "#64748B"
BORDER_COLOR = "#D9E2EC"

SIDEBAR_WIDTH = 200
SIDEBAR_MIN_WIDTH = 260
SIDEBAR_TEXT_RIGHT_GAP = 30
HEADER_HEIGHT = 100
FOOTER_HEIGHT = 34

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(BASE_DIR, "utils", "icons")


class PhotocopySchedulerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Mô phỏng hệ thống xếp hàng - Quán photocopy")
        self.geometry("1400x850")
        self.minsize(1200, 740)
        self.configure(bg=BACKGROUND_COLOR)

        self.tasks = []
        self.images = {}
        self.menu_items = {}
        self.current_page = "home"
        self.footer_status_label = None

        # =========================
        # CACHE PAGE
        # =========================
        self.pages = {}
        self.current_frame = None

        self.latest_simulation_payload = None
        self.latest_memory_payload = None
        self.latest_sync_payload = None

        self.create_layout()
        self.show_home_page()

    # =========================
    # IMAGE / ICON
    # =========================
    def normalize_icon_name(self, value):
        return shared_normalize_icon_name(value)

    def resolve_icon_path(self, filename):
        return shared_resolve_icon_path(ICON_DIR, filename)

    def load_image(self, filename, size=(28, 28)):
        return load_icon(
            self,
            ICON_DIR,
            filename,
            size=size,
            crop_transparency=True,
            keep_aspect=True
        )

    # =========================
    # MAIN LAYOUT
    # =========================
    def create_layout(self):
        self.header = tk.Frame(self, bg=WHITE_COLOR, height=HEADER_HEIGHT)
        self.header.pack(side=tk.TOP, fill=tk.X)
        self.header.pack_propagate(False)

        self.footer = tk.Frame(self, bg=PRIMARY_COLOR, height=FOOTER_HEIGHT)
        self.footer.pack(side=tk.BOTTOM, fill=tk.X)
        self.footer.pack_propagate(False)

        self.body = tk.Frame(self, bg=BACKGROUND_COLOR)
        self.body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.sidebar = tk.Frame(self.body, bg=PRIMARY_COLOR, width=SIDEBAR_WIDTH)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        self.main_area = tk.Frame(self.body, bg=BACKGROUND_COLOR)
        self.main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self.create_header()
        self.create_sidebar()
        self.create_footer()

    # =========================
    # HEADER
    # =========================
    def create_header(self):
        left = tk.Frame(self.header, bg=WHITE_COLOR)
        left.pack(side=tk.LEFT, padx=(24, 16), pady=14)

        logo_size = (74, 74)
        khoa_logo = self.load_image("khoa.jpg", logo_size)
        school_logo = self.load_image("school.png", logo_size)

        for logo, fallback in [(khoa_logo, "KHOA"), (school_logo, "DThU")]:
            if logo:
                tk.Label(
                    left,
                    image=logo,
                    bg=WHITE_COLOR
                ).pack(side=tk.LEFT, padx=4)
            else:
                tk.Label(
                    left,
                    text=fallback,
                    bg=WHITE_COLOR,
                    fg=PRIMARY_COLOR,
                    font=("Arial", 11, "bold"),
                    width=7,
                    height=4,
                    relief=tk.GROOVE,
                ).pack(side=tk.LEFT, padx=4)

        school_text = tk.Frame(self.header, bg=WHITE_COLOR)
        school_text.pack(side=tk.LEFT, pady=22)

        tk.Label(
            school_text,
            text="ĐẠI HỌC ĐỒNG THÁP",
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 16, "bold"),
        ).pack(anchor="w")

        tk.Label(
            school_text,
            text="KHOA SƯ PHẠM TOÁN - TIN",
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 15, "bold"),
        ).pack(anchor="w")

        tk.Label(
            school_text,
            text="FACULTY OF MATHEMATICS - INFORMATICS TEACHER EDUCATION",
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 7, "bold"),
        ).pack(anchor="w")

        divider = tk.Frame(
            self.header,
            bg=BORDER_COLOR,
            width=2,
            height=76
        )
        divider.pack(side=tk.LEFT, padx=24, pady=20)
        divider.pack_propagate(False)

        self.title_frame = tk.Frame(self.header, bg=WHITE_COLOR)
        self.title_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.header_title = tk.Label(
            self.title_frame,
            text="MÔ PHỎNG HỆ THỐNG XẾP HÀNG",
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 26, "bold"),
        )
        self.header_title.pack(pady=(22, 0))

        self.header_subtitle = tk.Label(
            self.title_frame,
            text="XỬ LÝ TÁC VỤ TRONG QUÁN PHOTOCOPY BẰNG CÁC GIẢI THUẬT LẬP LỊCH CPU",
            bg=WHITE_COLOR,
            fg=ACCENT_COLOR,
            font=("Arial", 11, "bold"),
        )
        self.header_subtitle.pack(pady=(2, 0))

    def set_header_text(self, title, subtitle):
        self.header_title.config(text=title)
        self.header_subtitle.config(text=subtitle)

    # =========================
    # SIDEBAR
    # =========================
    def create_sidebar(self):
        menu_data = [
            ("home", "Trang chủ", "Home.png", self.show_home_page),
            ("task", "Danh sách tác vụ", "Task_List.png", self.show_task_page),
            ("simulation", "Mô phỏng thuật toán", "Simulation_Algorithm.png", self.show_simulation_page),
            ("memory", "Bộ nhớ", "Memory.png", self.show_memory_page),
            ("sync", "Đồng bộ hóa", "Sync.png", self.show_sync_page),
            ("comparison", "So sánh thuật toán", "Compare_Algorithms.png", self.show_comparison_page),
            ("report", "Báo cáo", "Report.png", self.show_report_page),
        ]

        # Tự tính chiều rộng sidebar theo font thật của từng máy/DPI.
        # Công thức chừa đủ icon + khoảng đệm trái/phải và đảm bảo chữ dài nhất
        # còn cách mép khung ít nhất SIDEBAR_TEXT_RIGHT_GAP px.
        self.sidebar_width = self.calculate_sidebar_width(menu_data)
        self.sidebar.config(width=self.sidebar_width)

        tk.Frame(self.sidebar, bg=PRIMARY_COLOR, height=14).pack(fill=tk.X)

        for key, text, icon_name, command in menu_data:
            self.create_menu_item(key, text, icon_name, command)

        tk.Frame(self.sidebar, bg=PRIMARY_COLOR).pack(fill=tk.BOTH, expand=True)
        self.create_system_info_box()

    def calculate_sidebar_width(self, menu_data):
        try:
            menu_font = tkfont.Font(family="Arial", size=11, weight="bold")
            longest_text_width = max(menu_font.measure(text) for _, text, _, _ in menu_data)
        except Exception:
            longest_text_width = 170

        outer_item_pad = 12 * 2      # item.pack(padx=12)
        icon_left_pad = 14
        icon_width = 28
        icon_right_pad = 10
        safe_padding = outer_item_pad + icon_left_pad + icon_width + icon_right_pad + SIDEBAR_TEXT_RIGHT_GAP

        width = longest_text_width + safe_padding
        return max(SIDEBAR_MIN_WIDTH, int(width))

    def resolve_sidebar_icon_path(self, filename):
        """
        Chỉ tìm đúng icon sidebar theo tên file thật trong thư mục utils/icons.
        Không tự thử thêm tiền tố P_, H_, B_, G_, R_ nữa để tránh gọi nhầm icon cũ.
        """
        if not filename:
            return None

        filename = str(filename).strip()

        if os.path.isabs(filename):
            return filename if os.path.exists(filename) else None

        direct_path = os.path.join(ICON_DIR, filename)
        if os.path.exists(direct_path):
            return direct_path

        stem, ext = os.path.splitext(filename)
        if ext:
            return None

        for extension in (".png", ".jpg", ".jpeg"):
            path = os.path.join(ICON_DIR, filename + extension)
            if os.path.exists(path):
                return path

        return None

    def load_tinted_image(self, filename, size=(28, 28), color="#FFFFFF"):
        """
        Load icon sidebar theo đúng tên file hiện có, rồi tô màu theo trạng thái.
        Nếu thiếu icon thì trả None để giao diện dùng dấu chấm dự phòng, không in cảnh báo.
        """
        path = self.resolve_sidebar_icon_path(filename)

        if not path or not PIL_AVAILABLE:
            return None

        try:
            image = Image.open(path).convert("RGBA")

            alpha = image.getchannel("A")
            bbox = alpha.getbbox()
            if bbox:
                image = image.crop(bbox)

            try:
                resample_filter = Image.Resampling.LANCZOS
            except AttributeError:
                resample_filter = Image.LANCZOS

            image.thumbnail(size, resample_filter)

            canvas = Image.new("RGBA", size, (255, 255, 255, 0))
            x = (size[0] - image.width) // 2
            y = (size[1] - image.height) // 2

            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)

            tinted = Image.new("RGBA", image.size, (r, g, b, 0))
            tinted.putalpha(image.getchannel("A"))
            canvas.paste(tinted, (x, y), tinted)

            photo = ImageTk.PhotoImage(canvas)
            key = f"sidebar_{filename}_{size}_{color}_{len(self.images)}"
            self.images[key] = photo

            return photo

        except Exception:
            return None

    def create_menu_item(self, key, text, icon_name, command):
        item = tk.Frame(self.sidebar, bg=PRIMARY_COLOR, cursor="hand2")
        item.pack(fill=tk.X, padx=12, pady=5)

        normal_icon = self.load_tinted_image(icon_name, (28, 28), WHITE_COLOR)
        active_icon = self.load_tinted_image(icon_name, (28, 28), PRIMARY_COLOR)

        icon_label = tk.Label(item, bg=PRIMARY_COLOR, cursor="hand2")

        if normal_icon:
            icon_label.config(image=normal_icon)
        else:
            icon_label.config(
                text="●",
                fg=WHITE_COLOR,
                font=("Arial", 18, "bold"),
                width=2
            )

        icon_label.pack(side=tk.LEFT, padx=(14, 10), pady=11)

        text_label = tk.Label(
            item,
            text=text,
            bg=PRIMARY_COLOR,
            fg=WHITE_COLOR,
            font=("Arial", 11, "bold"),
            anchor="w",
            cursor="hand2",
        )
        text_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, SIDEBAR_TEXT_RIGHT_GAP), pady=11)

        for widget in (item, icon_label, text_label):
            widget.bind("<Button-1>", lambda event, cmd=command: cmd())

        self.menu_items[key] = {
            "frame": item,
            "icon": icon_label,
            "text": text_label,
            "normal_icon": normal_icon,
            "active_icon": active_icon,
        }

    def set_active_menu(self, active_key):
        for key, item in self.menu_items.items():
            active = key == active_key

            bg = WHITE_COLOR if active else PRIMARY_COLOR
            fg = PRIMARY_COLOR if active else WHITE_COLOR
            icon = item.get("active_icon") if active else item.get("normal_icon")
            icon = icon or item.get("normal_icon")

            item["frame"].config(bg=bg)
            item["icon"].config(bg=bg, fg=fg)
            item["text"].config(bg=bg, fg=fg)

            if icon:
                item["icon"].config(image=icon)

    def create_system_info_box(self):
        info_box = tk.Frame(self.sidebar, bg="#EAF4FF")
        info_box.pack(fill=tk.X, padx=14, pady=14)

        tk.Label(
            info_box,
            text="THÔNG TIN HỆ THỐNG",
            bg="#EAF4FF",
            fg=PRIMARY_COLOR,
            font=("Arial", 10, "bold"),
        ).pack(pady=(12, 8))

        now = datetime.now()

        info_items = [
            ("📅", "Ngày", now.strftime("%d/%m/%Y")),
            ("◷", "Giờ", now.strftime("%H:%M:%S")),
            ("👤", "Người dùng", "Sinh viên"),
            ("ⓘ", "Phiên bản", "1.0.0"),
        ]

        for icon, label, value in info_items:
            row = tk.Frame(info_box, bg="#EAF4FF")
            row.pack(fill=tk.X, padx=12, pady=4)

            tk.Label(
                row,
                text=icon,
                bg="#EAF4FF",
                fg=PRIMARY_COLOR,
                font=("Arial", 10)
            ).pack(side=tk.LEFT, padx=(0, 8))

            tk.Label(
                row,
                text=label,
                bg="#EAF4FF",
                fg=TEXT_COLOR,
                font=("Arial", 9),
                width=9,
                anchor="w"
            ).pack(side=tk.LEFT)

            tk.Label(
                row,
                text=value,
                bg="#EAF4FF",
                fg=TEXT_COLOR,
                font=("Arial", 9),
                anchor="e"
            ).pack(side=tk.RIGHT)

        tk.Frame(info_box, bg="#EAF4FF", height=10).pack()

    # =========================
    # FOOTER
    # =========================
    def create_footer(self):
        self.footer_status_label = tk.Label(
            self.footer,
            text="●  Sẵn sàng mô phỏng",
            bg=PRIMARY_COLOR,
            fg=WHITE_COLOR,
            font=("Arial", 10),
        )
        self.footer_status_label.pack(side=tk.LEFT, padx=24, pady=7)

        tk.Label(
            self.footer,
            text="© 2025 - Khoa Sư phạm Toán - Tin, Trường Đại học Đồng Tháp",
            bg=PRIMARY_COLOR,
            fg=WHITE_COLOR,
            font=("Arial", 10),
        ).pack(side=tk.RIGHT, padx=24, pady=7)

    def set_footer_status(self, text):
        if self.footer_status_label:
            self.footer_status_label.config(text="●  " + text)

    # =========================
    # NAVIGATION
    # =========================
    def hide_current_page(self):
        if self.current_frame is not None:
            if hasattr(self.current_frame, "on_page_hide"):
                self.current_frame.on_page_hide()

    def show_cached_page(self, page_key, frame_creator):
        if self.current_frame is not None and self.current_page == page_key:
            self.current_frame.tkraise()

            if hasattr(self.current_frame, "on_page_show"):
                self.current_frame.on_page_show()

            return self.current_frame

        self.hide_current_page()

        if page_key not in self.pages:
            frame = frame_creator()
            frame.grid(row=0, column=0, sticky="nsew", padx=14, pady=14)
            self.pages[page_key] = frame

        frame = self.pages[page_key]
        frame.tkraise()

        if hasattr(frame, "on_page_show"):
            frame.on_page_show()

        self.current_frame = frame
        self.current_page = page_key

        return frame

    def build_report_payload(self):
        return {
            "cpu": self.latest_simulation_payload or {},
            "memory": self.latest_memory_payload or {},
            "sync": self.latest_sync_payload or {},
        }

    def update_report_frame_payload(self, report_frame):
        """Cập nhật dữ liệu cho ReportFrame đang được cache trong app.

        Một số bản ReportFrame.refresh_report() không nhận tham số tasks/payload,
        nên app cần gán lại thuộc tính trước rồi mới gọi refresh_report().
        """
        if not report_frame:
            return

        payload = self.build_report_payload()
        report_frame.tasks = self.tasks
        report_frame.payload = payload

        if hasattr(report_frame, "extract_module_payload"):
            report_frame.cpu_payload = report_frame.extract_module_payload("cpu")
            report_frame.memory_payload = report_frame.extract_module_payload("memory")
            report_frame.sync_payload = report_frame.extract_module_payload("sync")

    def refresh_report_page(self):
        report_frame = self.pages.get("report")
        if report_frame and hasattr(report_frame, "refresh_report"):
            self.update_report_frame_payload(report_frame)
            report_frame.refresh_report()


    def on_memory_finished(self, payload):
        self.latest_memory_payload = payload
        self.refresh_report_page()
        self.set_footer_status("Mô phỏng bộ nhớ hoàn thành")


    def on_sync_finished(self, payload):
        self.latest_sync_payload = payload
        self.refresh_report_page()
        self.set_footer_status("Mô phỏng đồng bộ hóa hoàn thành")

    def refresh_existing_pages_tasks(self):
        for key, frame in self.pages.items():
            if hasattr(frame, "tasks"):
                frame.tasks = self.tasks

            if key == "task":
                if hasattr(frame, "refresh_task_table"):
                    frame.refresh_task_table()
                continue

            if key == "comparison":
                if hasattr(frame, "reset_comparison"):
                    frame.reset_comparison()
                continue

            if key == "memory":
                if hasattr(frame, "refresh_memory"):
                    frame.refresh_memory()
                elif hasattr(frame, "refresh_data"):
                    frame.refresh_data()
                continue

            if key == "sync":
                if hasattr(frame, "refresh_sync"):
                    frame.refresh_sync()
                elif hasattr(frame, "refresh_data"):
                    frame.refresh_data()
                continue

            if hasattr(frame, "refresh_data"):
                try:
                    frame.refresh_data()
                except TypeError:
                    pass

    def on_tasks_changed(self, tasks):
        self.tasks = tasks
        self.latest_simulation_payload = None
        self.latest_memory_payload = None
        self.latest_sync_payload = None
        self.refresh_existing_pages_tasks()

    def on_simulation_progress(self, payload):
        self.latest_simulation_payload = payload

        comparison_frame = self.pages.get("comparison")
        if comparison_frame and hasattr(comparison_frame, "receive_simulation_progress"):
            comparison_frame.receive_simulation_progress(payload)

        self.refresh_report_page()

    def on_simulation_finished(self, tasks, payload=None):
        self.tasks = tasks

        for frame in self.pages.values():
            if hasattr(frame, "tasks"):
                frame.tasks = self.tasks

        task_frame = self.pages.get("task")
        if task_frame:
            if hasattr(task_frame, "refresh_after_simulation"):
                try:
                    task_frame.refresh_after_simulation(
                        self.tasks,
                        payload=payload,
                        notify=False
                    )
                except TypeError:
                    task_frame.refresh_after_simulation(self.tasks)

            elif hasattr(task_frame, "refresh_task_table"):
                task_frame.refresh_task_table()

        if payload is not None:
            self.on_simulation_progress(payload)
        elif self.latest_simulation_payload is not None:
            self.on_simulation_progress(self.latest_simulation_payload)

        self.set_footer_status("Mô phỏng hoàn thành, danh sách tác vụ đã cập nhật")

    # =========================
    # PAGE: HOME
    # =========================
    def show_home_page(self):
        self.set_active_menu("home")

        self.set_header_text(
            "MÔ PHỎNG HỆ THỐNG XẾP HÀNG",
            "XỬ LÝ TÁC VỤ TRONG QUÁN PHOTOCOPY BẰNG CÁC GIẢI THUẬT LẬP LỊCH CPU",
        )

        self.set_footer_status("Sẵn sàng mô phỏng")

        self.show_cached_page(
            "home",
            lambda: HomeFrame(
                self.main_area,
                self.navigate_from_home,
                self.tasks
            )
        )

    # =========================
    # PAGE: TASK
    # =========================
    def show_task_page(self):
        self.set_active_menu("task")

        self.set_header_text(
            "QUẢN LÝ DANH SÁCH TÁC VỤ",
            "Thêm, sửa, xóa và quản lý yêu cầu in ấn, sao chép, scan"
        )

        self.set_footer_status("Sẵn sàng quản lý dữ liệu")

        self.show_cached_page(
            "task",
            lambda: TaskFrame(
                self.main_area,
                self.tasks,
                on_tasks_changed=self.on_tasks_changed
            )
        )

    # =========================
    # PAGE: SIMULATION
    # =========================
    def show_simulation_page(self):
        self.set_active_menu("simulation")

        self.set_header_text(
            "MÔ PHỎNG XỬ LÝ TÁC VỤ",
            "Mô phỏng các giải thuật lập lịch CPU trong quán photocopy"
        )

        self.set_footer_status("Đang mô phỏng thuật toán")

        self.show_cached_page(
            "simulation",
            lambda: SimulationFrame(
                self.main_area,
                self.tasks,
                on_simulation_finished=self.on_simulation_finished,
                on_simulation_progress=self.on_simulation_progress
            )
        )

    # =========================
    # PAGE: MEMORY
    # =========================
    def show_memory_page(self):
        self.set_active_menu("memory")

        self.set_header_text(
            "QUẢN LÝ BỘ NHỚ",
            "Mô phỏng cấp phát bộ nhớ cho các tác vụ trong hệ thống photocopy"
        )

        self.set_footer_status("Đang xem mô phỏng bộ nhớ")

        frame = self.show_cached_page(
            "memory",
            lambda: MemoryFrame(
                self.main_area,
                self.tasks,
                on_memory_finished=self.on_memory_finished
            )
        )

    # =========================
    # PAGE: SYNC
    # =========================
    def show_sync_page(self):
        self.set_active_menu("sync")

        self.set_header_text(
            "ĐỒNG BỘ HÓA TÁC VỤ",
            "Mô phỏng tranh chấp tài nguyên và đồng bộ hóa trong hệ thống photocopy"
        )

        self.set_footer_status("Đang xem mô phỏng đồng bộ hóa")

        frame = self.show_cached_page(
            "sync",
            lambda: SyncFrame(
                self.main_area,
                self.tasks,
                on_sync_finished=self.on_sync_finished
            )
        )

    # =========================
    # PAGE: COMPARISON
    # =========================
    def show_comparison_page(self):
        self.set_active_menu("comparison")

        self.set_header_text(
            "SO SÁNH HIỆU QUẢ THUẬT TOÁN",
            "Đánh giá thời gian chờ và thời gian hoàn thành của các giải thuật"
        )

        self.set_footer_status("Sẵn sàng so sánh thuật toán")

        frame = self.show_cached_page(
            "comparison",
            lambda: ComparisonFrame(
                self.main_area,
                self.tasks
            )
        )

        if self.latest_simulation_payload and hasattr(frame, "receive_simulation_progress"):
            frame.receive_simulation_progress(
                self.latest_simulation_payload,
                force=True
            )

    # =========================
    # PAGE: REPORT
    # =========================
    def show_report_page(self):
        self.set_active_menu("report")

        self.set_header_text(
            "BÁO CÁO MÔ PHỎNG",
            "Kết quả xử lý tác vụ của hệ thống photocopy"
        )

        self.set_footer_status("Sẵn sàng xuất báo cáo")

        frame = self.show_cached_page(
            "report",
            lambda: ReportFrame(
                self.main_area,
                tasks=self.tasks,
                payload=self.build_report_payload(),
                controller=self
            )
        )

        self.refresh_report_page()

    # =========================
    # HOME NAVIGATION
    # =========================
    def navigate_from_home(self, page_name):
        if page_name == "task":
            self.show_task_page()
        elif page_name == "simulation":
            self.show_simulation_page()
        elif page_name == "memory":
            self.show_memory_page()
        elif page_name == "sync":
            self.show_sync_page()
        elif page_name == "comparison":
            self.show_comparison_page()
        elif page_name == "report":
            self.show_report_page()


if __name__ == "__main__":
    app = PhotocopySchedulerApp()
    app.mainloop()