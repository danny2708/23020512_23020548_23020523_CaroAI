import sys
import unittest
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from core.board import Board
from core.constants import AI, HUMAN
from core.rules import check_winner
from engine.ai_runner import create_ai


def board_from_moves(moves: list[tuple[int, int]]) -> Board:
    board = Board(9)
    player = HUMAN
    for row, col in moves:
        board.place_move(row, col, player)
        player = AI if player == HUMAN else HUMAN
    return board


class TacticalSearchTests(unittest.TestCase):
    def test_check_winner_scans_existing_win_for_non_last_player(self):
        board = Board(9)
        for row, col, player in [
            (0, 0, AI),
            (1, 1, AI),
            (2, 2, AI),
            (3, 3, AI),
            (8, 8, HUMAN),
        ]:
            board.place_move(row, col, player)

        self.assertTrue(check_winner(board, AI))
        self.assertFalse(check_winner(board, HUMAN))

    def test_immediate_win_is_preferred_by_all_modes(self):
        rows = [
            ".........",
            ".........",
            ".........",
            "..OOO....",
            "..XX.....",
            ".........",
            ".........",
            ".........",
            ".........",
        ]
        winning_moves = {(3, 1), (3, 5)}

        for mode in ("minimax", "alphabeta", "minimax-improve", "alphabeta-improve"):
            with self.subTest(mode=mode):
                result = create_ai(mode).search(Board.from_strings(rows), 2, ai_player=AI)
                self.assertIn(result.best_move, winning_moves)

    def test_reported_depth8_positions_with_improved_modes(self):
        cases = [
            (
                "first_reported_position",
                [(4, 4), (3, 4), (0, 0), (4, 3), (5, 2), (2, 5), (1, 6), (3, 3), (3, 2)],
                (5, 3),
            ),
            (
                "second_reported_position",
                [(4, 4), (3, 4), (0, 0), (5, 5), (5, 4), (5, 3), (4, 6), (6, 4)],
                (4, 2),
            ),
        ]

        for name, moves, expected_move in cases:
            for mode in ("minimax-improve", "alphabeta-improve"):
                with self.subTest(position=name, mode=mode):
                    result = create_ai(mode).search(board_from_moves(moves), 8, ai_player=AI)
                    self.assertEqual(result.best_move, expected_move)


if __name__ == "__main__":
    unittest.main()
