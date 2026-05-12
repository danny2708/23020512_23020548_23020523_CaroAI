# cython: boundscheck=False, wraparound=False, initializedcheck=False, cdivision=True

cdef int EMPTY_CODE = 0


cdef inline int _score_counts(int player_count, int empty_count, int win_length):
    if player_count == win_length:
        return 100000
    if player_count == win_length - 1 and empty_count == 1:
        return 1000
    if player_count == win_length - 2 and empty_count == 2:
        return 100
    if player_count == 1 and empty_count == win_length - 1:
        return 10
    return 0


cdef inline int _score_line(int count, int open_ends, int win_length):
    if count >= win_length:
        return 10000000
    if count == win_length - 1:
        if open_ends == 2:
            return 150000
        return 45000
    if count == win_length - 2:
        if open_ends == 2:
            return 4000
        return 700
    if count == 1:
        return 10 * open_ends
    return 0


cpdef int check_winner_at_codes(object cells, int size, int row, int col, int player_code, int win_length):
    cdef int directions[4][2]
    directions[0][0] = 0
    directions[0][1] = 1
    directions[1][0] = 1
    directions[1][1] = 0
    directions[2][0] = 1
    directions[2][1] = 1
    directions[3][0] = 1
    directions[3][1] = -1

    cdef int i, dr, dc, count, nr, nc
    if row < 0 or row >= size or col < 0 or col >= size:
        return 0
    if <int>cells[row * size + col] != player_code:
        return 0

    for i in range(4):
        dr = directions[i][0]
        dc = directions[i][1]
        count = 1

        nr = row + dr
        nc = col + dc
        while 0 <= nr < size and 0 <= nc < size and <int>cells[nr * size + nc] == player_code:
            count += 1
            nr += dr
            nc += dc

        nr = row - dr
        nc = col - dc
        while 0 <= nr < size and 0 <= nc < size and <int>cells[nr * size + nc] == player_code:
            count += 1
            nr -= dr
            nc -= dc

        if count >= win_length:
            return 1
    return 0


cpdef int check_winner_full_codes(object cells, int size, int player_code, int win_length):
    cdef int directions[4][2]
    directions[0][0] = 0
    directions[0][1] = 1
    directions[1][0] = 1
    directions[1][1] = 0
    directions[2][0] = 1
    directions[2][1] = 1
    directions[3][0] = 1
    directions[3][1] = -1

    cdef int row, col, i, step, dr, dc, nr, nc, count
    for row in range(size):
        for col in range(size):
            if <int>cells[row * size + col] != player_code:
                continue
            for i in range(4):
                dr = directions[i][0]
                dc = directions[i][1]
                count = 0
                for step in range(win_length):
                    nr = row + dr * step
                    nc = col + dc * step
                    if 0 <= nr < size and 0 <= nc < size and <int>cells[nr * size + nc] == player_code:
                        count += 1
                    else:
                        break
                if count == win_length:
                    return 1
    return 0


cpdef int evaluate_codes(object cells, int size, int ai_code, int opponent_code, int win_length):
    cdef int directions[4][2]
    directions[0][0] = 0
    directions[0][1] = 1
    directions[1][0] = 1
    directions[1][1] = 0
    directions[2][0] = 1
    directions[2][1] = 1
    directions[3][0] = 1
    directions[3][1] = -1

    cdef int score = 0
    cdef int row, col, i, step, dr, dc, nr, nc
    cdef int value, ai_count, opponent_count, empty_count

    for row in range(size):
        for col in range(size):
            for i in range(4):
                dr = directions[i][0]
                dc = directions[i][1]
                ai_count = 0
                opponent_count = 0
                empty_count = 0

                for step in range(win_length):
                    nr = row + dr * step
                    nc = col + dc * step
                    if nr < 0 or nr >= size or nc < 0 or nc >= size:
                        ai_count = -1
                        break
                    value = <int>cells[nr * size + nc]
                    if value == ai_code:
                        ai_count += 1
                    elif value == opponent_code:
                        opponent_count += 1
                    elif value == EMPTY_CODE:
                        empty_count += 1

                if ai_count < 0 or (ai_count and opponent_count):
                    continue
                if ai_count:
                    score += _score_counts(ai_count, empty_count, win_length)
                elif opponent_count:
                    score -= _score_counts(opponent_count, empty_count, win_length)

    return score


cdef int _line_metrics_score(object cells, int size, int row, int col, int player_code, int dr, int dc, int win_length):
    cdef int count = 1
    cdef int open_ends = 0
    cdef int nr = row + dr
    cdef int nc = col + dc

    while 0 <= nr < size and 0 <= nc < size and <int>cells[nr * size + nc] == player_code:
        count += 1
        nr += dr
        nc += dc
    if 0 <= nr < size and 0 <= nc < size and <int>cells[nr * size + nc] == EMPTY_CODE:
        open_ends += 1

    nr = row - dr
    nc = col - dc
    while 0 <= nr < size and 0 <= nc < size and <int>cells[nr * size + nc] == player_code:
        count += 1
        nr -= dr
        nc -= dc
    if 0 <= nr < size and 0 <= nc < size and <int>cells[nr * size + nc] == EMPTY_CODE:
        open_ends += 1

    return _score_line(count, open_ends, win_length)


cpdef int quick_move_score_codes(
    object cells,
    int size,
    int row,
    int col,
    int player_code,
    int opponent_code,
    int win_length,
):
    cdef int attack_score = 0
    cdef int block_score = 0
    cdef int center_bonus

    attack_score += _line_metrics_score(cells, size, row, col, player_code, 0, 1, win_length)
    attack_score += _line_metrics_score(cells, size, row, col, player_code, 1, 0, win_length)
    attack_score += _line_metrics_score(cells, size, row, col, player_code, 1, 1, win_length)
    attack_score += _line_metrics_score(cells, size, row, col, player_code, 1, -1, win_length)

    block_score += _line_metrics_score(cells, size, row, col, opponent_code, 0, 1, win_length)
    block_score += _line_metrics_score(cells, size, row, col, opponent_code, 1, 0, win_length)
    block_score += _line_metrics_score(cells, size, row, col, opponent_code, 1, 1, win_length)
    block_score += _line_metrics_score(cells, size, row, col, opponent_code, 1, -1, win_length)

    if attack_score >= 10000000:
        return 20000000
    if block_score >= 10000000:
        return 9000000

    center_bonus = <int>((size - abs(row - (size - 1) / 2.0) - abs(col - (size - 1) / 2.0)) * 2)
    return attack_score * 2 + block_score * 3 + center_bonus
