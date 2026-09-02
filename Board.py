"""
Chess Game Engine - Board representation, move generation, and validation.
"""

import copy

# Piece constants
EMPTY = 0
W_PAWN, W_ROOK, W_KNIGHT, W_BISHOP, W_QUEEN, W_KING = 1, 2, 3, 4, 5, 6
B_PAWN, B_ROOK, B_KNIGHT, B_BISHOP, B_QUEEN, B_KING = -1, -2, -3, -4, -5, -6

# Piece symbols for display
PIECE_SYMBOLS = {
    W_PAWN: "♙", W_ROOK: "♖", W_KNIGHT: "♘", W_BISHOP: "♗", W_QUEEN: "♕", W_KING: "♔",
    B_PAWN: "♟", B_ROOK: "♜", B_KNIGHT: "♞", B_BISHOP: "♝", B_QUEEN: "♛", B_KING: "♚",
}

# Text labels
PIECE_NAMES = {
    W_PAWN: "wP", W_ROOK: "wR", W_KNIGHT: "wN", W_BISHOP: "wB", W_QUEEN: "wQ", W_KING: "wK",
    B_PAWN: "bP", B_ROOK: "bR", B_KNIGHT: "bN", B_BISHOP: "bB", B_QUEEN: "bQ", B_KING: "bK",
}

def is_white(piece):
    return piece > 0

def is_black(piece):
    return piece < 0

def is_empty(piece):
    return piece == 0

def piece_color(piece):
    if piece > 0:
        return "white"
    elif piece < 0:
        return "black"
    return None

def opponent(color):
    return "black" if color == "white" else "white"


