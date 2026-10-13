"""
Tic Tac Toe berbasis AI dengan algoritma Minimax dan Alpha-Beta Pruning.

Pemain (Human) memakai simbol X, sedangkan AI memakai simbol O.
Antarmuka dibuat dengan Tkinter (bawaan Python, tanpa dependensi tambahan).

Jalankan dengan:
    python tic_tac_toe_minimax.py
"""

from __future__ import annotations

import math
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox
from typing import Callable, Optional

HUMAN = "X"
AI = "O"
EMPTY = ""
DRAW = "draw"

WINNING_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # baris
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # kolom
    (0, 4, 8), (2, 4, 6),             # diagonal
)

ALGORITHM_MINIMAX = "minimax"
ALGORITHM_ALPHA_BETA = "alphabeta"
ALGORITHM_LABELS = {
    ALGORITHM_MINIMAX: "Minimax",
    ALGORITHM_ALPHA_BETA: "Alpha-Beta",
}

# Pengaturan tampilan dan waktu
FONT_FAMILY = "Segoe UI"
CELL_SIZE = 120
CELL_GAP = 8
CELL_RADIUS = 16
MARK_WIDTH = 10
AI_DELAY_MS = 450
RESULT_DIALOG_DELAY_MS = 800
ANIMATION_SCALES = (0.35, 0.65, 0.95, 1.1, 1.0)
ANIMATION_STEP_MS = 18


class Palette:
    """Kumpulan warna tema gelap."""

    BG = "#171923"
    CARD = "#232634"
    CELL = "#2d3148"
    CELL_HOVER = "#383d5c"
    WIN_TINT = "#274238"
    TEXT = "#eceff8"
    MUTED = "#8e94ad"
    ACCENT = "#6c7bff"
    ACCENT_HOVER = "#8592ff"
    X_COLOR = "#4dd0e1"
    O_COLOR = "#ffb74d"
    SUCCESS = "#69d58c"
    DANGER = "#ff6b7a"
    WARNING = "#ffd166"


TONE_COLORS = {
    "info": Palette.TEXT,
    "thinking": Palette.ACCENT_HOVER,
    "warning": Palette.WARNING,
    "win": Palette.SUCCESS,
    "lose": Palette.DANGER,
    "draw": Palette.WARNING,
}


# ---------------------------------------------------------------------------
# Logika permainan dan AI
# ---------------------------------------------------------------------------
class Board:
    """Papan permainan 3x3 yang disimpan sebagai list satu dimensi."""

    def __init__(self) -> None:
        self.cells: list[str] = [EMPTY] * 9

    def available_moves(self) -> list[int]:
        """Mengembalikan indeks semua kotak yang masih kosong."""
        return [i for i, cell in enumerate(self.cells) if cell == EMPTY]

    def place(self, index: int, symbol: str) -> None:
        """Menempatkan simbol; melempar ValueError jika langkah tidak valid."""
        if not 0 <= index < len(self.cells):
            raise ValueError("Posisi berada di luar papan.")
        if self.cells[index] != EMPTY:
            raise ValueError("Posisi sudah terisi.")
        self.cells[index] = symbol

    def undo(self, index: int) -> None:
        """Mengosongkan kembali sebuah kotak (dipakai saat pencarian AI)."""
        self.cells[index] = EMPTY

    def winning_line(self) -> Optional[tuple[int, int, int]]:
        """Mengembalikan garis kemenangan jika ada, selain itu None."""
        for a, b, c in WINNING_LINES:
            if self.cells[a] != EMPTY and self.cells[a] == self.cells[b] == self.cells[c]:
                return (a, b, c)
        return None

    def winner(self) -> Optional[str]:
        """Mengembalikan simbol pemenang, atau None jika belum ada."""
        line = self.winning_line()
        return self.cells[line[0]] if line else None

    def is_full(self) -> bool:
        return EMPTY not in self.cells

    def is_game_over(self) -> bool:
        return self.winner() is not None or self.is_full()


