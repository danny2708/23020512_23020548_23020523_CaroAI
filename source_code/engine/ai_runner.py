from ai.evaluator import Evaluator
from ai.minimax import MinimaxSearch
from ai.alpha_beta import AlphaBetaSearch
from core.move_generator import MoveGenerator


def create_ai(mode: str = "alphabeta", move_mode: str = "nearby", radius: int = 1):
    evaluator = Evaluator()
    move_generator = MoveGenerator(mode=move_mode, radius=radius)

    mode = mode.lower()
    if mode in {"minimax", "level1"}:
        return MinimaxSearch(evaluator, move_generator)
    if mode in {"alphabeta", "alpha-beta", "level2"}:
        return AlphaBetaSearch(evaluator, move_generator)
    raise ValueError("mode must be 'minimax' or 'alphabeta'")
