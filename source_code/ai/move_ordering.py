from core.constants import DIRECTIONS, EMPTY, WIN_LENGTH
from core.rules import get_opponent


def order_moves(
    board,
    moves: list[tuple[int, int]],
    current_player: str,
    ai_player: str,
) -> list[tuple[int, int]]:
    if len(moves) < 2:
        return moves

    opponent = get_opponent(current_player)
    maximizing = current_player == ai_player
    center = (board.size - 1) / 2
    scored_moves = []

    for index, (row, col) in enumerate(moves):
        board.place_move(row, col, current_player)
        wins_now = is_winning_move(board, row, col, current_player)
        score_after_move = move_score(board, row, col, ai_player)
        board.undo_move(row, col)

        board.place_move(row, col, opponent)
        blocks_opponent_win = is_winning_move(board, row, col, opponent)
        board.undo_move(row, col)

        if wins_now:
            priority = 0
        elif blocks_opponent_win:
            priority = 1
        else:
            priority = 2

        center_distance = abs(row - center) + abs(col - center)
        score_key = -score_after_move if maximizing else score_after_move
        scored_moves.append((priority, score_key, center_distance, index, (row, col)))

    scored_moves.sort()
    return [move for *_, move in scored_moves]


def is_winning_move(board, row: int, col: int, player: str) -> bool:
    for dr, dc in DIRECTIONS:
        count = 1
        count += _count_direction(board, row, col, dr, dc, player)
        count += _count_direction(board, row, col, -dr, -dc, player)
        if count >= WIN_LENGTH:
            return True
    return False


def _count_direction(board, row: int, col: int, dr: int, dc: int, player: str) -> int:
    count = 0
    for step in range(1, WIN_LENGTH):
        nr = row + dr * step
        nc = col + dc * step
        if not board.in_bounds(nr, nc) or board.grid[nr][nc] != player:
            break
        count += 1
    return count


def move_score(board, row: int, col: int, ai_player: str) -> int:
    opponent = get_opponent(ai_player)
    return _local_player_score(board, row, col, ai_player) - _local_player_score(
        board,
        row,
        col,
        opponent,
    )


def _local_player_score(board, row: int, col: int, player: str) -> int:
    total = 0
    opponent = get_opponent(player)

    for dr, dc in DIRECTIONS:
        for offset in range(WIN_LENGTH):
            cells = []
            for step in range(WIN_LENGTH):
                nr = row + (step - offset) * dr
                nc = col + (step - offset) * dc
                if not board.in_bounds(nr, nc):
                    cells = []
                    break
                cells.append(board.grid[nr][nc])

            if not cells:
                continue

            player_count = cells.count(player)
            opponent_count = cells.count(opponent)
            empty_count = cells.count(EMPTY)

            if player_count > 0 and opponent_count > 0:
                continue
            if player_count == 4:
                total += 100_000
            elif player_count == 3 and empty_count == 1:
                total += 1_000
            elif player_count == 2 and empty_count == 2:
                total += 100
            elif player_count == 1 and empty_count == 3:
                total += 10

    return total
