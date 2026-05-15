import sys
import unittest
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from core.board import Board
from core.constants import AI, HUMAN
from core.rules import check_winner
from ai.evaluator import Evaluator
from engine.auto_play import AutoPlayGame, AutoPlayStep
from engine.ai_runner import create_ai
from engine.game_engine import GameEngine, HumanVsAIMove


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

    def test_human_vs_ai_replays_backed_up_turn(self):
        game = GameEngine(9)
        game.human_move(4, 4)
        ai_move = HumanVsAIMove(player=AI, move=(4, 5))
        game.board.place_move(4, 5, AI)
        game.history.append(ai_move)

        removed = game.undo_last_turn()
        self.assertTrue(game.board.is_empty_cell(4, 4))
        self.assertTrue(game.board.is_empty_cell(4, 5))

        self.assertTrue(game.replay_turn(removed))
        self.assertEqual(game.board.grid[4][4], HUMAN)
        self.assertEqual(game.board.grid[4][5], AI)
        self.assertEqual([move.player for move in game.history], [HUMAN, AI])

    def test_ai_vs_ai_replays_backed_up_step(self):
        game = AutoPlayGame(size=9, max_turns=1)
        step = AutoPlayStep(
            turn=1,
            player=HUMAN,
            move=(4, 4),
            score=0,
            depth=1,
            nodes_visited=0,
            elapsed_time=0.0,
            algorithm="Manual",
            status_after_move="ONGOING",
        )

        self.assertTrue(game.replay_step(step))
        removed = game.undo_last_step()
        self.assertIsNotNone(removed)
        self.assertTrue(game.board.is_empty_cell(4, 4))

        self.assertTrue(game.replay_step(removed))
        self.assertEqual(game.board.grid[4][4], HUMAN)
        self.assertEqual(game.current_player, AI)

    def test_heuristic_breakdown_is_move_local(self):
        board = Board.from_strings(
            [
                ".........",
                ".........",
                ".........",
                "....X....",
                "....O....",
                ".........",
                ".........",
                ".........",
                ".........",
            ]
        )
        evaluator = Evaluator()

        near_center = evaluator.score_breakdown(board, ai_player=AI, evaluated_move=(4, 3))
        diagonal = evaluator.score_breakdown(board, ai_player=AI, evaluated_move=(3, 3))

        self.assertGreater(near_center["score_attack"], 0)
        self.assertGreater(diagonal["score_defense"], 0)
        self.assertGreater(near_center["position_weight"], 0)
        self.assertNotEqual(near_center["final_heuristic_score"], diagonal["final_heuristic_score"])
        self.assertEqual(
            near_center["final_heuristic_score"],
            near_center["score_attack"] + near_center["score_defense"] + near_center["position_weight"],
        )


if __name__ == "__main__":
    unittest.main()