@dataclass
class SearchStats:
    """Menghitung jumlah simpul yang dikunjungi selama pencarian."""

    nodes: int = 0


def evaluate(board: Board, depth: int) -> int:
    """Skor terminal dari sudut pandang AI.

    Kedalaman ikut diperhitungkan agar AI memilih kemenangan tercepat
    dan menunda kekalahan selama mungkin.
    """
    winner = board.winner()
    if winner == AI:
        return 10 - depth
    if winner == HUMAN:
        return depth - 10
    return 0


def minimax(board: Board, depth: int, is_maximizing: bool, stats: SearchStats) -> int:
    """Minimax murni tanpa pruning."""
    stats.nodes += 1
    if board.is_game_over():
        return evaluate(board, depth)

    symbol = AI if is_maximizing else HUMAN
    best: float = -math.inf if is_maximizing else math.inf
    for move in board.available_moves():
        board.place(move, symbol)
        score = minimax(board, depth + 1, not is_maximizing, stats)
        board.undo(move)
        best = max(best, score) if is_maximizing else min(best, score)
    return int(best)


def alpha_beta(
    board: Board,
    depth: int,
    is_maximizing: bool,
    alpha: float,
    beta: float,
    stats: SearchStats,
) -> int:
    """Minimax dengan Alpha-Beta Pruning."""
    stats.nodes += 1
    if board.is_game_over():
        return evaluate(board, depth)

    symbol = AI if is_maximizing else HUMAN
    best: float = -math.inf if is_maximizing else math.inf
    for move in board.available_moves():
        board.place(move, symbol)
        score = alpha_beta(board, depth + 1, not is_maximizing, alpha, beta, stats)
        board.undo(move)
        if is_maximizing:
            best = max(best, score)
            alpha = max(alpha, best)
        else:
            best = min(best, score)
            beta = min(beta, best)
        if beta <= alpha:
            break  # cabang sisanya tidak mungkin memengaruhi hasil akhir
    return int(best)


def find_best_move(board: Board, algorithm: str, stats: SearchStats) -> int:
    """Memilih langkah terbaik untuk AI dengan algoritma yang dipilih."""
    best_score = -math.inf
    best_move = -1
    alpha = -math.inf

    for move in board.available_moves():
        board.place(move, AI)
        if algorithm == ALGORITHM_ALPHA_BETA:
            score = alpha_beta(board, 1, False, alpha, math.inf, stats)
        else:
            score = minimax(board, 1, False, stats)
        board.undo(move)

        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, best_score)

    return best_move


# ---------------------------------------------------------------------------
# Komponen antarmuka
# ---------------------------------------------------------------------------
def rounded_rectangle(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float,
    **options,
) -> int:
    """Menggambar persegi panjang bersudut membulat pada canvas."""
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **options)


def make_button(
    master: tk.Misc, text: str, command: Callable[[], None], primary: bool = False
) -> tk.Button:
    """Membuat tombol flat dengan efek hover."""
    base = Palette.ACCENT if primary else Palette.CELL
    hover = Palette.ACCENT_HOVER if primary else Palette.CELL_HOVER
    button = tk.Button(
        master,
        text=text,
        command=command,
        font=(FONT_FAMILY, 10, "bold"),
        bg=base,
        fg=Palette.TEXT,
        activebackground=hover,
        activeforeground=Palette.TEXT,
        relief="flat",
        borderwidth=0,
        highlightthickness=0,
        padx=14,
        pady=9,
        cursor="hand2",
    )
    button.bind("<Enter>", lambda _event: button.config(bg=hover))
    button.bind("<Leave>", lambda _event: button.config(bg=base))
    return button


