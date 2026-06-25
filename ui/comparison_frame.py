import copy
import os
import tkinter as tk
from tkinter import ttk, messagebox

from algorithms import run_fcfs, run_sjf, run_priority, run_round_robin
from models import Task

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False

from ui.icon_utils import load_icon, resolve_icon_path as shared_resolve_icon_path, normalize_icon_name as shared_normalize_icon_name

try:
    from utils.constants import DEFAULT_TIME_QUANTUM
except Exception:
    DEFAULT_TIME_QUANTUM = 2


PRIMARY_COLOR = "#005BAC"
SECONDARY_COLOR = "#EAF4FF"
ACCENT_COLOR = "#D71920"
BACKGROUND_COLOR = "#F4F7FB"
WHITE_COLOR = "#FFFFFF"
TEXT_COLOR = "#1F2937"
BORDER_COLOR = "#D9E2EC"
GREEN = "#16A34A"
ORANGE = "#F97316"
MUTED_TEXT = "#64748B"

EVENT_STEP_MS = 450


class ComparisonFrame(tk.Frame):
    def __init__(self, parent, tasks):
        super().__init__(parent, bg=BACKGROUND_COLOR)

        self.tasks = tasks or []
        self.results = []
        self.images = {}

        self.current_time = 0
        self.max_time = 0
        self.timeline_points = [0]
        self.timeline_index = 0
        self.after_id = None
        self.is_running = False
        self.is_visible = True
        self.is_finished = False
        self.external_source = False
        self.last_external_payload = None

        self.icon_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "utils",
            "icons"
        )

        self.colors = {
            "FCFS": "#0B63CE",
            "SJF": GREEN,
            "Priority": "#F97316",
            "Round Robin": "#7C3AED"
        }

        self.configure_styles()

        self.canvas = tk.Canvas(self, bg=BACKGROUND_COLOR, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=BACKGROUND_COLOR)

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scroll_frame,
            anchor="nw"
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scroll_frame.bind(
            "<Configure>",
            lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(self.canvas_window, width=event.width)
        )

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.create_widgets()
        self.show_empty_state()

        self.canvas.bind_all(
            "<MouseWheel>",
            lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        )

        self.bind("<Destroy>", self._on_destroy, add="+")

    # =====================================================
    # PAGE LIFECYCLE
    # =====================================================
    def on_page_hide(self):
        self.is_visible = False

    def on_page_show(self):
        self.is_visible = True
        if self.results:
            self.refresh_realtime_comparison(force=True)

    def _on_destroy(self, event):
        if event.widget is self:
            self.stop_after_job()

    # =====================================================
    # UI
    # =====================================================
    def configure_styles(self):
        style = ttk.Style()
        style.configure(
            "Treeview",
            font=("Arial", 10),
            rowheight=44,
            background=WHITE_COLOR,
            fieldbackground=WHITE_COLOR
        )
        style.configure(
            "Treeview.Heading",
            font=("Arial", 10, "bold"),
            background="#F8FAFC",
            foreground=TEXT_COLOR
        )
        style.map(
            "Treeview",
            background=[("selected", "#DCFCE7")],
            foreground=[("selected", TEXT_COLOR)]
        )

    def section(self, parent, title):
        box = tk.Frame(
            parent,
            bg=WHITE_COLOR,
            highlightbackground="#E2E8F0",
            highlightthickness=1
        )

        head = tk.Frame(box, bg=WHITE_COLOR)
        head.pack(fill=tk.X)

        tk.Label(
            head,
            text="▣",
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 12, "bold")
        ).pack(side=tk.LEFT, padx=(16, 8), pady=10)

        tk.Label(
            head,
            text=title,
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 12, "bold")
        ).pack(side=tk.LEFT, pady=10)

        tk.Frame(box, bg="#E2E8F0", height=1).pack(fill=tk.X)

        return box

    def load_card_icon(self, filename, size=(42, 42)):
        if not filename or not PIL_AVAILABLE:
            return None

        path = os.path.join(self.icon_dir, filename)

        if not os.path.exists(path):
            print("Không tìm thấy icon card:", path)
            return None

        try:
            img = Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.images[f"{filename}_{size}"] = photo
            return photo
        except Exception as error:
            print("Lỗi load icon card:", filename, error)
            return None

    def stat(self, parent, title, value, icon, col):
        f = tk.Frame(
            parent,
            bg=WHITE_COLOR,
            highlightbackground="#E2E8F0",
            highlightthickness=1
        )

        f.grid(row=0, column=col, sticky="nsew", padx=7, pady=5)

        icon_box = tk.Frame(f, bg=PRIMARY_COLOR, width=64, height=64)
        icon_box.pack(side=tk.LEFT, padx=18, pady=14)
        icon_box.pack_propagate(False)

        icon_photo = self.load_card_icon(icon, (44, 44))

        if icon_photo:
            tk.Label(icon_box, image=icon_photo, bg=PRIMARY_COLOR).pack(expand=True)
        else:
            tk.Label(
                icon_box,
                text=icon,
                bg=PRIMARY_COLOR,
                fg=WHITE_COLOR,
                font=("Arial", 24, "bold")
            ).pack(expand=True)

        r = tk.Frame(f, bg=WHITE_COLOR)
        r.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, pady=12)

        tk.Label(
            r,
            text=title.upper(),
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 9, "bold")
        ).pack()

        label = tk.Label(
            r,
            text=value,
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 27, "bold")
        )
        label.pack()

        tk.Frame(r, bg=ACCENT_COLOR, height=2, width=28).pack()

        return label

    def create_widgets(self):
        top = tk.Frame(self.scroll_frame, bg=BACKGROUND_COLOR)
        top.pack(fill=tk.X)

        for i in range(4):
            top.grid_columnconfigure(i, weight=1)

        self.best_algorithm_label = self.stat(
            top,
            "Thuật toán tốt nhất",
            "---",
            "Best_Algorithm.png",
            0
        )

        self.total_algorithm_label = self.stat(
            top,
            "Số thuật toán so sánh",
            "4",
            "Comparison_Algorithm.png",
            1
        )

        self.best_waiting_label = self.stat(
            top,
            "Avg Waiting thấp nhất",
            "0.00",
            "AVG_Waiting.png",
            2
        )

        self.best_turnaround_label = self.stat(
            top,
            "Avg Turnaround thấp nhất",
            "0.00",
            "AVG_Turnaround.png",
            3
        )

        control = self.section(self.scroll_frame, "ĐIỀU KHIỂN SO SÁNH REALTIME")
        control.pack(fill=tk.X, padx=8, pady=8)

        control_body = tk.Frame(control, bg=WHITE_COLOR)
        control_body.pack(fill=tk.X, padx=14, pady=10)

        self.status_label = tk.Label(
            control_body,
            text="● Sẵn sàng so sánh",
            bg=WHITE_COLOR,
            fg=MUTED_TEXT,
            font=("Arial", 11, "bold")
        )
        self.status_label.pack(side=tk.LEFT, padx=(0, 16))

        self.time_label = tk.Label(
            control_body,
            text="Thời gian: 0 / 0",
            bg=WHITE_COLOR,
            fg=PRIMARY_COLOR,
            font=("Arial", 11, "bold")
        )
        self.time_label.pack(side=tk.LEFT, padx=(0, 16))

        self.run_button = tk.Button(
            control_body,
            text="▶ Chạy so sánh",
            bg=GREEN,
            fg=WHITE_COLOR,
            relief=tk.FLAT,
            font=("Arial", 10, "bold"),
            command=self.compare_algorithms
        )
        self.run_button.pack(side=tk.LEFT, padx=5, ipadx=8, ipady=4)

        self.pause_button = tk.Button(
            control_body,
            text="Ⅱ Tạm dừng",
            bg=ORANGE,
            fg=WHITE_COLOR,
            relief=tk.FLAT,
            font=("Arial", 10, "bold"),
            command=self.pause_or_resume
        )
        self.pause_button.pack(side=tk.LEFT, padx=5, ipadx=8, ipady=4)

        self.reset_button = tk.Button(
            control_body,
            text="↺ Đặt lại",
            bg=ACCENT_COLOR,
            fg=WHITE_COLOR,
            relief=tk.FLAT,
            font=("Arial", 10, "bold"),
            command=self.reset_comparison
        )
        self.reset_button.pack(side=tk.LEFT, padx=5, ipadx=8, ipady=4)

        table = self.section(self.scroll_frame, "BẢNG SO SÁNH TỔNG HỢP REALTIME")
        table.pack(fill=tk.X, padx=8, pady=8)
        self.build_table(table)

        bottom = tk.Frame(self.scroll_frame, bg=BACKGROUND_COLOR)
        bottom.pack(fill=tk.BOTH, expand=True)

        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=1)
        bottom.grid_columnconfigure(2, weight=1)

        w = self.section(bottom, "SO SÁNH AVG WAITING TIME")
        w.grid(row=0, column=0, sticky="nsew", padx=8)

        self.waiting_chart_canvas = tk.Canvas(
            w,
            height=270,
            bg=WHITE_COLOR,
            highlightthickness=0
        )
        self.waiting_chart_canvas.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)

        t = self.section(bottom, "SO SÁNH AVG TURNAROUND TIME")
        t.grid(row=0, column=1, sticky="nsew", padx=8)

        self.turnaround_chart_canvas = tk.Canvas(
            t,
            height=270,
            bg=WHITE_COLOR,
            highlightthickness=0
        )
        self.turnaround_chart_canvas.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)

        right = tk.Frame(bottom, bg=BACKGROUND_COLOR)
        right.grid(row=0, column=2, sticky="nsew", padx=8)

        cmt = self.section(right, "NHẬN XÉT & KẾT LUẬN")
        cmt.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.comment_text = tk.Text(
            cmt,
            height=8,
            bg=WHITE_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 10),
            relief=tk.FLAT,
            wrap="word"
        )
        self.comment_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        export = self.section(right, "XUẤT BÁO CÁO")
        export.pack(fill=tk.X)

        for txt in ["📄  Xuất báo cáo (PDF)", "💾  Lưu kết quả (CSV)", "🖨  In biểu đồ"]:
            tk.Button(
                export,
                text=txt,
                bg=WHITE_COLOR,
                fg=PRIMARY_COLOR,
                relief=tk.GROOVE,
                font=("Arial", 10, "bold")
            ).pack(fill=tk.X, padx=12, pady=5, ipady=5)

    def build_table(self, parent):
        wrap = tk.Frame(parent, bg=WHITE_COLOR)
        wrap.pack(fill=tk.X, padx=14, pady=10)

        cols = (
            "algorithm",
            "avg_waiting",
            "avg_turnaround",
            "avg_response",
            "comment"
        )

        self.comparison_table = ttk.Treeview(
            wrap,
            columns=cols,
            show="headings",
            height=5
        )

        self.comparison_table.tag_configure("best_row", background="#DCFCE7")

        heads = [
            "Thuật toán",
            "Avg Waiting Time",
            "Avg Turnaround Time",
            "Avg Response Time",
            "Nhận xét"
        ]

        widths = [210, 170, 190, 170, 360]

        for c, h, w in zip(cols, heads, widths):
            self.comparison_table.heading(c, text=h)
            self.comparison_table.column(c, width=w, anchor="center")

        self.comparison_table.pack(fill=tk.X)

    def normalize_algorithm_name(self, key):
        text = str(key).strip()
        upper = text.upper()
        if "ROUND" in upper:
            return "Round Robin"
        if "PRIORITY" in upper:
            return "Priority"
        if upper.startswith("SJF"):
            return "SJF"
        if upper.startswith("FCFS"):
            return "FCFS"
        return text

    def stamp_result_algorithm(self, result, key):
        if result is None:
            return result
        try:
            setattr(result, "algorithm_name", self.normalize_algorithm_name(key))
            setattr(result, "algorithm_key", key)
        except Exception:
            pass
        return result

    def receive_simulation_progress(self, payload, force=False):
        if not payload:
            return

        self.stop_after_job()
        self.external_source = True
        self.last_external_payload = payload

        self.tasks = payload.get("tasks", self.tasks)

        result_map = payload.get("result_map")
        if result_map:
            self.results = [
                self.stamp_result_algorithm(result, key)
                for key, result in result_map.items()
            ]
        else:
            incoming_results = list(payload.get("results", []) or [])
            selected_keys = list(payload.get("selected_keys", []) or [])
            self.results = []
            for index, result in enumerate(incoming_results):
                key = selected_keys[index] if index < len(selected_keys) else getattr(result, "algorithm_name", f"Algorithm {index + 1}")
                self.results.append(self.stamp_result_algorithm(result, key))

        self.current_time = self.to_int(payload.get("current_time", 0), 0)
        self.max_time = self.to_int(payload.get("max_time", 0), 0)
        self.timeline_points = list(payload.get("timeline_points", [0]) or [0])
        self.timeline_index = self.to_int(payload.get("timeline_index", 0), 0)
        self.is_running = bool(payload.get("is_running", False))
        self.is_finished = bool(payload.get("is_finished", False))

        if self.is_finished:
            self.status_label.config(
                text="● Đã nhận kết quả mô phỏng từ Simulation",
                fg=PRIMARY_COLOR
            )
            self.run_button.config(state=tk.NORMAL)
            self.pause_button.config(text="Ⅱ Tạm dừng", state=tk.NORMAL)
        elif self.is_running:
            self.status_label.config(
                text="● Đang nhận số liệu realtime từ Simulation...",
                fg=GREEN
            )
            self.run_button.config(state=tk.DISABLED)
            self.pause_button.config(text="Theo dõi", state=tk.DISABLED)
        else:
            self.status_label.config(
                text="● Đã nhận dữ liệu từ Simulation",
                fg=MUTED_TEXT
            )
            self.run_button.config(state=tk.NORMAL)
            self.pause_button.config(text="Ⅱ Tạm dừng", state=tk.NORMAL)

        self.refresh_realtime_comparison(force=force or self.is_visible)

    # =====================================================
    # REALTIME COMPARISON
    # =====================================================
    def compare_algorithms(self):
        self.external_source = False
        self.last_external_payload = None

        if not self.tasks:
            return messagebox.showwarning(
                "Chưa có dữ liệu",
                "Vui lòng nhập hoặc tạo dữ liệu mẫu ở màn hình Danh sách tác vụ."
            )

        try:
            self.stop_after_job()

            self.current_time = 0
            self.max_time = 0
            self.timeline_points = [0]
            self.timeline_index = 0
            self.results = []
            self.is_finished = False

            task_source, _ = self.prepare_simulation_tasks()
            q = int(DEFAULT_TIME_QUANTUM or 4)

            # FCFS and Round Robin should use a sequence-ordered source (T001, T002, ...)
            # to match the per-algorithm panels (same logic as SimulationFrame).
            sequence_source = self.prepare_sequence_algorithm_tasks(task_source)

            self.results = [
                self.stamp_result_algorithm(run_fcfs(copy.deepcopy(sequence_source)), "FCFS"),
                self.stamp_result_algorithm(run_sjf(copy.deepcopy(task_source)), "SJF"),
                self.stamp_result_algorithm(run_priority(copy.deepcopy(task_source)), "PRIORITY"),
                self.stamp_result_algorithm(run_round_robin(copy.deepcopy(sequence_source), q), "ROUND ROBIN"),
            ]

            self.max_time = max([
                self.to_int(self.safe_attr(result.gantt_chart[-1], "end_time", 0), 0)
                for result in self.results
                if getattr(result, "gantt_chart", None)
            ] or [0])

            if self.max_time <= 0:
                return messagebox.showwarning(
                    "Không có dữ liệu",
                    "Danh sách tác vụ chưa có thời gian xử lý hợp lệ."
                )

            self.timeline_points = self.build_timeline_points()
            self.timeline_index = 0
            self.current_time = self.timeline_points[0]

            self.is_running = True
            self.run_button.config(state=tk.DISABLED)
            self.pause_button.config(text="Ⅱ Tạm dừng", state=tk.NORMAL)

            self.status_label.config(
                text="● Đang so sánh realtime...",
                fg=GREEN
            )

            self.refresh_realtime_comparison(force=True)

            self.after_id = self.after(EVENT_STEP_MS, self.comparison_tick)

        except Exception as e:
            messagebox.showerror("Lỗi so sánh", str(e))

    def comparison_tick(self):
        if not self.is_running:
            return

        if self.timeline_index >= len(self.timeline_points) - 1:
            self.finish_comparison()
            return

        self.timeline_index += 1
        self.current_time = self.timeline_points[self.timeline_index]

        self.refresh_realtime_comparison()

        if self.timeline_index >= len(self.timeline_points) - 1:
            self.finish_comparison()
        else:
            self.after_id = self.after(EVENT_STEP_MS, self.comparison_tick)

    def pause_or_resume(self):
        if not self.results:
            return

        if self.timeline_index >= len(self.timeline_points) - 1:
            return

        if self.is_running:
            self.is_running = False
            self.stop_after_job()

            self.status_label.config(
                text="● Đã tạm dừng",
                fg=ORANGE
            )

            self.pause_button.config(text="▶ Tiếp tục")

        else:
            self.is_running = True

            self.status_label.config(
                text="● Đang so sánh realtime...",
                fg=GREEN
            )

            self.pause_button.config(text="Ⅱ Tạm dừng", state=tk.NORMAL)
            self.after_id = self.after(EVENT_STEP_MS, self.comparison_tick)

    def finish_comparison(self):
        self.is_running = False
        self.is_finished = True
        self.stop_after_job()

        self.timeline_index = len(self.timeline_points) - 1
        self.current_time = self.max_time

        self.refresh_realtime_comparison(force=True)

        self.status_label.config(
            text="● Đã hoàn thành so sánh",
            fg=PRIMARY_COLOR
        )

        self.run_button.config(state=tk.NORMAL)
        self.pause_button.config(text="Ⅱ Tạm dừng")

    def reset_comparison(self):
        self.stop_after_job()
        self.external_source = False
        self.last_external_payload = None

        self.is_running = False
        self.is_finished = False
        self.current_time = 0
        self.max_time = 0
        self.timeline_points = [0]
        self.timeline_index = 0
        self.results = []

        self.run_button.config(state=tk.NORMAL)
        self.pause_button.config(text="Ⅱ Tạm dừng")

        self.status_label.config(
            text="● Sẵn sàng so sánh",
            fg=MUTED_TEXT
        )

        self.show_empty_state()

    def stop_after_job(self):
        if self.after_id is not None:
            try:
                self.after_cancel(self.after_id)
            except Exception:
                pass

            self.after_id = None

    def refresh_realtime_comparison(self, force=False):
        if not self.results:
            return

        if not self.is_visible and not force:
            return

        self.time_label.config(
            text=f"Thời gian: {min(self.current_time, self.max_time)} / {self.max_time}"
        )

        live_rows = self.build_live_rows()

        self.refresh_comparison_table(live_rows)
        self.update_summary_cards(live_rows)
        self.draw_charts(live_rows)
        self.write_comments(live_rows)

    def build_timeline_points(self):
        points = {0, self.max_time}

        for result in self.results:
            for block in getattr(result, "gantt_chart", []) or []:
                points.add(self.to_int(self.safe_attr(block, "start_time", 0), 0))
                points.add(self.to_int(self.safe_attr(block, "end_time", 0), 0))

        return sorted(points)

    def build_live_rows(self):
        rows = []

        # If the simulation has finished, prefer final metrics stored on the result
        if getattr(self, 'is_finished', False):
            for result in self.results:
                total = len(getattr(result, 'tasks', []) or [])
                rows.append({
                    "result": result,
                    "algorithm_name": getattr(result, "algorithm_name", "Unknown"),
                    "avg_waiting": getattr(result, 'average_waiting_time', 0.0) or 0.0,
                    "avg_turnaround": getattr(result, 'average_turnaround_time', 0.0) or 0.0,
                    "avg_response": getattr(result, 'average_response_time', 0.0) or 0.0,
                    "completed": total,
                    "total": total,
                })

            return rows

        # Otherwise build live metrics based on current_time
        for result in self.results:
            avg_wait, avg_turn, avg_resp, completed, total = self.calculate_live_metrics(result)

            rows.append({
                "result": result,
                "algorithm_name": getattr(result, "algorithm_name", "Unknown"),
                "avg_waiting": avg_wait,
                "avg_turnaround": avg_turn,
                "avg_response": avg_resp,
                "completed": completed,
                "total": total,
            })

        return rows

    def calculate_live_metrics(self, result):
        now = min(self.current_time, self.max_time)
        tasks = getattr(result, "tasks", []) or []

        completed_tasks = []

        for task in tasks:
            completion = self.to_int(
                self.safe_attr(task, "completion_time", 999999),
                999999
            )

            if completion <= now:
                completed_tasks.append(task)

        if not completed_tasks:
            return 0.0, 0.0, 0.0, 0, len(tasks)

        avg_wait = sum(
            float(self.safe_attr(task, "waiting_time", 0) or 0)
            for task in completed_tasks
        ) / len(completed_tasks)

        avg_turn = sum(
            float(self.safe_attr(task, "turnaround_time", 0) or 0)
            for task in completed_tasks
        ) / len(completed_tasks)

        avg_resp = sum(
            float(self.safe_attr(task, "response_time", 0) or 0)
            for task in completed_tasks
        ) / len(completed_tasks)

        return avg_wait, avg_turn, avg_resp, len(completed_tasks), len(tasks)

    # =====================================================
    # TABLE, CHART, COMMENT
    # =====================================================
    def show_empty_state(self):
        for x in self.comparison_table.get_children():
            self.comparison_table.delete(x)

        self.best_algorithm_label.config(text="---")
        self.total_algorithm_label.config(text="4")
        self.best_waiting_label.config(text="0.00")
        self.best_turnaround_label.config(text="0.00")
        self.time_label.config(text="Thời gian: 0 / 0")

        self.waiting_chart_canvas.delete("all")
        self.turnaround_chart_canvas.delete("all")

        self.comment_text.delete("1.0", tk.END)
        self.comment_text.insert(
            tk.END,
            "Nhấn “Chạy so sánh” để xem các chỉ số cập nhật theo thời gian giống màn mô phỏng."
        )

    def refresh_comparison_table(self, live_rows):
        for x in self.comparison_table.get_children():
            self.comparison_table.delete(x)

        if not live_rows:
            return

        completed_rows = [
            row for row in live_rows
            if row["completed"] > 0
        ]

        best_algorithm_name = None

        if completed_rows:
            best = min(completed_rows, key=lambda row: row["avg_waiting"])
            best_algorithm_name = best["algorithm_name"]

        for row in live_rows:
            name = row["algorithm_name"]
            display_name = self.format_algorithm_name(name)

            # Nếu mô phỏng kết thúc, hiển thị mô tả thuật toán; nếu không, hiển thị tiến độ
            if self.is_finished:
                comment = self.get_algorithm_comment(name)
            else:
                progress = f"{row['completed']}/{row['total']} tác vụ hoàn thành"
                comment = progress if row["completed"] < row["total"] else self.get_algorithm_comment(name)

            tags = ("best_row",) if best_algorithm_name and name == best_algorithm_name else ()

            self.comparison_table.insert(
                "",
                tk.END,
                values=(
                    display_name,
                    self.format_metric(row["avg_waiting"]),
                    self.format_metric(row["avg_turnaround"]),
                    self.format_metric(row["avg_response"]),
                    comment
                ),
                tags=tags
            )

    def update_summary_cards(self, live_rows):
        if not live_rows:
            self.best_algorithm_label.config(text="---")
            self.total_algorithm_label.config(text="0")
            self.best_waiting_label.config(text="0.00")
            self.best_turnaround_label.config(text="0.00")
            return

        completed_rows = [
            row for row in live_rows
            if row["completed"] > 0
        ]

        self.total_algorithm_label.config(text=str(len(live_rows)))

        if not completed_rows:
            self.best_algorithm_label.config(text="---")
            self.best_waiting_label.config(text="0.00")
            self.best_turnaround_label.config(text="0.00")
            return

        best_waiting = min(completed_rows, key=lambda row: row["avg_waiting"])
        best_turnaround = min(completed_rows, key=lambda row: row["avg_turnaround"])

        self.best_algorithm_label.config(
            text=self.format_algorithm_name(best_waiting["algorithm_name"])
        )

        self.best_waiting_label.config(
            text=self.format_metric(best_waiting["avg_waiting"])
        )

        self.best_turnaround_label.config(
            text=self.format_metric(best_turnaround["avg_turnaround"])
        )

    def draw_charts(self, live_rows):
        waiting_data = [
            (row["algorithm_name"], float(row["avg_waiting"] or 0))
            for row in live_rows
        ]

        turnaround_data = [
            (row["algorithm_name"], float(row["avg_turnaround"] or 0))
            for row in live_rows
        ]

        self.draw_bar_chart(self.waiting_chart_canvas, waiting_data)
        self.draw_bar_chart(self.turnaround_chart_canvas, turnaround_data)

    def draw_bar_chart(self, canvas, data):
        canvas.delete("all")

        if not data:
            return

        w = max(canvas.winfo_width(), 350)
        h = max(canvas.winfo_height(), 250)

        left = 45
        bottom = 42
        top = 22

        cw = w - left - 25
        ch = h - top - bottom

        max_value = max(v for _, v in data) or 1

        for i in range(6):
            y = top + ch - i * ch / 5

            canvas.create_line(
                left,
                y,
                left + cw,
                y,
                fill="#E5E7EB"
            )

            canvas.create_text(
                left - 18,
                y,
                text=str(round(max_value * i / 5, 1)),
                fill=TEXT_COLOR,
                font=("Arial", 8)
            )

        gap = 18
        bar_width = (cw - gap * (len(data) + 1)) / len(data)

        for i, (name, val) in enumerate(data):
            short = self.short_algorithm_name(name)
            color = self.get_algorithm_color(name)

            x1 = left + gap + i * (bar_width + gap)
            x2 = x1 + bar_width
            y1 = top + ch - (val / max_value) * (ch - 10)
            y2 = top + ch

            canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=color,
                outline=color
            )

            canvas.create_text(
                (x1 + x2) / 2,
                y1 - 10,
                text=f"{val:.2f}",
                fill=TEXT_COLOR,
                font=("Arial", 9, "bold")
            )

            canvas.create_text(
                (x1 + x2) / 2,
                y2 + 18,
                text=short,
                fill=TEXT_COLOR,
                font=("Arial", 9)
            )

    def write_comments(self, live_rows):
        self.comment_text.delete("1.0", tk.END)

        if not live_rows:
            self.comment_text.insert(tk.END, "Chưa có kết quả so sánh.")
            return

        completed_rows = [
            row for row in live_rows
            if row["completed"] > 0
        ]

        if not completed_rows:
            self.comment_text.insert(
                tk.END,
                "• Đang khởi động mô phỏng, chưa có tác vụ nào hoàn thành.\n"
            )
            self.comment_text.insert(
                tk.END,
                "• Các chỉ số sẽ được cập nhật realtime khi từng tác vụ hoàn thành."
            )
            return

        best_waiting = min(completed_rows, key=lambda row: row["avg_waiting"])

        # Nếu mô phỏng kết thúc, hiển thị kết quả chi tiết
        if self.is_finished:
            self.comment_text.insert(
                tk.END,
                f"✓ Mô phỏng đã hoàn thành!\n\n"
            )

            self.comment_text.insert(
                tk.END,
                f"🏆 Thuật toán tốt nhất: {self.format_algorithm_name(best_waiting['algorithm_name'])}\n"
                f"  - Avg Waiting Time: {self.format_metric(best_waiting['avg_waiting'])} đơn vị thời gian\n\n"
            )

            self.comment_text.insert(
                tk.END,
                "📊 Đặc điểm từng thuật toán:\n"
                "• FCFS: Đơn giản, dễ triển khai nhưng thời gian chờ có thể cao.\n"
                "• SJF: Thường cho thời gian chờ thấp khi biết burst time.\n"
                "• Priority: Phù hợp khi có tác vụ khẩn cấp hoặc ưu tiên cao.\n"
                "• Round Robin: Công bằng, phù hợp khi cần chia lượt xử lý.\n"
            )
        else:
            # Đang chạy, hiển thị tiến độ
            self.comment_text.insert(
                tk.END,
                f"• Tại thời điểm t = {self.current_time}, "
                f"{self.format_algorithm_name(best_waiting['algorithm_name'])} "
                f"đang có Avg Waiting thấp nhất.\n"
            )

            self.comment_text.insert(
                tk.END,
                "• Bảng và biểu đồ đang cập nhật theo tiến trình mô phỏng.\n"
            )

            self.comment_text.insert(
                tk.END,
                "• Khi mô phỏng kết thúc, đây sẽ là kết quả so sánh cuối cùng.\n"
            )

            self.comment_text.insert(
                tk.END,
                "• FCFS đơn giản, SJF thường tối ưu thời gian chờ, Priority phù hợp tác vụ khẩn cấp, Round Robin đảm bảo tính công bằng."
            )

    # =====================================================
    # DATA HELPERS
    # =====================================================
    def refresh_data(self):
        self.reset_comparison()

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

    def prepare_simulation_tasks(self):
        tasks_copy = copy.deepcopy(self.tasks)

        if not tasks_copy:
            return [], ""

        for index, task in enumerate(tasks_copy):
            self.ensure_task_defaults(task, index)

        arrivals = [
            self.to_int(self.safe_attr(task, "arrival_time", 0), 0)
            for task in tasks_copy
        ]

        bursts = [
            max(1, self.to_int(self.safe_attr(task, "burst_time", 1), 1))
            for task in tasks_copy
        ]

        min_arrival = min(arrivals)
        max_arrival = max(arrivals)
        arrival_span = max_arrival - min_arrival
        total_burst = sum(bursts)

        LARGE_ARRIVAL_MIN_SPAN = 120
        LARGE_ARRIVAL_BURST_MULTIPLIER = 4

        should_compress = arrival_span > max(
            LARGE_ARRIVAL_MIN_SPAN,
            total_burst * LARGE_ARRIVAL_BURST_MULTIPLIER
        )

        if should_compress:
            unique_arrivals = sorted(set(arrivals))
            arrival_map = {
                arrival: pos
                for pos, arrival in enumerate(unique_arrivals)
            }

            for task in tasks_copy:
                original = self.to_int(
                    self.safe_attr(task, "arrival_time", 0),
                    0
                )
                setattr(task, "arrival_time", arrival_map[original])

            note = "arrival_time đã được nén để mô phỏng nhanh hơn."
        else:
            for task in tasks_copy:
                original = self.to_int(
                    self.safe_attr(task, "arrival_time", 0),
                    0
                )
                setattr(task, "arrival_time", original - min_arrival)

            note = ""

        for task in tasks_copy:
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

        return tasks_copy, note

    def prepare_sequence_algorithm_tasks(self, tasks):
        """
        Prepare a sequence-ordered task list for FCFS and Round Robin so that
        these algorithms run in T001, T002, ... order (matching SimulationFrame).
        This avoids discrepancies when arrival_time ordering in the source is different.
        """
        tasks_copy = copy.deepcopy(tasks or [])

        def get_task_number(task_id):
            try:
                import re
                m = re.search(r"\d+", str(task_id))
                return int(m.group()) if m else 999999
            except Exception:
                return 999999

        ordered_tasks = sorted(
            tasks_copy,
            key=lambda t: (get_task_number(getattr(t, 'task_id', '')), str(getattr(t, 'task_id', '')))
        )

        for index, task in enumerate(ordered_tasks):
            setattr(task, 'arrival_time', index)

        return ordered_tasks

    def safe_attr(self, obj, attr, default=None):
        if obj is None:
            return default

        return getattr(obj, attr, default)

    def to_int(self, value, default=0):
        try:
            return int(float(value))
        except Exception:
            return default

    def format_algorithm_name(self, algorithm_name):
        text = str(algorithm_name).strip()
        upper = text.upper()

        if "ROUND" in upper:
            return "Round Robin"
        if "PRIORITY" in upper:
            return "Priority"
        if upper.startswith("SJF"):
            return "SJF"
        if upper.startswith("FCFS"):
            return "FCFS"

        return text

    def short_algorithm_name(self, name):
        text = str(name).strip()
        upper = text.upper()

        if "ROUND" in upper:
            return "RR"
        if "PRIORITY" in upper:
            return "Prio"
        if upper.startswith("SJF"):
            return "SJF"
        if upper.startswith("FCFS"):
            return "FCFS"

        return text.split()[0] if text else ""

    def get_algorithm_color(self, name):
        upper = str(name).upper()

        if upper.startswith("SJF"):
            return GREEN

        if "PRIORITY" in upper:
            return ORANGE

        if "ROUND" in upper:
            return "#7C3AED"

        return PRIMARY_COLOR

    def format_metric(self, value):
        try:
            return f"{float(value):.2f}"
        except Exception:
            return "0.00"

    def get_algorithm_comment(self, name):
        upper = str(name).upper()

        if upper.startswith("FCFS"):
            return "Đơn giản, dễ triển khai nhưng thời gian chờ có thể cao."

        if upper.startswith("SJF"):
            return "Thường cho thời gian chờ thấp khi biết burst time."

        if "PRIORITY" in upper:
            return "Phù hợp khi có tác vụ khẩn cấp hoặc ưu tiên cao."

        return "Công bằng, phù hợp khi cần chia lượt xử lý."

