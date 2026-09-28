import random
import time
import tkinter as tk
from tkinter import ttk, messagebox

OP_NAMES = {
    "ortho": "1. «вверх-вниз-вправо-вліво»",
    "diag": "2. «перехід по діагоналях»",
    "combined": "3. Комбінація операторів",
}
OP_SHORT = {
    "ortho": "Вверх-вниз-вправо-вліво",
    "diag": "По діагоналях",
    "combined": "Комбінований",
}

COL_S_FRONT = "#4361ee"
COL_G_FRONT = "#f48c06"
COL_MEET = "#9d4edd"
COL_PATH_FILL = "#d8b4fe"
COL_PATH_LINE = "#6b21a8"


class WaveEngine:
    ORTHO = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    DIAG = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    OFFSETS = {"ortho": ORTHO, "diag": DIAG, "combined": ORTHO + DIAG}

    @staticmethod
    def neighbors(grid, r, c, op):
        rows, cols = len(grid), len(grid[0])
        for dr, dc in WaveEngine.OFFSETS[op]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != -1:
                yield (nr, nc)

    @staticmethod
    def search(grid, start, goal, op, bidirectional=True, snapshots=True):
        if grid[start[0]][start[1]] == -1 or grid[goal[0]][goal[1]] == -1:
            yield {'type': 'error',
                   'msg': "Start або Goal розміщені на непрохідній клітинці (-1)!"}
            return

        neighbors = WaveEngine.neighbors

        def expand(front, wave, parent):
            new_front = []
            for cell in front:
                label = wave[cell] + 1
                for nxt in neighbors(grid, cell[0], cell[1], op):
                    if nxt not in wave:
                        wave[nxt] = label
                        parent[nxt] = cell
                        new_front.append(nxt)
            return new_front

        wave_s, parent_s, front_s = {start: 0}, {start: None}, [start]
        if bidirectional:
            wave_g, parent_g, front_g = {goal: 0}, {goal: None}, [goal]
        else:
            wave_g, parent_g, front_g = {}, {}, []

        def make_event(kind, cycles, meet, found=False, path=None, copy=True):
            return {
                'type': kind,
                'bidirectional': bidirectional,
                'wave_s': dict(wave_s) if copy else wave_s,
                'wave_g': dict(wave_g) if copy else wave_g,
                'front_s': list(front_s) if copy else [],
                'front_g': list(front_g) if copy else [],
                'meet': list(meet),
                'cycles': cycles,
                'expanded': len(wave_s) + len(wave_g),
                'found': found,
                'path': path or [],
            }

        if start == goal:
            yield make_event('finished', 0, [start], True, [start], copy=False)
            return

        cycles = 0
        meet = []
        while front_s and (front_g or not bidirectional):
            cycles += 1
            front_s = expand(front_s, wave_s, parent_s)
            if bidirectional:
                front_g = expand(front_g, wave_g, parent_g)
                meet = sorted(set([v for v in front_s if v in wave_g] +
                                  [v for v in front_g if v in wave_s]))
            else:
                meet = [goal] if goal in wave_s else []

            if snapshots:
                yield make_event('step', cycles, meet)
            if meet:
                break

        if not meet:
            front_s, front_g = [], []
            yield make_event('finished', cycles, [], False, [], copy=False)
            return

        if bidirectional:
            meeting = min(meet, key=lambda v: (wave_s[v] + wave_g[v], v))
        else:
            meeting = goal

        left = []
        v = meeting
        while v is not None:
            left.append(v)
            v = parent_s[v]
        left.reverse()
        right = []
        v = parent_g.get(meeting)
        while v is not None:
            right.append(v)
            v = parent_g[v]
        path = left + right

        front_s, front_g = [], []
        yield make_event('finished', cycles, [meeting], True, path, copy=False)

    @staticmethod
    def timed(grid, start, goal, op, bidirectional=True, repeats=20):
        final = None
        t0 = time.perf_counter()
        for _ in range(repeats):
            for ev in WaveEngine.search(grid, start, goal, op, bidirectional, snapshots=False):
                final = ev
        elapsed = (time.perf_counter() - t0) * 1000.0 / repeats
        if final is None or final['type'] == 'error':
            return {'type': 'error', 'found': False, 'path': [], 'cycles': 0,
                    'expanded': 0, 'time_ms': 0.0, 'meet': [],
                    'bidirectional': bidirectional}
        final = dict(final)
        final['time_ms'] = elapsed
        return final

    @staticmethod
    def reachable(grid, start, goal, op):
        return WaveEngine.timed(grid, start, goal, op, False, repeats=1)['found']


class WaveMazeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторна робота 4: Двонаправлений хвильовий пошук")
        self.root.geometry("1200x820")
        self.root.minsize(1000, 700)

        self.rows = 15
        self.cols = 15
        self.start_pos = (1, 1)
        self.goal_pos = (self.rows - 2, self.cols - 2)

        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

        self.wave_s = {}
        self.wave_g = {}
        self.front_s = set()
        self.front_g = set()
        self.meet_cells = set()

        self.operator_var = tk.StringVar(value="ortho")
        self.mode_var = tk.StringVar(value="bi")
        self.mouse_mode = tk.StringVar(value="wall")

        self.is_running = False
        self.is_paused = False
        self.search_generator = None
        self.search_stats = None
        self.anim_job = None
        self.animation_speed = 50
        self.drag_paint_val = None

        self.cycles_count = 0
        self.expanded_count = 0
        self.final_path = []
        self.last_result = None

        self._create_ui()
        self._init_empty_grid_with_border()

    def _create_ui(self):
        main_frame = ttk.Frame(self.root, padding=8)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(main_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        dim_box = ttk.LabelFrame(left_panel, text="Граф і лабіринт (порядок 10-20)", padding=6)
        dim_box.pack(fill=tk.X, pady=(0, 5))

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

        ttk.Button(dim_box, text="Застосувати розмірність",
                   command=self._on_apply_dimensions).pack(fill=tk.X, pady=2)
        ttk.Button(dim_box, text="🎲 Згенерувати лабіринт",
                   command=self.generate_random_maze).pack(fill=tk.X, pady=1)
        ttk.Button(dim_box, text="Очистити внутрішні стіни (0)",
                   command=self.clear_all_obstacles).pack(fill=tk.X, pady=1)
        ttk.Button(dim_box, text="▦ Показати матрицю лабіринту",
                   command=self.show_matrix_window).pack(fill=tk.X, pady=1)
        self.lbl_order = ttk.Label(dim_box, text="", font=("Helvetica", 8))
        self.lbl_order.pack(anchor=tk.W, pady=(3, 0))

        node_box = ttk.LabelFrame(left_panel, text="Вершини графу", padding=6)
        node_box.pack(fill=tk.X, pady=(0, 5))

        st_row = ttk.Frame(node_box)
        st_row.pack(fill=tk.X, pady=1)
        ttk.Label(st_row, text="Початкова (S):").pack(side=tk.LEFT)
        self.lbl_start_coords = ttk.Label(st_row, text=str(self.start_pos),
                                          font=("Helvetica", 9, "bold"), foreground="#2d6a4f")
        self.lbl_start_coords.pack(side=tk.RIGHT)

        gl_row = ttk.Frame(node_box)
        gl_row.pack(fill=tk.X, pady=1)
        ttk.Label(gl_row, text="Цільова (G):").pack(side=tk.LEFT)
        self.lbl_goal_coords = ttk.Label(gl_row, text=str(self.goal_pos),
                                         font=("Helvetica", 9, "bold"), foreground="#d90429")
        self.lbl_goal_coords.pack(side=tk.RIGHT)

        ttk.Label(node_box, text="Інструмент миші (ЛКМ / протягування):").pack(anchor=tk.W, pady=(4, 1))
        tool_row = ttk.Frame(node_box)
        tool_row.pack(fill=tk.X)
        ttk.Radiobutton(tool_row, text="Стіна (-1/0)", variable=self.mouse_mode, value="wall").pack(side=tk.LEFT)
        ttk.Radiobutton(tool_row, text="Старт", variable=self.mouse_mode, value="start").pack(side=tk.LEFT, padx=3)
        ttk.Radiobutton(tool_row, text="Ціль", variable=self.mouse_mode, value="goal").pack(side=tk.LEFT)

        op_box = ttk.LabelFrame(left_panel, text="Оператор переходу", padding=6)
        op_box.pack(fill=tk.X, pady=(0, 5))
        for val in ("ortho", "diag", "combined"):
            ttk.Radiobutton(op_box, text=OP_NAMES[val], variable=self.operator_var, value=val,
                            command=self.reset_search_state).pack(anchor=tk.W, pady=1)

        mode_box = ttk.LabelFrame(left_panel, text="Тип пошуку", padding=6)
        mode_box.pack(fill=tk.X, pady=(0, 5))
        ttk.Radiobutton(mode_box, text="Двонаправлений (S ⇄ G)", variable=self.mode_var, value="bi",
                        command=self.reset_search_state).pack(anchor=tk.W, pady=1)
        ttk.Radiobutton(mode_box, text="Однонаправлений (S → G), для порівняння",
                        variable=self.mode_var, value="uni",
                        command=self.reset_search_state).pack(anchor=tk.W, pady=1)

        ctrl_box = ttk.LabelFrame(left_panel, text="Керування хвильовим пошуком", padding=6)
        ctrl_box.pack(fill=tk.X, pady=(0, 5))

        b_row1 = ttk.Frame(ctrl_box)
        b_row1.pack(fill=tk.X, pady=2)
        self.btn_run = ttk.Button(b_row1, text="▶ Старт", command=self.start_auto_search)
        self.btn_run.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        self.btn_pause = ttk.Button(b_row1, text="⏸ Пауза", command=self.pause_search, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        b_row2 = ttk.Frame(ctrl_box)
        b_row2.pack(fill=tk.X, pady=2)
        self.btn_step = ttk.Button(b_row2, text="⏭ Крок (цикл)", command=self.step_search)
        self.btn_step.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        self.btn_reset = ttk.Button(b_row2, text="↺ Скинути", command=self.reset_search_state)
        self.btn_reset.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        ttk.Label(ctrl_box, text="Час затримки візуалізації (мс):").pack(anchor=tk.W, pady=(4, 0))
        self.lbl_speed = ttk.Label(ctrl_box, text=f"Затримка: {self.animation_speed} мс",
                                   font=("Helvetica", 8))
        self.speed_slider = ttk.Scale(ctrl_box, from_=600, to=5, orient=tk.HORIZONTAL,
                                      command=self._on_speed_changed)
        self.speed_slider.set(self.animation_speed)
        self.speed_slider.pack(fill=tk.X)
        self.lbl_speed.pack(anchor=tk.E)

        res_box = ttk.LabelFrame(left_panel, text="Результати та дослідження", padding=6)
        res_box.pack(fill=tk.X)
        res_box.columnconfigure(0, weight=1)
        res_box.columnconfigure(1, weight=1)

        self.btn_results = ttk.Button(res_box, text="⧉ Результати", command=self.show_results_window,
                                      state=tk.DISABLED)
        self.btn_results.grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        ttk.Button(res_box, text="⚖ Порівняння", command=self.show_compare_window).grid(
            row=0, column=1, sticky="ew", padx=1, pady=1)
        ttk.Button(res_box, text="📈 Серійне дослідж.", command=self.show_statistics_window).grid(
            row=1, column=0, sticky="ew", padx=1, pady=1)
        ttk.Button(res_box, text="📖 Довідка", command=self.show_help_window).grid(
            row=1, column=1, sticky="ew", padx=1, pady=1)

        self.lbl_status = ttk.Label(canvas_frame, text="", font=("Helvetica", 10, "bold"))
        self.lbl_status.pack(side=tk.BOTTOM, anchor=tk.W, pady=(4, 0))

        legend = ttk.Frame(canvas_frame)
        legend.pack(side=tk.BOTTOM, fill=tk.X, pady=(4, 0))
        for color, text in ((COL_S_FRONT, "фронт хвилі від S"), (COL_G_FRONT, "фронт хвилі від G"),
                            (COL_MEET, "зустріч хвиль"), (COL_PATH_FILL, "найкоротший шлях")):
            tk.Label(legend, bg=color, width=2, relief=tk.SOLID, bd=1).pack(side=tk.LEFT, padx=(0, 3))
            ttk.Label(legend, text=text, font=("Helvetica", 8)).pack(side=tk.LEFT, padx=(0, 10))

        self.canvas = tk.Canvas(canvas_frame, bg="#ffffff", highlightthickness=1,
                                highlightbackground="#b0b0b0")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Configure>", lambda e: self.redraw_canvas())
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

    @staticmethod
    def _empty_grid(rows, cols):
        grid = [[0 for _ in range(cols)] for _ in range(rows)]
        for r in range(rows):
            grid[r][0] = -1
            grid[r][cols - 1] = -1
        for c in range(cols):
            grid[0][c] = -1
            grid[rows - 1][c] = -1
        return grid

    def _init_empty_grid_with_border(self):
        self.grid = self._empty_grid(self.rows, self.cols)
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
            old_grid, old_r, old_c = self.grid, self.rows, self.cols

            self.rows, self.cols = r, c
            self.grid = self._empty_grid(r, c)
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

    @staticmethod
    def _build_random_maze(rows, cols, start, goal):
        grid = WaveMazeApp._empty_grid(rows, cols)

        def divide(r1, r2, c1, c2):
            if r2 - r1 < 2 or c2 - c1 < 2:
                return
            width, height = c2 - c1, r2 - r1
            horizontal = height > width if width != height else random.choice([True, False])

            if horizontal:
                wall_r = random.randint(r1 + 1, r2 - 1)
                openings = {random.randint(c1, c2)}
                if c2 - c1 > 3 and random.random() < 0.45:
                    openings.add(random.randint(c1, c2))
                for c in range(c1, c2 + 1):
                    grid[wall_r][c] = 0 if c in openings else -1
                divide(r1, wall_r - 1, c1, c2)
                divide(wall_r + 1, r2, c1, c2)
            else:
                wall_c = random.randint(c1 + 1, c2 - 1)
                openings = {random.randint(r1, r2)}
                if r2 - r1 > 3 and random.random() < 0.45:
                    openings.add(random.randint(r1, r2))
                for r in range(r1, r2 + 1):
                    grid[r][wall_c] = 0 if r in openings else -1
                divide(r1, r2, c1, wall_c - 1)
                divide(r1, r2, wall_c + 1, c2)

        divide(1, rows - 2, 1, cols - 2)

        sr, sc = start
        gr, gc = goal
        grid[sr][sc] = 0
        grid[gr][gc] = 0
        for r_pos, c_pos in (start, goal):
            nbrs = []
            for dr, dc in WaveEngine.ORTHO:
                nr, nc = r_pos + dr, c_pos + dc
                if 0 < nr < rows - 1 and 0 < nc < cols - 1:
                    nbrs.append((nr, nc))
            if nbrs and all(grid[nr][nc] == -1 for nr, nc in nbrs):
                fnr, fnc = random.choice(nbrs)
                grid[fnr][fnc] = 0
        return grid

    @staticmethod
    def _random_field(n, density, start, goal):
        grid = WaveMazeApp._empty_grid(n, n)
        for r in range(1, n - 1):
            for c in range(1, n - 1):
                if random.random() < density:
                    grid[r][c] = -1
        grid[start[0]][start[1]] = 0
        grid[goal[0]][goal[1]] = 0
        return grid

    def generate_random_maze(self):
        self.reset_search_state()
        op = self.operator_var.get()
        grid = None
        for _ in range(60):
            grid = self._build_random_maze(self.rows, self.cols, self.start_pos, self.goal_pos)
            if WaveEngine.reachable(grid, self.start_pos, self.goal_pos, op):
                break
        self.grid = grid
        self.redraw_canvas()

    def clear_all_obstacles(self):
        self.reset_search_state()
        self._init_empty_grid_with_border()

    MARGIN = 24

    def _geometry(self):
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw <= 10 or ch <= 10:
            return None
        m = self.MARGIN
        cell = min((cw - 2 * m) / self.cols, (ch - 2 * m) / self.rows)
        sx = (cw - cell * self.cols) / 2
        sy = (ch - cell * self.rows) / 2
        return cell, sx, sy

    def _get_cell_at(self, x, y):
        geo = self._geometry()
        if geo is None:
            return None
        cell, sx, sy = geo
        if not (sx <= x <= sx + cell * self.cols and sy <= y <= sy + cell * self.rows):
            return None
        c = int((x - sx) // cell)
        r = int((y - sy) // cell)
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return (r, c)
        return None

    def _has_search_data(self):
        return bool(self.wave_s or self.wave_g or self.final_path)

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
                if self._has_search_data():
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
                if self._has_search_data():
                    self.reset_search_state()
                else:
                    self.redraw_canvas()

    def _on_canvas_release(self, event):
        self.drag_paint_val = None

    def _on_speed_changed(self, val):
        self.animation_speed = int(float(val))
        self.lbl_speed.config(text=f"Затримка: {self.animation_speed} мс")

    def _is_bidirectional(self):
        return self.mode_var.get() == "bi"

    def _prepare_search(self):
        self.reset_search_state()
        op = self.operator_var.get()
        bi = self._is_bidirectional()
        self.search_stats = WaveEngine.timed(self.grid, self.start_pos, self.goal_pos, op, bi)
        self.search_generator = WaveEngine.search(self.grid, self.start_pos, self.goal_pos, op, bi, True)
        self.is_running = True

    def start_auto_search(self):
        if not self.is_running:
            self._prepare_search()
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
            self._prepare_search()
            self.is_paused = True
            self.btn_run.config(text="▶ Продовжити", state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED)
        self._execute_single_step()

    def _execute_single_step(self):
        if not self.search_generator:
            return False
        try:
            res = next(self.search_generator)
            if res['type'] == 'error':
                messagebox.showerror("Помилка", res['msg'], parent=self.root)
                self.reset_search_state()
                return False

            self.cycles_count = res['cycles']
            self.expanded_count = res['expanded']
            self.wave_s = res['wave_s']
            self.wave_g = res['wave_g']
            self.front_s = set(res['front_s'])
            self.front_g = set(res['front_g'])
            self.meet_cells = set(res['meet'])

            if res['type'] == 'step':
                self.redraw_canvas()
                return True

            self.final_path = res['path']
            self.is_running = False
            self.is_paused = False
            self._cancel_scheduled_anim()
            self.btn_run.config(text="▶ Старт", state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED)
            self.btn_step.config(state=tk.DISABLED)
            self.btn_results.config(state=tk.NORMAL)
            self._build_last_result(res)
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

    def _build_last_result(self, res):
        op = self.operator_var.get()
        bi = res['bidirectional']
        current = self.search_stats
        other = WaveEngine.timed(self.grid, self.start_pos, self.goal_pos, op, not bi)
        self.last_result = {
            'bidirectional': bi,
            'op': op,
            'start': self.start_pos,
            'goal': self.goal_pos,
            'rows': self.rows,
            'cols': self.cols,
            'order': self._graph_order(),
            'meet': res['meet'],
            'bi': current if bi else other,
            'uni': other if bi else current,
        }

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
        self.search_stats = None
        self.last_result = None
        self.wave_s = {}
        self.wave_g = {}
        self.front_s = set()
        self.front_g = set()
        self.meet_cells = set()
        self.final_path = []
        self.cycles_count = 0
        self.expanded_count = 0
        self.btn_run.config(text="▶ Старт", state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED)
        self.btn_step.config(state=tk.NORMAL)
        self.btn_results.config(state=tk.DISABLED)
        self.redraw_canvas()

    def _graph_order(self):
        return sum(row.count(0) for row in self.grid)

    @staticmethod
    def _tint_s(w):
        t = max(150, 242 - w * 5)
        return f"#{t:02x}{t:02x}ff"

    @staticmethod
    def _tint_g(w):
        g = max(165, 236 - w * 4)
        b = max(95, 205 - w * 8)
        return f"#ff{g:02x}{b:02x}"

    def redraw_canvas(self):
        self.lbl_order.config(
            text=f"Матриця {self.rows}×{self.cols}; порядок графу |V| = {self._graph_order()} (прохідних вершин)")
        self.lbl_status.config(
            text=f"Цикл хвилі: {self.cycles_count}    |    Розкрито (позначено) вершин: {self.expanded_count}")

        self.canvas.delete("all")
        geo = self._geometry()
        if geo is None:
            return
        cell_size, start_x, start_y = geo
        path_set = set(self.final_path)

        if cell_size >= 16:
            for c in range(self.cols):
                self.canvas.create_text(start_x + (c + 0.5) * cell_size, start_y - 10, text=str(c),
                                        font=("Helvetica", 7), fill="#868e96")
            for r in range(self.rows):
                self.canvas.create_text(start_x - 11, start_y + (r + 0.5) * cell_size, text=str(r),
                                        font=("Helvetica", 7), fill="#868e96")

        for r in range(self.rows):
            for c in range(self.cols):
                x1 = start_x + c * cell_size
                y1 = start_y + r * cell_size
                x2, y2 = x1 + cell_size, y1 + cell_size
                pos = (r, c)
                val = self.grid[r][c]

                fill_col, outline_col, txt_col, label_txt = "#ffffff", "#dee2e6", "#495057", str(val)

                if val == -1:
                    fill_col, outline_col, txt_col, label_txt = "#2b2d42", "#1d1e2c", "#8d99ae", "-1"
                else:
                    in_s = pos in self.wave_s
                    in_g = pos in self.wave_g
                    if in_s:
                        label_txt = str(self.wave_s[pos])
                        fill_col = self._tint_s(self.wave_s[pos])
                    if in_g:
                        label_txt = str(self.wave_g[pos])
                        fill_col = self._tint_g(self.wave_g[pos])
                    if in_s and in_g:
                        label_txt = f"{self.wave_s[pos]}|{self.wave_g[pos]}"
                        fill_col = "#e9d8fd"

                    if pos in self.front_s:
                        fill_col, outline_col, txt_col = COL_S_FRONT, "#2b3fb8", "#ffffff"
                    elif pos in self.front_g:
                        fill_col, outline_col, txt_col = COL_G_FRONT, "#c46a00", "#ffffff"

                    if pos in path_set:
                        fill_col, outline_col, txt_col = COL_PATH_FILL, COL_PATH_LINE, "#000000"
                    if pos in self.meet_cells:
                        fill_col, outline_col, txt_col = COL_MEET, "#5a189a", "#ffffff"

                    if pos == self.start_pos:
                        fill_col, outline_col, txt_col = "#52b788", "#2d6a4f", "#ffffff"
                        label_txt = "S:0" if pos in self.wave_s else "S"
                    elif pos == self.goal_pos:
                        fill_col, outline_col, txt_col = "#e63946", "#ba181b", "#ffffff"
                        if pos in self.wave_g:
                            label_txt = f"G:{self.wave_g[pos]}"
                        elif pos in self.wave_s:
                            label_txt = f"G:{self.wave_s[pos]}"
                        else:
                            label_txt = "G"

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill_col, outline=outline_col, width=1.5)
                k = 0.26 if len(label_txt) > 3 else 0.32
                f_size = max(6, int(cell_size * k))
                is_bold = "bold" if (pos in (self.start_pos, self.goal_pos) or pos in path_set
                                     or pos in self.meet_cells) else "normal"
                self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=label_txt,
                                        font=("Helvetica", f_size, is_bold), fill=txt_col, tags="lbl")

        if len(self.final_path) > 1:
            pts = []
            for r, c in self.final_path:
                pts.extend([start_x + c * cell_size + cell_size / 2,
                            start_y + r * cell_size + cell_size / 2])
            self.canvas.create_line(pts, fill=COL_PATH_LINE, width=max(2.0, cell_size * 0.09),
                                    capstyle=tk.ROUND, joinstyle=tk.ROUND)
            self.canvas.tag_raise("lbl")

    @staticmethod
    def _gain(old, new):
        return (old - new) / old * 100.0 if old else 0.0

    @staticmethod
    def _make_table(parent, columns, widths, height):
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=height)
        for col, w in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor=tk.CENTER)
        return tree

    @staticmethod
    def _stat_row(name, s):
        if s['found']:
            return (name, len(s['path']), s['cycles'], s['expanded'], f"{s['time_ms']:.4f}")
        return (name, "недосяжна", s['cycles'], s['expanded'], f"{s['time_ms']:.4f}")

    def show_results_window(self):
        res = self.last_result
        if not res:
            return
        bi = res['bidirectional']
        cur = res['bi'] if bi else res['uni']

        win = tk.Toplevel(self.root)
        win.title("Результати пошуку")
        win.geometry("680x760")
        win.transient(self.root)

        frame = ttk.Frame(win, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        kind = "ДВОНАПРАВЛЕНОГО" if bi else "ОДНОНАПРАВЛЕНОГО"
        ttk.Label(frame, text=f"РЕЗУЛЬТАТИ {kind} ХВИЛЬОВОГО ПОШУКУ",
                  font=("Helvetica", 11, "bold")).pack(pady=(0, 8))

        info = ttk.LabelFrame(frame, text="Параметри та кількісні показники", padding=8)
        info.pack(fill=tk.X, pady=(0, 8))

        def line(text):
            ttk.Label(info, text=text).pack(anchor=tk.W)

        line(f"• Матриця лабіринту: {res['rows']}×{res['cols']}; порядок графу |V| = {res['order']} прохідних вершин")
        line(f"• Початкова S: {res['start']}    цільова G: {res['goal']}    (рядок, стовпець)")
        line(f"• Оператор переходу: {OP_NAMES[res['op']]}")
        if cur['found']:
            line(f"• Віддаль між S і G (кількість вершин шляху): {len(cur['path'])}")
            line(f"• Кількість переходів (ребер): {len(cur['path']) - 1}")
            if bi and res['meet']:
                line(f"• Вершина зустрічі хвиль: {res['meet'][0]}")
        else:
            line("• Цільова вершина НЕДОСЯЖНА з початкової для обраного оператора переходу")
        line(f"• Кількість циклів (кроків хвилі): {cur['cycles']}")
        line(f"• Кількість розкритих (позначених) вершин: {cur['expanded']}")
        line(f"• Час здійснення пошуку: {cur['time_ms']:.4f} мс")

        cmp_box = ttk.LabelFrame(frame, text="Порівняння: однонаправлений і двонаправлений (той самий лабіринт)",
                                 padding=8)
        cmp_box.pack(fill=tk.X, pady=(0, 8))
        cols = ("Алгоритм", "Вершин у шляху", "Циклів", "Розкрито вершин", "Час, мс")
        tree = self._make_table(cmp_box, cols, (135, 125, 70, 135, 80), 2)
        tree.insert("", tk.END, values=self._stat_row("Однонаправлений", res['uni']))
        tree.insert("", tk.END, values=self._stat_row("Двонаправлений", res['bi']))
        tree.pack(fill=tk.X)
        if res['uni']['found'] and res['bi']['found']:
            g_c = self._gain(res['uni']['cycles'], res['bi']['cycles'])
            g_e = self._gain(res['uni']['expanded'], res['bi']['expanded'])
            ttk.Label(cmp_box, text=f"Двонаправлений відносно однонаправленого: циклів {-g_c:+.1f}%, "
                                    f"розкритих вершин {-g_e:+.1f}%",
                      foreground="#2d6a4f", font=("Helvetica", 9, "bold")).pack(anchor=tk.W, pady=(4, 0))

        path_box = ttk.LabelFrame(frame, text="Координати вершин найкоротшого шляху (рядок, стовпець)", padding=8)
        path_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        txt = tk.Text(path_box, height=8, wrap=tk.WORD, font=("Consolas", 10))
        scroll = ttk.Scrollbar(path_box, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        if cur['found']:
            txt.insert(tk.END, " -> ".join(f"({r},{c})" for r, c in cur['path']))
        else:
            txt.insert(tk.END, "Шляху не існує.")
        txt.config(state=tk.DISABLED)

        ttk.Button(frame, text="Закрити", command=win.destroy).pack(anchor=tk.E)

    def show_matrix_window(self):
        win = tk.Toplevel(self.root)
        win.title("Матриця лабіринту (-1 непрохідна, 0 прохідна)")
        win.geometry("640x520")
        win.transient(self.root)

        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text=f"Розмірність {self.rows}×{self.cols};  S = {self.start_pos},  G = {self.goal_pos}"
                              f"  (вершини S і G мають значення 0)",
                  font=("Helvetica", 9, "bold")).pack(anchor=tk.W, pady=(0, 6))

        text = "\n".join(" ".join(f"{v:2d}" for v in row) for row in self.grid)

        box = ttk.Frame(frame)
        box.pack(fill=tk.BOTH, expand=True)
        txt = tk.Text(box, wrap=tk.NONE, font=("Consolas", 10))
        sy = ttk.Scrollbar(box, orient=tk.VERTICAL, command=txt.yview)
        sx = ttk.Scrollbar(box, orient=tk.HORIZONTAL, command=txt.xview)
        txt.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side=tk.RIGHT, fill=tk.Y)
        sx.pack(side=tk.BOTTOM, fill=tk.X)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        txt.insert(tk.END, text)
        txt.config(state=tk.DISABLED)

        def copy():
            win.clipboard_clear()
            win.clipboard_append(text)

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btns, text="Копіювати", command=copy).pack(side=tk.LEFT)
        ttk.Button(btns, text="Закрити", command=win.destroy).pack(side=tk.RIGHT)

    def show_compare_window(self):
        s, g = self.start_pos, self.goal_pos
        if self.grid[s[0]][s[1]] == -1 or self.grid[g[0]][g[1]] == -1:
            messagebox.showerror("Помилка", "Start або Goal розміщені на непрохідній клітинці (-1)!",
                                 parent=self.root)
            return
        self.root.config(cursor="watch")
        self.root.update_idletasks()

        results = {}
        for op in ("ortho", "diag", "combined"):
            for bi in (False, True):
                results[(op, bi)] = WaveEngine.timed(self.grid, s, g, op, bi)
        self.root.config(cursor="")

        win = tk.Toplevel(self.root)
        win.title("Порівняння операторів переходу та алгоритмів")
        win.geometry("860x560")
        win.transient(self.root)
        frame = ttk.Frame(win, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=f"Поточний лабіринт {self.rows}×{self.cols}, порядок графу |V| = "
                              f"{self._graph_order()},  S = {s},  G = {g}",
                  font=("Helvetica", 10, "bold")).pack(anchor=tk.W, pady=(0, 6))

        cols = ("Оператор", "Алгоритм", "Вершин у шляху", "Циклів", "Розкрито вершин", "Час, мс")
        tree = self._make_table(frame, cols, (200, 130, 110, 80, 120, 90), 6)
        for op in ("ortho", "diag", "combined"):
            for bi in (False, True):
                st = results[(op, bi)]
                name = "Двонаправлений" if bi else "Однонаправлений"
                row = self._stat_row(name, st)
                tree.insert("", tk.END, values=(OP_SHORT[op],) + row)
        tree.pack(fill=tk.X)

        notes = ttk.LabelFrame(frame, text="Висновки за таблицею", padding=8)
        notes.pack(fill=tk.BOTH, expand=True, pady=(10, 6))
        out = []
        for op in ("ortho", "diag", "combined"):
            u, b = results[(op, False)], results[(op, True)]
            if u['found'] and b['found']:
                out.append(f"• {OP_SHORT[op]}: шлях {len(b['path'])} вершин; двонаправлений пошук - "
                           f"циклів {b['cycles']} проти {u['cycles']} "
                           f"({-self._gain(u['cycles'], b['cycles']):+.0f}%), розкритих вершин "
                           f"{b['expanded']} проти {u['expanded']} "
                           f"({-self._gain(u['expanded'], b['expanded']):+.0f}%).")
            else:
                out.append(f"• {OP_SHORT[op]}: цільова вершина недосяжна (для оператора «по діагоналях» "
                           f"досяжні лише клітинки з тією ж парністю r+c, що й у S).")
        lens = {op: len(results[(op, True)]['path']) for op in ("ortho", "diag", "combined")
                if results[(op, True)]['found']}
        if lens:
            best = min(lens, key=lens.get)
            out.append(f"• Найкоротший шлях дає оператор «{OP_SHORT[best]}» ({lens[best]} вершин).")
        ttk.Label(notes, text="\n".join(out), wraplength=800, justify=tk.LEFT).pack(anchor=tk.W)

        ttk.Button(frame, text="Закрити", command=win.destroy).pack(anchor=tk.E)

    def show_statistics_window(self):
        win = tk.Toplevel(self.root)
        win.title("Серійне дослідження: різні розміри графу та оператори")
        win.geometry("1080x520")
        win.transient(self.root)
        frame = ttk.Frame(win, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Випадкові квадратні поля з перешкодами; S = (1,1), G = (n-2, n-2) - протилежні кути. "
                              "Усереднення по вибірці (враховуються лише поля, де шлях існує).",
                  wraplength=1000).pack(anchor=tk.W, pady=(0, 6))

        ctrl = ttk.Frame(frame)
        ctrl.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(ctrl, text="Щільність перешкод, %:").pack(side=tk.LEFT)
        sp_dens = ttk.Spinbox(ctrl, from_=0, to=50, width=4)
        sp_dens.set(25)
        sp_dens.pack(side=tk.LEFT, padx=(2, 12))
        ttk.Label(ctrl, text="Розмір вибірки:").pack(side=tk.LEFT)
        sp_n = ttk.Spinbox(ctrl, from_=5, to=300, width=5)
        sp_n.set(60)
        sp_n.pack(side=tk.LEFT, padx=(2, 12))

        cols = ("Розмір", "Оператор", "Вибірка",
                "Однонапр.: цикли", "Однонапр.: розкрито", "Двонапр.: цикли", "Двонапр.: розкрито",
                "Менше розкритих, %", "Час однонапр., мс", "Час двонапр., мс")
        tree = self._make_table(frame, cols, (60, 170, 65, 105, 115, 100, 110, 115, 115, 110), 12)
        tree.pack(fill=tk.BOTH, expand=True)

        def run():
            try:
                density = int(sp_dens.get()) / 100.0
                samples = int(sp_n.get())
                if not (0 <= density <= 0.5 and 5 <= samples <= 300):
                    raise ValueError
            except ValueError:
                messagebox.showerror("Помилка", "Щільність 0-50 %, вибірка 5-300.", parent=win)
                return
            win.config(cursor="watch")
            win.update_idletasks()
            tree.delete(*tree.get_children())
            for n in (10, 15, 20):
                s, g = (1, 1), (n - 2, n - 2)
                fields = [self._random_field(n, density, s, g) for _ in range(samples)]
                for op in ("ortho", "diag", "combined"):
                    acc = [0, 0, 0.0, 0, 0, 0.0]
                    used = 0
                    for fld in fields:
                        ru = WaveEngine.timed(fld, s, g, op, False, repeats=1)
                        if not ru['found']:
                            continue
                        rb = WaveEngine.timed(fld, s, g, op, True, repeats=1)
                        used += 1
                        acc[0] += ru['cycles']; acc[1] += ru['expanded']; acc[2] += ru['time_ms']
                        acc[3] += rb['cycles']; acc[4] += rb['expanded']; acc[5] += rb['time_ms']
                    if used == 0:
                        tree.insert("", tk.END, values=(f"{n}×{n}", OP_SHORT[op], 0, "-", "-", "-", "-", "-", "-", "-"))
                        continue
                    a = [x / used for x in acc]
                    tree.insert("", tk.END, values=(
                        f"{n}×{n}", OP_SHORT[op], used,
                        f"{a[0]:.1f}", f"{a[1]:.1f}", f"{a[3]:.1f}", f"{a[4]:.1f}",
                        f"{self._gain(a[1], a[4]):.1f}", f"{a[2]:.4f}", f"{a[5]:.4f}"))
            win.config(cursor="")

        ttk.Button(ctrl, text="▶ Запустити дослідження", command=run).pack(side=tk.LEFT)
        ttk.Button(ctrl, text="Закрити", command=win.destroy).pack(side=tk.RIGHT)
        run()

    def show_help_window(self):
        win = tk.Toplevel(self.root)
        win.title("Довідка: організація двонаправленого хвильового пошуку")
        win.geometry("860x700")
        win.transient(self.root)
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        txt = tk.Text(frame, wrap=tk.WORD, font=("Helvetica", 10), padx=8, pady=8)
        sc = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=sc.set)
        sc.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        txt.tag_configure("h", font=("Helvetica", 11, "bold"), spacing1=8, spacing3=3)
        for block in HELP_TEXT:
            if block.startswith("#"):
                txt.insert(tk.END, block[1:].strip() + "\n", "h")
            else:
                txt.insert(tk.END, block.strip() + "\n")
        txt.config(state=tk.DISABLED)


