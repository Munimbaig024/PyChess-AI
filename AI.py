"""
Chess AI - Minimax with Alpha-Beta Pruning and positional evaluation.
"""

import random
import time
from Board import (
    ChessBoard, is_empty, is_white, is_black, piece_color,
    W_PAWN, W_ROOK, W_KNIGHT, W_BISHOP, W_QUEEN, W_KING,
    B_PAWN, B_ROOK, B_KNIGHT, B_BISHOP, B_QUEEN, B_KING,
)

# Piece values (centipawns)
PIECE_VALUES = {
    1: 100, 2: 500, 3: 320, 4: 330, 5: 900, 6: 20000,
}

# Pawn positional tables (bonus for good squares)
# White pawn: rows 0-7 correspond to ranks 8-1
PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

KING_MID_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
]

POSITIONAL_TABLES = {
    1: PAWN_TABLE,
    2: ROOK_TABLE,
    3: KNIGHT_TABLE,
    4: BISHOP_TABLE,
    5: QUEEN_TABLE,
    6: KING_MID_TABLE,
}


def evaluate_board(board: ChessBoard, ai_color: str) -> int:
    """
    Evaluate the board from the AI's perspective.
    Positive = good for AI, negative = good for opponent.
    """
    score = 0

    for r in range(8):
        for c in range(8):
            piece = board.board[r][c]
            if is_empty(piece):
                continue

            pt = abs(piece)
            value = PIECE_VALUES[pt]

            # Positional bonus
            table = POSITIONAL_TABLES.get(pt)
            if table:
                if is_white(piece):
                    pos_bonus = table[r * 8 + c]
                else:
                    # Mirror the table for black
                    pos_bonus = table[(7 - r) * 8 + c]
            else:
                pos_bonus = 0

            total = value + pos_bonus

            if piece_color(piece) == ai_color:
                score += total
            else:
                score -= total

    # Mobility bonus
    ai_moves = len(board.get_all_legal_moves(ai_color))
    opp_moves = len(board.get_all_legal_moves(opponent(ai_color)))

    mobility_bonus = (ai_moves - opp_moves) * 2
    score += mobility_bonus

    return score


def opponent(color):
    return "black" if color == "white" else "white"


def order_moves(board: ChessBoard, moves, ai_color):
    """
    Order moves to improve alpha-beta pruning efficiency.
    Prioritize: captures, checks, promotions.
    """
    scored = []
    for move in moves:
        fr, fc, tr, tc, flags = move
        score = 0

        # MVV-LVA for captures
        if not is_empty(board.board[tr][tc]):
            victim = abs(board.board[tr][tc])
            attacker = abs(board.board[fr][fc])
            score += PIECE_VALUES.get(victim, 0) * 10 - PIECE_VALUES.get(attacker, 0)

        # En passant
        if flags.get("en_passant"):
            score += 100

        # Promotion
        if "promotion" in flags:
            score += PIECE_VALUES.get(abs(flags["promotion"]), 0)

        scored.append((score, move))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def alpha_beta(board: ChessBoard, depth: int, alpha: int, beta: int,
               ai_color: str, maximizing: bool, start_time: float, time_limit: float) -> int:
    """
    Alpha-Beta minimax search.
    Returns evaluation score.
    """
    # Time check
    if time.time() - start_time > time_limit:
        return evaluate_board(board, ai_color)

    current_color = ai_color if maximizing else opponent(ai_color)
    moves = board.get_all_legal_moves(current_color)

    # Terminal states
    if len(moves) == 0:
        if board.is_in_check(current_color):
            # Checkmate - worst score
            if maximizing:
                return -100000 + (100 - depth)  # Prefer faster checkmates
            else:
                return 100000 - (100 - depth)
        else:
            return 0  # Stalemate

    if board.halfmove_clock >= 100:
        return 0

    if depth == 0:
        return evaluate_board(board, ai_color)

    # Move ordering
    moves = order_moves(board, moves, current_color)

    if maximizing:
        max_eval = -200000
        for fr, fc, tr, tc, flags in moves:
            board.make_move(fr, fc, tr, tc, flags)
            eval_score = alpha_beta(board, depth - 1, alpha, beta, ai_color, False, start_time, time_limit)
            board.undo_last_move()
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = 200000
        for fr, fc, tr, tc, flags in moves:
            board.make_move(fr, fc, tr, tc, flags)
            eval_score = alpha_beta(board, depth - 1, alpha, beta, ai_color, True, start_time, time_limit)
            board.undo_last_move()
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval


class ChessAI:
    def __init__(self, color="black", depth=4, time_limit=5.0):
        """
        Initialize the AI.
        color: which color the AI plays
        depth: max search depth
        time_limit: max seconds per move
        """
        self.color = color
        self.depth = depth
        self.time_limit = time_limit

    def get_best_move(self, board: ChessBoard):
        """
        Find the best move for the current position.
        Returns (from_row, from_col, to_row, to_col, flags).
        """
        start_time = time.time()
        moves = board.get_all_legal_moves(self.color)

        if len(moves) == 0:
            return None
        if len(moves) == 1:
            return moves[0]

        # Order moves for better pruning
        moves = order_moves(board, moves, self.color)

        best_move = moves[0]
        best_score = -200000

        # Iterative deepening
        for depth_limit in range(1, self.depth + 1):
            current_best = moves[0]
            current_best_score = -200000

            for fr, fc, tr, tc, flags in moves:
                if time.time() - start_time > self.time_limit * 0.8:
                    break

                board.make_move(fr, fc, tr, tc, flags)
                score = alpha_beta(board, depth_limit - 1, -200000, 200000,
                                   self.color, False, start_time, self.time_limit)
                board.undo_last_move()

                if score > current_best_score:
                    current_best_score = score
                    current_best = (fr, fc, tr, tc, flags)

            if time.time() - start_time < self.time_limit * 0.8:
                best_move = current_best
                best_score = current_best_score

            # If we found a forced checkmate, stop searching
            if abs(best_score) > 90000:
                break

        print(f"AI thinks for {time.time() - start_time:.2f}s, score: {best_score}")
        return best_move
