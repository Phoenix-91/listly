"""
To-Do List Application — glassmorphism dark UI edition.
Python + Tkinter, local JSON storage, no external libraries.
"""

import json
import os
import tkinter as tk
from tkinter import messagebox

DATA_FILE = "tasks.json"

# ---------------------------------------------------------------- THEME ----

BG            = "#0c1018"   # app background
SIDEBAR_BG    = "#0f1420"
PANEL_GLASS   = "#161c2b"   # "glass" card base
PANEL_GLASS_2 = "#1b2334"   # lighter glass layer (hover / header bars)
BORDER        = "#242d42"
TEXT          = "#eef1f8"
TEXT_DIM      = "#8992a9"
TEXT_FAINT    = "#5b6478"
ACCENT        = "#5b6bff"
ACCENT_SOFT   = "#242a4d"
DONE_GREEN    = "#2fd480"
DANGER        = "#ff5c6c"

CATEGORIES = {
    "Work":     "#5b6bff",
    "Personal": "#2fd480",
    "Study":    "#f2b84b",
    "Health":   "#ff5c6c",
}

FONT_FAMILY = "Segoe UI"


def mix(hex_a, hex_b, t):
    """Blend two hex colors; t=0 -> a, t=1 -> b. Used for subtle hover tints."""
    a = tuple(int(hex_a[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(hex_b[i:i + 2], 16) for i in (1, 3, 5))
    out = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return "#%02x%02x%02x" % out


# ----------------------------------------------------------- DATA LAYER ----

class TaskStore:
    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        self.tasks = []
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.tasks = []
        for t in self.tasks:
            t.setdefault("category", "Personal")
            t.setdefault("due", "")

    def save(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, indent=2, ensure_ascii=False)

    def add_task(self, text, category, due):
        new_id = (max([t["id"] for t in self.tasks], default=0)) + 1
        task = {"id": new_id, "text": text, "done": False,
                "category": category, "due": due}
        self.tasks.append(task)
        self.save()
        return task

    def delete_task(self, task_id):
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        self.save()

    def toggle_done(self, task_id):
        for t in self.tasks:
            if t["id"] == task_id:
                t["done"] = not t["done"]
        self.save()

    def counts(self):
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t["done"]])
        pending = total - completed
        return total, completed, pending


# --------------------------------------------------------- ROUNDED CARD ----

class GlassCard(tk.Canvas):
    """A canvas that draws a rounded, softly-bordered 'glass' panel and
    hosts a Frame on top of it where normal widgets can be packed."""

    def __init__(self, parent, radius=16, fill=PANEL_GLASS, outline=BORDER, **kw):
        super().__init__(parent, bg=parent["bg"], highlightthickness=0, bd=0, **kw)
        self.radius = radius
        self.fill = fill
        self.outline = outline
        self.inner = tk.Frame(self, bg=fill)
        self.bind("<Configure>", self._redraw)

    def _round_rect(self, x1, y1, x2, y2, r):
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        return self.create_polygon(points, smooth=True,
                                    fill=self.fill, outline=self.outline, width=1)

    def _redraw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2:
            return
        self._round_rect(1, 1, w - 1, h - 1, self.radius)
        # faint top highlight line to fake a glass sheen
        self.create_line(self.radius, 2, w - self.radius, 2,
                          fill=mix(self.fill, "#ffffff", 0.08))
        self.create_window(0, 0, window=self.inner, anchor="nw",
                            width=w, height=h)