HELP_TEXT = [
    "# 1. Як організовується «хвиля» у двонаправленому пошуку",
    "Одночасно запускаються дві незалежні хвилі: від початкової вершини S (мітки dS = 0, 1, 2, …) і від "
    "цільової вершини G (мітки dG = 0, 1, 2, …). Кожна хвиля має свій фронт (клітинки з останньою міткою), "
    "свою таблицю міток і свої вказівники на попередників. За один цикл кожен фронт розширюється на один "
    "шар: усім прохідним непозначеним сусідам клітинок фронту (згідно з оператором переходу) присвоюється "
    "мітка «поточна + 1» у власній хвилі. Хвилі рухаються назустріч одна одній і зустрічаються, коли "
    "деяка клітинка отримує мітки обох хвиль.",

    "# 2. Відмінності в організації циклу порівняно з однонаправленим пошуком",
    "• Дві структури даних (мітки та фронт для S і для G) замість однієї.\n"
    "• Умова завершення - не «досягнуто G», а «фронти зустрілись» (клітинка позначена обома хвилями). "
    "Перевірка виконується наприкінці кожного циклу.\n"
    "• Хвилі рухаються одночасно, тому за один цикл може виникнути кілька точок зустрічі, і їхні суми "
    "dS + dG можуть відрізнятись на 1. Обирається клітинка з мінімальною сумою - це гарантує "
    "найкоротший шлях.\n"
    "• Умова недосяжності: порожнім став фронт будь-якої з двох хвиль (а не лише хвилі від S).\n"
    "• Шлях відновлюється з двох частин: від точки зустрічі назад до S (вказівники хвилі S) і від точки "
    "зустрічі до G (вказівники хвилі G).\n"
    "• Кількість циклів приблизно вдвічі менша: якщо шлях має L переходів, потрібно близько L/2 циклів.",

    "# 3. Оператори переходу: переваги та недоліки",
    "«Вверх-вниз-вправо-вліво» (4 сусіди). + Простий, мінімум перевірок на клітинку, вузький фронт "
    "(ромбоподібна хвиля), шлях не «протискується» між діагональними стінами. − Шляхи довші (відстань "
    "за Манхеттеном), більше циклів.",
    "«Перехід по діагоналях» (4 діагональні сусіди). + Хвиля швидко розходиться по діагоналі. − З клітинки "
    "можна потрапити лише в клітинки тієї ж парності (r + c): якщо S і G мають різну парність, шлях не "
    "існує; можливе «просочування» між двома діагональними стінами; шляхи, як правило, неприродні.",
    "Комбінація (8 сусідів). + Найкоротші шляхи (відстань за Чебишовим), найменше циклів, немає проблеми "
    "парності. − Найбільше перевірок на клітинку і найширший фронт (більше клітинок за шар); шлях може "
    "«зрізати» кути перешкод.",

    "# 4. Переваги двонаправленого пошуку та за рахунок чого вони досягаються",
    "1) Кількість циклів приблизно вдвічі менша. Кожна хвиля має пройти лише половину шляху (~L/2 шарів "
    "замість L), а обидві хвилі просуваються одночасно (паралельно) - це стабільний ефект, він видний у "
    "будь-якому лабіринті (див. «Серійне дослідження»: ≈ -50% циклів).\n"
    "2) Менше розкритих вершин. У необмеженому двовимірному просторі однонаправлена хвиля охоплює область "
    "радіуса L (площа ~ L²), а дві зустрічні хвилі - дві області радіуса ~L/2 (сумарно ~ L²/2), тобто "
    "приблизно вдвічі менше. Що більше розгалужень (більший ступінь розгалуження графу), то більший "
    "виграш. Проте на полях розміром до 20×20 хвилі впираються в межі поля й перешкоди, тому реальна "
    "економія розкритих вершин помірна (порядку 5-30%), а на короткому прямому шляху для оператора з "
    "8 сусідами вона може бути й нульовою чи від'ємною (обидві хвилі розкриваються «віялом»). У вузьких "
    "лабіринтах-коридорах виграш малий, бо хвиля й так не розгалужується.\n"
    "3) Недоліки: складніша реалізація, подвійний набір міток, перевірка перетину хвиль і вибір "
    "оптимальної точки зустрічі; на малих полях виграш у часі може нівелюватись накладними витратами.",
]


if __name__ == "__main__":
    root = tk.Tk()
    app = WaveMazeApp(root)
    root.mainloop()