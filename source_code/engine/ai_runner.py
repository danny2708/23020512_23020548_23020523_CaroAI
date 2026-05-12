from ai.evaluator import Evaluator
from ai.minimax import MinimaxSearch
from ai.alpha_beta import AlphaBetaSearch
from core.move_generator import MoveGenerator


def normalize_ai_mode(mode: str = "alphabeta") -> str:
    raw_mode = (mode or "alphabeta").strip().lower()
    compact_mode = raw_mode.replace("-", "").replace("_", "").replace(" ", "")

    if raw_mode == "1" or compact_mode in {"minimax", "mini", "level1"}:
        return "minimax"
    if raw_mode == "2" or compact_mode in {"alphabeta", "ab", "level2"}:
        return "alphabeta"

    raise ValueError("mode must be '1'/'minimax' or '2'/'alphabeta'")


def create_ai(
    mode: str = "alphabeta",
    move_mode: str = "nearby",
    radius: int = 1,
    max_candidates: int = 7,
    root_max_candidates: int = 10,
    deep_max_candidates: int = 4,
    very_deep_max_candidates: int = 3,
    ultra_deep_max_candidates: int = 2,
):
    evaluator = Evaluator()
    move_generator = MoveGenerator(
        mode=move_mode,
        radius=radius,
        max_candidates=max_candidates,
        root_max_candidates=root_max_candidates,
        deep_max_candidates=deep_max_candidates,
        very_deep_max_candidates=very_deep_max_candidates,
        ultra_deep_max_candidates=ultra_deep_max_candidates,
    )

    mode = normalize_ai_mode(mode)
    if mode == "minimax":
        return MinimaxSearch(evaluator, move_generator)
    if mode == "alphabeta":
        return AlphaBetaSearch(evaluator, move_generator)
    raise ValueError("mode must be '1'/'minimax' or '2'/'alphabeta'")
