import tkinter as tk
from tkinter import ttk
from datetime import datetime

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


class ReportFrame(tk.Frame):
    def __init__(self, parent, tasks=None, payload=None, controller=None):
        super().__init__(parent, bg=BACKGROUND_COLOR)

        self.controller = controller
        self.tasks = tasks or []
        self.payload = payload or {}

        self.cpu_payload = self.extract_module_payload("cpu")
        self.memory_payload = self.extract_module_payload("memory")
        self.sync_payload = self.extract_module_payload("sync")

        self.metric_labels = {}

        self.build_ui()
        self.refresh_report()

    # =====================================================
    # PAYLOAD HELPERS
    # =====================================================
    def extract_module_payload(self, key):
        """Lấy payload theo từng module nhưng vẫn tương thích bản app cũ.

        - App mới truyền dạng {"cpu": ..., "memory": ..., "sync": ...}.
        - Một số bản cũ truyền thẳng payload từ SimulationFrame, có result_map/results.
        """
        if not isinstance(self.payload, dict) or not self.payload:
            return {}

        # Payload tổng hợp từ app.py hiện tại
        if key in self.payload:
            return self.payload.get(key) or {}

        # Tương thích bản cũ: payload truyền trực tiếp từ SimulationFrame
        if key == "cpu" and any(name in self.payload for name in ("result_map", "results", "preferred_result")):
            return self.payload

        return {}

    def get_value(self, obj, names, default=None):
        if obj is None:
            return default

        if isinstance(obj, dict):
            for name in names:
                if name in obj:
                    return obj[name]

        for name in names:
            if hasattr(obj, name):
                return getattr(obj, name)

        return default

    def get_cpu_results(self):
        payload = self.cpu_payload or {}

        result_map = payload.get("result_map") if isinstance(payload, dict) else None
        if isinstance(result_map, dict) and result_map:
            return list(result_map.values())

        results = payload.get("results") if isinstance(payload, dict) else None
        if isinstance(results, list):
            return results

        preferred = payload.get("preferred_result") if isinstance(payload, dict) else None
        if preferred:
            return [preferred]

        return []

    def get_best_cpu_result(self):
        results = self.get_cpu_results()
        if not results:
            return None

        return min(
            results,
            key=lambda result: self.get_value(result, ["average_waiting_time"], 999999)
        )

    def get_algorithm_name(self, result):
        return self.get_value(result, ["algorithm_name"], "Chưa có")

    def get_avg_waiting(self, result):
        return self.get_value(result, ["average_waiting_time"], 0)

    def get_avg_turnaround(self, result):
        return self.get_value(result, ["average_turnaround_time"], 0)

    def get_avg_response(self, result):
        return self.get_value(result, ["average_response_time"], 0)

    # =====================================================
    # UI HELPERS
    # =====================================================
    def section(self, parent, title, icon="▣"):
        box = tk.Frame(
            parent,
            bg=WHITE_COLOR,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )

        head = tk.Frame(box, bg=WHITE_COLOR)
        head.pack(fill="x")

        tk.Label(
            head,
            text=icon,
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 13, "bold")
        ).pack(side="left", padx=(14, 8), pady=10)

        tk.Label(
            head,
            text=title,
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 12, "bold")
        ).pack(side="left", pady=10)

        tk.Frame(box, bg=BORDER_COLOR, height=1).pack(fill="x")
        return box

    def make_kpi(self, parent, key, title, value, icon, col, color=PRIMARY_COLOR):
        card = tk.Frame(
            parent,
            bg=WHITE_COLOR,
            height=150,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        card.grid(row=0, column=col, sticky="nsew", padx=5)
        card.pack_propagate(False)

        tk.Label(
            card,
            text=icon,
            bg=color,
            fg=WHITE_COLOR,
            font=("Arial", 20, "bold"),
            width=3,
            height=2
        ).pack(pady=(14, 6))

        tk.Label(
            card,
            text=title,
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 9, "bold"),
            justify="center"
        ).pack()

        value_label = tk.Label(
            card,
            text=value,
            bg=WHITE_COLOR,
            fg=color,
            font=("Arial", 22, "bold")
        )
        value_label.pack(pady=(4, 0))

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

        self.build_title()
        self.build_overview_and_kpi()
        self.build_cpu_and_memory()
        self.build_sync_and_conclusion()

    def build_title(self):
        top = tk.Frame(self.content, bg=BACKGROUND_COLOR)
        top.pack(fill="x", padx=16, pady=(0, 10))

        tk.Label(
            top,
            text="BÁO CÁO TỔNG HỢP HỆ THỐNG",
            bg=BACKGROUND_COLOR,
            fg=DARK_BLUE,
            font=("Arial", 20, "bold")
        ).pack(anchor="center")

        tk.Label(
            top,
            text="Đánh giá lập lịch CPU, cấp phát bộ nhớ và đồng bộ hóa tiến trình",
            bg=BACKGROUND_COLOR,
            fg=ACCENT_COLOR,
            font=("Arial", 11, "bold")
        ).pack(anchor="center", pady=(2, 0))

    def build_overview_and_kpi(self):
        row = tk.Frame(self.content, bg=BACKGROUND_COLOR)
        row.pack(fill="x", padx=16, pady=6)
        row.columnconfigure(0, weight=4)
        row.columnconfigure(1, weight=6)
        row.columnconfigure(2, weight=3)

        overview = self.section(row, "A. TỔNG QUAN MÔ PHỎNG", "ⓘ")
        overview.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        body = tk.Frame(overview, bg=WHITE_COLOR)
        body.pack(fill="both", expand=True, padx=16, pady=14)

        self.overview_labels = {}

        rows = [
            ("model", "Mô hình:", "Một máy xử lý chung"),
            ("tasks", "Số tác vụ:", "0"),
            ("modules", "Module đã chạy:", "Lập lịch CPU, Cấp phát bộ nhớ, Đồng bộ hóa"),
            ("data", "Dữ liệu:", "Dữ liệu mô phỏng hiện tại"),
            ("note", "Ghi chú:", "Báo cáo tổng hợp dựa trên kết quả mô phỏng mới nhất."),
        ]

        for i, (key, label, value) in enumerate(rows):
            tk.Label(
                body,
                text=label,
                bg=WHITE_COLOR,
                fg=TEXT_COLOR,
                font=("Arial", 10, "bold")
            ).grid(row=i, column=0, sticky="w", pady=7)

            value_label = tk.Label(
                body,
                text=value,
                bg=WHITE_COLOR,
                fg=TEXT_COLOR,
                font=("Arial", 10),
                wraplength=280,
                justify="left"
            )
            value_label.grid(row=i, column=1, sticky="w", padx=18, pady=7)
            self.overview_labels[key] = value_label

        kpi = self.section(row, "B. KẾT QUẢ HIỆU NĂNG CHÍNH", "▥")
        kpi.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        kpi_body = tk.Frame(kpi, bg=WHITE_COLOR)
        kpi_body.pack(fill="both", expand=True, padx=12, pady=14)

        for i in range(6):
            kpi_body.columnconfigure(i, weight=1)

        self.make_kpi(kpi_body, "total_tasks", "Tổng tác vụ", "0", "▤", 0)
        self.make_kpi(kpi_body, "best_cpu", "Thuật toán CPU\nđề xuất", "---", "🏆", 1)
        self.make_kpi(kpi_body, "memory_usage", "Hiệu suất\nbộ nhớ", "---", "▣", 2, GREEN)
        self.make_kpi(kpi_body, "deadlock", "Deadlock", "Không", "!", 3, GREEN)
        self.make_kpi(kpi_body, "best_wait", "Avg Waiting\ntốt nhất", "---", "◷", 4)
        self.make_kpi(kpi_body, "cpu_util", "CPU\nUtilization", "---", "▣", 5)

        system = self.section(row, "TỔNG QUAN HỆ THỐNG", "◉")
        system.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        self.chart_canvas = tk.Canvas(
            system,
            width=230,
            height=220,
            bg=WHITE_COLOR,
            highlightthickness=0
        )
        self.chart_canvas.pack(pady=(10, 4))

        self.system_legend_frame = tk.Frame(system, bg=WHITE_COLOR)
        self.system_legend_frame.pack(pady=(0, 10), anchor="center")

        self.draw_system_chart()

    def get_module_statuses(self):
        cpu_done = bool(self.get_cpu_results())
        memory_done = bool(self.memory_payload)
        sync_done = bool(self.sync_payload)

        return [
            ("Lập lịch CPU", cpu_done, "#0B63CE"),
            ("Cấp phát bộ nhớ", memory_done, "#16A34A"),
            ("Đồng bộ hóa", sync_done, "#F97316"),
        ]

    def draw_system_chart(self):
        if not hasattr(self, "chart_canvas"):
            return

        canvas = self.chart_canvas
        canvas.delete("all")

        data = self.get_module_statuses()
        completed = sum(1 for _, done, _ in data if done)
        overall_percent = round(completed / len(data) * 100) if data else 0

        # Nền donut
        canvas.create_oval(
            25, 18, 205, 198,
            fill="#F1F5F9",
            outline="#E2E8F0"
        )

        start = -90
        segment_extent = 360 / max(1, len(data))
        for _name, done, color in data:
            if done:
                canvas.create_arc(
                    25, 18, 205, 198,
                    start=start,
                    extent=segment_extent,
                    fill=color,
                    outline=WHITE_COLOR,
                    width=2
                )
            start += segment_extent

        # Lỗ giữa
        canvas.create_oval(
            72, 65, 158, 151,
            fill=WHITE_COLOR,
            outline=WHITE_COLOR
        )

        canvas.create_text(
            115, 96,
            text=f"{overall_percent}%",
            font=("Arial", 18, "bold"),
            fill=TEXT_COLOR
        )

        canvas.create_text(
            115, 121,
            text="Hoàn thành" if overall_percent == 100 else "Đã chạy",
            font=("Arial", 9),
            fill=MUTED_TEXT
        )

        self.refresh_system_legend(data)

    def refresh_system_legend(self, data=None):
        if not hasattr(self, "system_legend_frame"):
            return

        for widget in self.system_legend_frame.winfo_children():
            widget.destroy()

        data = data or self.get_module_statuses()
        for name, done, color in data:
            row = tk.Frame(self.system_legend_frame, bg=WHITE_COLOR)
            row.pack(anchor="w", pady=2)

            tk.Label(
                row,
                text="●",
                fg=color if done else "#CBD5E1",
                bg=WHITE_COLOR,
                font=("Arial", 12, "bold")
            ).pack(side="left")

            tk.Label(
                row,
                text=name,
                fg=TEXT_COLOR,
                bg=WHITE_COLOR,
                font=("Arial", 9)
            ).pack(side="left", padx=5)

            tk.Label(
                row,
                text="100%" if done else "0%",
                fg=TEXT_COLOR if done else MUTED_TEXT,
                bg=WHITE_COLOR,
                font=("Arial", 9, "bold")
            ).pack(side="right", padx=10)

    def build_cpu_and_memory(self):
        row = tk.Frame(self.content, bg=BACKGROUND_COLOR)
        row.pack(fill="both", expand=True, padx=16, pady=6)
        row.columnconfigure(0, weight=5)
        row.columnconfigure(1, weight=5)

        cpu = self.section(row, "C. TÓM TẮT LẬP LỊCH CPU", "▥")
        cpu.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.cpu_tree = ttk.Treeview(
            cpu,
            columns=("rank", "algo", "wait", "turn", "resp", "note"),
            show="headings",
            height=6
        )

        columns = {
            "rank": "Xếp hạng",
            "algo": "Thuật toán",
            "wait": "Avg Waiting",
            "turn": "Avg Turnaround",
            "resp": "Avg Response",
            "note": "Nhận xét ngắn"
        }

        for col, title in columns.items():
            self.cpu_tree.heading(col, text=title)
            self.cpu_tree.column(col, anchor="center", width=110)

        self.cpu_tree.pack(fill="both", expand=True, padx=14, pady=12)

        self.cpu_note = tk.Label(
            cpu,
            text="Chưa có kết quả lập lịch CPU.",
            bg="#EAF4FF",
            fg=PRIMARY_COLOR,
            font=("Arial", 9, "italic"),
            anchor="w",
            padx=10,
            pady=8
        )
        self.cpu_note.pack(fill="x", padx=14, pady=(0, 12))

        memory = self.section(row, "D. KẾT QUẢ CẤP PHÁT BỘ NHỚ", "▦")
        memory.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.memory_tree = ttk.Treeview(
            memory,
            columns=("algo", "success", "usage", "fragment", "note"),
            show="headings",
            height=6
        )

        mem_columns = {
            "algo": "Thuật toán",
            "success": "Thành công",
            "usage": "Hiệu suất",
            "fragment": "Phân mảnh",
            "note": "Khuyến nghị"
        }

        for col, title in mem_columns.items():
            self.memory_tree.heading(col, text=title)
            self.memory_tree.column(col, anchor="center", width=120)

        self.memory_tree.pack(fill="both", expand=True, padx=14, pady=12)

        self.memory_note = tk.Label(
            memory,
            text="Chưa có kết quả cấp phát bộ nhớ.",
            bg="#EAF4FF",
            fg=PRIMARY_COLOR,
            font=("Arial", 9, "italic"),
            anchor="w",
            padx=10,
            pady=8
        )
        self.memory_note.pack(fill="x", padx=14, pady=(0, 12))

    def build_sync_and_conclusion(self):
        row = tk.Frame(self.content, bg=BACKGROUND_COLOR)
        row.pack(fill="x", padx=16, pady=(6, 16))
        row.columnconfigure(0, weight=4)
        row.columnconfigure(1, weight=6)

        sync = self.section(row, "E. KẾT QUẢ ĐỒNG BỘ HÓA", "●")
        sync.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        sync_body = tk.Frame(sync, bg=WHITE_COLOR)
        sync_body.pack(fill="both", expand=True, padx=14, pady=12)

        self.sync_labels = {}

        items = [
            ("mechanism", "Cơ chế", "---"),
            ("buffer", "Dung lượng buffer", "---"),
            ("producer_wait", "Producer chờ", "---"),
            ("consumer_wait", "Consumer chờ", "---"),
            ("deadlock", "Deadlock", "Không"),
            ("status", "Trạng thái", "---"),
        ]

        for i, (key, title, value) in enumerate(items):
            card = tk.Frame(
                sync_body,
                bg=WHITE_COLOR,
                highlightbackground=BORDER_COLOR,
                highlightthickness=1
            )
            card.grid(row=i // 3, column=i % 3, sticky="nsew", padx=5, pady=5)
            sync_body.columnconfigure(i % 3, weight=1)

            tk.Label(card, text=title, bg=WHITE_COLOR, fg=TEXT_COLOR, font=("Arial", 9, "bold")).pack(pady=(10, 0))
            label = tk.Label(card, text=value, bg=WHITE_COLOR, fg=PRIMARY_COLOR, font=("Arial", 15, "bold"))
            label.pack(pady=(2, 10))

            self.sync_labels[key] = label

        conclusion = self.section(row, "F. KẾT LUẬN & HƯỚNG PHÁT TRIỂN", "✓")
        conclusion.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.conclusion_text = tk.Text(
            conclusion,
            height=11,
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 10),
            relief=tk.FLAT,
            wrap="word"
        )
        self.conclusion_text.pack(fill="both", expand=True, padx=14, pady=12)

    # =====================================================
    # REFRESH DATA
    # =====================================================
    def refresh_report(self, tasks=None, payload=None):
        if tasks is not None:
            self.tasks = tasks

        if payload is not None:
            self.payload = payload or {}

        self.cpu_payload = self.extract_module_payload("cpu")
        self.memory_payload = self.extract_module_payload("memory")
        self.sync_payload = self.extract_module_payload("sync")

        self.refresh_overview()
        self.refresh_kpi()
        self.refresh_cpu_summary()
        self.refresh_memory_summary()
        self.refresh_sync_summary()
        self.refresh_conclusion()

    def refresh_overview(self):
        self.overview_labels["tasks"].config(text=str(len(self.tasks)))
        self.overview_labels["modules"].config(text="Lập lịch CPU, Cấp phát bộ nhớ, Đồng bộ hóa")
        self.overview_labels["note"].config(text="Báo cáo tổng hợp dùng để đánh giá kết quả cuối cùng, không lặp lại Gantt hoặc bảng tác vụ chi tiết.")

    def refresh_kpi(self):
        best_cpu = self.get_best_cpu_result()
        cpu_name = self.get_algorithm_name(best_cpu) if best_cpu else "---"
        best_wait = self.get_avg_waiting(best_cpu) if best_cpu else "---"

        memory_usage = self.get_value(self.memory_payload, ["usage"], None)
        if memory_usage is None:
            memory_usage = self.get_value(self.memory_payload, ["memory_usage"], "---")

        deadlock = self.get_value(self.sync_payload, ["deadlock"], False)
        deadlock_text = "Có" if deadlock else "Không"

        cpu_util = self.calculate_cpu_utilization(best_cpu)

        self.metric_labels["total_tasks"].config(text=str(len(self.tasks)))
        self.metric_labels["best_cpu"].config(text=cpu_name)
        self.metric_labels["memory_usage"].config(text=f"{memory_usage}%" if isinstance(memory_usage, (int, float)) else str(memory_usage))
        self.metric_labels["deadlock"].config(text=deadlock_text)
        self.metric_labels["best_wait"].config(text=f"{best_wait}" if best_wait != "---" else "---")
        self.metric_labels["cpu_util"].config(text=f"{cpu_util}%" if cpu_util is not None else "---")
        self.draw_system_chart()

    def calculate_cpu_utilization(self, result):
        if result is None:
            return None

        tasks = self.get_value(result, ["tasks"], [])
        gantt = self.get_value(result, ["gantt_chart"], [])

        if not gantt:
            return None

        start = min(self.get_value(block, ["start_time"], 0) for block in gantt)
        end = max(self.get_value(block, ["end_time"], 0) for block in gantt)

        total = end - start
        if total <= 0:
            return None

        busy = 0
        for block in gantt:
            task_id = self.get_value(block, ["task_id"], "")
            if str(task_id).upper() != "IDLE":
                busy += self.get_value(block, ["end_time"], 0) - self.get_value(block, ["start_time"], 0)

        return round(busy / total * 100, 1)

    def refresh_cpu_summary(self):
        for item in self.cpu_tree.get_children():
            self.cpu_tree.delete(item)

        results = self.get_cpu_results()

        if not results:
            self.cpu_note.config(text="Chưa có kết quả lập lịch CPU. Hãy chạy mô phỏng trước khi xem báo cáo.")
            return

        sorted_results = sorted(results, key=lambda result: self.get_avg_waiting(result))

        for index, result in enumerate(sorted_results, start=1):
            algo = self.get_algorithm_name(result)
            note = self.get_cpu_note(algo, index)

            self.cpu_tree.insert(
                "",
                "end",
                values=(
                    index,
                    algo,
                    self.get_avg_waiting(result),
                    self.get_avg_turnaround(result),
                    self.get_avg_response(result),
                    note
                )
            )

        best = sorted_results[0]
        self.cpu_note.config(
            text=f"{self.get_algorithm_name(best)} cho kết quả tốt nhất theo Avg Waiting trong bộ dữ liệu hiện tại."
        )

    def get_cpu_note(self, algo, rank):
        lower = str(algo).lower()

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

    def refresh_memory_summary(self):
        for item in self.memory_tree.get_children():
            self.memory_tree.delete(item)

        compare = self.get_value(self.memory_payload, ["compare_results"], None)

        if isinstance(compare, dict) and compare:
            rows = []
            for algo, data in compare.items():
                rows.append({
                    "algorithm": algo,
                    "success": self.get_value(data, ["success"], 0),
                    "usage": self.get_value(data, ["usage"], 0),
                    "fragmentation": self.get_value(data, ["fragmentation"], 0)
                })
        elif self.memory_payload:
            rows = [{
                "algorithm": self.get_value(self.memory_payload, ["algorithm"], "Đã chạy"),
                "success": self.get_value(self.memory_payload, ["success"], 0),
                "usage": self.get_value(self.memory_payload, ["usage"], 0),
                "fragmentation": self.get_value(self.memory_payload, ["fragmentation"], 0)
            }]
        else:
            rows = []

        if not rows:
            self.memory_note.config(text="Chưa có kết quả cấp phát bộ nhớ.")
            return

        best = max(rows, key=lambda row: row["usage"])

        for row in rows:
            note = "Khuyến nghị" if row is best else ""
            self.memory_tree.insert(
                "",
                "end",
                values=(
                    row["algorithm"],
                    row["success"],
                    f"{row['usage']}%",
                    f"{row['fragmentation']}%",
                    note
                )
            )

        self.memory_note.config(
            text=f"{best['algorithm']} có hiệu suất sử dụng bộ nhớ cao nhất trong bộ dữ liệu hiện tại."
        )

    def refresh_sync_summary(self):
        payload = self.sync_payload or {}

        self.sync_labels["mechanism"].config(text=self.get_value(payload, ["mechanism"], "---"))
        self.sync_labels["buffer"].config(text=self.get_value(payload, ["buffer_size"], "---"))
        self.sync_labels["producer_wait"].config(text=f"{self.get_value(payload, ['producer_wait'], 0)} lần")
        self.sync_labels["consumer_wait"].config(text=f"{self.get_value(payload, ['consumer_wait'], 0)} lần")

        deadlock = self.get_value(payload, ["deadlock"], False)
        self.sync_labels["deadlock"].config(text="Có" if deadlock else "Không", fg=RED if deadlock else GREEN)

        self.sync_labels["status"].config(text=self.get_value(payload, ["status"], "Ổn định" if payload else "---"))

    def refresh_conclusion(self):
        best_cpu = self.get_best_cpu_result()
        best_cpu_name = self.get_algorithm_name(best_cpu) if best_cpu else "chưa có dữ liệu"

        memory_algo = self.get_value(self.memory_payload, ["algorithm"], "chưa có dữ liệu")
        memory_usage = self.get_value(self.memory_payload, ["usage"], "---")

        deadlock = self.get_value(self.sync_payload, ["deadlock"], False)
        sync_status = "không xảy ra deadlock" if not deadlock else "có dấu hiệu deadlock"

        text = (
            f"✓ Thuật toán CPU đề xuất: {best_cpu_name}. "
            "Kết quả được chọn dựa trên Avg Waiting Time thấp nhất trong các thuật toán đã chạy.\n\n"
            f"✓ Cấp phát bộ nhớ: thuật toán {memory_algo} đạt hiệu suất {memory_usage}% trong phiên mô phỏng hiện tại.\n\n"
            f"✓ Đồng bộ hóa: hệ thống {sync_status}, buffer được kiểm soát bằng cơ chế Producer - Consumer/Mutex.\n\n"
            "✓ Hạn chế hiện tại: mô hình đang giả định một máy xử lý chung, chưa mô phỏng nhiều máy in, máy scan hoặc nhiều CPU chạy song song.\n\n"
            "✓ Hướng phát triển: bổ sung mô hình nhiều máy, thuật toán quản lý bộ nhớ nâng cao như phân trang/thay thế trang, "
            "và các bài toán đồng bộ hóa phức tạp hơn như deadlock hoặc dining philosophers."
        )

        self.conclusion_text.delete("1.0", tk.END)
        self.conclusion_text.insert(tk.END, text)