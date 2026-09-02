"""
Chess Game - Main entry point with Tkinter GUI.
Player (white) vs AI (black) with drag-and-drop piece movement.
"""

import tkinter as tk
from tkinter import messagebox, font as tkfont
from Board import (
    ChessBoard, is_empty, is_white, is_black, piece_color, PIECE_SYMBOLS, PIECE_NAMES,
    W_PAWN, W_ROOK, W_KNIGHT, W_BISHOP, W_QUEEN, W_KING,
    B_PAWN, B_ROOK, B_KNIGHT, B_BISHOP, B_QUEEN, B_KING,
)
from AI import ChessAI

# ─── Colors ──────────────────────────────────────────────────────
LIGHT_SQUARE = "#F0D9B5"
DARK_SQUARE = "#B58863"
HIGHLIGHT_COLOR = "#FFFF00"       # Selected square highlight
LEGAL_MOVE_DOT = "#88C057"        # Legal move indicator
LAST_MOVE_COLOR = "#CDD26A"       # Last move highlight
CHECK_COLOR = "#FF0000"           # Check highlight
BG_COLOR = "#312E2B"              # App background
TEXT_COLOR = "#FFFFFF"             # Text color

# ─── Unicode piece mapping ──────────────────────────────────────
UNICODE_PIECES = {
    W_PAWN:   "♙", W_ROOK:   "♖", W_KNIGHT: "♘",
    W_BISHOP: "♗", W_QUEEN:  "♕", W_KING:   "♔",
    B_PAWN:   "♟", B_ROOK:   "♜", B_KNIGHT: "♞",
    B_BISHOP: "♝", B_QUEEN:  "♛", B_KING:   "♚",
}

# Piece images using colored text for better visibility on both square colors
PIECE_DISPLAY_WHITE = {
    W_PAWN:   ("♟", "#FFFFFF"), W_ROOK:   ("♜", "#FFFFFF"), W_KNIGHT: ("♞", "#FFFFFF"),
    W_BISHOP: ("♝", "#FFFFFF"), W_QUEEN:  ("♛", "#FFFFFF"), W_KING:   ("♚", "#FFFFFF"),
}
PIECE_DISPLAY_BLACK = {
    B_PAWN:   ("♟", "#000000"), B_ROOK:   ("♜", "#000000"), B_KNIGHT: ("♞", "#000000"),
    B_BISHOP: ("♝", "#000000"), B_QUEEN:  ("♛", "#000000"), B_KING:   ("♚", "#000000"),
}


