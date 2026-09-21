import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
import time
import random

class WaveMazeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторна робота 3: Одно-направлений хвильовий пошук")
        self.root.geometry("1120x760")
        self.root.minsize(920, 660)

        self.rows = 15
        self.cols = 15
        self.start_pos = (1, 1)
        self.goal_pos = (self.rows - 2, self.cols - 2)

        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.wave_grid = {}

        self.operator_var = tk.StringVar(value="ortho")
        self.mouse_mode = tk.StringVar(value="wall")

        self.is_running = False
        self.is_paused = False
        self.search_generator = None
        self.anim_job = None
        self.animation_speed = 50
        self.drag_paint_val = None

        self.cycles_count = 0
        self.expanded_count = 0
        self.pure_search_time = 0.0
        self.final_path = []
        self.current_active_cell = None

        self._create_ui()
        self._init_empty_grid_with_border()

    def _create_ui(self):
        main_frame = ttk.Frame(self.root, padding=8)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(main_frame, width=290)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        dim_box = ttk.LabelFrame(left_panel, text="Граф і лабіринт (порядок 10-20)", padding=6)
        dim_box.pack(fill=tk.X, pady=(0, 6))

        dim_row = ttk.Frame(dim_box)
        dim_row.pack(fill=tk.X, pady=2)
        ttk.Label(dim_row, text="Рядки:").pack(side=tk.LEFT)
        self.sp_rows = ttk.Spinbox(dim_row, from_=10, to=20, width=4)
        self.sp_rows.set(self.rows)
        self.sp_rows.pack(side=tk.LEFT, padx=(2, 6))

        ttk.Label(dim_row, text="Стовпці:").pack(side=tk.LEFT)
        self.sp_cols = ttk.Spinbox(dim_row, from_=10, to=20, width=4)
        self.sp_cols.set(self.cols)
        self.sp_cols.pack(side=tk.LEFT, padx=2)

        ttk.Button(dim_box, text="Застосувати розмірність", command=self._on_apply_dimensions).pack(fill=tk.X, pady=3)
        ttk.Button(dim_box, text="🎲 Згенерувати лабіринт", command=self.generate_random_maze).pack(fill=tk.X, pady=1)
        ttk.Button(dim_box, text="Очистити внутрішні стіни (0)", command=self.clear_all_obstacles).pack(fill=tk.X, pady=1)

        node_box = ttk.LabelFrame(left_panel, text="Вершини графу", padding=6)
        node_box.pack(fill=tk.X, pady=(0, 6))

        st_row = ttk.Frame(node_box)
        st_row.pack(fill=tk.X, pady=1)
        ttk.Label(st_row, text="Початкова (S):").pack(side=tk.LEFT)
        self.lbl_start_coords = ttk.Label(st_row, text=str(self.start_pos), font=("Helvetica", 9, "bold"), foreground="#2d6a4f")
        self.lbl_start_coords.pack(side=tk.RIGHT)

        gl_row = ttk.Frame(node_box)
        gl_row.pack(fill=tk.X, pady=1)
        ttk.Label(gl_row, text="Цільова (G):").pack(side=tk.LEFT)
        self.lbl_goal_coords = ttk.Label(gl_row, text=str(self.goal_pos), font=("Helvetica", 9, "bold"), foreground="#d90429")
        self.lbl_goal_coords.pack(side=tk.RIGHT)

        ttk.Label(node_box, text="Інструмент миші (ЛКМ / протягування):").pack(anchor=tk.W, pady=(4, 1))
        tool_row = ttk.Frame(node_box)
        tool_row.pack(fill=tk.X)
        ttk.Radiobutton(tool_row, text="Стіна (-1/0)", variable=self.mouse_mode, value="wall").pack(side=tk.LEFT)
        ttk.Radiobutton(tool_row, text="Старт", variable=self.mouse_mode, value="start").pack(side=tk.LEFT, padx=3)
        ttk.Radiobutton(tool_row, text="Ціль", variable=self.mouse_mode, value="goal").pack(side=tk.LEFT)

        op_box = ttk.LabelFrame(left_panel, text="Оператор переходу", padding=6)
        op_box.pack(fill=tk.X, pady=(0, 6))

        ttk.Radiobutton(op_box, text="1. «вверх-вниз-вправо-вліво»", 
                        variable=self.operator_var, value="ortho", command=self.reset_search_state).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(op_box, text="2. «перехід по діагоналях»", 
                        variable=self.operator_var, value="diag", command=self.reset_search_state).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(op_box, text="3. Комбінація операторів", 
                        variable=self.operator_var, value="combined", command=self.reset_search_state).pack(anchor=tk.W, pady=2)

        ctrl_box = ttk.LabelFrame(left_panel, text="Керування хвильовим пошуком", padding=6)
        ctrl_box.pack(fill=tk.X, pady=(0, 6))

        b_row1 = ttk.Frame(ctrl_box)
        b_row1.pack(fill=tk.X, pady=2)
        self.btn_run = ttk.Button(b_row1, text="▶ Старт", command=self.start_auto_search)
        self.btn_run.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        self.btn_pause = ttk.Button(b_row1, text="⏸ Пауза", command=self.pause_search, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        b_row2 = ttk.Frame(ctrl_box)
        b_row2.pack(fill=tk.X, pady=2)
        self.btn_step = ttk.Button(b_row2, text="⏭ Крок", command=self.step_search)
        self.btn_step.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        self.btn_reset = ttk.Button(b_row2, text="↺ Скинути", command=self.reset_search_state)
        self.btn_reset.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        ttk.Label(ctrl_box, text="Час затримки візуалізації (мс):").pack(anchor=tk.W, pady=(4, 0))
        self.speed_slider = ttk.Scale(ctrl_box, from_=300, to=5, orient=tk.HORIZONTAL, command=self._on_speed_changed)
        self.speed_slider.set(self.animation_speed)
        self.speed_slider.pack(fill=tk.X)
        self.lbl_speed = ttk.Label(ctrl_box, text=f"Затримка: {self.animation_speed} мс", font=("Helvetica", 8))
        self.lbl_speed.pack(anchor=tk.E)

        self.btn_results = ttk.Button(left_panel, text="⧉ Останні результати пошуку", command=self.show_results_window, state=tk.DISABLED)
        self.btn_results.pack(fill=tk.X, pady=(6, 0))

        self.canvas = tk.Canvas(canvas_frame, bg="#ffffff", highlightthickness=1, highlightbackground="#b0b0b0")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Configure>", lambda e: self.redraw_canvas())
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

    def _init_empty_grid_with_border(self):
        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        for r in range(self.rows):
            self.grid[r][0] = -1
            self.grid[r][self.cols - 1] = -1
        for c in range(self.cols):
            self.grid[0][c] = -1
            self.grid[self.rows - 1][c] = -1

        self.grid[self.start_pos[0]][self.start_pos[1]] = 0
        self.grid[self.goal_pos[0]][self.goal_pos[1]] = 0
        self.redraw_canvas()

    def _on_apply_dimensions(self):
        try:
            r = int(self.sp_rows.get())
            c = int(self.sp_cols.get())
            if not (10 <= r <= 20 and 10 <= c <= 20):
                messagebox.showerror("Помилка", "Розмірність має бути в межах 10-20!", parent=self.root)
                return

            self._cancel_scheduled_anim()
            old_grid = self.grid
            old_r = self.rows
            old_c = self.cols

            self.rows = r
            self.cols = c
            self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

            for i in range(self.rows):
                self.grid[i][0] = -1
                self.grid[i][self.cols - 1] = -1
            for j in range(self.cols):
                self.grid[0][j] = -1
                self.grid[self.rows - 1][j] = -1

            for i in range(1, min(old_r - 1, self.rows - 1)):
                for j in range(1, min(old_c - 1, self.cols - 1)):
                    self.grid[i][j] = old_grid[i][j]

            sr = min(max(1, self.start_pos[0]), self.rows - 2)
            sc = min(max(1, self.start_pos[1]), self.cols - 2)
            gr = min(max(1, self.goal_pos[0]), self.rows - 2)
            gc = min(max(1, self.goal_pos[1]), self.cols - 2)

            if (sr, sc) == (gr, gc):
                sr, sc = (1, 1)
                gr, gc = (self.rows - 2, self.cols - 2)

            self.start_pos = (sr, sc)
            self.goal_pos = (gr, gc)
            self.grid[sr][sc] = 0
            self.grid[gr][gc] = 0

            self.lbl_start_coords.config(text=str(self.start_pos))
            self.lbl_goal_coords.config(text=str(self.goal_pos))

            self.reset_search_state()

        except ValueError:
            messagebox.showerror("Помилка", "Введіть ціле число в діапазоні 10-20.", parent=self.root)

    def generate_random_maze(self):
        self.reset_search_state()
        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

        for r in range(self.rows):
            self.grid[r][0] = -1
            self.grid[r][self.cols - 1] = -1
        for c in range(self.cols):
            self.grid[0][c] = -1
            self.grid[self.rows - 1][c] = -1

        def divide(r1, r2, c1, c2):
            if r2 - r1 < 2 or c2 - c1 < 2:
                return

            width = c2 - c1
            height = r2 - r1
            horizontal = height > width if width != height else random.choice([True, False])

            if horizontal:
                wall_r = random.randint(r1 + 1, r2 - 1)
                openings = {random.randint(c1, c2)}
                if c2 - c1 > 3 and random.random() < 0.45:
                    openings.add(random.randint(c1, c2))

                for c in range(c1, c2 + 1):
                    self.grid[wall_r][c] = 0 if c in openings else -1

                divide(r1, wall_r - 1, c1, c2)
                divide(wall_r + 1, r2, c1, c2)
            else:
                wall_c = random.randint(c1 + 1, c2 - 1)
                openings = {random.randint(r1, r2)}
                if r2 - r1 > 3 and random.random() < 0.45:
                    openings.add(random.randint(r1, r2))

                for r in range(r1, r2 + 1):
                    self.grid[r][wall_c] = 0 if r in openings else -1

                divide(r1, r2, c1, wall_c - 1)
                divide(r1, r2, wall_c + 1, c2)

        divide(1, self.rows - 2, 1, self.cols - 2)

        sr, sc = self.start_pos
        gr, gc = self.goal_pos
        self.grid[sr][sc] = 0
        self.grid[gr][gc] = 0

        for r_pos, c_pos in [(sr, sc), (gr, gc)]:
            neighbors = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r_pos + dr, c_pos + dc
                if 0 < nr < self.rows - 1 and 0 < nc < self.cols - 1:
                    neighbors.append((nr, nc))
            if neighbors and all(self.grid[nr][nc] == -1 for nr, nc in neighbors):
                fnr, fnc = random.choice(neighbors)
                self.grid[fnr][fnc] = 0

        self.redraw_canvas()

    def clear_all_obstacles(self):
        self.reset_search_state()
        self._init_empty_grid_with_border()

    def _get_cell_at(self, x, y):
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw <= 10 or ch <= 10:
            return None
        margin = 15
        cell_size = min((cw - 2 * margin) / self.cols, (ch - 2 * margin) / self.rows)
        start_x = (cw - cell_size * self.cols) / 2
        start_y = (ch - cell_size * self.rows) / 2

        if not (start_x <= x <= start_x + cell_size * self.cols and start_y <= y <= start_y + cell_size * self.rows):
            return None

        c = int((x - start_x) // cell_size)
        r = int((y - start_y) // cell_size)
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return (r, c)
        return None

    def _on_canvas_click(self, event):
        if self.is_running and not self.is_paused:
            return
        cell = self._get_cell_at(event.x, event.y)
        if not cell:
            return

        mode = self.mouse_mode.get()
        r, c = cell

        if mode == "start":
            if cell != self.goal_pos:
                self.start_pos = cell
                self.grid[r][c] = 0
                self.lbl_start_coords.config(text=str(self.start_pos))
                self.reset_search_state()
        elif mode == "goal":
            if cell != self.start_pos:
                self.goal_pos = cell
                self.grid[r][c] = 0
                self.lbl_goal_coords.config(text=str(self.goal_pos))
                self.reset_search_state()
        else:
            if cell not in (self.start_pos, self.goal_pos):
                self.drag_paint_val = -1 if self.grid[r][c] == 0 else 0
                self.grid[r][c] = self.drag_paint_val
                if self.wave_grid or self.final_path:
                    self.reset_search_state()
                else:
                    self.redraw_canvas()

    def _on_canvas_drag(self, event):
        if self.is_running and not self.is_paused:
            return
        if self.mouse_mode.get() != "wall" or self.drag_paint_val is None:
            return
        cell = self._get_cell_at(event.x, event.y)
        if cell and cell not in (self.start_pos, self.goal_pos):
            r, c = cell
            if self.grid[r][c] != self.drag_paint_val:
                self.grid[r][c] = self.drag_paint_val
                if self.wave_grid or self.final_path:
                    self.reset_search_state()
                else:
                    self.redraw_canvas()

    def _on_canvas_release(self, event):
        self.drag_paint_val = None

    def _on_speed_changed(self, val):
        self.animation_speed = int(float(val))
        self.lbl_speed.config(text=f"Затримка: {self.animation_speed} мс")

    def get_neighbors(self, r, c, operator_type):
        if operator_type == "ortho":
            offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        elif operator_type == "diag":
            offsets = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            offsets = [(-1, 0), (1, 0), (0, -1), (0, 1),
                       (-1, -1), (-1, 1), (1, -1), (1, 1)]

        neighbors = []
        for dr, dc in offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc] != -1:
                    neighbors.append((nr, nc))
        return neighbors

    def _calculate_pure_search_time(self):
        start = self.start_pos
        goal = self.goal_pos
        op_type = self.operator_var.get()

        if self.grid[start[0]][start[1]] == -1 or self.grid[goal[0]][goal[1]] == -1:
            return 0.0

        t_start = time.perf_counter()
        queue = deque([start])
        visited = {start}

        while queue:
            curr = queue.popleft()
            if curr == goal:
                break
            for nxt in self.get_neighbors(curr[0], curr[1], op_type):
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)

        t_end = time.perf_counter()
        return (t_end - t_start) * 1000.0

    def wave_search_generator(self):
        start = self.start_pos
        goal = self.goal_pos
        op_type = self.operator_var.get()

        if self.grid[start[0]][start[1]] == -1 or self.grid[goal[0]][goal[1]] == -1:
            yield {'type': 'error', 'msg': "Start або Goal розміщені на непрохідній клітинці (-1)!"}
            return

        if start == goal:
            yield {
                'type': 'finished',
                'found': True,
                'path': [start],
                'wave_labels': {start: 0},
                'cycles': 1,
                'expanded': 1
            }
            return

        queue = deque([start])
        visited = {start}
        parent = {}
        wave_labels = {start: 0}

        cycles = 0
        found = False

        while queue:
            cycles += 1
            curr = queue.popleft()
            curr_wave = wave_labels[curr]

            yield {
                'type': 'step',
                'active_cell': curr,
                'wave_labels': wave_labels.copy(),
                'cycles': cycles,
                'expanded': len(wave_labels)
            }

            if curr == goal:
                found = True
                break

            for nxt in self.get_neighbors(curr[0], curr[1], op_type):
                if nxt not in visited:
                    visited.add(nxt)
                    parent[nxt] = curr
                    wave_labels[nxt] = curr_wave + 1
                    queue.append(nxt)

        if found:
            path = []
            curr_step = goal
            while curr_step is not None:
                path.append(curr_step)
                curr_step = parent.get(curr_step)
            path.reverse()
            yield {
                'type': 'finished',
                'found': True,
                'path': path,
                'wave_labels': wave_labels,
                'cycles': cycles,
                'expanded': len(wave_labels)
            }
        else:
            yield {
                'type': 'finished',
                'found': False,
                'path': [],
                'wave_labels': wave_labels,
                'cycles': cycles,
                'expanded': len(wave_labels)
            }

    def start_auto_search(self):
        if not self.is_running:
            self.reset_search_state()
            self.pure_search_time = self._calculate_pure_search_time()
            self.search_generator = self.wave_search_generator()
            self.is_running = True
            self.is_paused = False
        elif self.is_paused:
            self.is_paused = False

        self.btn_run.config(text="▶ Старт", state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL)
        self.btn_step.config(state=tk.DISABLED)
        self.btn_results.config(state=tk.DISABLED)
        self._step_animation()

    def pause_search(self):
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self._cancel_scheduled_anim()
            self.btn_run.config(text="▶ Продовжити", state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED)
            self.btn_step.config(state=tk.NORMAL)

    def step_search(self):
        if not self.is_running:
            self.reset_search_state()
            self.pure_search_time = self._calculate_pure_search_time()
            self.search_generator = self.wave_search_generator()
            self.is_running = True
            self.is_paused = True
            self.btn_run.config(text="▶ Продовжити", state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED)

        self._execute_single_step()

    def _execute_single_step(self):
        if not self.search_generator:
            return False

        try:
            res = next(self.search_generator)
            step_type = res['type']

            if step_type == 'error':
                messagebox.showerror("Помилка", res['msg'], parent=self.root)
                self.reset_search_state()
                return False

            self.cycles_count = res['cycles']
            self.expanded_count = res['expanded']
            self.wave_grid = res['wave_labels']

            if step_type == 'step':
                self.current_active_cell = res['active_cell']
                self.redraw_canvas()
                return True
            elif step_type == 'finished':
                self.current_active_cell = None
                self.final_path = res['path']
                self.is_running = False
                self.is_paused = False
                self._cancel_scheduled_anim()
                self.btn_run.config(text="▶ Старт", state=tk.NORMAL)
                self.btn_pause.config(state=tk.DISABLED)
                self.btn_step.config(state=tk.DISABLED)
                self.btn_results.config(state=tk.NORMAL)
                self.redraw_canvas()
                self.show_results_window()
                return False

        except StopIteration:
            self.is_running = False
            self.is_paused = False
            self._cancel_scheduled_anim()
            self.btn_run.config(text="▶ Старт", state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED)
            self.btn_step.config(state=tk.DISABLED)
            return False

    def _step_animation(self):
        self.anim_job = None
        if self.is_running and not self.is_paused:
            has_next = self._execute_single_step()
            if has_next and self.is_running and not self.is_paused:
                self.anim_job = self.root.after(self.animation_speed, self._step_animation)

    def _cancel_scheduled_anim(self):
        if self.anim_job is not None:
            self.root.after_cancel(self.anim_job)
            self.anim_job = None

    def reset_search_state(self):
        self._cancel_scheduled_anim()
        self.is_running = False
        self.is_paused = False
        self.search_generator = None
        self.wave_grid.clear()
        self.final_path = []
        self.current_active_cell = None
        self.cycles_count = 0
        self.expanded_count = 0
        self.btn_run.config(text="▶ Старт", state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED)
        self.btn_step.config(state=tk.NORMAL)
        self.btn_results.config(state=tk.DISABLED)
        self.redraw_canvas()

    def redraw_canvas(self):
        self.canvas.delete("all")
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw <= 10 or ch <= 10:
            return

        margin = 15
        cell_size = min((cw - 2 * margin) / self.cols, (ch - 2 * margin) / self.rows)
        start_x = (cw - cell_size * self.cols) / 2
        start_y = (ch - cell_size * self.rows) / 2
        path_set = set(self.final_path)

        for r in range(self.rows):
            for c in range(self.cols):
                x1 = start_x + c * cell_size
                y1 = start_y + r * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                pos = (r, c)
                val = self.grid[r][c]

                fill_col = "#ffffff"
                outline_col = "#dee2e6"
                txt_col = "#495057"
                label_txt = str(val)

                if val == -1:
                    fill_col = "#2b2d42"
                    outline_col = "#1d1e2c"
                    txt_col = "#8d99ae"
                    label_txt = "-1"
                else:
                    if pos in self.wave_grid:
                        wave_num = self.wave_grid[pos]
                        label_txt = str(wave_num)
                        tint = max(150, 242 - wave_num * 5)
                        fill_col = f"#{tint:02x}{tint:02x}ff"

                    if pos in path_set:
                        fill_col = "#ffd166"
                        outline_col = "#f77f00"
                        txt_col = "#000000"

                    if pos == self.current_active_cell:
                        fill_col = "#ff70a6"
                        outline_col = "#d90429"

                    if pos == self.start_pos:
                        fill_col = "#52b788"
                        outline_col = "#2d6a4f"
                        txt_col = "#ffffff"
                        label_txt = "S:0" if pos in self.wave_grid else "S"
                    elif pos == self.goal_pos:
                        fill_col = "#e63946"
                        outline_col = "#ba181b"
                        txt_col = "#ffffff"
                        label_txt = f"G:{self.wave_grid[pos]}" if pos in self.wave_grid else "G"

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill_col, outline=outline_col, width=1.5)
                f_size = max(7, int(cell_size * 0.32))
                is_bold = "bold" if (pos in (self.start_pos, self.goal_pos) or pos in path_set) else "normal"
                self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=label_txt,
                                        font=("Helvetica", f_size, is_bold), fill=txt_col)

        if len(self.final_path) > 1:
            line_pts = []
            for r, c in self.final_path:
                line_pts.extend([start_x + c * cell_size + cell_size / 2,
                                 start_y + r * cell_size + cell_size / 2])
            self.canvas.create_line(line_pts, fill="#d90429", width=max(2.5, cell_size * 0.12),
                                    capstyle=tk.ROUND, joinstyle=tk.ROUND)

    def show_results_window(self):
        win = tk.Toplevel(self.root)
        win.title("Результати пошуку")
        win.geometry("540x440")
        win.transient(self.root)

        frame = ttk.Frame(win, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="РЕЗУЛЬТАТИ ХВИЛЬОВОГО ПОШУКУ", font=("Helvetica", 11, "bold")).pack(pady=(0, 10))

        op_dict = {
            "ortho": "1. «вверх-вниз-вправо-вліво»",
            "diag": "2. «перехід по діагоналях»",
            "combined": "3. Комбінація операторів"
        }

        info_box = ttk.LabelFrame(frame, text="Параметри та кількісні показники", padding=8)
        info_box.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(info_box, text=f"• Порядок графу (|V|): {self.rows * self.cols} (розмірність {self.rows}x{self.cols})").pack(anchor=tk.W)
        ttk.Label(info_box, text=f"• Оператор переходу: {op_dict[self.operator_var.get()]}").pack(anchor=tk.W)
        ttk.Label(info_box, text=f"• Кількість циклів розкриття вершин: {self.cycles_count}").pack(anchor=tk.W)
        ttk.Label(info_box, text=f"• Кількість усіх розкритих вершин: {self.expanded_count}").pack(anchor=tk.W)
        ttk.Label(info_box, text=f"• Час комп'ютера на здійснення пошуку: {self.pure_search_time:.4f} мс").pack(anchor=tk.W)

        path_len = len(self.final_path) - 1 if self.final_path else 0
        ttk.Label(info_box, text=f"• Довжина знайденого шляху: {path_len} переходів").pack(anchor=tk.W)

        path_box = ttk.LabelFrame(frame, text="Послідовність вершин у знайденому шляху", padding=8)
        path_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        txt = tk.Text(path_box, height=5, wrap=tk.WORD, font=("Consolas", 9))
        scroll = ttk.Scrollbar(path_box, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        if self.final_path:
            path_str = " -> ".join([f"({r},{c})" for r, c in self.final_path])
            txt.insert(tk.END, path_str)
        else:
            txt.insert(tk.END, "Цільова точка недосяжна з початкової для обраного оператора переходу.")
        txt.config(state=tk.DISABLED)

        ttk.Button(frame, text="Закрити", command=win.destroy).pack(anchor=tk.E)


if __name__ == "__main__":
    root = tk.Tk()
    app = WaveMazeApp(root)
    root.mainloop()