# ----------------------------------------------------------------- APP -----

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.store = TaskStore()
        self.filter_mode = "All"        # All | Today-less (kept simple) | Completed | Pending
        self.category_var = None
        self.due_var = None

        root.title("ToDo — Plan. Focus. Achieve.")
        root.geometry("920x620")
        root.minsize(760, 520)
        root.configure(bg=BG)

        self._build_sidebar()
        self._build_main()
        self.refresh()

    # ----------------------------------------------------------- SIDEBAR --

    def _build_sidebar(self):
        sidebar = tk.Frame(self.root, bg=SIDEBAR_BG, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=SIDEBAR_BG)
        brand.pack(fill="x", padx=20, pady=(24, 28))
        badge = tk.Label(brand, text="✓", font=(FONT_FAMILY, 13, "bold"),
                          bg=ACCENT, fg="white", width=2, height=1)
        badge.pack(side="left")
        tk.Label(brand, text="ToDo", font=(FONT_FAMILY, 16, "bold"),
                 bg=SIDEBAR_BG, fg=TEXT).pack(side="left", padx=10)

        tk.Label(sidebar, text="Plan · Focus · Achieve",
                 font=(FONT_FAMILY, 8), bg=SIDEBAR_BG, fg=TEXT_FAINT
                 ).pack(anchor="w", padx=20, pady=(0, 20))

        self.nav_buttons = {}
        for label in ("All", "Pending", "Completed"):
            self._nav_item(sidebar, label)

        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=20, pady=16)
        tk.Label(sidebar, text="CATEGORIES", font=(FONT_FAMILY, 8, "bold"),
                 bg=SIDEBAR_BG, fg=TEXT_FAINT).pack(anchor="w", padx=22, pady=(0, 8))

        self.category_count_labels = {}
        for cat, color in CATEGORIES.items():
            row = tk.Frame(sidebar, bg=SIDEBAR_BG)
            row.pack(fill="x", padx=22, pady=4)
            dot = tk.Label(row, text="●", font=(FONT_FAMILY, 9), bg=SIDEBAR_BG, fg=color)
            dot.pack(side="left")
            tk.Label(row, text=cat, font=(FONT_FAMILY, 10), bg=SIDEBAR_BG, fg=TEXT_DIM
                      ).pack(side="left", padx=8)
            count_lbl = tk.Label(row, text="0", font=(FONT_FAMILY, 9),
                                  bg=SIDEBAR_BG, fg=TEXT_FAINT)
            count_lbl.pack(side="right")
            self.category_count_labels[cat] = count_lbl

    def _nav_item(self, parent, label):
        frame = tk.Frame(parent, bg=SIDEBAR_BG, cursor="hand2")
        frame.pack(fill="x", padx=12, pady=3)
        text_lbl = tk.Label(frame, text=label, font=(FONT_FAMILY, 10),
                             bg=SIDEBAR_BG, fg=TEXT_DIM, anchor="w")
        text_lbl.pack(side="left", fill="x", expand=True, padx=12, pady=9)
        count_lbl = tk.Label(frame, text="0", font=(FONT_FAMILY, 9),
                              bg=SIDEBAR_BG, fg=TEXT_FAINT)
        count_lbl.pack(side="right", padx=12)

        widgets = (frame, text_lbl, count_lbl)
        for w in widgets:
            w.bind("<Button-1>", lambda e, l=label: self.set_filter(l))
        self.nav_buttons[label] = widgets

    def set_filter(self, label):
        self.filter_mode = label
        self.refresh()

    def _style_nav(self):
        for label, (frame, text_lbl, count_lbl) in self.nav_buttons.items():
            active = (label == self.filter_mode)
            bg = ACCENT_SOFT if active else SIDEBAR_BG
            fg = TEXT if active else TEXT_DIM
            frame.configure(bg=bg)
            text_lbl.configure(bg=bg, fg=fg,
                                font=(FONT_FAMILY, 10, "bold" if active else "normal"))
            count_lbl.configure(bg=bg, fg=ACCENT if active else TEXT_FAINT)

    # -------------------------------------------------------------- MAIN --

    def _build_main(self):
        main = tk.Frame(self.root, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        header = tk.Frame(main, bg=BG)
        header.pack(fill="x", padx=28, pady=(24, 10))
        tk.Label(header, text="All Tasks", font=(FONT_FAMILY, 20, "bold"),
                 bg=BG, fg=TEXT).pack(side="left")
        self.subtitle = tk.Label(header, text="", font=(FONT_FAMILY, 10),
                                  bg=BG, fg=TEXT_DIM)
        self.subtitle.pack(side="left", padx=14, pady=(8, 0))

        # ---- glass input bar ----
        input_card = GlassCard(main, radius=14, height=56)
        input_card.pack(fill="x", padx=28, pady=(4, 14))
        input_card.pack_propagate(False)
        inner = input_card.inner

        self.task_entry = tk.Entry(inner, font=(FONT_FAMILY, 11),
                                    bg=PANEL_GLASS, fg=TEXT, insertbackground=TEXT,
                                    relief="flat")
        self.task_entry.insert(0, "")
        self.task_entry.pack(side="left", fill="both", expand=True, padx=(16, 8), pady=12)
        self.task_entry.bind("<Return>", lambda e: self.add_task())
        self._placeholder(self.task_entry, "What do you want to do?")

        self.category_var = tk.StringVar(value="Personal")
        cat_menu = tk.OptionMenu(inner, self.category_var, *CATEGORIES.keys())
        cat_menu.configure(font=(FONT_FAMILY, 9), bg=PANEL_GLASS_2, fg=TEXT,
                            activebackground=ACCENT_SOFT, relief="flat",
                            highlightthickness=0, bd=0, padx=10)
        cat_menu["menu"].configure(bg=PANEL_GLASS_2, fg=TEXT)
        cat_menu.pack(side="left", padx=6, pady=12)

        self.due_entry = tk.Entry(inner, font=(FONT_FAMILY, 9), width=10,
                                   bg=PANEL_GLASS_2, fg=TEXT_DIM, insertbackground=TEXT,
                                   relief="flat", justify="center")
        self.due_entry.pack(side="left", padx=6, pady=12, ipady=4)
        self._placeholder(self.due_entry, "Due date")

        add_btn = tk.Label(inner, text="+  Add Task", font=(FONT_FAMILY, 10, "bold"),
                            bg=ACCENT, fg="white", cursor="hand2", padx=16, pady=8)
        add_btn.pack(side="left", padx=(6, 14), pady=10)
        add_btn.bind("<Button-1>", lambda e: self.add_task())
        add_btn.bind("<Enter>", lambda e: add_btn.configure(bg=mix(ACCENT, "#ffffff", 0.15)))
        add_btn.bind("<Leave>", lambda e: add_btn.configure(bg=ACCENT))

        # ---- scrollable task list ----
        list_container = tk.Frame(main, bg=BG)
        list_container.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        self.canvas = tk.Canvas(list_container, bg=BG, highlightthickness=0)
        vscroll = tk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.list_frame = tk.Frame(self.canvas, bg=BG)
        self.list_frame.bind("<Configure>",
                              lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._canvas_window = self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.canvas.bind("<Configure>",
                          lambda e: self.canvas.itemconfig(self._canvas_window, width=e.width))
        self.canvas.configure(yscrollcommand=vscroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>",
                              lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _placeholder(self, entry, text):
        entry.insert(0, text)
        entry.configure(fg=TEXT_FAINT)

        def on_focus_in(_):
            if entry.get() == text:
                entry.delete(0, tk.END)
                entry.configure(fg=TEXT)

        def on_focus_out(_):
            if not entry.get():
                entry.insert(0, text)
                entry.configure(fg=TEXT_FAINT)

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        entry._placeholder_text = text

    def _value_or_blank(self, entry):
        val = entry.get().strip()
        return "" if val == getattr(entry, "_placeholder_text", None) else val

    # ------------------------------------------------------------ ACTIONS --

    def add_task(self):
        text = self._value_or_blank(self.task_entry)
        if not text:
            messagebox.showwarning("Empty Task", "Please enter a task before adding.")
            return
        category = self.category_var.get()
        due = self._value_or_blank(self.due_entry)
        self.store.add_task(text, category, due)
        self.task_entry.delete(0, tk.END)
        self._placeholder(self.task_entry, "What do you want to do?")
        self.due_entry.delete(0, tk.END)
        self._placeholder(self.due_entry, "Due date")
        self.refresh()

    def delete_task(self, task_id):
        self.store.delete_task(task_id)
        self.refresh()

    def toggle_done(self, task_id):
        self.store.toggle_done(task_id)
        self.refresh()

    # ------------------------------------------------------------ RENDER --

    def refresh(self):
        self._style_nav()

        total, completed, pending = self.store.counts()
        self.subtitle.configure(
            text=f"{total} tasks  ·  {pending} pending  ·  {completed} completed")

        for cat, lbl in self.category_count_labels.items():
            n = len([t for t in self.store.tasks if t["category"] == cat])
            lbl.configure(text=str(n))

        for w in self.list_frame.winfo_children():
            w.destroy()

        tasks = self.store.tasks
        if self.filter_mode == "Completed":
            tasks = [t for t in tasks if t["done"]]
        elif self.filter_mode == "Pending":
            tasks = [t for t in tasks if not t["done"]]

        if not tasks:
            tk.Label(self.list_frame, text="Nothing here yet ✨",
                     font=(FONT_FAMILY, 11, "italic"), bg=BG, fg=TEXT_FAINT
                     ).pack(pady=40)
            return

        for task in tasks:
            self._render_row(task)

    def _render_row(self, task):
        card = GlassCard(self.list_frame, radius=12, height=56,
                          fill=PANEL_GLASS if not task["done"] else "#141a27")
        card.pack(fill="x", pady=5)
        card.pack_propagate(False)
        row = card.inner

        def on_enter(_e):
            card.fill = mix(PANEL_GLASS, "#ffffff", 0.03) if not task["done"] else "#141a27"
            card._redraw()
            row.configure(bg=card.fill)
            for child in row.winfo_children():
                try:
                    child.configure(bg=card.fill)
                except tk.TclError:
                    pass
            del_btn.pack(side="right", padx=(0, 14))

        def on_leave(_e):
            card.fill = PANEL_GLASS if not task["done"] else "#141a27"
            card._redraw()
            row.configure(bg=card.fill)
            for child in row.winfo_children():
                try:
                    child.configure(bg=card.fill)
                except tk.TclError:
                    pass
            del_btn.pack_forget()

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

        # checkbox circle
        check_canvas = tk.Canvas(row, width=26, height=26, bg=row["bg"],
                                  highlightthickness=0, cursor="hand2")
        check_canvas.pack(side="left", padx=(16, 12))
        if task["done"]:
            check_canvas.create_oval(2, 2, 24, 24, fill=DONE_GREEN, outline=DONE_GREEN)
            check_canvas.create_text(13, 13, text="✓", fill="white",
                                      font=(FONT_FAMILY, 11, "bold"))
        else:
            check_canvas.create_oval(2, 2, 24, 24, outline=TEXT_FAINT, width=2)
        check_canvas.bind("<Button-1>", lambda e: self.toggle_done(task["id"]))

        # task text
        text_color = TEXT_FAINT if task["done"] else TEXT
        font_style = (FONT_FAMILY, 11, "overstrike") if task["done"] else (FONT_FAMILY, 11)
        label = tk.Label(row, text=task["text"], font=font_style,
                          bg=row["bg"], fg=text_color, anchor="w")
        label.pack(side="left", fill="x", expand=True, padx=4)

        # due date
        if task["due"]:
            tk.Label(row, text=task["due"], font=(FONT_FAMILY, 9),
                     bg=row["bg"], fg=TEXT_FAINT).pack(side="right", padx=12)

        # category badge
        color = CATEGORIES.get(task["category"], TEXT_FAINT)
        badge = tk.Label(row, text=task["category"], font=(FONT_FAMILY, 8, "bold"),
                          bg=mix(color, PANEL_GLASS, 0.6), fg=color, padx=8, pady=3)
        badge.pack(side="right", padx=6)

        # delete button (shown on hover)
        del_btn = tk.Label(row, text="🗑", font=(FONT_FAMILY, 10),
                            bg=row["bg"], fg=DANGER, cursor="hand2")
        del_btn.bind("<Button-1>", lambda e: self.delete_task(task["id"]))


def main():
    root = tk.Tk()
    TodoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