class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess - You (White) vs AI (Black)")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)

        # Game state
        self.board = ChessBoard()
        self.ai = ChessAI(color="black", depth=4, time_limit=5.0)
        self.selected = None           # (row, col) of selected square
        self.legal_moves_for_selected = []
        self.drag_data = {"piece_id": None, "from_row": None, "from_col": None}
        self.last_move = None          # (from, to)
        self.game_over = False
        self.player_color = "white"

        # Square size
        self.square_size = 80
        self.board_size = self.square_size * 8

        self._build_ui()

    # ─── UI Setup ───────────────────────────────────────────────

    def _build_ui(self):
        # Top frame for game info
        self.info_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.info_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.status_label = tk.Label(
            self.info_frame, text="Your turn (White)", font=("Helvetica", 14, "bold"),
            bg=BG_COLOR, fg=TEXT_COLOR
        )
        self.status_label.pack(side=tk.LEFT)

        self.turn_indicator = tk.Label(
            self.info_frame, text="●", font=("Helvetica", 20),
            bg=BG_COLOR, fg="#FFFFFF"
        )
        self.turn_indicator.pack(side=tk.RIGHT)

        # Board frame with rank/file labels
        self.board_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.board_frame.pack(padx=10, pady=5)

        # File labels (a-h) at top
        self.file_frame = tk.Frame(self.board_frame, bg=BG_COLOR)
        self.file_frame.pack(side=tk.TOP)
        file_canvas = tk.Canvas(self.file_frame, width=self.board_size, height=20,
                                bg=BG_COLOR, highlightthickness=0)
        file_canvas.pack()
        for c in range(8):
            letter = chr(ord('a') + c)
            file_canvas.create_text(
                c * self.square_size + self.square_size // 2, 10,
                text=letter, fill=TEXT_COLOR, font=("Helvetica", 11, "bold")
            )

        # Main board area with rank labels
        self.board_container = tk.Frame(self.board_frame, bg=BG_COLOR)
        self.board_container.pack(side=tk.TOP)

        # Rank labels on left
        self.rank_frame = tk.Frame(self.board_container, bg=BG_COLOR)
        self.rank_frame.pack(side=tk.LEFT)
        for r in range(8):
            lbl = tk.Label(
                self.rank_frame, text=str(8 - r), font=("Helvetica", 11, "bold"),
                bg=BG_COLOR, fg=TEXT_COLOR, width=2, height=1
            )
            lbl.pack(side=tk.TOP, ipady=self.square_size // 2 - 8)

        # Canvas
        self.canvas = tk.Canvas(
            self.board_container, width=self.board_size, height=self.board_size,
            bg=LIGHT_SQUARE, highlightthickness=2, highlightbackground="#312E2B"
        )
        self.canvas.pack(side=tk.LEFT)

        # Rank labels on right
        self.rank_frame_r = tk.Frame(self.board_container, bg=BG_COLOR)
        self.rank_frame_r.pack(side=tk.LEFT)
        for r in range(8):
            lbl = tk.Label(
                self.rank_frame_r, text=str(8 - r), font=("Helvetica", 11, "bold"),
                bg=BG_COLOR, fg=TEXT_COLOR, width=2, height=1
            )
            lbl.pack(side=tk.TOP, ipady=self.square_size // 2 - 8)

        # File labels (a-h) at bottom
        self.file_frame_b = tk.Frame(self.board_frame, bg=BG_COLOR)
        self.file_frame_b.pack(side=tk.TOP)
        file_canvas_b = tk.Canvas(self.file_frame_b, width=self.board_size, height=20,
                                  bg=BG_COLOR, highlightthickness=0)
        file_canvas_b.pack()
        for c in range(8):
            letter = chr(ord('a') + c)
            file_canvas_b.create_text(
                c * self.square_size + self.square_size // 2, 10,
                text=letter, fill=TEXT_COLOR, font=("Helvetica", 11, "bold")
            )

        # Bottom controls
        self.control_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.control_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        # Undo button
        self.undo_btn = tk.Button(
            self.control_frame, text="↩ Undo Move", font=("Helvetica", 11),
            bg="#4a4a4a", fg=TEXT_COLOR, activebackground="#5a5a5a",
            relief=tk.FLAT, padx=10, pady=5,
            command=self._undo_move
        )
        self.undo_btn.pack(side=tk.LEFT, padx=(0, 10))

        # New Game button
        self.new_game_btn = tk.Button(
            self.control_frame, text="🔄 New Game", font=("Helvetica", 11),
            bg="#4a4a4a", fg=TEXT_COLOR, activebackground="#5a5a5a",
            relief=tk.FLAT, padx=10, pady=5,
            command=self._new_game
        )
        self.new_game_btn.pack(side=tk.LEFT)

        # Move list
        self.move_list_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.move_list_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.move_label = tk.Label(
            self.move_list_frame, text="Moves:", font=("Helvetica", 11, "bold"),
            bg=BG_COLOR, fg=TEXT_COLOR, anchor=tk.W
        )
        self.move_label.pack(fill=tk.X)

        self.move_text = tk.Text(
            self.move_list_frame, height=4, font=("Consolas", 10),
            bg="#1a1a1a", fg=TEXT_COLOR, relief=tk.FLAT,
            state=tk.DISABLED, wrap=tk.WORD
        )
        self.move_text.pack(fill=tk.X, pady=(3, 0))

        # Bind mouse events
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        # Draw initial board
        self._draw_board()

    # ─── Drawing ────────────────────────────────────────────────

    def _draw_board(self):
        """Redraw the entire board."""
        self.canvas.delete("all")

        for r in range(8):
            for c in range(8):
                x1 = c * self.square_size
                y1 = r * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                # Base square color
                is_light = (r + c) % 2 == 0
                color = LIGHT_SQUARE if is_light else DARK_SQUARE

                # Highlight last move
                if self.last_move:
                    fr, fc = self.last_move[0]
                    tr, tc = self.last_move[1]
                    if (r, c) == (fr, fc) or (r, c) == (tr, tc):
                        color = LAST_MOVE_COLOR

                # Highlight selected square
                if self.selected == (r, c):
                    color = HIGHLIGHT_COLOR

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="", tags="square")

                # Draw piece
                piece = self.board.board[r][c]
                if not is_empty(piece):
                    self._draw_piece(r, c, piece, on_square=color)

        # Draw legal move indicators
        for (mr, mc, flags) in self.legal_moves_for_selected:
            cx = mc * self.square_size + self.square_size // 2
            cy = mr * self.square_size + self.square_size // 2
            piece_on_target = self.board.board[mr][mc]
            if not is_empty(piece_on_target) or flags.get("en_passant"):
                # Draw circle outline for captures
                rad = self.square_size // 2 - 5
                self.canvas.create_oval(
                    cx - rad, cy - rad, cx + rad, cy + rad,
                    outline=LEGAL_MOVE_DOT, width=4, tags="legal_move"
                )
            else:
                # Draw small dot for empty squares
                rad = 10
                self.canvas.create_oval(
                    cx - rad, cy - rad, cx + rad, cy + rad,
                    fill=LEGAL_MOVE_DOT, outline="", tags="legal_move"
                )

        # Highlight king in check
        if self.board.is_in_check(self.board.turn):
            king_pos = self.board.find_king(self.board.turn)
            if king_pos:
                kr, kc = king_pos
                x1 = kc * self.square_size
                y1 = kr * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="", outline=CHECK_COLOR, width=4, tags="check")

    def _draw_piece(self, row, col, piece, on_square=LIGHT_SQUARE):
        """Draw a single piece on the canvas."""
        cx = col * self.square_size + self.square_size // 2
        cy = row * self.square_size + self.square_size // 2

        # Determine display properties
        pt = abs(piece)
        color_white = is_white(piece)

        # Choose piece symbol and colors for contrast
        if color_white:
            symbol = UNICODE_PIECES[piece]
            # White pieces: dark outline for visibility on light squares, light fill
            fill = "#FFFFFF"
            outline = "#000000"
        else:
            symbol = UNICODE_PIECES[piece]
            # Black pieces: very dark fill
            fill = "#000000"
            outline = "#333333"

        font_size = 52

        # Draw shadow for depth effect
        self.canvas.create_text(
            cx + 2, cy + 2, text=symbol,
            font=("Segoe UI Symbol", font_size), fill="#777777",
            anchor=tk.CENTER, tags="piece_shadow"
        )

        # Draw the piece
        self.canvas.create_text(
            cx, cy, text=symbol,
            font=("Segoe UI Symbol", font_size), fill=fill,
            anchor=tk.CENTER, tags="piece"
        )

    # ─── Interaction ────────────────────────────────────────────

    def _on_click(self, event):
        """Handle mouse click - select piece or make move."""
        if self.game_over:
            return
        if self.board.turn != self.player_color:
            return

        col = event.x // self.square_size
        row = event.y // self.square_size

        if not (0 <= row < 8 and 0 <= col < 8):
            return

        piece = self.board.board[row][col]

        # If we have a piece selected and click on a legal move target
        if self.selected is not None:
            move = None
            for (mr, mc, flags) in self.legal_moves_for_selected:
                if (mr, mc) == (row, col):
                    move = (row, col, flags)
                    break

            if move:
                # Handle promotion: auto-promote to queen (can add UI later)
                tr, tc, flags = move
                self._make_player_move(
                    self.selected[0], self.selected[1], tr, tc, flags
                )
                return
            else:
                # Deselect or select new piece
                self.selected = None
                self.legal_moves_for_selected = []

        # Select a new piece
        if not is_empty(piece) and piece_color(piece) == self.player_color:
            self.selected = (row, col)
            self.legal_moves_for_selected = self.board.get_legal_moves(row, col)
            self._draw_board()
            # Start drag
            self.drag_data["from_row"] = row
            self.drag_data["from_col"] = col

    def _on_drag(self, event):
        """Handle dragging a piece."""
        if self.selected is None:
            return

        # Move the piece image with the cursor
        col = event.x // self.square_size
        row = event.y // self.square_size

    def _on_release(self, event):
        """Handle release - complete move if valid."""
        if self.selected is None:
            return

        col = event.x // self.square_size
        row = event.y // self.square_size

        if not (0 <= row < 8 and 0 <= col < 8):
            return

        # Check if this is a legal move target
        if (row, col) != self.selected:
            move = None
            for (mr, mc, flags) in self.legal_moves_for_selected:
                if (mr, mc) == (row, col):
                    move = (row, col, flags)
                    break

            if move:
                tr, tc, flags = move
                self._make_player_move(
                    self.selected[0], self.selected[1], tr, tc, flags
                )
                return

    def _make_player_move(self, fr, fc, tr, tc, flags):
        """Execute a player move, then trigger AI."""
        # Handle promotion - auto queen for simplicity
        piece = self.board.board[fr][fc]
        if abs(piece) == 1 and (tr == 0 or tr == 7):
            from Board import W_QUEEN, B_QUEEN
            flags["promotion"] = W_QUEEN if piece_color(piece) == "white" else B_QUEEN

        self.board.make_move(fr, fc, tr, tc, flags)
        self.last_move = ((fr, fc), (tr, tc))
        self.selected = None
        self.legal_moves_for_selected = []

        self._update_move_list(fr, fc, tr, tc, flags)
        self._draw_board()
        self._update_status()

        if not self.game_over:
            self.root.after(100, self._ai_move)

    def _ai_move(self):
        """Let the AI make a move."""
        if self.game_over:
            return

        self.status_label.config(text="AI is thinking...")
        self.turn_indicator.config(fg="#000000")
        self.root.update()

        move = self.ai.get_best_move(self.board)

        if move is None:
            self._check_game_over()
            return

        fr, fc, tr, tc, flags = move
        self.board.make_move(fr, fc, tr, tc, flags)
        self.last_move = ((fr, fc), (tr, tc))

        self._update_move_list(fr, fc, tr, tc, flags)
        self._draw_board()
        self._update_status()

    def _update_move_list(self, fr, fc, tr, tc, flags):
        """Add a move to the move list display."""
        from Board import square_to_string

        move_str = square_to_string(fr, fc) + square_to_string(tr, tc)
        if "promotion" in flags:
            move_str += "=" + PIECE_NAMES[flags["promotion"]]

        # Add check/checkmate symbol
        if self.board.is_in_check(self.board.turn):
            if len(self.board.get_all_legal_moves(self.board.turn)) == 0:
                move_str += "#"
            else:
                move_str += "+"

        self.move_text.config(state=tk.NORMAL)
        self.move_text.insert(tk.END, move_str + "  ")
        self.move_text.see(tk.END)
        self.move_text.config(state=tk.DISABLED)

    def _update_status(self):
        """Update the status label."""
        self._check_game_over()
        if self.game_over:
            return

        turn = self.board.turn
        if turn == self.player_color:
            self.status_label.config(text="Your turn (White)")
            self.turn_indicator.config(fg="#FFFFFF")
        else:
            self.status_label.config(text="AI is thinking (Black)...")
            self.turn_indicator.config(fg="#000000")

    def _check_game_over(self):
        """Check if the game has ended."""
        if self.board.is_checkmate():
            winner = "Black" if self.board.turn == "white" else "White"
            self.game_over = True
            self.status_label.config(text=f"Checkmate! {winner} wins!")
            self.turn_indicator.config(fg="#FF0000")
            messagebox.showinfo("Game Over", f"Checkmate!\n{winner} wins!")
        elif self.board.is_stalemate():
            self.game_over = True
            self.status_label.config(text="Stalemate! Draw!")
            self.turn_indicator.config(fg="#888888")
            messagebox.showinfo("Game Over", "Stalemate!\nThe game is a draw.")
        elif self.board.is_draw():
            self.game_over = True
            self.status_label.config(text="Draw!")
            self.turn_indicator.config(fg="#888888")
            messagebox.showinfo("Game Over", "Draw!")

    def _undo_move(self):
        """Undo both the last AI move and the last player move."""
        if self.game_over or len(self.board.move_history) < 2:
            return

        # Undo AI move
        self.board.undo_last_move()
        # Undo player move
        self.board.undo_last_move()

        self.last_move = None
        if self.board.move_history:
            last = self.board.move_history[-1]
            self.last_move = (last["from"], last["to"])

        self.selected = None
        self.legal_moves_for_selected = []

        # Rebuild move list text
        self.move_text.config(state=tk.NORMAL)
        self.move_text.delete("1.0", tk.END)
        self.move_text.config(state=tk.DISABLED)
        for info in self.board.move_history:
            fr, fc = info["from"]
            tr, tc = info["to"]
            from Board import square_to_string
            move_str = square_to_string(fr, fc) + square_to_string(tr, tc)
            if "promotion" in info["flags"]:
                move_str += "=" + PIECE_NAMES[info["flags"]["promotion"]]
            self.move_text.config(state=tk.NORMAL)
            self.move_text.insert(tk.END, move_str + "  ")
            self.move_text.config(state=tk.DISABLED)

        self._draw_board()
        self._update_status()

    def _new_game(self):
        """Reset the game."""
        self.board = ChessBoard()
        self.selected = None
        self.legal_moves_for_selected = []
        self.last_move = None
        self.game_over = False
        self.move_text.config(state=tk.NORMAL)
        self.move_text.delete("1.0", tk.END)
        self.move_text.config(state=tk.DISABLED)
        self._draw_board()
        self._update_status()


def main():
    root = tk.Tk()
    root.configure(bg=BG_COLOR)
    app = ChessGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
