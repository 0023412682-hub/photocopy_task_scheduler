import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import re
import random

# --- IMPORT THƯ VIỆN ẢNH VÀ ICON UTILS ---
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False

from ui.icon_utils import load_icon

# Định vị thư mục chứa icons
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(BASE_DIR, "utils", "icons")

PRIMARY_COLOR = "#005BAC"
BACKGROUND_COLOR = "#F4F7FB"
WHITE_COLOR = "#FFFFFF"
TEXT_COLOR = "#1F2937"
MUTED_TEXT = "#64748B"
BORDER_COLOR = "#D9E2EC"

GREEN = "#16A34A"
ORANGE = "#F97316"
RED = "#DC2626"
PURPLE = "#7C3AED"


class SyncFrame(tk.Frame):
    def __init__(self, parent, tasks=None, on_sync_finished=None):
        super().__init__(parent, bg=BACKGROUND_COLOR)

        self.tasks = tasks or []
        self.on_sync_finished = on_sync_finished

        self.mechanism_var = tk.StringVar(value="Producer - Consumer")
        self.buffer_size_var = tk.StringVar(value="5")
        self.producer_speed_var = tk.StringVar(value="Trung bình (500 ms)")
        self.consumer_speed_var = tk.StringVar(value="Trung bình (500 ms)")

        self.max_buffer_size = 5
        self.buffer = [None] * self.max_buffer_size
        self.count = 0
        self.in_ptr = 0
        self.out_ptr = 0

        self.task_index = 0
        self.produced_count = 0
        self.consumed_count = 0
        self.producer_wait = 0
        self.consumer_wait = 0
        self.critical_access = 0
        self.event_count = 0

        self.is_running = False
        self.after_id = None
        self.step_index = 0

        self.metric_labels = {}
        self.status_labels = {}
        self.status_sublabels = {}

        self.build_ui()
        self.refresh_ui()

        # Liên kết với app.py: khi frame bị destroy thật sự thì hủy after job.
        self.bind("<Destroy>", self._on_destroy, add="+")

    # =====================================================
    # APP LIFECYCLE / APP LINKING
    # =====================================================
    def stop_after_job(self):
        if self.after_id is not None:
            try:
                self.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def _on_destroy(self, event):
        if event.widget is self:
            self.stop_after_job()

    def on_page_hide(self):
        # App đang cache page, nên khi chuyển trang không reset dữ liệu.
        # Mô phỏng vẫn có thể chạy tiếp để hoàn tất và trả payload cho Báo cáo.
        return

    def on_page_show(self):
        # Khi quay lại trang Sync, cập nhật lại giao diện theo trạng thái hiện tại.
        self.refresh_ui()

    def refresh_data(self):
        # App gọi hàm này khi danh sách tác vụ thay đổi từ TaskFrame.
        if self.is_running:
            return
        self.reset_simulation()

    def refresh_sync(self):
        # Alias để app.py có thể gọi riêng cho module Sync.
        self.refresh_data()

    # =====================================================
    # IMAGE HELPER
    # =====================================================
    def load_image(self, icon_name, size=(24, 24)):
        """Hàm gọi ảnh từ thư mục utils/icons, có cơ chế fallback"""
        if not PIL_AVAILABLE or not icon_name:
            return None
        # Nếu truyền vào emoji ngắn (1-2 ký tự) thì bỏ qua không load ảnh
        if len(icon_name) <= 2: 
            return None
        return load_icon(self, ICON_DIR, f"{icon_name}.png", size)

    # =====================================================
    # UI HELPERS
    # =====================================================
    def section(self, parent, title, icon="▣", fallback_icon="▣"):
        box = tk.Frame(
            parent,
            bg=WHITE_COLOR,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )

        head = tk.Frame(box, bg=WHITE_COLOR)
        head.pack(fill="x")

        # Load ảnh thay vì dùng text. Nếu không có ảnh thì xài fallback_icon
        img = self.load_image(icon, (24, 24))
        if img:
            tk.Label(head, image=img, bg=WHITE_COLOR).pack(side="left", padx=(14, 8), pady=10)
        else:
            tk.Label(head, text=fallback_icon, bg=WHITE_COLOR, fg=PRIMARY_COLOR, font=("Arial", 13, "bold")).pack(side="left", padx=(14, 8), pady=10)

        tk.Label(
            head,
            text=title,
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 12, "bold")
        ).pack(side="left", pady=10)

        tk.Frame(box, bg=BORDER_COLOR, height=1).pack(fill="x")
        return box

    def make_button(self, parent, command, icon_name, fallback_text, width_px=110, height_px=36):
        # Nạp hình ảnh
        img = self.load_image(icon_name, (width_px, height_px))
        
        if img:
            # 1. DÙNG LABEL THAY VÌ BUTTON ĐỂ VƯỢT QUA OS NATIVE STYLING
            btn = tk.Label(
                parent,
                image=img,
                bg=WHITE_COLOR,
                bd=0,
                cursor="hand2"
            )
            # 2. Gán sự kiện Click chuột trái vào Label
            btn.bind("<Button-1>", lambda e: command())
        else:
            # Fallback: Trở về tk.Button mặc định nếu chưa kịp copy ảnh
            btn = tk.Button(
                parent,
                text=fallback_text,
                command=command,
                bg="#EAF4FF",
                fg=PRIMARY_COLOR,
                font=("Arial", 10, "bold"),
                relief=tk.FLAT,
                bd=0,
                width=12,
                cursor="hand2"
            )
            
        return btn

    def make_metric_card(self, parent, key, title, value, subtitle, icon, fallback_icon, col, icon_size=(40, 40)):
        card = tk.Frame(
            parent,
            bg=WHITE_COLOR,
            height=105,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        card.grid(row=0, column=col, sticky="nsew", padx=6)
        card.pack_propagate(False)

        # ĐÃ SỬA: Xóa width=56, height=56 và pack_propagate(False) 
        # Để khung tự động ôm vừa vặn theo kích thước ảnh mới
        icon_box = tk.Frame(card, bg=WHITE_COLOR)
        icon_box.pack(side="left", padx=16, pady=16)

        # ĐÃ SỬA: Truyền icon_size thay vì (40, 40)
        img = self.load_image(icon, icon_size)
        if img:
            lbl = tk.Label(icon_box, image=img, bg=WHITE_COLOR)
            lbl.pack() # Dùng pack thay vì place để ảnh tự động nằm giữa khung
        else:
            lbl = tk.Label(icon_box, text=fallback_icon, bg=WHITE_COLOR, fg=PRIMARY_COLOR, font=("Arial", 28, "bold"))
            lbl.pack()

        text_box = tk.Frame(card, bg=WHITE_COLOR)
        text_box.pack(side="left", fill="both", expand=True, pady=12)

        tk.Label(
            text_box,
            text=title.upper(),
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 9, "bold")
        ).pack(anchor="w")

        value_label = tk.Label(
            text_box,
            text=value,
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 24, "bold")
        )
        value_label.pack(anchor="w")

        tk.Label(
            text_box,
            text=subtitle,
            bg=WHITE_COLOR,
            fg=MUTED_TEXT,
            font=("Arial", 9)
        ).pack(anchor="w")

        self.metric_labels[key] = value_label

    # =====================================================
    # BUILD UI
    # =====================================================
    def build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        canvas = tk.Canvas(self, bg=BACKGROUND_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.content = tk.Frame(canvas, bg=BACKGROUND_COLOR)

        window = canvas.create_window((0, 0), window=self.content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(window, width=e.width)
        )

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.build_metrics()
        self.build_setup_and_status()
        self.build_buffer_and_log()
        self.build_stats_and_conclusion()

    def build_metrics(self):
        wrapper = tk.Frame(self.content, bg=BACKGROUND_COLOR)
        wrapper.pack(fill="x", padx=16, pady=(0, 10))

        for i in range(4):
            wrapper.columnconfigure(i, weight=1)

        # ĐÃ THÊM: Tham số icon_size=(60, 60) để phóng to riêng ô này
        self.make_metric_card(wrapper, "buffer", "Kích thước Buffer", "5", "ô", "Buffer", "▣", 0, icon_size=(60, 60))
        
        # 3 ô dưới không truyền icon_size, hệ thống sẽ lấy mức (40, 40) mặc định
        self.make_metric_card(wrapper, "produced", "Đã sản xuất", "0", "tác vụ", "Producer", "↗", 1, icon_size=(60, 60))
        self.make_metric_card(wrapper, "consumed", "Đã tiêu thụ", "0", "tác vụ", "Consumer", "↘", 2, icon_size=(60, 60))
        self.make_metric_card(wrapper, "deadlock", "Deadlock", "Không", "", "Deadlock", "⊘", 3, icon_size=(60, 60))

    def build_setup_and_status(self):
        row = tk.Frame(self.content, bg=BACKGROUND_COLOR)
        row.pack(fill="x", padx=16, pady=6)
        
        # --- ĐIỀU CHỈNH LẠI TỶ LỆ TRỌNG SỐ Ở ĐÂY ---
        row.columnconfigure(0, weight=3)  # Giảm xuống 3: Ép ô Thiết lập gọn lại (chiếm 30%)
        row.columnconfigure(1, weight=7)  # Tăng lên 7: Mở rộng tối đa ô Trạng thái (chiếm 70%)

        setup = self.section(row, "THIẾT LẬP MÔ PHỎNG", "Settings", "⚙")
        setup.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        # ... (Phần code phía dưới giữ nguyên)

        body = tk.Frame(setup, bg=WHITE_COLOR)
        body.pack(fill="both", expand=True, padx=16, pady=14)
        
        # Vẫn giữ weight=1 để đẩy các cột ra xa nhau cho thoáng, 
        # nhưng ta sẽ khóa kích thước Combobox lại.
        body.columnconfigure(1, weight=1)
        body.columnconfigure(3, weight=1)

        # --- ĐÃ THÊM width=20 VÀ ĐỔI THÀNH sticky="w" ---
        tk.Label(body, text="Cơ chế đồng bộ", bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=7)
        ttk.Combobox(body, textvariable=self.mechanism_var, values=["Producer - Consumer", "Mutex"], state="readonly", width=20).grid(row=0, column=1, sticky="w", padx=8, pady=7)

        tk.Label(body, text="Sức chứa buffer", bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 10, "bold")).grid(row=0, column=2, sticky="w", pady=7)
        tk.Entry(body, textvariable=self.buffer_size_var, width=10).grid(row=0, column=3, sticky="w", padx=8, pady=7)

        speed_options = [
            "Rất chậm (2000 ms)", 
            "Chậm (1000 ms)", 
            "Trung bình (500 ms)", 
            "Nhanh (250 ms)", 
            "Rất nhanh (125 ms)"
        ]

        # --- ĐÃ THÊM width=20 VÀ ĐỔI THÀNH sticky="w" ---
        tk.Label(body, text="Tốc độ Producer", bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=7)
        ttk.Combobox(body, textvariable=self.producer_speed_var, values=speed_options, state="readonly", width=20).grid(row=1, column=1, sticky="w", padx=8, pady=7)

        tk.Label(body, text="Tốc độ Consumer", bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 10, "bold")).grid(row=1, column=2, sticky="w", pady=7)
        ttk.Combobox(body, textvariable=self.consumer_speed_var, values=speed_options, state="readonly", width=20).grid(row=1, column=3, sticky="w", padx=8, pady=7)

        btns = tk.Frame(body, bg=WHITE_COLOR)
        btns.grid(row=2, column=0, columnspan=4, sticky="w", pady=(14, 0))

        # --- GỌI HÀM MAKE_BUTTON MỚI CHỈ VỚI LỆNH VÀ TÊN ẢNH ---
        # Tham số (110, 36) là chiều ngang và chiều cao của ảnh nút bấm. 
        # Nếu nút bạn thiết kế to/nhỏ hơn, hãy tự chỉnh 2 con số này nhé!
        self.make_button(btns, self.start_simulation, "Run_Simulation", "▶ Chạy", 250, 36).pack(side="left", padx=(0, 0))
        self.make_button(btns, self.pause_simulation, "Pause", "Ⅱ Dừng", 250, 36).pack(side="left", padx=0)
        self.make_button(btns, self.reset_simulation, "Reset", "↻ Đặt lại", 220, 36).pack(side="left", padx=0)

        status = self.section(row, "TRẠNG THÁI HỆ THỐNG", "Status", "▤")
        status.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        status_body = tk.Frame(status, bg=WHITE_COLOR)
        status_body.pack(fill="both", expand=True, padx=14, pady=14)

        items = [
            ("mutex", "MUTEX", "Mở", "Mutex", "🔒", "Sẵn sàng cho truy cập"),
            ("buffer_status", "BUFFER", "Bình thường", "Buffer", "▣", "0 / 5 ô đang sử dụng"),
            ("producer", "PRODUCER", "Sẵn sàng", "Producer", "👤", "Chưa chạy"),
            ("consumer", "CONSUMER", "Sẵn sàng", "Consumer", "👤", "Chưa chạy"),
        ]

        for i, (key, title, value, icon, fallback_icon, sub_text) in enumerate(items):
            card = tk.Frame(
                status_body,
                bg=WHITE_COLOR,
                highlightbackground=BORDER_COLOR,
                highlightthickness=1
                # 1. ĐÃ XÓA: height=115 để thẻ được tự do co giãn chiều cao
            )
            card.grid(row=0, column=i, sticky="nsew", padx=5)
            status_body.columnconfigure(i, weight=1)
            # 2. ĐÃ XÓA: card.pack_propagate(False)

            img = self.load_image(icon, (32, 32))
            if img:
                tk.Label(card, image=img, bg=WHITE_COLOR).pack(pady=(12, 4))
            else:
                tk.Label(card, text=fallback_icon, bg=WHITE_COLOR, fg=PRIMARY_COLOR, font=("Arial", 22)).pack(pady=(6, 0))
                
            tk.Label(card, text=title, bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 9, "bold")).pack()

            label = tk.Label(card, text=value, bg="#DCFCE7", fg=GREEN, font=("Arial", 9, "bold"), padx=8, pady=2)
            label.pack(pady=4)
            self.status_labels[key] = label
            
            # 3. NÂNG CẤP: Thêm wraplength=95 để chữ tự động xuống dòng nếu quá dài, và tăng lề dưới (pady=10)
            sub_label = tk.Label(
                card, 
                text=sub_text, 
                bg=WHITE_COLOR, 
                fg=MUTED_TEXT, 
                font=("Arial", 8),
                wraplength=95, 
                justify="center"
            )
            sub_label.pack(pady=(0, 10))
            self.status_sublabels[key] = sub_label

    def build_buffer_and_log(self):
        row = tk.Frame(self.content, bg=BACKGROUND_COLOR)
        row.pack(fill="both", expand=True, padx=16, pady=6)
        row.columnconfigure(0, weight=7)
        row.columnconfigure(1, weight=3)

        visual = self.section(row, "TRỰC QUAN BUFFER DÙNG CHUNG", "Buffer", "▣")
        visual.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        canvas_wrap = tk.Frame(visual, bg=WHITE_COLOR)
        canvas_wrap.pack(fill="both", expand=True, padx=16, pady=12)

        self.buffer_canvas = tk.Canvas(canvas_wrap, height=210, bg=WHITE_COLOR, highlightthickness=0)
        self.buffer_scroll = ttk.Scrollbar(canvas_wrap, orient="horizontal", command=self.buffer_canvas.xview)
        
        self.buffer_canvas.configure(xscrollcommand=self.buffer_scroll.set)

        self.buffer_canvas.pack(side="top", fill="both", expand=True)
        self.buffer_scroll.pack(side="bottom", fill="x")

        log = self.section(row, "NHẬT KÝ SỰ KIỆN", "Log", "●")
        log.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.log_text = tk.Text(log, height=13, width=20, bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 10), relief=tk.FLAT)
        self.log_text.pack(fill="both", expand=True, padx=14, pady=12)
        
        self.log_text.tag_config("default", foreground=TEXT_COLOR)
        self.log_text.tag_config("green", foreground=GREEN)
        self.log_text.tag_config("purple", foreground=PURPLE)
        self.log_text.tag_config("orange", foreground=ORANGE)
        self.log_text.tag_config("blue", foreground=PRIMARY_COLOR)

    def build_stats_and_conclusion(self):
        row = tk.Frame(self.content, bg=BACKGROUND_COLOR)
        row.pack(fill="x", padx=16, pady=(6, 16))
        
        # --- 1. THU HẸP Ô NHẬN XÉT, MỞ RỘNG Ô THỐNG KÊ ---
        row.columnconfigure(0, weight=7)  # Tăng lên chiếm 70% không gian
        row.columnconfigure(1, weight=3)  # Giảm xuống chiếm 30% không gian

        stats = self.section(row, "THỐNG KÊ ĐỒNG BỘ HÓA", "Statistics", "▥")
        stats.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        stat_body = tk.Frame(stats, bg=WHITE_COLOR)
        stat_body.pack(fill="both", expand=True, padx=14, pady=12)

        self.stat_labels = {}
        
        stat_items = [
            ("producer_wait", "Producer chờ", "0 lần", PRIMARY_COLOR, "Waiting_producer"),
            ("consumer_wait", "Consumer chờ", "0 lần", PURPLE, "Waiting_consumer"),
            ("critical", "Truy cập vùng tới hạn", "0 lần", GREEN, "Critical_section_access"),
            ("events", "Tổng sự kiện", "0", ORANGE, "total_event"),
        ]

        for i, (key, title, value, color, icon_name) in enumerate(stat_items):
            card = tk.Frame(
                stat_body,
                bg=WHITE_COLOR,
                highlightbackground=BORDER_COLOR,
                highlightthickness=1
            )
            card.grid(row=0, column=i, sticky="nsew", padx=4)
            stat_body.columnconfigure(i, weight=1)

            # --- 2. TẠO LAYOUT NGANG (ICON BÊN TRÁI, TEXT BÊN PHẢI) ---
            # Cột chứa Icon được ép sang mép trái (side="left")
            icon_box = tk.Frame(card, bg=WHITE_COLOR)
            icon_box.pack(side="left", padx=(10, 6), pady=12)

            # Tăng size icon một chút để cân bằng khi đứng ngang với 2 dòng chữ
            img = self.load_image(icon_name, (34, 34))
            if img:
                tk.Label(icon_box, image=img, bg=WHITE_COLOR).pack()
            else:
                tk.Label(icon_box, text="●", fg=color, bg=WHITE_COLOR, font=("Arial", 18)).pack()

            # Cột chứa Chữ (chiếm không gian còn lại bên phải)
            text_box = tk.Frame(card, bg=WHITE_COLOR)
            text_box.pack(side="left", fill="both", expand=True, pady=12)

            # Thêm anchor="w" (West) để chữ căn sát lề trái, đẩy về phía Icon
            tk.Label(text_box, text=title, bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 2))
            
            # Thu nhỏ font size của con số một chút (từ 20 xuống 18) để tránh bị tràn thẻ
            label = tk.Label(text_box, text=value, bg=WHITE_COLOR, fg=color, font=("Arial", 18, "bold"))
            label.pack(anchor="w")

            self.stat_labels[key] = label

        conclusion = self.section(row, "NHẬN XÉT & KẾT LUẬN", "Comment", "💬")
        conclusion.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.conclusion_text = tk.Text(conclusion, height=6, bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 10), relief=tk.FLAT)
        self.conclusion_text.pack(fill="both", expand=True, padx=14, pady=12)
        self.update_conclusion()

    # =====================================================
    # SIMULATION LOGIC
    # =====================================================
    def get_delay(self):
        text = self.producer_speed_var.get()
        match = re.search(r'\d+', text)
        if match:
            return int(match.group())
        return 500

    def start_simulation(self):
        if not self.tasks:
            messagebox.showwarning(
                "Chưa có dữ liệu", 
                "Vui lòng thêm dữ liệu ở màn hình Quản lý tác vụ trước khi chạy mô phỏng đồng bộ hóa."
            )
            return

        try:
            self.max_buffer_size = max(1, int(self.buffer_size_var.get()))
        except Exception:
            self.max_buffer_size = 5
            self.buffer_size_var.set("5")

        if self.is_running:
            return

        # Nếu đã chạy xong toàn bộ tác vụ, bấm Chạy lại sẽ bắt đầu phiên mới.
        if self.tasks and self.consumed_count >= len(self.tasks):
            self.reset_simulation()

        if self.step_index == 0 or len(self.buffer) != self.max_buffer_size:
            self.buffer = [None] * self.max_buffer_size
            self.in_ptr = 0
            self.out_ptr = 0
            self.count = 0
            self.task_index = 0
            self.log_text.delete("1.0", tk.END)
            self.refresh_ui()

        self.is_running = True
        self.add_log(f"Bắt đầu đồng bộ hóa {len(self.tasks)} tác vụ gốc.", "blue")
        self.run_step()

    def pause_simulation(self):
        self.is_running = False
        self.stop_after_job()
        self.add_log("Tạm dừng mô phỏng.", "orange")

    def reset_simulation(self):
        self.pause_simulation()

        try:
            self.max_buffer_size = max(1, int(self.buffer_size_var.get()))
        except Exception:
            self.max_buffer_size = 5
            self.buffer_size_var.set("5")

        self.buffer = [None] * self.max_buffer_size
        self.count = 0
        self.in_ptr = 0
        self.out_ptr = 0

        self.task_index = 0
        self.produced_count = 0
        self.consumed_count = 0
        self.producer_wait = 0
        self.consumer_wait = 0
        self.critical_access = 0
        self.event_count = 0
        self.step_index = 0

        self.log_text.delete("1.0", tk.END)
        
        self.status_labels["mutex"].config(text="Mở", bg="#DCFCE7", fg=GREEN)
        self.status_sublabels["mutex"].config(text="Sẵn sàng cho truy cập")
        self.status_labels["producer"].config(text="Sẵn sàng", bg="#DCFCE7", fg=GREEN)
        self.status_sublabels["producer"].config(text="Chưa chạy")
        self.status_labels["consumer"].config(text="Sẵn sàng", bg="#DCFCE7", fg=GREEN)
        self.status_sublabels["consumer"].config(text="Chưa chạy")

        self.refresh_ui()

    def run_step(self):
        if not self.is_running:
            return

        self.step_index += 1

        if self.consumed_count >= len(self.tasks):
            self.is_running = False
            self.finish_simulation()
            return

        has_more_tasks = self.task_index < len(self.tasks)

        if has_more_tasks:
            is_producer = random.choice([True, True, True, False, False])
        else:
            is_producer = False

        if is_producer:
            self.producer_action()
        else:
            self.consumer_action()

        self.refresh_ui()

        self.after_id = self.after(self.get_delay(), self.run_step)

    def producer_action(self):
        p_name = random.choice(["P1", "P2"])
        
        if self.count >= self.max_buffer_size:
            self.producer_wait += 1
            self.add_log(f"🟠 Producer ({p_name}) chờ vì buffer đầy", "orange")
            self.status_labels["producer"].config(text="Đang chờ", bg="#FFEDD5", fg=ORANGE)
            self.status_sublabels["producer"].config(text=f"{p_name} bị chặn")
            return

        current_task = self.tasks[self.task_index]
        task_id = getattr(current_task, "task_id", f"T{self.task_index + 1:03d}")
        
        self.buffer[self.in_ptr] = task_id
        slot = self.in_ptr + 1
        self.in_ptr = (self.in_ptr + 1) % self.max_buffer_size
        self.count += 1
        self.produced_count += 1
        self.critical_access += 1
        
        self.task_index += 1 

        self.status_labels["mutex"].config(text="Khóa", bg="#FEE2E2", fg=RED)
        self.status_sublabels["mutex"].config(text=f"{p_name} đang ghi")
        
        self.status_labels["producer"].config(text="Hoạt động", bg="#DCFCE7", fg=GREEN)
        self.status_sublabels["producer"].config(text=f"{p_name} đang chạy")

        self.add_log(f"🟢 {p_name} nạp tác vụ {task_id} vào buffer (ô {slot})", "green")
        self.add_log(f"🔒 Mutex mở ({p_name} kết thúc truy cập)", "blue")

    def consumer_action(self):
        c_name = random.choice(["C1", "C2"])
        
        if self.count == 0:
            self.consumer_wait += 1
            self.add_log(f"🟠 Consumer ({c_name}) chờ vì buffer rỗng", "orange")
            self.status_labels["consumer"].config(text="Đang chờ", bg="#FFEDD5", fg=ORANGE)
            self.status_sublabels["consumer"].config(text=f"{c_name} bị chặn")
            return

        task_id = self.buffer[self.out_ptr]
        self.buffer[self.out_ptr] = None
        slot = self.out_ptr + 1
        self.out_ptr = (self.out_ptr + 1) % self.max_buffer_size
        self.count -= 1
        self.consumed_count += 1
        self.critical_access += 1

        self.status_labels["mutex"].config(text="Khóa", bg="#FEE2E2", fg=RED)
        self.status_sublabels["mutex"].config(text=f"{c_name} đang đọc")

        self.status_labels["consumer"].config(text="Hoạt động", bg="#DCFCE7", fg=GREEN)
        self.status_sublabels["consumer"].config(text=f"{c_name} đang chạy")

        self.add_log(f"🟣 Máy in ({c_name}) lấy tác vụ {task_id} (từ ô {slot})", "purple")
        self.add_log(f"🔒 Mutex mở ({c_name} kết thúc truy cập)", "blue")

    def add_log(self, message, color_tag="default"):
        self.event_count += 1
        now = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"{now}  ", "default")
        self.log_text.insert(tk.END, f" {message}\n", color_tag)
        self.log_text.see(tk.END)

    def refresh_ui(self):
        self.metric_labels["buffer"].config(text=str(self.max_buffer_size))
        
        total = len(self.tasks)
        self.metric_labels["produced"].config(text=f"{self.produced_count} / {total}")
        self.metric_labels["consumed"].config(text=f"{self.consumed_count} / {total}")
        self.metric_labels["deadlock"].config(text="Không")

        if self.count == 0:
            buffer_status = "Rỗng"
        elif self.count >= self.max_buffer_size:
            buffer_status = "Đầy"
        else:
            buffer_status = "Bình thường"

        if "buffer_status" in getattr(self, "status_labels", {}):
            self.status_labels["buffer_status"].config(text=buffer_status)
            if hasattr(self, "status_sublabels"):
                self.status_sublabels["buffer_status"].config(text=f"{self.count} / {self.max_buffer_size} ô đang sử dụng")

        self.stat_labels["producer_wait"].config(text=f"{self.producer_wait} lần")
        self.stat_labels["consumer_wait"].config(text=f"{self.consumer_wait} lần")
        self.stat_labels["critical"].config(text=f"{self.critical_access} lần")
        self.stat_labels["events"].config(text=str(self.event_count))

        self.draw_buffer()

    def draw_buffer(self):
        self.buffer_canvas.delete("all")

        start_x = 230
        y = 85
        slot_w = 86
        slot_h = 62
        gap = 12

        self.buffer_canvas.create_text(90, 60, text="PRODUCER", fill=PRIMARY_COLOR, font=("Arial", 12, "bold"))
        
        # --- DRAW PRODUCER IMAGES ---
        p_img = self.load_image("Produced", (32, 32))
        if p_img:
            self.buffer_canvas.create_image(115, 110, image=p_img)
            self.buffer_canvas.create_text(70, 110, text="P1", fill=PRIMARY_COLOR, font=("Arial", 16, "bold"))
            self.buffer_canvas.create_image(115, 155, image=p_img)
            self.buffer_canvas.create_text(70, 155, text="P2", fill=PRIMARY_COLOR, font=("Arial", 16, "bold"))
        else:
            self.buffer_canvas.create_text(90, 110, text="P1 👤", fill=PRIMARY_COLOR, font=("Arial", 16, "bold"))
            self.buffer_canvas.create_text(90, 155, text="P2 👤", fill=PRIMARY_COLOR, font=("Arial", 16, "bold"))

        self.buffer_canvas.create_line(140, 110, start_x - 20, 110, arrow=tk.LAST, fill=PRIMARY_COLOR, width=2)
        self.buffer_canvas.create_line(140, 155, start_x - 20, 130, arrow=tk.LAST, fill=PRIMARY_COLOR, width=2)

        self.buffer_canvas.create_text(
            start_x + (slot_w + gap) * self.max_buffer_size / 2 - 20,
            48,
            text=f"BUFFER (SỨC CHỨA: {self.max_buffer_size})",
            fill=PRIMARY_COLOR,
            font=("Arial", 12, "bold")
        )

        for i in range(self.max_buffer_size):
            x = start_x + i * (slot_w + gap)
            value = self.buffer[i] if (hasattr(self, 'buffer') and i < len(self.buffer) and self.buffer[i] is not None) else "—"
            
            if value != "—":
                self.buffer_canvas.create_rectangle(x, y, x + slot_w, y + slot_h, fill="#FEF3C7", outline="#F59E0B", width=2)
                self.buffer_canvas.create_text(x + slot_w / 2, y + slot_h / 2, text=value, fill=TEXT_COLOR, font=("Arial", 12, "bold"))
            else:
                self.buffer_canvas.create_rectangle(x, y, x + slot_w, y + slot_h, fill="#F8FAFC", outline="#CBD5E1", width=1, dash=(4,4))
                self.buffer_canvas.create_text(x + slot_w / 2, y + slot_h / 2, text="—", fill="#CBD5E1", font=("Arial", 12, "bold"))
                
            self.buffer_canvas.create_text(x + slot_w / 2, y + slot_h + 24, text=str(i + 1), fill=TEXT_COLOR, font=("Arial", 10, "bold"))

        consumer_x = start_x + self.max_buffer_size * (slot_w + gap) + 40
        self.buffer_canvas.create_text(consumer_x + 60, 60, text="CONSUMER", fill=PRIMARY_COLOR, font=("Arial", 12, "bold"))
        
        # --- DRAW CONSUMER IMAGES ---
        c_img = self.load_image("Consumed", (32, 32))
        if c_img:
            self.buffer_canvas.create_image(consumer_x + 25, 110, image=c_img)
            self.buffer_canvas.create_text(consumer_x + 75, 110, text="C1", fill=PURPLE, font=("Arial", 16, "bold"))
            self.buffer_canvas.create_image(consumer_x + 25, 155, image=c_img)
            self.buffer_canvas.create_text(consumer_x + 75, 155, text="C2", fill=PURPLE, font=("Arial", 16, "bold"))
        else:
            self.buffer_canvas.create_text(consumer_x + 60, 110, text="👤 C1", fill=PURPLE, font=("Arial", 16, "bold"))
            self.buffer_canvas.create_text(consumer_x + 60, 155, text="👤 C2", fill=PURPLE, font=("Arial", 16, "bold"))

        self.buffer_canvas.create_line(consumer_x, 110, consumer_x - 60, 110, arrow=tk.LAST, fill=PRIMARY_COLOR, width=2)
        self.buffer_canvas.create_line(consumer_x, 155, consumer_x - 60, 130, arrow=tk.LAST, fill=PRIMARY_COLOR, width=2)

        legend_y = 195
        self.buffer_canvas.create_rectangle(start_x, legend_y, start_x + 16, legend_y + 16, fill="#FEF3C7", outline="#F59E0B", width=1)
        self.buffer_canvas.create_text(start_x + 24, legend_y + 8, anchor="w", text="Ô đã có tác vụ", fill=TEXT_COLOR, font=("Arial", 9))
        
        self.buffer_canvas.create_rectangle(start_x + 130, legend_y, start_x + 146, legend_y + 16, fill="#F8FAFC", outline="#CBD5E1", width=1, dash=(2,2))
        self.buffer_canvas.create_text(start_x + 154, legend_y + 8, anchor="w", text="Ô trống", fill=TEXT_COLOR, font=("Arial", 9))

        max_x = consumer_x + 150
        
        self.buffer_canvas.configure(scrollregion=(0, 0, max_x, 230))

    def update_conclusion(self):
        text = (
            "✓ Hệ thống hoạt động đúng cơ chế Producer - Consumer với Mutex.\n"
            "✓ Không xảy ra deadlock trong quá trình xử lý chuỗi tác vụ thực tế.\n"
            "✓ Buffer được quản lý đúng kích thước, không ghi đè và không tràn.\n"
            "✓ Đồng bộ hóa đảm bảo truy cập vùng tới hạn an toàn và hiệu quả."
        )

        self.conclusion_text.delete("1.0", tk.END)
        self.conclusion_text.insert(tk.END, text)

    def finish_simulation(self):
        self.add_log("Mô phỏng hoàn tất (Đã xử lý xong toàn bộ danh sách tác vụ).", "blue")

        self.status_labels["producer"].config(text="Hoàn thành", bg="#DCFCE7", fg=GREEN)
        self.status_sublabels["producer"].config(text="Không còn tác vụ nạp")
        self.status_labels["consumer"].config(text="Hoàn thành", bg="#DCFCE7", fg=GREEN)
        self.status_sublabels["consumer"].config(text="Đã xử lý hết buffer")

        payload = {
            "mechanism": self.mechanism_var.get(),
            "buffer_size": self.max_buffer_size,
            "produced_count": self.produced_count,
            "consumed_count": self.consumed_count,
            "producer_wait": self.producer_wait,
            "consumer_wait": self.consumer_wait,
            "critical_access": self.critical_access,
            "event_count": self.event_count,
            "deadlock": False,
            "status": "Ổn định"
        }

        if callable(self.on_sync_finished):
            self.on_sync_finished(payload)