class ChessBoard:
    def __init__(self):
        self.board = self._initial_board()
        self.turn = "white"
        self.castling_rights = {
            "white": {"king": True, "queen": True},
            "black": {"king": True, "queen": True},
        }
        self.en_passant_target = None  # (row, col) of the square behind the pawn that can be captured en passant
        self.move_history = []
        self.halfmove_clock = 0
        self.fullmove_number = 1

    def _initial_board(self):
        """Set up the standard chess starting position."""
        board = [[EMPTY] * 8 for _ in range(8)]
        # Black pieces (row 0 = rank 8)
        board[0] = [B_ROOK, B_KNIGHT, B_BISHOP, B_QUEEN, B_KING, B_BISHOP, B_KNIGHT, B_ROOK]
        board[1] = [B_PAWN] * 8
        # White pieces (row 7 = rank 1)
        board[7] = [W_ROOK, W_KNIGHT, W_BISHOP, W_QUEEN, W_KING, W_BISHOP, W_KNIGHT, W_ROOK]
        board[6] = [W_PAWN] * 8
        return board

    def copy(self):
        """Create a deep copy of the board for AI search."""
        new = ChessBoard.__new__(ChessBoard)
        new.board = [row[:] for row in self.board]
        new.turn = self.turn
        new.castling_rights = {
            "white": dict(self.castling_rights["white"]),
            "black": dict(self.castling_rights["black"]),
        }
        new.en_passant_target = self.en_passant_target
        new.halfmove_clock = self.halfmove_clock
        new.fullmove_number = self.fullmove_number
        new.move_history = []
        return new

    def get_piece(self, row, col):
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None

    def set_piece(self, row, col, piece):
        self.board[row][col] = piece

    def find_king(self, color):
        king = W_KING if color == "white" else B_KING
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == king:
                    return (r, c)
        return None

    def is_in_bounds(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    # ---------- Raw move generation (no check filtering) ----------

    def _raw_pseudo_legal_moves(self, row, col):
        """Generate pseudo-legal moves for a piece at (row, col). Doesn't check for self-check."""
        piece = self.board[row][col]
        if is_empty(piece):
            return []

        moves = []
        color = piece_color(piece)
        piece_type = abs(piece)

        if piece_type == 1:  # Pawn
            moves = self._pawn_moves(row, col, color)
        elif piece_type == 2:  # Rook
            moves = self._sliding_moves(row, col, color, [(0,1),(0,-1),(1,0),(-1,0)])
        elif piece_type == 3:  # Knight
            moves = self._knight_moves(row, col, color)
        elif piece_type == 4:  # Bishop
            moves = self._sliding_moves(row, col, color, [(1,1),(1,-1),(-1,1),(-1,-1)])
        elif piece_type == 5:  # Queen
            moves = self._sliding_moves(row, col, color,
                [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)])
        elif piece_type == 6:  # King
            moves = self._king_moves(row, col, color)

        return moves

    def _pawn_moves(self, row, col, color):
        moves = []
        direction = -1 if color == "white" else 1
        start_row = 6 if color == "white" else 1
        prom_row = 0 if color == "white" else 7

        # Forward one
        nr = row + direction
        if self.is_in_bounds(nr, col) and is_empty(self.board[nr][col]):
            if nr == prom_row:
                # Promotion
                for promo in [W_QUEEN, W_ROOK, W_BISHOP, W_KNIGHT] if color == "white" else [B_QUEEN, B_ROOK, B_BISHOP, B_KNIGHT]:
                    moves.append((nr, col, {"promotion": promo}))
            else:
                moves.append((nr, col, {}))

            # Forward two from start
            if row == start_row:
                nr2 = row + 2 * direction
                if self.is_in_bounds(nr2, col) and is_empty(self.board[nr2][col]):
                    moves.append((nr2, col, {"double_pawn_push": True}))

        # Captures
        for dc in [-1, 1]:
            nc = col + dc
            nr = row + direction
            if self.is_in_bounds(nr, nc):
                target = self.board[nr][nc]
                if not is_empty(target) and piece_color(target) != color:
                    if nr == prom_row:
                        for promo in [W_QUEEN, W_ROOK, W_BISHOP, W_KNIGHT] if color == "white" else [B_QUEEN, B_ROOK, B_BISHOP, B_KNIGHT]:
                            moves.append((nr, nc, {"promotion": promo}))
                    else:
                        moves.append((nr, nc, {}))

                # En passant
                if self.en_passant_target == (nr, nc):
                    moves.append((nr, nc, {"en_passant": True}))

        return moves

    def _sliding_moves(self, row, col, color, directions):
        moves = []
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while self.is_in_bounds(r, c):
                target = self.board[r][c]
                if is_empty(target):
                    moves.append((r, c, {}))
                else:
                    if piece_color(target) != color:
                        moves.append((r, c, {}))
                    break
                r += dr
                c += dc
        return moves

    def _knight_moves(self, row, col, color):
        moves = []
        offsets = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
        for dr, dc in offsets:
            r, c = row + dr, col + dc
            if self.is_in_bounds(r, c):
                target = self.board[r][c]
                if is_empty(target) or piece_color(target) != color:
                    moves.append((r, c, {}))
        return moves

    def _king_moves(self, row, col, color):
        moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if self.is_in_bounds(r, c):
                    target = self.board[r][c]
                    if is_empty(target) or piece_color(target) != color:
                        moves.append((r, c, {}))

        # Castling
        if color == "white" and row == 7 and col == 4:
            # Kingside
            if self.castling_rights["white"]["king"]:
                if (is_empty(self.board[7][5]) and is_empty(self.board[7][6])
                        and self.board[7][7] == W_ROOK
                        and not self._is_square_attacked(7, 4, "black")
                        and not self._is_square_attacked(7, 5, "black")
                        and not self._is_square_attacked(7, 6, "black")):
                    moves.append((7, 6, {"castle": "king"}))
            # Queenside
            if self.castling_rights["white"]["queen"]:
                if (is_empty(self.board[7][3]) and is_empty(self.board[7][2]) and is_empty(self.board[7][1])
                        and self.board[7][0] == W_ROOK
                        and not self._is_square_attacked(7, 4, "black")
                        and not self._is_square_attacked(7, 3, "black")
                        and not self._is_square_attacked(7, 2, "black")):
                    moves.append((7, 2, {"castle": "queen"}))

        elif color == "black" and row == 0 and col == 4:
            # Kingside
            if self.castling_rights["black"]["king"]:
                if (is_empty(self.board[0][5]) and is_empty(self.board[0][6])
                        and self.board[0][7] == B_ROOK
                        and not self._is_square_attacked(0, 4, "white")
                        and not self._is_square_attacked(0, 5, "white")
                        and not self._is_square_attacked(0, 6, "white")):
                    moves.append((0, 6, {"castle": "king"}))
            # Queenside
            if self.castling_rights["black"]["queen"]:
                if (is_empty(self.board[0][3]) and is_empty(self.board[0][2]) and is_empty(self.board[0][1])
                        and self.board[0][0] == B_ROOK
                        and not self._is_square_attacked(0, 4, "white")
                        and not self._is_square_attacked(0, 3, "white")
                        and not self._is_square_attacked(0, 2, "white")):
                    moves.append((0, 2, {"castle": "queen"}))

        return moves

    # ---------- Attack detection ----------

    def _is_square_attacked(self, row, col, by_color):
        """Check if (row, col) is attacked by any piece of 'by_color'."""
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if is_empty(piece) or piece_color(piece) != by_color:
                    continue
                if self._attacks(r, c, row, col):
                    return True
        return False

    def _attacks(self, from_row, from_col, to_row, to_col):
        """Check if a piece at (from_row, from_col) attacks (to_row, to_col)."""
        piece = self.board[from_row][from_col]
        pt = abs(piece)
        color = piece_color(piece)
        dr = to_row - from_row
        dc = to_col - from_col

        if pt == 1:  # Pawn
            direction = -1 if color == "white" else 1
            return dr == direction and abs(dc) == 1

        elif pt == 2:  # Rook
            return self._slides_clear(from_row, from_col, to_row, to_col, [(0,1),(0,-1),(1,0),(-1,0)])

        elif pt == 3:  # Knight
            return (abs(dr), abs(dc)) in [(1,2), (2,1)]

        elif pt == 4:  # Bishop
            return self._slides_clear(from_row, from_col, to_row, to_col, [(1,1),(1,-1),(-1,1),(-1,-1)])

        elif pt == 5:  # Queen
            return self._slides_clear(from_row, from_col, to_row, to_col,
                [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)])

        elif pt == 6:  # King
            return abs(dr) <= 1 and abs(dc) <= 1

        return False

    def _slides_clear(self, fr, fc, tr, tc, directions):
        """For sliding pieces: check that the direction matches and path is clear."""
        dr = tr - fr
        dc = tc - fc

        for ddr, ddc in directions:
            if ddr == 0 and ddc == 0:
                continue

            # Need (dr, dc) = k * (ddr, ddc) for some k > 0
            if ddr != 0 and ddc != 0:
                # Both nonzero: check cross-product ratio and sign
                if dr * ddc != dc * ddr:
                    continue
                if dr * ddr < 0 or dc * ddc < 0:
                    continue
                steps = abs(dr) // abs(ddr)
            elif ddr != 0:
                # Vertical only movement
                if dc != 0:
                    continue
                if dr * ddr < 0:
                    continue
                steps = abs(dr) // abs(ddr)
            elif ddc != 0:
                # Horizontal only movement
                if dr != 0:
                    continue
                if dc * ddc < 0:
                    continue
                steps = abs(dc) // abs(ddc)
            else:
                continue

            if steps <= 0:
                continue

            # Check all squares along the path (excluding start and end)
            r, c = fr + ddr, fc + ddc
            for _ in range(steps - 1):
                if not is_empty(self.board[r][c]):
                    return False
                r += ddr
                c += ddc
            return True

        return False

    # ---------- Check detection ----------

    def is_in_check(self, color):
        king_pos = self.find_king(color)
        if king_pos is None:
            return True
        return self._is_square_attacked(king_pos[0], king_pos[1], opponent(color))

    # ---------- Legal move generation ----------

    def get_legal_moves(self, row, col):
        """Return list of (to_row, to_col, flags_dict) that are legal."""
        piece = self.board[row][col]
        if is_empty(piece):
            return []

        color = piece_color(piece)
        if color != self.turn:
            return []

        pseudo = self._raw_pseudo_legal_moves(row, col)
        legal = []

        for tr, tc, flags in pseudo:
            test = self.copy()
            test._apply_move_raw(row, col, tr, tc, flags)
            if not test.is_in_check(color):
                legal.append((tr, tc, flags))

        return legal

    def get_all_legal_moves(self, color=None):
        """Get all legal moves for a color. Returns list of (from_r, from_c, to_r, to_c, flags)."""
        if color is None:
            color = self.turn
        all_moves = []
        saved_turn = self.turn
        self.turn = color  # Temporarily set turn for get_legal_moves
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if not is_empty(piece) and piece_color(piece) == color:
                    for tr, tc, flags in self.get_legal_moves(r, c):
                        all_moves.append((r, c, tr, tc, flags))
        self.turn = saved_turn
        return all_moves

    def _apply_move_raw(self, fr, fc, tr, tc, flags):
        """Apply a move without updating turn or castling rights (for test positions)."""
        piece = self.board[fr][fc]
        color = piece_color(piece)

        # En passant capture
        if flags.get("en_passant"):
            captured_pawn_row = fr  # same row as the moving pawn
            self.board[captured_pawn_row][tc] = EMPTY

        # Castling
        if "castle" in flags:
            if flags["castle"] == "king":
                self.board[fr][5] = self.board[fr][7]
                self.board[fr][7] = EMPTY
            else:
                self.board[fr][3] = self.board[fr][0]
                self.board[fr][0] = EMPTY

        # Move piece
        self.board[tr][tc] = piece
        self.board[fr][fc] = EMPTY

        # Promotion
        if "promotion" in flags:
            self.board[tr][tc] = flags["promotion"]

    def make_move(self, fr, fc, tr, tc, flags=None):
        """Make a legal move, updating all state."""
        if flags is None:
            flags = {}

        piece = self.board[fr][fc]
        color = piece_color(piece)

        # Save to history
        self.move_history.append({
            "from": (fr, fc), "to": (tr, tc), "flags": dict(flags),
            "piece": piece, "captured": self.board[tr][tc],
            "castling": {k: dict(v) for k, v in self.castling_rights.items()},
            "en_passant": self.en_passant_target,
        })

        # En passant capture
        if flags.get("en_passant"):
            self.board[fr][tc] = EMPTY

        # Castling rook move
        if "castle" in flags:
            if flags["castle"] == "king":
                self.board[fr][5] = self.board[fr][7]
                self.board[fr][7] = EMPTY
            else:
                self.board[fr][3] = self.board[fr][0]
                self.board[fr][0] = EMPTY

        # Move the piece
        self.board[tr][tc] = piece
        self.board[fr][fc] = EMPTY

        # Promotion
        if "promotion" in flags:
            self.board[tr][tc] = flags["promotion"]

        # Update en passant target
        self.en_passant_target = None
        if flags.get("double_pawn_push"):
            direction = -1 if color == "white" else 1
            self.en_passant_target = (fr + direction, fc)

        # Update castling rights
        piece_type = abs(piece)
        if piece_type == 6:  # King moved
            self.castling_rights[color]["king"] = False
            self.castling_rights[color]["queen"] = False
        if piece_type == 2:  # Rook moved
            if fr == (7 if color == "white" else 0) and fc == 0:
                self.castling_rights[color]["queen"] = False
            if fr == (7 if color == "white" else 0) and fc == 7:
                self.castling_rights[color]["king"] = False

        # If a rook is captured, update opponent's castling rights
        if tr == 0 and tc == 0:
            self.castling_rights["black"]["queen"] = False
        if tr == 0 and tc == 7:
            self.castling_rights["black"]["king"] = False
        if tr == 7 and tc == 0:
            self.castling_rights["white"]["queen"] = False
        if tr == 7 and tc == 7:
            self.castling_rights["white"]["king"] = False

        # Update halfmove clock
        if piece_type == 1 or not is_empty(self.move_history[-1]["captured"]):
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # Switch turn
        if color == "black":
            self.fullmove_number += 1
        self.turn = opponent(color)

    def undo_last_move(self):
        """Undo the last move (for AI search)."""
        if not self.move_history:
            return
        info = self.move_history.pop()
        fr, fc = info["from"]
        tr, tc = info["to"]
        flags = info["flags"]

        piece = info["piece"]
        color = piece_color(piece)

        # Undo promotion
        if "promotion" in flags:
            self.board[fr][fc] = W_PAWN if color == "white" else B_PAWN
        else:
            self.board[fr][fc] = piece

        # Undo en passant capture
        if flags.get("en_passant"):
            self.board[tr][tc] = EMPTY
            captured_pawn = B_PAWN if color == "white" else W_PAWN
            self.board[fr][tc] = captured_pawn
        else:
            self.board[tr][tc] = info["captured"]

        # Undo castling rook move
        if "castle" in flags:
            if flags["castle"] == "king":
                self.board[fr][7] = self.board[fr][5]
                self.board[fr][5] = EMPTY
            else:
                self.board[fr][0] = self.board[fr][3]
                self.board[fr][3] = EMPTY

        # Restore state
        self.castling_rights = info["castling"]
        self.en_passant_target = info["en_passant"]
        self.turn = color

    # ---------- Game state ----------

    def is_checkmate(self, color=None):
        if color is None:
            color = self.turn
        return self.is_in_check(color) and len(self.get_all_legal_moves(color)) == 0

    def is_stalemate(self, color=None):
        if color is None:
            color = self.turn
        return not self.is_in_check(color) and len(self.get_all_legal_moves(color)) == 0

    def is_draw(self):
        # Fifty-move rule
        if self.halfmove_clock >= 100:
            return True
        # Insufficient material
        if self._insufficient_material():
            return True
        # Stalemate
        if self.is_stalemate():
            return True
        return False

    def _insufficient_material(self):
        white_pieces = []
        black_pieces = []
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p == W_KING:
                    continue
                if p == B_KING:
                    continue
                if p > 0:
                    white_pieces.append(abs(p))
                elif p < 0:
                    black_pieces.append(abs(p))

        # King vs King
        if len(white_pieces) == 0 and len(black_pieces) == 0:
            return True
        # King + Bishop/Knight vs King
        if len(white_pieces) == 1 and len(black_pieces) == 0 and white_pieces[0] in (3, 4):
            return True
        if len(black_pieces) == 1 and len(white_pieces) == 0 and black_pieces[0] in (3, 4):
            return True
        return False

    def board_to_string(self):
        """Pretty-print the board."""
        lines = []
        lines.append("  a b c d e f g h")
        for r in range(8):
            row_str = f"{8 - r} "
            for c in range(8):
                p = self.board[r][c]
                if is_empty(p):
                    row_str += ". "
                else:
                    row_str += PIECE_NAMES[p] + " "
            row_str += f"{8 - r}"
            lines.append(row_str)
        lines.append("  a b c d e f g h")
        return "\n".join(lines)


def parse_square(sq_str):
    """Parse a square like 'e2' to (row, col)."""
    if len(sq_str) != 2:
        return None
    col = ord(sq_str[0]) - ord('a')
    row = 8 - int(sq_str[1])
    if 0 <= row < 8 and 0 <= col < 8:
        return (row, col)
    return None

def square_to_string(row, col):
    """Convert (row, col) to string like 'e2'."""
    return chr(ord('a') + col) + str(8 - row)
