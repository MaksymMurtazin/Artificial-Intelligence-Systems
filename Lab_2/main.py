import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
import time
import math


class GraphDFSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторна робота: Пошук у глибину (DFS) на графах")
        self.root.geometry("1300x820")
        self.root.minsize(1050, 700)

        self.nodes = {}
        self.edges = {}

        self.start_node = 1
        self.goal_node = 24
        self.traversal_order = "asc"
        self.search_mode = "first"
        
        self.is_running = False
        self.is_paused = False
        self.search_generator = None
        self.animation_speed = 300
        self.step_counter = 0
        self.expanded_nodes_count = 0
        self.start_time = 0.0
        self.elapsed_time = 0.0
        self.final_path = []
        
        self.dragged_node = None
        self.drag_start_pos = (0, 0)

        self._create_ui()
        self.load_default_graph(with_cross_edges=True)


    def _create_ui(self):
        main_frame = ttk.Frame(self.root, padding=6)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(main_frame, width=280)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))

        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_panel = ttk.Frame(main_frame, width=260)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 0))

        search_cfg_box = ttk.LabelFrame(left_panel, text="1. Параметри пошуку", padding=6)
        search_cfg_box.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(search_cfg_box, text="Початкова вершина (Start):").pack(anchor=tk.W)
        self.start_cb = ttk.Combobox(search_cfg_box, state="readonly")
        self.start_cb.pack(fill=tk.X, pady=(0, 4))
        self.start_cb.bind("<<ComboboxSelected>>", self._on_start_changed)

        ttk.Label(search_cfg_box, text="Цільова вершина (Goal):").pack(anchor=tk.W)
        self.goal_cb = ttk.Combobox(search_cfg_box, state="readonly")
        self.goal_cb.pack(fill=tk.X, pady=(0, 4))
        self.goal_cb.bind("<<ComboboxSelected>>", self._on_goal_changed)

        btn_swap = ttk.Button(search_cfg_box, text="⇄ Дзеркальна заміна (Start ↔ Goal)", command=self.swap_start_goal)
        btn_swap.pack(fill=tk.X, pady=2)

        ttk.Label(search_cfg_box, text="Напрямок обходу сусідів:").pack(anchor=tk.W, pady=(4, 0))
        self.order_var = tk.StringVar(value="asc")
        ttk.Radiobutton(search_cfg_box, text="За зростанням (Прямий)", variable=self.order_var, value="asc").pack(anchor=tk.W)
        ttk.Radiobutton(search_cfg_box, text="За спаданням (Зворотний)", variable=self.order_var, value="desc").pack(anchor=tk.W)

        ttk.Label(search_cfg_box, text="Алгоритм пошуку:").pack(anchor=tk.W, pady=(4, 0))
        self.mode_var = tk.StringVar(value="shortest")
        ttk.Radiobutton(search_cfg_box, text="DFS: Найкоротший (B&B)", variable=self.mode_var, value="shortest").pack(anchor=tk.W)
        ttk.Radiobutton(search_cfg_box, text="DFS: Перший знайдений", variable=self.mode_var, value="first").pack(anchor=tk.W)
        ttk.Radiobutton(search_cfg_box, text="BFS: Пошук у ширину", variable=self.mode_var, value="bfs").pack(anchor=tk.W)

        exec_box = ttk.LabelFrame(left_panel, text="2. Керування візуалізацією", padding=6)
        exec_box.pack(fill=tk.X, pady=(0, 6))

        btn_row1 = ttk.Frame(exec_box)
        btn_row1.pack(fill=tk.X, pady=2)
        self.btn_play = ttk.Button(btn_row1, text="▶ Авто", command=self.start_auto_search)
        self.btn_play.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        self.btn_pause = ttk.Button(btn_row1, text="⏸ Пауза", command=self.pause_search, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        btn_row2 = ttk.Frame(exec_box)
        btn_row2.pack(fill=tk.X, pady=2)
        self.btn_step = ttk.Button(btn_row2, text="⏭ Крок", command=self.step_search)
        self.btn_step.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        self.btn_reset = ttk.Button(btn_row2, text="↺ Скинути", command=self.reset_search_state)
        self.btn_reset.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        ttk.Label(exec_box, text="Швидкість анімації:").pack(anchor=tk.W, pady=(4, 0))
        self.speed_slider = ttk.Scale(exec_box, from_=800, to=40, orient=tk.HORIZONTAL, command=self._on_speed_changed)
        self.speed_slider.set(250)
        self.speed_slider.pack(fill=tk.X)

        edit_box = ttk.LabelFrame(left_panel, text="3. Ручна модифікація графа", padding=6)
        edit_box.pack(fill=tk.X, pady=(0, 6))

        v_row = ttk.Frame(edit_box)
        v_row.pack(fill=tk.X, pady=2)
        ttk.Button(v_row, text="+ Вершина", command=self.gui_add_node_dialog).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        ttk.Button(v_row, text="- Вершина", command=self.gui_remove_node_dialog).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        e_row = ttk.Frame(edit_box)
        e_row.pack(fill=tk.X, pady=2)
        ttk.Button(e_row, text="+ Ребро/Дуга", command=self.gui_add_edge_dialog).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        ttk.Button(e_row, text="- Ребро/Дуга", command=self.gui_remove_edge_dialog).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        ttk.Button(edit_box, text="⇄ Змінити ребро ↔ дуга (тип)", command=self.gui_toggle_edge_type_dialog).pack(fill=tk.X, pady=2)

        preset_box = ttk.LabelFrame(left_panel, text="4. Структура для дослідження", padding=6)
        preset_box.pack(fill=tk.X, pady=(0, 2))
        ttk.Button(preset_box, text="Граф із міжгілковими зв'язками (N=31)", command=lambda: self.load_default_graph(True)).pack(fill=tk.X, pady=1)
        ttk.Button(preset_box, text="Чисте дерево без циклів (N=31)", command=lambda: self.load_default_graph(False)).pack(fill=tk.X, pady=1)
        ttk.Button(preset_box, text="Хаотичний мережевий граф (N=32)", command=self.load_chaotic_graph).pack(fill=tk.X, pady=1)

        hint_lbl = ttk.Label(left_panel, text="Полотно: тягніть вершину лівою кнопкою миші; ЛКМ/ПКМ — встановити Start/Goal.", font=("Helvetica", 8), wraplength=260, foreground="#FF0000")
        hint_lbl.pack(fill=tk.X, pady=(6, 0))

        self.canvas = tk.Canvas(canvas_frame, bg="#ffffff", highlightthickness=1, highlightbackground="#cccccc")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._init_mouse_bindings()

        res_box = ttk.LabelFrame(right_panel, text="Результати пошуку", padding=8)
        res_box.pack(fill=tk.BOTH, expand=True)

        self.lbl_graph_order = ttk.Label(res_box, text="Порядок графу (|V|): 0", font=("Helvetica", 9))
        self.lbl_graph_order.pack(anchor=tk.W, pady=2)

        self.lbl_graph_size = ttk.Label(res_box, text="Розмір графу (|E|): 0", font=("Helvetica", 9))
        self.lbl_graph_size.pack(anchor=tk.W, pady=2)

        self.lbl_status = ttk.Label(res_box, text="Статус: Очікування", foreground="#0066cc", font=("Helvetica", 9, "bold"))
        self.lbl_status.pack(anchor=tk.W, pady=4)

        self.lbl_expanded = ttk.Label(res_box, text="Розкрито вершин: 0", font=("Helvetica", 9))
        self.lbl_expanded.pack(anchor=tk.W, pady=2)

        self.lbl_time = ttk.Label(res_box, text="Час пошуку: 0.00 мс", font=("Helvetica", 9))
        self.lbl_time.pack(anchor=tk.W, pady=2)

        self.lbl_length = ttk.Label(res_box, text="Довжина шляху: 0", font=("Helvetica", 9))
        self.lbl_length.pack(anchor=tk.W, pady=2)

        ttk.Label(res_box, text="Знайдений шлях:", font=("Helvetica", 9, "bold")).pack(anchor=tk.W, pady=(6, 2))
        
        self.txt_path = tk.Text(res_box, height=8, width=28, wrap=tk.WORD, font=("Consolas", 9))
        self.txt_path.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(res_box, text="Журнал кроків DFS:", font=("Helvetica", 9, "bold")).pack(anchor=tk.W, pady=(4, 2))
        self.txt_log = tk.Text(res_box, height=14, width=28, wrap=tk.WORD, font=("Consolas", 8), bg="#f8f9fa")
        self.txt_log.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        ttk.Button(res_box, text="⧉ Відкрити в окремому вікні", command=self.open_separate_results_window).pack(fill=tk.X)
        ttk.Button(res_box, text="⚖ Порівняти DFS та BFS (Таблиця)", command=self.open_comparison_window).pack(fill=tk.X, pady=(4, 0))


    def _init_mouse_bindings(self):
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)

    def _find_node_at(self, x, y):
        for nid, pos in self.nodes.items():
            if math.hypot(x - pos['x'], y - pos['y']) <= 16:
                return nid
        return None

    def _on_canvas_press(self, event):
        nid = self._find_node_at(event.x, event.y)
        if nid is not None:
            self.dragged_node = nid
            self.drag_start_pos = (event.x, event.y)

    def _on_canvas_drag(self, event):
        if self.dragged_node is not None:
            self.nodes[self.dragged_node]['x'] = max(20, min(event.x, self.canvas.winfo_width() - 20))
            self.nodes[self.dragged_node]['y'] = max(20, min(event.y, self.canvas.winfo_height() - 20))
            self.redraw_graph()

    def _on_canvas_release(self, event):
        if self.dragged_node is not None:
            dx = abs(event.x - self.drag_start_pos[0])
            dy = abs(event.y - self.drag_start_pos[1])
            if dx < 4 and dy < 4:
                self.start_node = self.dragged_node
                self.start_cb.set(str(self.start_node))
                self.log(f"Стартову вершину (Start) встановлено на: {self.start_node}")
                self.redraw_graph()
        self.dragged_node = None

    def _on_canvas_right_click(self, event):
        nid = self._find_node_at(event.x, event.y)
        if nid is not None:
            self.goal_node = nid
            self.goal_cb.set(str(self.goal_node))
            self.log(f"Цільову вершину (Goal) встановлено на: {self.goal_node}")
            self.redraw_graph()


    def load_default_graph(self, with_cross_edges=True):
        self.reset_search_state()
        self.nodes.clear()
        self.edges.clear()

        self.nodes[1] = {'x': 450, 'y': 60}

        branch_roots = [2, 3, 4, 5, 6]
        xs_level1 = [130, 290, 450, 610, 770]
        for idx, br_id in enumerate(branch_roots):
            self.nodes[br_id] = {'x': xs_level1[idx], 'y': 180}
            self.edges[(1, br_id)] = {'directed': False}

        level2_map = {
            2: [7, 8],
            3: [9, 10],
            4: [11, 12],
            5: [13, 14],
            6: [15, 16]
        }
        xs_level2 = {
            7: 90, 8: 170,
            9: 250, 10: 330,
            11: 410, 12: 490,
            13: 570, 14: 650,
            15: 730, 16: 810
        }
        for parent, children in level2_map.items():
            for child in children:
                self.nodes[child] = {'x': xs_level2[child], 'y': 330}
                self.edges[(parent, child)] = {'directed': False}

        level3_map = {
            7: [17, 18], 8: [19],
            9: [20, 21], 10: [22],
            11: [23, 24], 12: [25],
            13: [26, 27], 14: [28],
            15: [29, 30], 16: [31]
        }
        xs_level3 = {
            17: 60, 18: 110, 19: 170,
            20: 230, 21: 270, 22: 330,
            23: 390, 24: 430, 25: 490,
            26: 550, 27: 590, 28: 650,
            29: 710, 30: 750, 31: 810
        }
        for parent, children in level3_map.items():
            for child in children:
                self.nodes[child] = {'x': xs_level3[child], 'y': 480}
                self.edges[(parent, child)] = {'directed': False}

        if with_cross_edges:
            cross_edges = [
                (7, 9, False),
                (8, 10, False),
                (10, 11, False),
                (12, 13, True),
                (14, 15, False),
                (18, 20, False),
                (22, 23, True),
                (25, 26, False),
                (28, 29, True),
                (17, 31, False)
            ]
            for u, v, is_dir in cross_edges:
                key = (u, v) if is_dir else (min(u, v), max(u, v))
                self.edges[key] = {'directed': is_dir, 'curved': True}

        self._refresh_comboboxes()
        self.redraw_graph()
        self._update_graph_metrics()
        self.log(f"Завантажено граф: |V| = {len(self.nodes)}, |E| = {len(self.edges)}")

    def load_chaotic_graph(self):
        self.reset_search_state()
        self.nodes.clear()
        self.edges.clear()

        coords = {
            1: (450, 270), 2: (400, 210), 3: (500, 210), 4: (400, 330), 5: (500, 330),
            6: (280, 150), 7: (190, 110), 8: (120, 180), 9: (200, 230), 10: (290, 270),
            11: (150, 310), 12: (80, 260), 13: (90, 390), 14: (180, 420),
            15: (620, 150), 16: (710, 110), 17: (780, 180), 18: (700, 230), 19: (610, 270),
            20: (750, 310), 21: (820, 260), 22: (810, 390), 23: (720, 420),
            24: (270, 470), 25: (360, 520), 26: (450, 490), 27: (540, 520), 28: (630, 470),
            29: (450, 110), 30: (360, 80), 31: (540, 80), 32: (450, 570)
        }
        for nid, (x, y) in coords.items():
            self.nodes[nid] = {'x': x, 'y': y}

        raw_edges = [
            (1, 2, False), (1, 3, False), (1, 4, False), (1, 5, False),
            (2, 3, False), (4, 5, False), (2, 4, False), (3, 5, False),
            (2, 6, False), (4, 10, False), (1, 10, False),
            (6, 7, False), (7, 8, False), (8, 9, False), (9, 10, False),
            (6, 9, False), (8, 12, False), (12, 11, False), (9, 11, False),
            (11, 13, False), (13, 14, False), (14, 10, False), (11, 14, False),
            (3, 15, False), (5, 19, False), (1, 19, False),
            (15, 16, False), (16, 17, False), (17, 18, False), (18, 19, False),
            (15, 18, False), (17, 21, False), (21, 20, False), (18, 20, False),
            (20, 22, False), (22, 23, False), (23, 19, False), (20, 23, False),
            (29, 30, False), (29, 31, False), (7, 30, False), (16, 31, False), (2, 29, False),
            (14, 24, False), (24, 25, False), (25, 26, False), (26, 27, False),
            (27, 28, False), (28, 23, False), (26, 32, False), (4, 26, False), (5, 26, False),
            (10, 19, True),
            (24, 11, True),
            (23, 28, True),
            (29, 1, True),
            (25, 32, True),
            (27, 32, True)
        ]

        for u, v, is_dir in raw_edges:
            key = (u, v) if is_dir else (min(u, v), max(u, v))
            self.edges[key] = {'directed': is_dir}

        self.start_node = 8
        self.goal_node = 21
        self._refresh_comboboxes()
        self.redraw_graph()
        self._update_graph_metrics()
        self.log(f"Завантажено хаотичний мережевий граф: |V| = {len(self.nodes)}, |E| = {len(self.edges)}")


    def _refresh_comboboxes(self):
        sorted_nodes = sorted(self.nodes.keys())
        node_strs = [str(n) for n in sorted_nodes]
        self.start_cb['values'] = node_strs
        self.goal_cb['values'] = node_strs
        if self.start_node in self.nodes:
            self.start_cb.set(str(self.start_node))
        elif sorted_nodes:
            self.start_node = sorted_nodes[0]
            self.start_cb.set(str(self.start_node))

        if self.goal_node in self.nodes:
            self.goal_cb.set(str(self.goal_node))
        elif sorted_nodes:
            self.goal_node = sorted_nodes[-1]
            self.goal_cb.set(str(self.goal_node))

    def _update_graph_metrics(self):
        self.lbl_graph_order.config(text=f"Порядок графу (|V|): {len(self.nodes)}")
        self.lbl_graph_size.config(text=f"Розмір графу (|E|): {len(self.edges)}")

    def _on_start_changed(self, event):
        self.start_node = int(self.start_cb.get())
        self.redraw_graph()

    def _on_goal_changed(self, event):
        self.goal_node = int(self.goal_cb.get())
        self.redraw_graph()

    def swap_start_goal(self):
        self.start_node, self.goal_node = self.goal_node, self.start_node
        self.start_cb.set(str(self.start_node))
        self.goal_cb.set(str(self.goal_node))
        self.reset_search_state()
        self.log(f"Дзеркально замінено: Start = {self.start_node}, Goal = {self.goal_node}")

    def _on_speed_changed(self, val):
        self.animation_speed = int(float(val))


    def get_neighbors(self, u):
        neighbors = []
        for (src, dst), meta in self.edges.items():
            if meta['directed']:
                if src == u:
                    neighbors.append(dst)
            else:
                if src == u:
                    neighbors.append(dst)
                elif dst == u:
                    neighbors.append(src)
        
        direction = self.order_var.get()
        neighbors = sorted(list(set(neighbors)), reverse=(direction == "desc"))
        return neighbors

    def bfs_generator(self):
        start = self.start_node
        goal = self.goal_node
        visited_nodes_count = 0
        queue = deque([(start, [start])])
        explored_set = set()

        while queue:
            curr, path = queue.popleft()

            if curr in explored_set:
                continue

            explored_set.add(curr)
            visited_nodes_count += 1

            yield {
                'type': 'visit',
                'current': curr,
                'path': path,
                'visited_count': visited_nodes_count,
                'message': f"BFS розкриття вершини {curr} (глибина {len(path)-1}). Шлях: {' -> '.join(map(str, path))}"
            }

            if curr == goal:
                yield {
                    'type': 'found',
                    'final_path': path,
                    'visited_count': visited_nodes_count,
                    'message': f"BFS: Ціль {goal} знайдено! Довжина шляху: {len(path)-1}"
                }
                return

            neighbors = self.get_neighbors(curr)
            for nxt in neighbors:
                if nxt not in explored_set:
                    queue.append((nxt, path + [nxt]))

        yield {
            'type': 'not_found',
            'final_path': [],
            'visited_count': visited_nodes_count,
            'message': f"BFS: Ціль {goal} недосяжна з вершини {start}."
        }

    def dfs_generator(self):
        start = self.start_node
        goal = self.goal_node
        mode = self.mode_var.get()
        
        visited_nodes_count = 0
        best_path = None
        best_length = float('inf')

        stack = [(start, [start])]
        explored_set = set()

        if mode == "first":
            while stack:
                curr, path = stack.pop()

                if curr in explored_set:
                    continue

                explored_set.add(curr)
                visited_nodes_count += 1

                yield {
                    'type': 'visit',
                    'current': curr,
                    'path': path,
                    'visited_count': visited_nodes_count,
                    'message': f"Розкриття вершини {curr}. Поточний шлях: {' -> '.join(map(str, path))}"
                }

                if curr == goal:
                    best_path = path
                    yield {
                        'type': 'found',
                        'final_path': best_path,
                        'visited_count': visited_nodes_count,
                        'message': f"Ціль {goal} знайдено! Довжина шляху: {len(best_path)-1}"
                    }
                    return

                neighbors = self.get_neighbors(curr)
                for nxt in reversed(neighbors):
                    if nxt not in explored_set:
                        stack.append((nxt, path + [nxt]))

            yield {
                'type': 'not_found',
                'final_path': [],
                'visited_count': visited_nodes_count,
                'message': f"Ціль {goal} недосяжна з вершини {start}."
            }

        else:
            def dfs_branch_and_bound(u, current_path):
                nonlocal best_path, best_length, visited_nodes_count
                visited_nodes_count += 1

                yield {
                    'type': 'visit',
                    'current': u,
                    'path': current_path,
                    'visited_count': visited_nodes_count,
                    'message': f"DFS розкриття {u} (глибина {len(current_path)-1}). Шлях: {' -> '.join(map(str, current_path))}"
                }

                if u == goal:
                    if len(current_path) < best_length:
                        best_length = len(current_path)
                        best_path = list(current_path)
                        yield {
                            'type': 'update_best',
                            'best_path': best_path,
                            'visited_count': visited_nodes_count,
                            'message': f"★ Знайдено коротший шлях: {' -> '.join(map(str, best_path))} (довжина {best_length-1})"
                        }
                    return

                neighbors = self.get_neighbors(u)
                for nxt in neighbors:
                    if nxt not in current_path:
                        if len(current_path) + 1 < best_length:
                            yield from dfs_branch_and_bound(nxt, current_path + [nxt])
                        else:
                            yield {
                                'type': 'prune',
                                'current': nxt,
                                'path': current_path,
                                'visited_count': visited_nodes_count,
                                'message': f"Відсікання гілки у вершині {nxt}: довжина перевищує рекорд ({best_length-1})"
                            }

            yield from dfs_branch_and_bound(start, [start])

            if best_path:
                yield {
                    'type': 'found',
                    'final_path': best_path,
                    'visited_count': visited_nodes_count,
                    'message': f"Пошук завершено. Найкоротший шлях: {' -> '.join(map(str, best_path))}"
                }
            else:
                yield {
                    'type': 'not_found',
                    'final_path': [],
                    'visited_count': visited_nodes_count,
                    'message': f"Ціль {goal} не знайдено."
                }


    def reset_search_state(self):
        self.is_running = False
        self.is_paused = False
        self.search_generator = None
        self.final_path = []
        self.expanded_nodes_count = 0
        self.elapsed_time = 0.0
        self.btn_play.config(text="▶ Авто", state=tk.NORMAL)
        self.btn_pause.config(text="⏸ Пауза", state=tk.DISABLED)
        self.btn_step.config(state=tk.NORMAL)
        self.lbl_status.config(text="Статус: Очікування", foreground="#0066cc")
        self.lbl_expanded.config(text="Розкрито вершин: 0")
        self.lbl_time.config(text="Час пошуку: 0.00 мс")
        self.lbl_length.config(text="Довжина шляху: 0")
        self.txt_path.delete("1.0", tk.END)
        self.redraw_graph()

    def get_active_generator(self):
        if self.mode_var.get() == "bfs":
            return self.bfs_generator()
        return self.dfs_generator()

    def start_auto_search(self):
        if not self.is_running:
            self.reset_search_state()
            self.is_running = True
            self.is_paused = False
            self.start_time = time.perf_counter()
            self.search_generator = self.get_active_generator()
            self.btn_play.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL)
            self.btn_step.config(state=tk.DISABLED)
            self.lbl_status.config(text="Статус: Пошук...", foreground="#ff8800")
            self.run_animation_loop()
        elif self.is_paused:
            self.is_paused = False
            self.btn_play.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL)
            self.btn_step.config(state=tk.DISABLED)
            self.lbl_status.config(text="Статус: Пошук...", foreground="#ff8800")
            self.run_animation_loop()

    def pause_search(self):
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.btn_play.config(text="▶ Продовжити", state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED)
            self.btn_step.config(state=tk.NORMAL)
            self.lbl_status.config(text="Статус: На паузі", foreground="#777777")

    def step_search(self):
        if not self.is_running:
            self.reset_search_state()
            self.is_running = True
            self.is_paused = True
            self.start_time = time.perf_counter()
            self.search_generator = self.get_active_generator()
            self.btn_play.config(text="▶ Авто", state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED)

        self._execute_single_step()

    def _execute_single_step(self):
        if not self.search_generator:
            return False

        try:
            state = next(self.search_generator)
            self.expanded_nodes_count = state.get('visited_count', self.expanded_nodes_count)
            self.lbl_expanded.config(text=f"Розкрито вершин: {self.expanded_nodes_count}")
            self.log(state['message'])

            curr_node = state.get('current', None)
            path = state.get('path', [])
            best = state.get('best_path', [])

            if state['type'] == 'visit':
                self.redraw_graph(active_node=curr_node, current_path=path)
            elif state['type'] == 'update_best':
                self.redraw_graph(active_node=curr_node, current_path=best, is_best=True)
            elif state['type'] == 'prune':
                self.redraw_graph(active_node=curr_node, current_path=path, pruned=True)
            elif state['type'] == 'found':
                self.elapsed_time = (time.perf_counter() - self.start_time) * 1000
                self.final_path = state['final_path']
                self.lbl_status.config(text="Статус: Шлях знайдено!", foreground="#00aa00")
                self.lbl_time.config(text=f"Час пошуку: {self.elapsed_time:.2f} мс")
                self.lbl_length.config(text=f"Довжина шляху: {len(self.final_path) - 1}")
                self.txt_path.delete("1.0", tk.END)
                self.txt_path.insert(tk.END, " -> ".join(map(str, self.final_path)))
                self.redraw_graph(final_path=self.final_path)
                self._finish_execution()
                return False
            elif state['type'] == 'not_found':
                self.elapsed_time = (time.perf_counter() - self.start_time) * 1000
                self.lbl_status.config(text="Статус: Не знайдено", foreground="#cc0000")
                self.lbl_time.config(text=f"Час пошуку: {self.elapsed_time:.2f} мс")
                self._finish_execution()
                return False

            return True

        except StopIteration:
            self._finish_execution()
            return False

    def run_animation_loop(self):
        if self.is_running and not self.is_paused:
            has_more = self._execute_single_step()
            if has_more:
                self.root.after(self.animation_speed, self.run_animation_loop)

    def _finish_execution(self):
        self.is_running = False
        self.is_paused = False
        self.search_generator = None
        self.btn_play.config(text="▶ Авто", state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED)
        self.btn_step.config(state=tk.DISABLED)

    def log(self, text):
        self.txt_log.insert(tk.END, text + "\n")
        self.txt_log.see(tk.END)


    def redraw_graph(self, active_node=None, current_path=None, final_path=None, is_best=False, pruned=False):
        self.canvas.delete("all")
        if current_path is None:
            current_path = []
        if final_path is None:
            final_path = self.final_path

        path_edges = set()
        if final_path and len(final_path) > 1:
            for i in range(len(final_path) - 1):
                path_edges.add((final_path[i], final_path[i+1]))
        elif current_path and len(current_path) > 1:
            for i in range(len(current_path) - 1):
                path_edges.add((current_path[i], current_path[i+1]))

        for (u, v), meta in self.edges.items():
            if u not in self.nodes or v not in self.nodes:
                continue

            x1, y1 = self.nodes[u]['x'], self.nodes[u]['y']
            x2, y2 = self.nodes[v]['x'], self.nodes[v]['y']
            is_directed = meta['directed']

            is_in_path = (u, v) in path_edges or (not is_directed and (v, u) in path_edges)
            is_cross_edge = meta.get('curved', False)

            if is_in_path:
                edge_color = "#28a745" if final_path else "#ff9900"
                width = 3.5
            elif is_cross_edge:
                edge_color = "#7b2cbf"
                width = 2
            else:
                edge_color = "#b0b0b0"
                width = 1.5

            arrow_opt = tk.LAST if is_directed else None

            if is_cross_edge:
                dx, dy = x2 - x1, y2 - y1
                dist = math.hypot(dx, dy)
                curvature = 40 if y1 > 350 and y2 > 350 else -40
                cx = (x1 + x2) / 2 - (dy / (dist + 0.001)) * curvature
                cy = (y1 + y2) / 2 + (dx / (dist + 0.001)) * curvature

                if is_directed:
                    vx, vy = x2 - cx, y2 - cy
                    v_len = math.hypot(vx, vy)
                    x2_arr = x2 - (vx / (v_len + 0.001)) * 16
                    y2_arr = y2 - (vy / (v_len + 0.001)) * 16
                else:
                    x2_arr, y2_arr = x2, y2

                self.canvas.create_line(
                    x1, y1, cx, cy, x2_arr, y2_arr,
                    smooth=True, fill=edge_color, width=width,
                    arrow=arrow_opt, arrowshape=(10, 12, 5)
                )
            else:
                dx, dy = x2 - x1, y2 - y1
                dist = math.hypot(dx, dy)
                if is_directed:
                    x2_arr = x2 - (dx / (dist + 0.001)) * 16
                    y2_arr = y2 - (dy / (dist + 0.001)) * 16
                else:
                    x2_arr, y2_arr = x2, y2
                self.canvas.create_line(x1, y1, x2_arr, y2_arr, fill=edge_color, width=width, arrow=arrow_opt, arrowshape=(10, 12, 5))

        r = 15
        for n_id, pos in self.nodes.items():
            x, y = pos['x'], pos['y']

            if n_id == self.start_node:
                fill_col, border_col = "#70e000", "#38b000"
            elif n_id == self.goal_node:
                fill_col, border_col = "#ff4d6d", "#c9184a"
            elif n_id == active_node:
                fill_col, border_col = "#ffb703", "#fb8500"
            elif final_path and n_id in final_path:
                fill_col, border_col = "#a3e635", "#4d7c0f"
            elif n_id in current_path:
                fill_col, border_col = "#90e0ef", "#0077b6"
            else:
                fill_col, border_col = "#ffffff", "#343a40"

            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill_col, outline=border_col, width=2)
            self.canvas.create_text(x, y, text=str(n_id), font=("Helvetica", 9, "bold"), fill="#111111")


    def gui_add_node_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Додати вершину")
        dialog.geometry("260x180")
        dialog.transient(self.root)

        ttk.Label(dialog, text="Номер нової вершини:").pack(pady=2)
        ent_id = ttk.Entry(dialog)
        next_id = max(self.nodes.keys(), default=0) + 1
        ent_id.insert(0, str(next_id))
        ent_id.pack(pady=2)

        ttk.Label(dialog, text="Координата X (50-850):").pack(pady=2)
        ent_x = ttk.Entry(dialog)
        ent_x.insert(0, "450")
        ent_x.pack(pady=2)

        ttk.Label(dialog, text="Координата Y (50-600):").pack(pady=2)
        ent_y = ttk.Entry(dialog)
        ent_y.insert(0, "550")
        ent_y.pack(pady=2)

        def save():
            try:
                nid = int(ent_id.get().strip())
                x = int(ent_x.get().strip())
                y = int(ent_y.get().strip())
                if nid in self.nodes:
                    messagebox.showerror("Помилка", f"Вершина {nid} вже існує!", parent=dialog)
                    return
                self.nodes[nid] = {'x': x, 'y': y}
                self._refresh_comboboxes()
                self._update_graph_metrics()
                self.redraw_graph()
                self.log(f"Додано вершину {nid} на ({x}, {y})")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Помилка", "Введіть коректні числові координати", parent=dialog)

        ttk.Button(dialog, text="Додати", command=save).pack(pady=8)

    def gui_remove_node_dialog(self):
        if not self.nodes:
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Вилучити вершину")
        dialog.geometry("260x120")
        dialog.transient(self.root)

        ttk.Label(dialog, text="Оберіть вершину для видалення:").pack(pady=4)
        cb = ttk.Combobox(dialog, values=sorted(list(self.nodes.keys())), state="readonly")
        cb.pack(pady=4)
        cb.current(0)

        def remove():
            nid = int(cb.get())
            if nid in self.nodes:
                del self.nodes[nid]
                to_del = [k for k in self.edges.keys() if k[0] == nid or k[1] == nid]
                for k in to_del:
                    del self.edges[k]
                self._refresh_comboboxes()
                self._update_graph_metrics()
                self.redraw_graph()
                self.log(f"Вилучено вершину {nid} та прилеглі ребра")
                dialog.destroy()

        ttk.Button(dialog, text="Вилучити", command=remove).pack(pady=6)

    def gui_add_edge_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Додати ребро/дугу")
        dialog.geometry("300x230")
        dialog.transient(self.root)

        nodes_list = sorted(list(self.nodes.keys()))
        ttk.Label(dialog, text="Звідки (Вершина 1):").pack(pady=2)
        cb1 = ttk.Combobox(dialog, values=nodes_list, state="readonly")
        cb1.pack(pady=2)
        if nodes_list: cb1.current(0)

        ttk.Label(dialog, text="Куди (Вершина 2):").pack(pady=2)
        cb2 = ttk.Combobox(dialog, values=nodes_list, state="readonly")
        cb2.pack(pady=2)
        if len(nodes_list) > 1: cb2.current(1)

        is_dir_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Це напрямлена дуга (1 -> 2)?", variable=is_dir_var).pack(pady=6)

        def add():
            u = int(cb1.get())
            v = int(cb2.get())
            if u == v:
                messagebox.showerror("Помилка", "Петлі не підтримуються", parent=dialog)
                return
            is_dir = is_dir_var.get()
            key = (u, v) if is_dir else (min(u, v), max(u, v))
            self.edges[key] = {'directed': is_dir}
            self._update_graph_metrics()
            self.redraw_graph()
            self.log(f"Додано {'дугу' if is_dir else 'ребро'}: {u} {'->' if is_dir else '<->'} {v}")
            dialog.destroy()

        ttk.Button(dialog, text="Зберегти", command=add).pack(pady=6)

    def gui_remove_edge_dialog(self):
        if not self.edges:
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Вилучити ребро/дугу")
        dialog.geometry("320x140")
        dialog.transient(self.root)

        edge_strs = [f"{u} {'->' if m['directed'] else '<->'} {v}" for (u, v), m in self.edges.items()]
        edge_keys = list(self.edges.keys())

        ttk.Label(dialog, text="Оберіть ребро або дугу:").pack(pady=4)
        cb = ttk.Combobox(dialog, values=edge_strs, state="readonly")
        cb.pack(fill=tk.X, padx=10, pady=4)
        cb.current(0)

        def remove():
            idx = cb.current()
            key = edge_keys[idx]
            del self.edges[key]
            self._update_graph_metrics()
            self.redraw_graph()
            self.log(f"Вилучено зв'язок між {key[0]} та {key[1]}")
            dialog.destroy()

        ttk.Button(dialog, text="Вилучити", command=remove).pack(pady=6)

    def gui_toggle_edge_type_dialog(self):
        if not self.edges:
            messagebox.showinfo("Інформація", "У графі немає ребер для зміни.", parent=self.root)
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Зміна типу та напрямку зв'язку")
        dialog.geometry("380x260")
        dialog.transient(self.root)

        edge_keys = list(self.edges.keys())

        def get_display_str(k):
            m = self.edges[k]
            return f"{k[0]} {'->' if m['directed'] else '<->'} {k[1]}"

        ttk.Label(dialog, text="Оберіть ребро/дугу зі списку:").pack(pady=(8, 2))
        cb = ttk.Combobox(dialog, values=[get_display_str(k) for k in edge_keys], state="readonly", width=35)
        cb.pack(fill=tk.X, padx=12, pady=4)
        cb.current(0)

        type_var = tk.StringVar(value="undirected")
        rb_frame = ttk.LabelFrame(dialog, text="Оберіть новий стан зв'язку", padding=8)
        rb_frame.pack(fill=tk.X, padx=12, pady=8)

        rb_undir = ttk.Radiobutton(rb_frame, text="", variable=type_var, value="undirected")
        rb_undir.pack(anchor=tk.W, pady=2)

        rb_dir_fwd = ttk.Radiobutton(rb_frame, text="", variable=type_var, value="forward")
        rb_dir_fwd.pack(anchor=tk.W, pady=2)

        rb_dir_rev = ttk.Radiobutton(rb_frame, text="", variable=type_var, value="reverse")
        rb_dir_rev.pack(anchor=tk.W, pady=2)

        def update_radio_labels(*args):
            idx = cb.current()
            if idx < 0:
                return
            u, v = edge_keys[idx]
            meta = self.edges[edge_keys[idx]]

            rb_undir.config(text=f"Неорієнтоване ребро ({u} <-> {v})")
            rb_dir_fwd.config(text=f"Пряма дуга ({u} -> {v})")
            rb_dir_rev.config(text=f"Зворотна дуга ({v} -> {u})")

            if not meta['directed']:
                type_var.set("undirected")
            else:
                type_var.set("forward")

        cb.bind("<<ComboboxSelected>>", update_radio_labels)
        update_radio_labels()

        def apply_change():
            idx = cb.current()
            old_key = edge_keys[idx]
            u, v = old_key
            choice = type_var.get()

            old_meta = self.edges[old_key]
            is_curved = old_meta.get('curved', False)

            del self.edges[old_key]

            if choice == "undirected":
                new_key = (min(u, v), max(u, v))
                self.edges[new_key] = {'directed': False, 'curved': is_curved}
                self.log(f"Зв'язок між {u} та {v} змінено на неорієнтоване ребро: {new_key[0]} <-> {new_key[1]}")
            elif choice == "forward":
                new_key = (u, v)
                self.edges[new_key] = {'directed': True, 'curved': is_curved}
                self.log(f"Зв'язок між {u} та {v} змінено на дугу: {u} -> {v}")
            else:
                new_key = (v, u)
                self.edges[new_key] = {'directed': True, 'curved': is_curved}
                self.log(f"Зв'язок між {u} та {v} змінено на дугу: {v} -> {u}")

            self.redraw_graph()
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=12, pady=(4, 8))
        ttk.Button(btn_frame, text="Застосувати зміни", command=apply_change).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Скасувати", command=dialog.destroy).pack(side=tk.RIGHT, padx=4)

    def open_separate_results_window(self):
        res_win = tk.Toplevel(self.root)
        res_win.title("Детальні результати пошуку DFS")
        res_win.geometry("520x420")
        res_win.transient(self.root)

        frame = ttk.Frame(res_win, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="ПРОТОКОЛ РЕЗУЛЬТАТІВ ПОШУКУ", font=("Helvetica", 11, "bold")).pack(pady=(0, 8))

        cond_box = ttk.LabelFrame(frame, text="Початкові умови пошуку", padding=8)
        cond_box.pack(fill=tk.X, pady=(0, 8))

        mode_name = "Найкоротший шлях (DFS B&B)" if self.mode_var.get() == "shortest" else "Перший шлях (Standard DFS)"
        order_name = "За зростанням ID" if self.order_var.get() == "asc" else "За спаданням ID"

        ttk.Label(cond_box, text=f"• Порядок графу (|V|): {len(self.nodes)}").pack(anchor=tk.W)
        ttk.Label(cond_box, text=f"• Розмір графу (|E|): {len(self.edges)}").pack(anchor=tk.W)
        ttk.Label(cond_box, text=f"• Початкова вершина: {self.start_node}").pack(anchor=tk.W)
        ttk.Label(cond_box, text=f"• Цільова вершина: {self.goal_node}").pack(anchor=tk.W)
        ttk.Label(cond_box, text=f"• Напрямок обходу суміжних вершин: {order_name}").pack(anchor=tk.W)
        ttk.Label(cond_box, text=f"• Алгоритм / режим: {mode_name}").pack(anchor=tk.W)

        out_box = ttk.LabelFrame(frame, text="Отримані результати", padding=8)
        out_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        path_str = " -> ".join(map(str, self.final_path)) if self.final_path else "Шлях не знайдено / не запущено"
        path_len = len(self.final_path) - 1 if self.final_path else 0

        ttk.Label(out_box, text=f"• Кількість розкритих вершин: {self.expanded_nodes_count}").pack(anchor=tk.W)
        ttk.Label(out_box, text=f"• Час виконання пошуку: {self.elapsed_time:.3f} мс").pack(anchor=tk.W)
        ttk.Label(out_box, text=f"• Довжина знайденого шляху: {path_len}").pack(anchor=tk.W)
        ttk.Label(out_box, text="• Знайдений шлях:", font=("Helvetica", 9, "bold")).pack(anchor=tk.W, pady=(4, 1))

        t = tk.Text(out_box, height=4, wrap=tk.WORD, font=("Consolas", 9))
        t.pack(fill=tk.BOTH, expand=True)
        t.insert(tk.END, path_str)
        t.config(state=tk.DISABLED)

        ttk.Button(frame, text="Закрити", command=res_win.destroy).pack(anchor=tk.E)

    def _run_pure_search(self, algo_type):
        start = self.start_node
        goal = self.goal_node
        t_start = time.perf_counter()
        visited_count = 0
        best_path = []

        if algo_type == "bfs":
            queue = deque([(start, [start])])
            explored = set()
            while queue:
                curr, path = queue.popleft()
                if curr in explored:
                    continue
                explored.add(curr)
                visited_count += 1
                if curr == goal:
                    best_path = path
                    break
                for nxt in self.get_neighbors(curr):
                    if nxt not in explored:
                        queue.append((nxt, path + [nxt]))

        elif algo_type == "dfs_first":
            stack = [(start, [start])]
            explored = set()
            while stack:
                curr, path = stack.pop()
                if curr in explored:
                    continue
                explored.add(curr)
                visited_count += 1
                if curr == goal:
                    best_path = path
                    break
                for nxt in reversed(self.get_neighbors(curr)):
                    if nxt not in explored:
                        stack.append((nxt, path + [nxt]))

        elif algo_type == "dfs_bb":
            best_len = float('inf')
            def bb(u, path):
                nonlocal best_path, best_len, visited_count
                visited_count += 1
                if u == goal:
                    if len(path) < best_len:
                        best_len = len(path)
                        best_path = list(path)
                    return
                for nxt in self.get_neighbors(u):
                    if nxt not in path and len(path) + 1 < best_len:
                        bb(nxt, path + [nxt])
            bb(start, [start])

        elapsed_ms = (time.perf_counter() - t_start) * 1000
        path_len = len(best_path) - 1 if best_path else 0
        path_str = " -> ".join(map(str, best_path)) if best_path else "Не знайдено"

        return {
            'expanded': visited_count,
            'len': path_len,
            'path': path_str,
            'time': f"{elapsed_ms:.3f} мс"
        }

    def open_comparison_window(self):
        comp_win = tk.Toplevel(self.root)
        comp_win.title("Порівняльний аналіз: DFS проти BFS")
        comp_win.geometry("740x520")
        comp_win.minsize(620, 440)
        comp_win.transient(self.root)

        frame = ttk.Frame(comp_win, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        order_str = "За зростанням ID" if self.order_var.get() == "asc" else "За спаданням ID"
        ttk.Label(
            frame, 
            text=f"Порівняння при однакових умовах (Start: {self.start_node}, Goal: {self.goal_node}, Обхід: {order_str})", 
            font=("Helvetica", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 8))

        res_dfs_first = self._run_pure_search("dfs_first")
        res_dfs_bb = self._run_pure_search("dfs_bb")
        res_bfs = self._run_pure_search("bfs")

        table_frame = ttk.LabelFrame(frame, text="Числові показники ефективності", padding=6)
        table_frame.pack(fill=tk.X, pady=(0, 8))

        cols = ("algo", "expanded", "len", "time")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=3)
        tree.heading("algo", text="Алгоритм")
        tree.heading("expanded", text="Розкрито вершин")
        tree.heading("len", text="Довжина шляху")
        tree.heading("time", text="Час виконання")

        tree.column("algo", width=220, anchor=tk.W)
        tree.column("expanded", width=140, anchor=tk.CENTER)
        tree.column("len", width=130, anchor=tk.CENTER)
        tree.column("time", width=130, anchor=tk.CENTER)

        tree.insert("", tk.END, values=("DFS (Перший знайдений)", res_dfs_first['expanded'], res_dfs_first['len'], res_dfs_first['time']))
        tree.insert("", tk.END, values=("DFS (Найкоротший B&B)", res_dfs_bb['expanded'], res_dfs_bb['len'], res_dfs_bb['time']))
        tree.insert("", tk.END, values=("BFS (Пошук у ширину)", res_bfs['expanded'], res_bfs['len'], res_bfs['time']))

        tree.pack(fill=tk.X)

        paths_frame = ttk.LabelFrame(frame, text="Знайдені шляхи", padding=6)
        paths_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        txt_paths = tk.Text(paths_frame, wrap=tk.WORD, height=7, font=("Consolas", 9), bg="#fdfdfd", padx=6, pady=6)
        scroll = ttk.Scrollbar(paths_frame, orient=tk.VERTICAL, command=txt_paths.yview)
        txt_paths.configure(yscrollcommand=scroll.set)

        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        txt_paths.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        txt_paths.tag_configure("algo_title", font=("Consolas", 9, "bold"), foreground="#004085")
        txt_paths.tag_configure("path_val", font=("Consolas", 9), foreground="#212529")

        items = [
            ("• DFS (Перший знайдений):", res_dfs_first['path']),
            ("• DFS (Найкоротший B&B):", res_dfs_bb['path']),
            ("• BFS (Пошук у ширину):", res_bfs['path'])
        ]
        for title, p in items:
            txt_paths.insert(tk.END, f"{title}\n", "algo_title")
            txt_paths.insert(tk.END, f"  {p}\n\n", "path_val")

        txt_paths.config(state=tk.DISABLED)

        diff_len = res_dfs_first['len'] - res_bfs['len']
        comment = (
            f"Висновки:\n"
            f"• BFS гарантовано знайшов найкоротший шлях ({res_bfs['len']} ребер), розкривши {res_bfs['expanded']} вершин.\n"
            f"• DFS (перший знайдений) знайшов шлях довжиною {res_dfs_first['len']} (довший на {diff_len} ребер), "
            f"розкривши {res_dfs_first['expanded']} вершин."
        )
        lbl_c = ttk.Label(frame, text=comment, foreground="#003366", font=("Helvetica", 8), wraplength=700, justify=tk.LEFT)
        lbl_c.pack(anchor=tk.W, pady=(0, 6))

        ttk.Button(frame, text="Закрити", command=comp_win.destroy).pack(anchor=tk.E)


if __name__ == "__main__":
    root = tk.Tk()
    app = GraphDFSApp(root)
    root.mainloop()