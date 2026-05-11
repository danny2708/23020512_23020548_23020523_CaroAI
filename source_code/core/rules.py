from core.constants import AI, HUMAN, EMPTY, WIN_LENGTH, DIRECTIONS
from core.board import Board


def check_winner(board: Board, player: str) -> bool:
    """Return True if player has 4 consecutive stones in any valid direction."""
    n = board.size
    for r in range(n):
        for c in range(n):
            if board.grid[r][c] != player:
                continue
            for dr, dc in DIRECTIONS:
                count = 0
                for k in range(WIN_LENGTH):
                    nr, nc = r + dr * k, c + dc * k
                    if 0 <= nr < n and 0 <= nc < n and board.grid[nr][nc] == player:
                        count += 1
                    else:
                        break
                if count == WIN_LENGTH:
                    return True
    return False


def check_draw(board: Board) -> bool:
    return board.is_full() and not check_winner(board, AI) and not check_winner(board, HUMAN)


def get_terminal_score(board: Board) -> int | None:
    if check_winner(board, AI):
        return 100_000
    if check_winner(board, HUMAN):
        return -100_000
    if check_draw(board):
        return 0
    return None


def is_terminal_state(board: Board) -> bool:
    return get_terminal_score(board) is not None