def make_segmented_control(
    master: tk.Misc,
    options: list[tuple[str, str]],
    variable: tk.StringVar,
    command: Optional[Callable[[], None]] = None,
) -> tk.Frame:
    """Membuat pilihan bergaya segmented control dari Radiobutton."""
    frame = tk.Frame(master, bg=Palette.CARD)
    callback: Callable[[], None] = command if command is not None else lambda: None
    for label, value in options:
        tk.Radiobutton(
            frame,
            text=label,
            value=value,
            variable=variable,
            command=callback,
            indicatoron=False,
            bg=Palette.CELL,
            fg=Palette.TEXT,
            selectcolor=Palette.ACCENT,
            activebackground=Palette.CELL_HOVER,
            activeforeground=Palette.TEXT,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            font=(FONT_FAMILY, 10),
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(side="left", padx=(0, 2))
    return frame


class ScoreCard(tk.Frame):
    """Kartu kecil untuk menampilkan skor salah satu pihak."""

    def __init__(self, master: tk.Misc, caption: str, accent: str) -> None:
        super().__init__(master, bg=Palette.CARD, padx=10, pady=8)
        tk.Label(
            self,
            text=caption,
            font=(FONT_FAMILY, 9, "bold"),
            fg=Palette.MUTED,
            bg=Palette.CARD,
        ).pack()
        self.value_label = tk.Label(
            self,
            text="0",
            font=(FONT_FAMILY, 22, "bold"),
            fg=accent,
            bg=Palette.CARD,
        )
        self.value_label.pack()

    def set_value(self, value: int) -> None:
        self.value_label.config(text=str(value))


class BoardCanvas(tk.Canvas):
    """Papan permainan yang digambar di canvas, lengkap dengan animasi."""

    def __init__(self, master: tk.Misc, on_cell_click: Callable[[int], None]) -> None:
        size = 3 * CELL_SIZE + 4 * CELL_GAP
        super().__init__(
            master, width=size, height=size, bg=Palette.BG, highlightthickness=0
        )
        self.on_cell_click = on_cell_click
        self.interactive = False
        self.cells: list[str] = [EMPTY] * 9
        self.hover_index: Optional[int] = None
        self.cell_items = [self._create_cell(i) for i in range(9)]

        self.bind("<Button-1>", self._handle_click)
        self.bind("<Motion>", self._handle_motion)
        self.bind("<Leave>", lambda _event: self._set_hover(None))

    # -- geometri ---------------------------------------------------------
    @staticmethod
    def _cell_bounds(index: int) -> tuple[int, int, int, int]:
        row, col = divmod(index, 3)
        x1 = CELL_GAP + col * (CELL_SIZE + CELL_GAP)
        y1 = CELL_GAP + row * (CELL_SIZE + CELL_GAP)
        return x1, y1, x1 + CELL_SIZE, y1 + CELL_SIZE

    def _cell_center(self, index: int) -> tuple[float, float]:
        x1, y1, x2, y2 = self._cell_bounds(index)
        return (x1 + x2) / 2, (y1 + y2) / 2

    def _index_at(self, x: int, y: int) -> Optional[int]:
        for index in range(9):
            x1, y1, x2, y2 = self._cell_bounds(index)
            if x1 <= x <= x2 and y1 <= y <= y2:
                return index
        return None

    def _create_cell(self, index: int) -> int:
        return rounded_rectangle(
            self, *self._cell_bounds(index), CELL_RADIUS, fill=Palette.CELL, outline=""
        )

    # -- interaksi --------------------------------------------------------
    def _handle_click(self, event: tk.Event) -> None:
        if not self.interactive:
            return
        index = self._index_at(event.x, event.y)
        if index is not None:
            self.on_cell_click(index)

    def _handle_motion(self, event: tk.Event) -> None:
        self._set_hover(self._index_at(event.x, event.y))

    def _set_hover(self, index: Optional[int]) -> None:
        if index is not None and not (self.interactive and self.cells[index] == EMPTY):
            index = None
        if index == self.hover_index:
            return
        if self.hover_index is not None:
            self.itemconfig(self.cell_items[self.hover_index], fill=Palette.CELL)
        if index is not None:
            self.itemconfig(self.cell_items[index], fill=Palette.CELL_HOVER)
        self.hover_index = index
        self.config(cursor="hand2" if index is not None else "")

    def set_interactive(self, interactive: bool) -> None:
        self.interactive = interactive
        self._set_hover(None)

    # -- menggambar -------------------------------------------------------
    def reset(self) -> None:
        """Mengosongkan papan dan menghapus semua tanda."""
        self.delete("mark")
        self.delete("winline")
        self.cells = [EMPTY] * 9
        for item in self.cell_items:
            self.itemconfig(item, fill=Palette.CELL)
        self.hover_index = None
        self.config(cursor="")

    def place_mark(self, index: int, symbol: str) -> None:
        """Menempatkan tanda pada kotak dengan animasi singkat."""
        self.cells[index] = symbol
        self._set_hover(None)
        self.itemconfig(self.cell_items[index], fill=Palette.CELL)
        self._animate_mark(index, symbol, 0)

    def _animate_mark(self, index: int, symbol: str, step: int) -> None:
        if self.cells[index] != symbol:  # papan sudah di-reset
            return
        self.delete(f"mark{index}")
        self._draw_mark(index, symbol, ANIMATION_SCALES[step])
        if step + 1 < len(ANIMATION_SCALES):
            self.after(ANIMATION_STEP_MS, self._animate_mark, index, symbol, step + 1)

    def _draw_mark(self, index: int, symbol: str, scale: float) -> None:
        cx, cy = self._cell_center(index)
        half = CELL_SIZE * 0.26 * scale
        tags = ("mark", f"mark{index}")
        if symbol == HUMAN:
            options = {
                "fill": Palette.X_COLOR,
                "width": MARK_WIDTH,
                "capstyle": "round",
                "tags": tags,
            }
            self.create_line(cx - half, cy - half, cx + half, cy + half, **options)
            self.create_line(cx - half, cy + half, cx + half, cy - half, **options)
        else:
            self.create_oval(
                cx - half,
                cy - half,
                cx + half,
                cy + half,
                outline=Palette.O_COLOR,
                width=MARK_WIDTH,
                tags=tags,
            )

    def show_winner(self, line: tuple[int, int, int]) -> None:
        """Menandai garis kemenangan setelah animasi tanda selesai."""
        delay = len(ANIMATION_SCALES) * ANIMATION_STEP_MS + 40
        self.after(delay, self._draw_winner, line)

    def _draw_winner(self, line: tuple[int, int, int]) -> None:
        if any(self.cells[i] == EMPTY for i in line):  # papan sudah di-reset
            return
        for index in line:
            self.itemconfig(self.cell_items[index], fill=Palette.WIN_TINT)
        x1, y1 = self._cell_center(line[0])
        x2, y2 = self._cell_center(line[2])
        self.create_line(
            x1, y1, x2, y2,
            fill=Palette.SUCCESS,
            width=8,
            capstyle="round",
            tags="winline",
        )


# ---------------------------------------------------------------------------
# Aplikasi utama
# ---------------------------------------------------------------------------
class TicTacToeApp(tk.Tk):
    """Jendela utama permainan Tic Tac Toe."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Tic Tac Toe - AI Minimax")
        self.configure(bg=Palette.BG, padx=24, pady=20)
        self.resizable(False, False)

        self.board = Board()
        self.game_id = 0  # penanda game aktif agar callback lama diabaikan
        self.input_locked = True
        self.scores = {HUMAN: 0, AI: 0, DRAW: 0}

        self.algorithm = tk.StringVar(value=ALGORITHM_ALPHA_BETA)
        self.first_player = tk.StringVar(value=HUMAN)
        self.status_text = tk.StringVar()
        self.search_text = {key: tk.StringVar(value="-") for key in ALGORITHM_LABELS}

        self._build_widgets()
        self.new_game()

    def _build_widgets(self) -> None:
        tk.Label(
            self,
            text="Tic Tac Toe",
            font=(FONT_FAMILY, 24, "bold"),
            fg=Palette.TEXT,
            bg=Palette.BG,
        ).grid(row=0, column=0, columnspan=2)
        tk.Label(
            self,
            text=f"Pemain ({HUMAN})  melawan  AI ({AI})",
            font=(FONT_FAMILY, 10),
            fg=Palette.MUTED,
            bg=Palette.BG,
        ).grid(row=1, column=0, columnspan=2, pady=(0, 14))

        left = tk.Frame(self, bg=Palette.BG)
        left.grid(row=2, column=0, sticky="n")
        right = tk.Frame(self, bg=Palette.BG)
        right.grid(row=2, column=1, sticky="nsew", padx=(24, 0))
        self.columnconfigure(1, minsize=330)
        self.rowconfigure(2, weight=1)

        self._build_board_panel(left)
        self._build_side_panel(right)

    def _build_board_panel(self, panel: tk.Frame) -> None:
        self.status_label = tk.Label(
            panel,
            textvariable=self.status_text,
            font=(FONT_FAMILY, 12, "bold"),
            fg=Palette.TEXT,
            bg=Palette.CARD,
            pady=10,
        )
        self.status_label.pack(fill="x", pady=(0, 10))
        self.board_view = BoardCanvas(panel, on_cell_click=self.on_cell_click)
        self.board_view.pack()

    def _build_side_panel(self, panel: tk.Frame) -> None:
        buttons = tk.Frame(panel, bg=Palette.BG)
        buttons.pack(side="bottom", fill="x")
        buttons.columnconfigure(0, weight=3, uniform="buttons")
        buttons.columnconfigure(1, weight=2, uniform="buttons")
        make_button(buttons, "Permainan Baru", self.new_game, primary=True).grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )
        make_button(buttons, "Reset Skor", self.reset_scores).grid(
            row=0, column=1, sticky="ew"
        )

        score_row = tk.Frame(panel, bg=Palette.BG)
        score_row.pack(fill="x")
        self.score_cards = {
            HUMAN: ScoreCard(score_row, f"ANDA ({HUMAN})", Palette.X_COLOR),
            DRAW: ScoreCard(score_row, "SERI", Palette.WARNING),
            AI: ScoreCard(score_row, f"AI ({AI})", Palette.O_COLOR),
        }
        for column, card in enumerate(self.score_cards.values()):
            score_row.columnconfigure(column, weight=1, uniform="score")
            card.grid(
                row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0)
            )

        info = tk.Frame(panel, bg=Palette.CARD, padx=14, pady=10)
        info.pack(fill="x", pady=(12, 0))
        tk.Label(
            info,
            text="PENCARIAN AI - LANGKAH TERAKHIR",
            font=(FONT_FAMILY, 8, "bold"),
            fg=Palette.MUTED,
            bg=Palette.CARD,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        for row, (key, label) in enumerate(ALGORITHM_LABELS.items(), start=1):
            tk.Label(
                info,
                text=label,
                font=(FONT_FAMILY, 10, "bold"),
                fg=Palette.TEXT,
                bg=Palette.CARD,
                width=11,
                anchor="w",
            ).grid(row=row, column=0, sticky="w")
            tk.Label(
                info,
                textvariable=self.search_text[key],
                font=(FONT_FAMILY, 10),
                fg=Palette.MUTED,
                bg=Palette.CARD,
                anchor="w",
            ).grid(row=row, column=1, sticky="w")

        settings = tk.Frame(panel, bg=Palette.CARD, padx=14, pady=10)
        settings.pack(fill="x", pady=(12, 0))
        self._add_setting_row(
            settings,
            "Algoritma AI",
            [
                (ALGORITHM_LABELS[ALGORITHM_MINIMAX], ALGORITHM_MINIMAX),
                ("Minimax + Alpha-Beta", ALGORITHM_ALPHA_BETA),
            ],
            self.algorithm,
        )
        self._add_setting_row(
            settings,
            "Jalan duluan",
            [(f"Pemain ({HUMAN})", HUMAN), (f"AI ({AI})", AI)],
            self.first_player,
            command=self.new_game,
        )

    @staticmethod
    def _add_setting_row(
        master: tk.Misc,
        caption: str,
        options: list[tuple[str, str]],
        variable: tk.StringVar,
        command: Optional[Callable[[], None]] = None,
    ) -> None:
        tk.Label(
            master,
            text=caption,
            font=(FONT_FAMILY, 9, "bold"),
            fg=Palette.MUTED,
            bg=Palette.CARD,
            anchor="w",
        ).pack(fill="x")
        make_segmented_control(master, options, variable, command).pack(
            anchor="w", pady=(2, 8)
        )

    # -- status dan skor --------------------------------------------------
    def set_status(self, text: str, tone: str = "info") -> None:
        self.status_text.set(text)
        self.status_label.config(fg=TONE_COLORS[tone])

    def update_scores(self) -> None:
        for key, card in self.score_cards.items():
            card.set_value(self.scores[key])

    def reset_scores(self) -> None:
        self.scores = {HUMAN: 0, AI: 0, DRAW: 0}
        self.update_scores()
        self.new_game()

    def _set_locked(self, locked: bool) -> None:
        self.input_locked = locked
        self.board_view.set_interactive(not locked)

    # -- alur permainan ---------------------------------------------------
    def new_game(self) -> None:
        """Mengatur ulang papan dan memulai permainan baru."""
        self.game_id += 1
        self.board = Board()
        self.board_view.reset()

        if self.first_player.get() == AI:
            self.start_ai_turn()
        else:
            self._set_locked(False)
            self.set_status(f"Giliran Anda ({HUMAN})")

    def on_cell_click(self, index: int) -> None:
        if self.input_locked:
            return
        try:
            self.board.place(index, HUMAN)
        except ValueError as error:
            self.set_status(f"{error} Pilih kotak lain.", "warning")
            return

        self.board_view.place_mark(index, HUMAN)
        if self.finish_if_over():
            return
        self.start_ai_turn()

    def start_ai_turn(self) -> None:
        self._set_locked(True)
        self.set_status("AI sedang berpikir...", "thinking")
        self.after(AI_DELAY_MS, self.ai_turn, self.game_id)

    def ai_turn(self, game_id: int) -> None:
        if game_id != self.game_id:  # game sudah diganti saat AI "berpikir"
            return

        algorithm = self.algorithm.get()
        stats = SearchStats()
        started = time.perf_counter()
        move = find_best_move(self.board, algorithm, stats)
        elapsed_ms = (time.perf_counter() - started) * 1000

        self.board.place(move, AI)
        self.board_view.place_mark(move, AI)
        self.search_text[algorithm].set(
            f"{stats.nodes:,} simpul  |  {elapsed_ms:.1f} ms"
        )

        if self.finish_if_over():
            return
        self._set_locked(False)
        self.set_status(f"Giliran Anda ({HUMAN})")

    def finish_if_over(self) -> bool:
        """Memeriksa akhir permainan; menampilkan hasil dan opsi main lagi."""
        if not self.board.is_game_over():
            return False

        self._set_locked(True)
        line = self.board.winning_line()
        if line:
            self.board_view.show_winner(line)

        winner = self.board.winner()
        if winner == HUMAN:
            result, tone, key = "Selamat, Anda menang!", "win", HUMAN
        elif winner == AI:
            result, tone, key = "AI menang.", "lose", AI
        else:
            result, tone, key = "Permainan seri (draw).", "draw", DRAW

        self.scores[key] += 1
        self.update_scores()
        self.set_status(result, tone)
        self.after(RESULT_DIALOG_DELAY_MS, self.show_result_dialog, self.game_id, result)
        return True

    def show_result_dialog(self, game_id: int, result: str) -> None:
        if game_id != self.game_id:
            return
        if messagebox.askyesno("Permainan Selesai", f"{result}\n\nMain lagi?"):
            self.new_game()


def main() -> None:
    app = TicTacToeApp()
    app.mainloop()


if __name__ == "__main__":
    main()