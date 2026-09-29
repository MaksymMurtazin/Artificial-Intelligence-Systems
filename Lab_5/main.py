import heapq
import math
import time
import tkinter as tk
from tkinter import ttk, messagebox

INF = float("inf")

LOGICAL_W, LOGICAL_H = 1000, 680
NODE_RADIUS = 8

CITY_COORDS = {
    "Вінниця": (28.47, 49.23),
    "Житомир": (28.66, 50.25),
    "Київ": (30.52, 50.45),
    "Кропивницький": (32.26, 48.51),
    "Миколаїв": (31.99, 46.97),
    "Одеса": (30.73, 46.48),
    "Черкаси": (32.06, 49.44),
    "Чернівці": (25.94, 48.29),
    "Дніпро": (35.05, 48.46),
    "Донецьк": (37.80, 48.02),
    "Запоріжжя": (35.14, 47.84),
    "Кривий Ріг": (33.39, 47.91),
    "Полтава": (34.55, 49.59),
    "Харків": (36.23, 49.99),
    "Луганськ": (39.30, 48.57),
    "Маріуполь": (37.55, 47.10),
    "Мелітополь": (35.37, 46.84),
    "Івано-Франківськ": (24.71, 48.92),
    "Тернопіль": (25.59, 49.55),
    "Ужгород": (22.30, 48.62),
    "Суми": (34.80, 50.91),
    "Чернігів": (31.29, 51.50),
    "Львів": (24.03, 49.84),
    "Луцьк": (25.34, 50.75),
    "Рівне": (26.25, 50.62),
    "Сімферополь": (34.10, 44.95),
    "Херсон": (32.62, 46.64),
    "Хмельницький": (27.00, 49.42),
    "Севастополь": (33.52, 44.62),
}

DISTANCES = [
    ("Вінниця", "Житомир", 127),
    ("Вінниця", "Київ", 267),
    ("Вінниця", "Кропивницький", 320),
    ("Вінниця", "Миколаїв", 428),
    ("Вінниця", "Одеса", 423),
    ("Вінниця", "Черкаси", 341),
    ("Вінниця", "Чернівці", 276),
    ("Дніпро", "Донецьк", 248),
    ("Дніпро", "Запоріжжя", 85),
    ("Дніпро", "Кропивницький", 244),
    ("Дніпро", "Кривий Ріг", 146),
    ("Дніпро", "Полтава", 160),
    ("Дніпро", "Харків", 218),
    ("Донецьк", "Луганськ", 156),
    ("Донецьк", "Маріуполь", 113),
    ("Донецьк", "Харків", 294),
    ("Запоріжжя", "Мелітополь", 125),
    ("Івано-Франківськ", "Тернопіль", 133),
    ("Івано-Франківськ", "Ужгород", 293),
    ("Київ", "Житомир", 140),
    ("Київ", "Полтава", 340),
    ("Київ", "Суми", 333),
    ("Київ", "Черкаси", 189),
    ("Київ", "Чернігів", 148),
    ("Кропивницький", "Полтава", 246),
    ("Луганськ", "Харків", 325),
    ("Львів", "Івано-Франківськ", 134),
    ("Львів", "Луцьк", 151),
    ("Львів", "Рівне", 211),
    ("Львів", "Тернопіль", 127),
    ("Львів", "Ужгород", 268),
    ("Львів", "Чернівці", 268),
    ("Мелітополь", "Маріуполь", 192),
    ("Мелітополь", "Сімферополь", 250),
    ("Миколаїв", "Херсон", 69),
    ("Рівне", "Житомир", 188),
    ("Рівне", "Луцьк", 73),
    ("Рівне", "Тернопіль", 155),
    ("Харків", "Полтава", 143),
    ("Херсон", "Мелітополь", 231),
    ("Хмельницький", "Вінниця", 119),
    ("Хмельницький", "Житомир", 183),
    ("Хмельницький", "Рівне", 194),
    ("Хмельницький", "Тернопіль", 112),
    ("Хмельницький", "Чернівці", 187),
    ("Суми", "Харків", 184),
    ("Черкаси", "Полтава", 233),
    ("Полтава", "Суми", 175),
    ("Чернігів", "Суми", 306),
    ("Сімферополь", "Севастополь", 81),
]


def fmt(x):
    if x == INF:
        return "∞"
    x = float(x)
    return str(int(x)) if x.is_integer() else f"{x:.1f}"


_UA_ALPHABET = "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"


def ua_sort_key(text):
    return [(_UA_ALPHABET.index(ch) if ch in _UA_ALPHABET else 100 + ord(ch))
            for ch in text.lower()]


LAYOUT_OVERRIDES = {
    "Сімферополь": (665, 585), "Севастополь": (590, 648),
    "Миколаїв": (525, 418), "Херсон": (592, 488), "Одеса": (450, 500),
    "Запоріжжя": (738, 388), "Дніпро": (702, 312), "Кривий Ріг": (620, 368),
    "Мелітополь": (735, 480),
    "Львів": (128, 195), "Тернопіль": (238, 238), "Івано-Франківськ": (160, 292),
    "Ужгород": (50, 312), "Чернівці": (245, 350), "Хмельницький": (318, 250),
    "Луцьк": (195, 112), "Рівне": (272, 130),
}


def project_city(name, lon, lat):
    if name in LAYOUT_OVERRIDES:
        return LAYOUT_OVERRIDES[name]
    x = 30 + (lon - 21.8) / (40.4 - 21.8) * 940
    y = 30 + (51.9 - lat) / (51.9 - 44.4) * 620
    return round(x), round(y)


class WeightedGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, name, x, y):
        if name in self.nodes:
            raise ValueError(f"Вершина «{name}» вже існує")
        self.nodes[name] = {'x': x, 'y': y}

    def remove_node(self, name):
        self.nodes.pop(name, None)
        for key in [k for k in self.edges if name in k]:
            del self.edges[key]

    def add_edge(self, u, v, weight, directed=False):
        if u == v:
            raise ValueError("Петлі не підтримуються")
        if u not in self.nodes or v not in self.nodes:
            raise ValueError("Обидві вершини мають існувати в графі")
        if weight <= 0:
            raise ValueError("Вага має бути додатною (алгоритм Дейкстри "
                             "не працює з від'ємними вагами)")
        if directed:
            for key in list(self.edges):
                if set(key) == {u, v} and not self.edges[key]['directed']:
                    del self.edges[key]
            self.edges[(u, v)] = {'weight': weight, 'directed': True}
        else:
            for key in list(self.edges):
                if set(key) == {u, v}:
                    del self.edges[key]
            key = tuple(sorted((u, v)))
            self.edges[key] = {'weight': weight, 'directed': False}

    def remove_edge(self, key):
        self.edges.pop(key, None)

    def neighbors(self, u):
        result = []
        for (a, b), meta in self.edges.items():
            if a == u:
                result.append((b, meta['weight']))
            elif b == u and not meta['directed']:
                result.append((a, meta['weight']))
        return result

    @staticmethod
    def _restore_path(prev, goal):
        path, node = [], goal
        while node is not None:
            path.append(node)
            node = prev[node]
        return path[::-1]

    def dijkstra_steps(self, start, goal):
        dist = {n: INF for n in self.nodes}
        prev = {n: None for n in self.nodes}
        dist[start] = 0
        visited = set()
        heap = [(0, 0, start)]
        tie = 1
        relax_count = 0

        def snap(kind, message, **extra):
            state = {
                'type': kind,
                'message': message,
                'dist': dict(dist),
                'prev': dict(prev),
                'visited': set(visited),
                'frontier': {n for n, d in dist.items()
                             if d < INF and n not in visited},
                'visited_count': len(visited),
                'relax_count': relax_count,
            }
            state.update(extra)
            return state

        yield snap('init', f"Ініціалізація: мітка «{start}» = 0, решта = ∞. "
                           f"Черга пріоритетів: [{start}]")

        while heap:
            d, _, u = heapq.heappop(heap)
            if u in visited or d > dist[u]:
                continue

            visited.add(u)
            yield snap('visit',
                       f"Із черги обрано «{u}» з мінімальною міткою {fmt(d)} км "
                       f"- мітку зафіксовано (остаточна).",
                       current=u)

            if u == goal:
                path = self._restore_path(prev, goal)
                yield snap('found',
                           f"Ціль «{goal}» досягнуто! Найкоротша відстань: "
                           f"{fmt(dist[goal])} км.",
                           current=u, path=path, distance=dist[goal])
                return

            for v, w in self.neighbors(u):
                if v in visited:
                    continue
                relax_count += 1
                nd = d + w
                if nd < dist[v]:
                    old = dist[v]
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(heap, (nd, tie, v))
                    tie += 1
                    yield snap('relax',
                               f"   {u} → {v}: {fmt(d)} + {fmt(w)} = {fmt(nd)} "
                               f"< {fmt(old)} - мітку «{v}» оновлено",
                               current=u, relax_edge=(u, v), improved=True)
                else:
                    yield snap('relax',
                               f"   {u} → {v}: {fmt(d)} + {fmt(w)} = {fmt(nd)} "
                               f"≥ {fmt(dist[v])} - без змін",
                               current=u, relax_edge=(u, v), improved=False)

        yield snap('not_found',
                   f"Ціль «{goal}» недосяжна з вершини «{start}».",
                   path=[], distance=INF)


def build_ukraine_graph():
    g = WeightedGraph()
    for name, (lon, lat) in CITY_COORDS.items():
        x, y = project_city(name, lon, lat)
        g.add_node(name, x, y)
    for a, b, w in DISTANCES:
        g.add_edge(a, b, w)
    return g


class DijkstraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторна робота №5: Алгоритм Дейкстри - "
                        "найкоротший шлях автошляхами України")
        self.root.geometry("1440x880")
        self.root.minsize(1180, 740)

        self.graph = build_ukraine_graph()
        self.start_node = "Львів"
        self.goal_node = "Харків"

        self.is_running = False
        self.is_paused = False
        self.search_generator = None
        self._after_id = None
        self.animation_speed = 250

        self.vis = None
        self.final_path = []
        self.result = None
        self.result_win = None
        self.expanded_count = 0
        self.relax_count = 0
        self.elapsed_time = 0.0

        self.dragged_node = None
        self.drag_start_pos = (0, 0)

        self._create_ui()
        self._refresh_comboboxes()
        self._update_graph_metrics()
        self.reset_search_state()
        self.log(f"Завантажено граф автошляхів України: |V| = "
                 f"{len(self.graph.nodes)}, |E| = {len(self.graph.edges)}")

    def _create_ui(self):
        main_frame = ttk.Frame(self.root, padding=6)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(main_frame, width=290)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))

        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_panel = ttk.Frame(main_frame, width=320)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 0))

        cfg = ttk.LabelFrame(left_panel, text="1. Параметри пошуку", padding=6)
        cfg.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(cfg, text="Початкове місто (Start):").pack(anchor=tk.W)
        self.start_cb = ttk.Combobox(cfg, state="readonly")
        self.start_cb.pack(fill=tk.X, pady=(0, 4))
        self.start_cb.bind("<<ComboboxSelected>>", self._on_start_changed)

        ttk.Label(cfg, text="Цільове місто (Goal):").pack(anchor=tk.W)
        self.goal_cb = ttk.Combobox(cfg, state="readonly")
        self.goal_cb.pack(fill=tk.X, pady=(0, 4))
        self.goal_cb.bind("<<ComboboxSelected>>", self._on_goal_changed)

        ttk.Button(cfg, text="⇄ Поміняти місцями (Start ↔ Goal)",
                   command=self.swap_start_goal).pack(fill=tk.X, pady=2)

        exec_box = ttk.LabelFrame(left_panel, text="2. Керування візуалізацією",
                                  padding=6)
        exec_box.pack(fill=tk.X, pady=(0, 6))

        row1 = ttk.Frame(exec_box)
        row1.pack(fill=tk.X, pady=2)
        self.btn_play = ttk.Button(row1, text="▶ Авто", command=self.start_auto_search)
        self.btn_play.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        self.btn_pause = ttk.Button(row1, text="⏸ Пауза", command=self.pause_search,
                                    state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        row2 = ttk.Frame(exec_box)
        row2.pack(fill=tk.X, pady=2)
        self.btn_step = ttk.Button(row2, text="⏭ Крок", command=self.step_search)
        self.btn_step.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        self.btn_reset = ttk.Button(row2, text="↺ Скинути", command=self.reset_search_state)
        self.btn_reset.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        ttk.Label(exec_box, text="Швидкість анімації:").pack(anchor=tk.W, pady=(4, 0))
        self.speed_slider = ttk.Scale(exec_box, from_=800, to=40, orient=tk.HORIZONTAL,
                                      command=self._on_speed_changed)
        self.speed_slider.set(250)
        self.speed_slider.pack(fill=tk.X)

        edit_box = ttk.LabelFrame(left_panel, text="3. Модифікація графа", padding=6)
        edit_box.pack(fill=tk.X, pady=(0, 6))

        v_row = ttk.Frame(edit_box)
        v_row.pack(fill=tk.X, pady=2)
        ttk.Button(v_row, text="+ Вершина", command=self.gui_add_node_dialog
                   ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        ttk.Button(v_row, text="- Вершина", command=self.gui_remove_node_dialog
                   ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        e_row = ttk.Frame(edit_box)
        e_row.pack(fill=tk.X, pady=2)
        ttk.Button(e_row, text="+ Ребро/Дуга", command=self.gui_add_edge_dialog
                   ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        ttk.Button(e_row, text="- Ребро/Дуга", command=self.gui_remove_edge_dialog
                   ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        ttk.Button(edit_box, text="✎ Змінити вагу (відстань) ребра",
                   command=self.gui_edit_weight_dialog).pack(fill=tk.X, pady=2)
        ttk.Button(edit_box, text="⇄ Змінити ребро ↔ дуга (тип)",
                   command=self.gui_toggle_edge_type_dialog).pack(fill=tk.X, pady=2)

        preset_box = ttk.LabelFrame(left_panel, text="4. Граф для дослідження", padding=6)
        preset_box.pack(fill=tk.X, pady=(0, 2))
        ttk.Button(preset_box, text="Відновити граф України (табл. 1)",
                   command=self.reload_ukraine_graph).pack(fill=tk.X, pady=1)

        ttk.Label(left_panel,
                  text="Полотно: тягніть місто лівою кнопкою миші; клік ЛКМ по місту - "
                       "встановити Start, клік ПКМ - встановити Goal.",
                  font=("Helvetica", 8), wraplength=270, foreground="#FF0000"
                  ).pack(fill=tk.X, pady=(6, 0))

        self.canvas = tk.Canvas(canvas_frame, bg="#ffffff", highlightthickness=1,
                                highlightbackground="#cccccc")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)
        self.canvas.bind("<Button-2>", self._on_canvas_right_click)
        self.canvas.bind("<Configure>", lambda e: self.redraw_graph())

        res_box = ttk.LabelFrame(right_panel, text="Результати пошуку", padding=8)
        res_box.pack(fill=tk.BOTH, expand=True)

        self.lbl_graph_order = ttk.Label(res_box, text="Порядок графу (|V|): 0")
        self.lbl_graph_order.pack(anchor=tk.W, pady=1)
        self.lbl_graph_size = ttk.Label(res_box, text="Розмір графу (|E|): 0")
        self.lbl_graph_size.pack(anchor=tk.W, pady=1)

        self.lbl_status = ttk.Label(res_box, text="Статус: Очікування",
                                    foreground="#0066cc", font=("Helvetica", 9, "bold"))
        self.lbl_status.pack(anchor=tk.W, pady=4)

        self.lbl_expanded = ttk.Label(res_box, text="Зафіксовано вершин: 0")
        self.lbl_expanded.pack(anchor=tk.W, pady=1)
        self.lbl_relax = ttk.Label(res_box, text="Перевірено ребер: 0")
        self.lbl_relax.pack(anchor=tk.W, pady=1)
        self.lbl_time = ttk.Label(res_box, text="Час обчислень: 0.00 мс")
        self.lbl_time.pack(anchor=tk.W, pady=1)
        self.lbl_length = ttk.Label(res_box, text="Найкоротша відстань: -",
                                    font=("Helvetica", 10, "bold"))
        self.lbl_length.pack(anchor=tk.W, pady=(4, 1))

        ttk.Label(res_box, text="Знайдений шлях:", font=("Helvetica", 9, "bold")
                  ).pack(anchor=tk.W, pady=(6, 2))
        self.txt_path = tk.Text(res_box, height=6, width=36, wrap=tk.WORD,
                                font=("Consolas", 9))
        self.txt_path.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(res_box, text="Журнал кроків алгоритму Дейкстри:",
                  font=("Helvetica", 9, "bold")).pack(anchor=tk.W, pady=(4, 2))
        log_frame = ttk.Frame(res_box)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))
        self.txt_log = tk.Text(log_frame, height=14, width=36, wrap=tk.WORD,
                               font=("Consolas", 8), bg="#f8f9fa")
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Button(res_box, text="⧉ Показати результат в окремому вікні",
                   command=self.show_results_window).pack(fill=tk.X)

    def _transform(self):
        cw = max(self.canvas.winfo_width(), 200)
        ch = max(self.canvas.winfo_height(), 200)
        s = min(cw / LOGICAL_W, ch / LOGICAL_H)
        ox = (cw - LOGICAL_W * s) / 2
        oy = (ch - LOGICAL_H * s) / 2
        return s, ox, oy

    def _screen_pos(self, name):
        s, ox, oy = self._transform()
        n = self.graph.nodes[name]
        return ox + n['x'] * s, oy + n['y'] * s

    def _find_node_at(self, sx, sy):
        for name in self.graph.nodes:
            x, y = self._screen_pos(name)
            if math.hypot(sx - x, sy - y) <= NODE_RADIUS + 6:
                return name
        return None

    def _on_canvas_press(self, event):
        name = self._find_node_at(event.x, event.y)
        if name is not None:
            self.dragged_node = name
            self.drag_start_pos = (event.x, event.y)

    def _on_canvas_drag(self, event):
        if self.dragged_node is None:
            return
        s, ox, oy = self._transform()
        lx = max(10, min((event.x - ox) / s, LOGICAL_W - 10))
        ly = max(10, min((event.y - oy) / s, LOGICAL_H - 10))
        node = self.graph.nodes[self.dragged_node]
        node['x'], node['y'] = lx, ly
        self.redraw_graph()

    def _on_canvas_release(self, event):
        if self.dragged_node is not None:
            moved = (abs(event.x - self.drag_start_pos[0]) >= 4 or
                     abs(event.y - self.drag_start_pos[1]) >= 4)
            if not moved:
                self.start_node = self.dragged_node
                self.start_cb.set(self.start_node)
                self.reset_search_state()
                self.log(f"Початкове місто (Start): {self.start_node}")
        self.dragged_node = None

    def _on_canvas_right_click(self, event):
        name = self._find_node_at(event.x, event.y)
        if name is not None:
            self.goal_node = name
            self.goal_cb.set(self.goal_node)
            self.reset_search_state()
            self.log(f"Цільове місто (Goal): {self.goal_node}")

    def _sorted_names(self):
        return sorted(self.graph.nodes, key=ua_sort_key)

    def _edge_text(self, key):
        meta = self.graph.edges[key]
        arrow = "→" if meta['directed'] else "—"
        return f"{key[0]} {arrow} {key[1]}  ({fmt(meta['weight'])} км)"

    def _sorted_edge_keys(self):
        return sorted(self.graph.edges,
                      key=lambda k: (ua_sort_key(k[0]), ua_sort_key(k[1])))

    def _refresh_comboboxes(self):
        names = self._sorted_names()
        self.start_cb['values'] = names
        self.goal_cb['values'] = names
        if self.start_node not in self.graph.nodes:
            self.start_node = names[0] if names else ""
        if self.goal_node not in self.graph.nodes:
            self.goal_node = names[-1] if names else ""
        self.start_cb.set(self.start_node)
        self.goal_cb.set(self.goal_node)

    def _update_graph_metrics(self):
        self.lbl_graph_order.config(text=f"Порядок графу (|V|): {len(self.graph.nodes)}")
        self.lbl_graph_size.config(text=f"Розмір графу (|E|): {len(self.graph.edges)}")

    def _graph_changed(self, message):
        self._refresh_comboboxes()
        self._update_graph_metrics()
        self.reset_search_state()
        self.log(message + f"  [|V| = {len(self.graph.nodes)}, |E| = {len(self.graph.edges)}]")

    def _on_start_changed(self, _event):
        self.start_node = self.start_cb.get()
        self.reset_search_state()

    def _on_goal_changed(self, _event):
        self.goal_node = self.goal_cb.get()
        self.reset_search_state()

    def swap_start_goal(self):
        self.start_node, self.goal_node = self.goal_node, self.start_node
        self.start_cb.set(self.start_node)
        self.goal_cb.set(self.goal_node)
        self.reset_search_state()
        self.log(f"Місцями змінено: Start = {self.start_node}, Goal = {self.goal_node}")

    def _on_speed_changed(self, val):
        self.animation_speed = int(float(val))

    def reload_ukraine_graph(self):
        self.graph = build_ukraine_graph()
        self._graph_changed("Відновлено початковий граф автошляхів України (табл. 1)")

    def log(self, text):
        self.txt_log.insert(tk.END, text + "\n")
        self.txt_log.see(tk.END)

    def reset_search_state(self):
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self.is_running = False
        self.is_paused = False
        self.search_generator = None
        self.vis = None
        self.final_path = []
        self.result = None
        self.expanded_count = 0
        self.relax_count = 0
        self.elapsed_time = 0.0
        self.btn_play.config(text="▶ Авто", state=tk.NORMAL)
        self.btn_pause.config(text="⏸ Пауза", state=tk.DISABLED)
        self.btn_step.config(state=tk.NORMAL)
        self.lbl_status.config(text="Статус: Очікування", foreground="#0066cc")
        self.lbl_expanded.config(text="Зафіксовано вершин: 0")
        self.lbl_relax.config(text="Перевірено ребер: 0")
        self.lbl_time.config(text="Час обчислень: 0.00 мс")
        self.lbl_length.config(text="Найкоротша відстань: -")
        self.txt_path.delete("1.0", tk.END)
        self.redraw_graph()

    def _begin_search(self):
        if not self.graph.nodes:
            messagebox.showinfo("Інформація", "Граф порожній.", parent=self.root)
            return False
        if self.start_node not in self.graph.nodes or self.goal_node not in self.graph.nodes:
            messagebox.showerror("Помилка", "Оберіть початкове та цільове місто.",
                                 parent=self.root)
            return False
        self.reset_search_state()
        self.txt_log.delete("1.0", tk.END)
        self.log(f"Пошук найкоротшого шляху: {self.start_node} → {self.goal_node}")
        self.is_running = True
        self.search_generator = self.graph.dijkstra_steps(self.start_node, self.goal_node)
        return True

    def start_auto_search(self):
        if not self.is_running:
            if not self._begin_search():
                return
            self.is_paused = False
        elif self.is_paused:
            self.is_paused = False
        else:
            return
        self.btn_play.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL)
        self.btn_step.config(state=tk.DISABLED)
        self.lbl_status.config(text="Статус: Пошук...", foreground="#ff8800")
        self.run_animation_loop()

    def pause_search(self):
        if self.is_running and not self.is_paused:
            self.is_paused = True
            if self._after_id is not None:
                self.root.after_cancel(self._after_id)
                self._after_id = None
            self.btn_play.config(text="▶ Продовжити", state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED)
            self.btn_step.config(state=tk.NORMAL)
            self.lbl_status.config(text="Статус: На паузі", foreground="#777777")

    def step_search(self):
        if not self.is_running:
            if not self._begin_search():
                return
            self.is_paused = True
            self.btn_play.config(text="▶ Продовжити", state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED)
            self.lbl_status.config(text="Статус: Покроково", foreground="#777777")
        self._execute_single_step()

    def run_animation_loop(self):
        self._after_id = None
        if self.is_running and not self.is_paused:
            if self._execute_single_step():
                self._after_id = self.root.after(self.animation_speed,
                                                 self.run_animation_loop)

    def _execute_single_step(self):
        if not self.search_generator:
            return False

        t0 = time.perf_counter()
        try:
            state = next(self.search_generator)
        except StopIteration:
            self._finish_execution()
            return False
        self.elapsed_time += (time.perf_counter() - t0) * 1000

        self.vis = state
        self.expanded_count = state['visited_count']
        self.relax_count = state['relax_count']
        self.lbl_expanded.config(text=f"Зафіксовано вершин: {self.expanded_count}")
        self.lbl_relax.config(text=f"Перевірено ребер: {self.relax_count}")
        self.lbl_time.config(text=f"Час обчислень: {self.elapsed_time:.2f} мс")
        self.log(state['message'])

        kind = state['type']
        if kind == 'found':
            self.final_path = state['path']
            self.result = {'found': True, 'path': state['path'],
                           'distance': state['distance'], 'dist': state['dist']}
            self.lbl_status.config(text="Статус: Шлях знайдено!", foreground="#00aa00")
            self.lbl_length.config(text=f"Найкоротша відстань: {fmt(state['distance'])} км")
            self.txt_path.delete("1.0", tk.END)
            self.txt_path.insert(tk.END, " → ".join(state['path']))
            self.redraw_graph()
            self._finish_execution()
            self.show_results_window()
            return False
        if kind == 'not_found':
            self.result = {'found': False, 'path': [], 'distance': INF, 'dist': state['dist']}
            self.lbl_status.config(text="Статус: Шлях не існує", foreground="#cc0000")
            self.lbl_length.config(text="Найкоротша відстань: ∞")
            self.txt_path.delete("1.0", tk.END)
            self.txt_path.insert(tk.END, "Шлях не знайдено")
            self.redraw_graph()
            self._finish_execution()
            self.show_results_window()
            return False

        self.redraw_graph()
        return True

    def _finish_execution(self):
        self.is_running = False
        self.is_paused = False
        self.search_generator = None
        self._after_id = None
        self.btn_play.config(text="▶ Авто", state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED)
        self.btn_step.config(state=tk.DISABLED)

    def redraw_graph(self):
        c = self.canvas
        c.delete("all")
        g = self.graph
        vis = self.vis
        r = NODE_RADIUS

        final_pairs = set(zip(self.final_path, self.final_path[1:]))
        tree_pairs = set()
        relax_pair = None
        active = None
        if vis:
            tree_pairs = {(p, v) for v, p in vis['prev'].items() if p is not None}
            relax_pair = vis.get('relax_edge')
            if vis['type'] in ('visit', 'relax'):
                active = vis.get('current')

        def matches(pairs, u, v, directed):
            return (u, v) in pairs or (not directed and (v, u) in pairs)

        styled = []
        for (u, v), meta in g.edges.items():
            if u not in g.nodes or v not in g.nodes:
                continue
            directed = meta['directed']
            if matches(final_pairs, u, v, directed):
                prio, color, width, tcolor = 3, "#28a745", 4.5, "#1b5e20"
            elif relax_pair and matches({relax_pair}, u, v, directed):
                prio, color, width, tcolor = 2, "#ff9900", 3.5, "#b36b00"
            elif matches(tree_pairs, u, v, directed):
                prio, color, width, tcolor = 1, "#4a90d9", 2.5, "#1f4e8c"
            else:
                prio, color, width, tcolor = 0, "#b0b0b0", 1.5, "#444444"
            styled.append((prio, u, v, meta, color, width, tcolor))
        styled.sort(key=lambda t: t[0])

        labels = []
        for prio, u, v, meta, color, width, tcolor in styled:
            x1, y1 = self._screen_pos(u)
            x2, y2 = self._screen_pos(v)
            directed = meta['directed']
            dx, dy = x2 - x1, y2 - y1
            dist = math.hypot(dx, dy) + 0.001
            ux, uy = dx / dist, dy / dist

            if directed and (v, u) in g.edges and g.edges[(v, u)]['directed']:
                nx, ny = -uy * 5, ux * 5
                x1, y1, x2, y2 = x1 + nx, y1 + ny, x2 + nx, y2 + ny

            if directed:
                x2 -= ux * (r + 1)
                y2 -= uy * (r + 1)
            c.create_line(x1, y1, x2, y2, fill=color, width=width,
                          arrow=tk.LAST if directed else None, arrowshape=(10, 12, 4))
            labels.append(((x1 + x2) / 2, (y1 + y2) / 2, fmt(meta['weight']), tcolor))

        for mx, my, text, tcolor in labels:
            item = c.create_text(mx, my, text=text, font=("Helvetica", 8), fill=tcolor)
            x0, y0, x1_, y1_ = c.bbox(item)
            bg = c.create_rectangle(x0 - 1, y0, x1_ + 1, y1_, fill="#ffffff", outline="")
            c.tag_lower(bg, item)

        visited = vis['visited'] if vis else set()
        frontier = vis['frontier'] if vis else set()
        dist = vis['dist'] if vis else {}
        for name in g.nodes:
            x, y = self._screen_pos(name)

            if name in (self.start_node, self.goal_node):
                ring = "#38b000" if name == self.start_node else "#c9184a"
                if name == self.start_node == self.goal_node:
                    ring = "#8338ec"
                c.create_oval(x - r - 4, y - r - 4, x + r + 4, y + r + 4,
                              outline=ring, width=3)

            if name == active:
                fill = "#ffb703"
            elif name in self.final_path:
                fill = "#a3e635"
            elif name in visited:
                fill = "#90e0ef"
            elif name in frontier:
                fill = "#fff3b0"
            else:
                fill = "#ffffff"
            c.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline="#343a40", width=2)
            c.create_text(x, y + r + 9, text=name, font=("Helvetica", 8, "bold"),
                          fill="#111111")

            d = dist.get(name, INF)
            if vis and d < INF:
                c.create_text(x, y - r - 8, text=fmt(d), font=("Helvetica", 8, "bold"),
                              fill="#0b3d91" if name in visited else "#c1121f")

        self._draw_legend()

    def _draw_legend(self):
        c = self.canvas
        ch = max(c.winfo_height(), 200)
        items = [
            ("#ffb703", "поточна вершина"),
            ("#90e0ef", "мітку зафіксовано"),
            ("#fff3b0", "у черзі (мітка тимчасова)"),
            ("#a3e635", "вершина найкоротшого шляху"),
        ]
        x0, y0 = 12, ch - 12 - 18 * (len(items) + 1)
        for i, (color, text) in enumerate(items):
            y = y0 + i * 18
            c.create_oval(x0, y, x0 + 12, y + 12, fill=color, outline="#343a40", width=1)
            c.create_text(x0 + 20, y + 6, text=text, anchor=tk.W, font=("Helvetica", 8))
        y = y0 + len(items) * 18
        c.create_line(x0, y + 6, x0 + 12, y + 6, fill="#4a90d9", width=3)
        c.create_text(x0 + 20, y + 6, text="дерево найкоротших шляхів; числа - мітки/км",
                      anchor=tk.W, font=("Helvetica", 8))

    def show_results_window(self):
        if self.result is None:
            messagebox.showinfo("Результат", "Пошук ще не виконано або не було завершено.",
                                parent=self.root)
            return
        if self.result_win is not None and self.result_win.winfo_exists():
            self.result_win.destroy()

        res = self.result
        win = tk.Toplevel(self.root)
        self.result_win = win
        win.title("Результат пошуку найкоротшого шляху")
        win.geometry("600x520")
        win.minsize(480, 380)
        win.transient(self.root)

        frame = ttk.Frame(win, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="РЕЗУЛЬТАТ ПОШУКУ (алгоритм Дейкстри)",
                  font=("Helvetica", 11, "bold")).pack(pady=(0, 8))

        ttk.Button(frame, text="Закрити", command=win.destroy).pack(side=tk.BOTTOM, anchor=tk.E)

        cond = ttk.LabelFrame(frame, text="Умови пошуку", padding=8)
        cond.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(cond, text=f"• Початкове місто: {self.start_node}").pack(anchor=tk.W)
        ttk.Label(cond, text=f"• Цільове місто: {self.goal_node}").pack(anchor=tk.W)
        ttk.Label(cond, text=f"• Порядок графу (|V|): {len(self.graph.nodes)},  "
                             f"розмір графу (|E|): {len(self.graph.edges)}").pack(anchor=tk.W)

        out = ttk.LabelFrame(frame, text="Отримані результати", padding=8)
        out.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        if not res['found']:
            ttk.Label(out, text=f"Шлях із «{self.start_node}» до «{self.goal_node}» "
                                f"не існує.", foreground="#cc0000",
                      font=("Helvetica", 10, "bold")).pack(anchor=tk.W, pady=4)
        else:
            path, dist = res['path'], res['dist']
            ttk.Label(out, text=f"Найкоротша відстань: {fmt(res['distance'])} км",
                      font=("Helvetica", 12, "bold"), foreground="#1b5e20"
                      ).pack(anchor=tk.W, pady=(0, 2))
            ttk.Label(out, text=f"Кількість міст на маршруті: {len(path)}").pack(anchor=tk.W)

            cols = ("n", "city", "seg", "total")
            tree_frame = ttk.Frame(out)
            tree_frame.pack(fill=tk.BOTH, expand=True, pady=6)
            tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=8)
            tree.heading("n", text="№")
            tree.heading("city", text="Місто")
            tree.heading("seg", text="Ділянка, км")
            tree.heading("total", text="Від старту, км")
            tree.column("n", width=40, anchor=tk.CENTER, stretch=False)
            tree.column("city", width=200, anchor=tk.W)
            tree.column("seg", width=100, anchor=tk.CENTER)
            tree.column("total", width=110, anchor=tk.CENTER)
            sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=sb.set)
            sb.pack(side=tk.RIGHT, fill=tk.Y)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            for i, city in enumerate(path):
                seg = "-" if i == 0 else fmt(dist[city] - dist[path[i - 1]])
                tree.insert("", tk.END, values=(i + 1, city, seg, fmt(dist[city])))

            ttk.Label(out, text="Маршрут:", font=("Helvetica", 9, "bold")).pack(anchor=tk.W)
            t = tk.Text(out, height=3, wrap=tk.WORD, font=("Consolas", 9))
            t.pack(fill=tk.X)
            t.insert(tk.END, " → ".join(path))
            t.config(state=tk.DISABLED)

    def _make_dialog(self, title):
        d = tk.Toplevel(self.root)
        d.title(title)
        d.transient(self.root)
        d.resizable(False, False)
        body = ttk.Frame(d, padding=12)
        body.pack(fill=tk.BOTH, expand=True)
        try:
            d.wait_visibility()
            d.grab_set()
        except tk.TclError:
            pass
        return d, body

    @staticmethod
    def _parse_weight(text):
        try:
            w = float(text.strip().replace(",", "."))
        except ValueError:
            raise ValueError("Вага має бути числом")
        if w <= 0 or math.isinf(w) or math.isnan(w):
            raise ValueError("Вага має бути скінченним додатним числом")
        return int(w) if w.is_integer() else w

    def gui_add_node_dialog(self):
        d, body = self._make_dialog("Додати вершину (місто)")

        ttk.Label(body, text="Назва міста:").pack(anchor=tk.W)
        ent_name = ttk.Entry(body, width=30)
        ent_name.pack(fill=tk.X, pady=(0, 6))
        ent_name.focus_set()

        ttk.Label(body, text=f"Координата X (0-{LOGICAL_W}):").pack(anchor=tk.W)
        ent_x = ttk.Entry(body)
        ent_x.insert(0, str(LOGICAL_W // 2))
        ent_x.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(body, text=f"Координата Y (0-{LOGICAL_H}):").pack(anchor=tk.W)
        ent_y = ttk.Entry(body)
        ent_y.insert(0, str(LOGICAL_H // 2))
        ent_y.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(body, text="Після додавання вершину можна перетягнути мишею.\n"
                             "Не забудьте з'єднати її ребрами.",
                  font=("Helvetica", 8), foreground="#666666").pack(anchor=tk.W, pady=(0, 6))

        def save():
            name = ent_name.get().strip()
            if not name:
                messagebox.showerror("Помилка", "Введіть назву міста", parent=d)
                return
            try:
                x = float(ent_x.get().replace(",", "."))
                y = float(ent_y.get().replace(",", "."))
            except ValueError:
                messagebox.showerror("Помилка", "Координати мають бути числами", parent=d)
                return
            x = max(10, min(x, LOGICAL_W - 10))
            y = max(10, min(y, LOGICAL_H - 10))
            try:
                self.graph.add_node(name, x, y)
            except ValueError as e:
                messagebox.showerror("Помилка", str(e), parent=d)
                return
            d.destroy()
            self._graph_changed(f"Додано вершину «{name}»")

        ttk.Button(body, text="Додати", command=save).pack(anchor=tk.E)

    def gui_remove_node_dialog(self):
        if not self.graph.nodes:
            return
        d, body = self._make_dialog("Вилучити вершину (місто)")
        ttk.Label(body, text="Оберіть місто для видалення:").pack(anchor=tk.W)
        cb = ttk.Combobox(body, values=self._sorted_names(), state="readonly", width=30)
        cb.pack(fill=tk.X, pady=6)
        cb.current(0)

        def remove():
            name = cb.get()
            if name not in self.graph.nodes:
                return
            deg = sum(1 for k in self.graph.edges if name in k)
            self.graph.remove_node(name)
            d.destroy()
            self._graph_changed(f"Вилучено вершину «{name}» та {deg} прилеглих ребер/дуг")

        ttk.Button(body, text="Вилучити", command=remove).pack(anchor=tk.E)

    def gui_add_edge_dialog(self):
        names = self._sorted_names()
        if len(names) < 2:
            messagebox.showinfo("Інформація", "Для ребра потрібно щонайменше 2 вершини.",
                                parent=self.root)
            return
        d, body = self._make_dialog("Додати ребро / дугу")

        ttk.Label(body, text="З міста (вершина 1):").pack(anchor=tk.W)
        cb1 = ttk.Combobox(body, values=names, state="readonly", width=30)
        cb1.pack(fill=tk.X, pady=(0, 6))
        cb1.current(0)

        ttk.Label(body, text="До міста (вершина 2):").pack(anchor=tk.W)
        cb2 = ttk.Combobox(body, values=names, state="readonly", width=30)
        cb2.pack(fill=tk.X, pady=(0, 6))
        cb2.current(1)

        ttk.Label(body, text="Відстань (вага), км:").pack(anchor=tk.W)
        ent_w = ttk.Entry(body)
        ent_w.pack(fill=tk.X, pady=(0, 6))

        dir_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(body, text="Орієнтована дуга (від першого міста до другого)",
                        variable=dir_var).pack(anchor=tk.W, pady=(0, 8))

        def add():
            u, v = cb1.get(), cb2.get()
            try:
                w = self._parse_weight(ent_w.get())
                existed = any(set(k) == {u, v} for k in self.graph.edges)
                self.graph.add_edge(u, v, w, dir_var.get())
            except ValueError as e:
                messagebox.showerror("Помилка", str(e), parent=d)
                return
            d.destroy()
            arrow = "→" if dir_var.get() else "—"
            verb = "Змінено" if existed else "Додано"
            kind = "дугу" if dir_var.get() else "ребро"
            self._graph_changed(f"{verb} {kind}: {u} {arrow} {v} ({fmt(w)} км)")

        ttk.Button(body, text="Зберегти", command=add).pack(anchor=tk.E)

    def gui_remove_edge_dialog(self):
        if not self.graph.edges:
            messagebox.showinfo("Інформація", "У графі немає ребер.", parent=self.root)
            return
        keys = self._sorted_edge_keys()
        d, body = self._make_dialog("Вилучити ребро / дугу")
        ttk.Label(body, text="Оберіть ребро або дугу:").pack(anchor=tk.W)
        cb = ttk.Combobox(body, values=[self._edge_text(k) for k in keys],
                          state="readonly", width=44)
        cb.pack(fill=tk.X, pady=6)
        cb.current(0)

        def remove():
            idx = cb.current()
            if idx < 0:
                return
            key = keys[idx]
            text = self._edge_text(key)
            self.graph.remove_edge(key)
            d.destroy()
            self._graph_changed(f"Вилучено зв'язок: {text}")

        ttk.Button(body, text="Вилучити", command=remove).pack(anchor=tk.E)

    def gui_edit_weight_dialog(self):
        if not self.graph.edges:
            messagebox.showinfo("Інформація", "У графі немає ребер.", parent=self.root)
            return
        keys = self._sorted_edge_keys()
        d, body = self._make_dialog("Змінити вагу ребра")
        ttk.Label(body, text="Оберіть ребро або дугу:").pack(anchor=tk.W)
        cb = ttk.Combobox(body, values=[self._edge_text(k) for k in keys],
                          state="readonly", width=44)
        cb.pack(fill=tk.X, pady=(0, 6))
        cb.current(0)

        ttk.Label(body, text="Нова відстань (вага), км:").pack(anchor=tk.W)
        ent_w = ttk.Entry(body)
        ent_w.pack(fill=tk.X, pady=(0, 8))

        def load_weight(*_):
            idx = cb.current()
            if idx >= 0:
                ent_w.delete(0, tk.END)
                ent_w.insert(0, fmt(self.graph.edges[keys[idx]]['weight']))

        cb.bind("<<ComboboxSelected>>", load_weight)
        load_weight()

        def apply():
            idx = cb.current()
            if idx < 0:
                return
            try:
                w = self._parse_weight(ent_w.get())
            except ValueError as e:
                messagebox.showerror("Помилка", str(e), parent=d)
                return
            key = keys[idx]
            old = self.graph.edges[key]['weight']
            self.graph.edges[key]['weight'] = w
            d.destroy()
            self._graph_changed(f"Вагу зв'язку {key[0]} - {key[1]} змінено: "
                                f"{fmt(old)} → {fmt(w)} км")

        ttk.Button(body, text="Застосувати", command=apply).pack(anchor=tk.E)

    def gui_toggle_edge_type_dialog(self):
        if not self.graph.edges:
            messagebox.showinfo("Інформація", "У графі немає ребер для зміни.",
                                parent=self.root)
            return
        keys = self._sorted_edge_keys()
        d, body = self._make_dialog("Зміна типу та напрямку зв'язку")
        ttk.Label(body, text="Оберіть ребро/дугу зі списку:").pack(anchor=tk.W)
        cb = ttk.Combobox(body, values=[self._edge_text(k) for k in keys],
                          state="readonly", width=44)
        cb.pack(fill=tk.X, pady=(0, 6))
        cb.current(0)

        type_var = tk.StringVar(value="undirected")
        box = ttk.LabelFrame(body, text="Новий стан зв'язку", padding=8)
        box.pack(fill=tk.X, pady=6)
        rb_undir = ttk.Radiobutton(box, text="", variable=type_var, value="undirected")
        rb_fwd = ttk.Radiobutton(box, text="", variable=type_var, value="forward")
        rb_rev = ttk.Radiobutton(box, text="", variable=type_var, value="reverse")
        for rb in (rb_undir, rb_fwd, rb_rev):
            rb.pack(anchor=tk.W, pady=2)

        def update_labels(*_):
            idx = cb.current()
            if idx < 0:
                return
            u, v = keys[idx]
            rb_undir.config(text=f"Неорієнтоване ребро ({u} — {v})")
            rb_fwd.config(text=f"Дуга ({u} → {v})")
            rb_rev.config(text=f"Дуга ({v} → {u})")
            type_var.set("forward" if self.graph.edges[keys[idx]]['directed'] else "undirected")

        cb.bind("<<ComboboxSelected>>", update_labels)
        update_labels()

        def apply():
            idx = cb.current()
            if idx < 0:
                return
            old_key = keys[idx]
            u, v = old_key
            w = self.graph.edges[old_key]['weight']
            choice = type_var.get()
            self.graph.remove_edge(old_key)
            if choice == "undirected":
                self.graph.add_edge(u, v, w, False)
                msg = f"Зв'язок {u} - {v} став неорієнтованим ребром ({fmt(w)} км)"
            elif choice == "forward":
                self.graph.add_edge(u, v, w, True)
                msg = f"Зв'язок {u} - {v} став дугою {u} → {v} ({fmt(w)} км)"
            else:
                self.graph.add_edge(v, u, w, True)
                msg = f"Зв'язок {u} - {v} став дугою {v} → {u} ({fmt(w)} км)"
            d.destroy()
            self._graph_changed(msg)

        btns = ttk.Frame(body)
        btns.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btns, text="Застосувати", command=apply).pack(side=tk.RIGHT)
        ttk.Button(btns, text="Скасувати", command=d.destroy).pack(side=tk.RIGHT, padx=4)


if __name__ == "__main__":
    root = tk.Tk()
    app = DijkstraApp(root)
    root.mainloop()
