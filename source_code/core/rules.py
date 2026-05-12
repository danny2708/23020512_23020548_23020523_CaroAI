from core.constants import AI, HUMAN, EMPTY, WIN_LENGTH, DIRECTIONS
from core.board import Board, PLAYER_CODE

try:
    from accel import CYTHON_AVAILABLE, check_winner_at_codes, check_winner_full_codes
except ImportError:
    CYTHON_AVAILABLE = False
    check_winner_at_codes = None
    check_winner_full_codes = None


def check_winner_at(board: Board, row: int, col: int, player: str) -> bool:
    """Return True if the last move at (row, col) completes a winning line."""
    if CYTHON_AVAILABLE and check_winner_at_codes is not None:
        return bool(check_winner_at_codes(board.cell_codes, board.size, row, col, PLAYER_CODE[player], WIN_LENGTH))

    if not board.in_bounds(row, col) or board.grid[row][col] != player:
        return False

    for dr, dc in DIRECTIONS:
        count = 1

        nr, nc = row + dr, col + dc
        while board.in_bounds(nr, nc) and board.grid[nr][nc] == player:
            count += 1
            nr += dr
            nc += dc

        nr, nc = row - dr, col - dc
        while board.in_bounds(nr, nc) and board.grid[nr][nc] == player:
            count += 1
            nr -= dr
            nc -= dc

        if count >= WIN_LENGTH:
            return True
    return False


def check_winner(board: Board, player: str) -> bool:
    """Return True if player has 4 consecutive stones in any valid direction."""
    last_move = board.last_move()
    if last_move is not None:
        row, col, last_player = last_move
        if last_player == player:
            return check_winner_at(board, row, col, player)
        return False

    if CYTHON_AVAILABLE and check_winner_full_codes is not None:
        return bool(check_winner_full_codes(board.cell_codes, board.size, PLAYER_CODE[player], WIN_LENGTH))

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


def get_opponent(player: str) -> str:
    return HUMAN if player == AI else AI


def get_terminal_score(board: Board, ai_player: str = AI) -> int | None:
    opponent = get_opponent(ai_player)
    last_move = board.last_move()
    if last_move is not None:
        row, col, last_player = last_move
        if last_player == ai_player and check_winner_at(board, row, col, ai_player):
            return 100_000
        if last_player == opponent and check_winner_at(board, row, col, opponent):
            return -100_000
        if board.is_full():
            return 0
        return None

    if check_winner(board, ai_player):
        return 100_000
    if check_winner(board, opponent):
        return -100_000
    if check_draw(board):
        return 0
    return None


def is_terminal_state(board: Board) -> bool:
    return get_terminal_score(board) is not None
