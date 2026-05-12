from ai.alpha_beta import AlphaBetaSearch
from ai.evaluator import Evaluator
from ai.minimax import MinimaxSearch
from core.move_generator import MoveGenerator


AI_MODE_OPTIONS = (
    "1 - minimax",
    "2 - alphabeta",
    "3 - minimax-improve",
    "4 - alphabeta-improve",
)


def normalize_ai_mode(mode: str = "alphabeta") -> str:
    raw_mode = (mode or "alphabeta").strip().lower()
    compact_mode = raw_mode.replace("-", "").replace("_", "").replace(" ", "")

    if raw_mode == "1" or compact_mode in {"minimax", "mini", "level1"}:
        return "minimax"
    if raw_mode == "2" or compact_mode in {"alphabeta", "ab", "level2"}:
        return "alphabeta"
    if raw_mode == "3" or compact_mode in {
        "minimaximprove",
        "minimaximproved",
        "minimaxplus",
        "minimaxbeam",
        "level3",
    }:
        return "minimax-improve"
    if raw_mode == "4" or compact_mode in {
        "alphabetaimprove",
        "alphabetaimproved",
        "alphabetaplus",
        "alphabetabeam",
        "abimprove",
        "level4",
    }:
        return "alphabeta-improve"

    raise ValueError(
        "mode must be '1'/'minimax', '2'/'alphabeta', "
        "'3'/'minimax-improve', or '4'/'alphabeta-improve'"
    )


def is_improved_mode(mode: str) -> bool:
    return normalize_ai_mode(mode).endswith("-improve")


def base_algorithm(mode: str) -> str:
    normalized = normalize_ai_mode(mode)
    return normalized.removesuffix("-improve")


def display_ai_mode(mode: str) -> str:
    normalized = normalize_ai_mode(mode)
    labels = {
        "minimax": "Minimax",
        "alphabeta": "Alpha-Beta",
        "minimax-improve": "Minimax-Improve",
        "alphabeta-improve": "Alpha-Beta-Improve",
    }
    return labels[normalized]


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
    normalized_mode = normalize_ai_mode(mode)
    improved = is_improved_mode(normalized_mode)

    if not improved:
        max_candidates = 0
        root_max_candidates = 0
        deep_max_candidates = 0
        very_deep_max_candidates = 0
        ultra_deep_max_candidates = 0

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

    algorithm = base_algorithm(normalized_mode)
    algorithm_name = display_ai_mode(normalized_mode)
    if algorithm == "minimax":
        return MinimaxSearch(evaluator, move_generator, algorithm_name=algorithm_name)
    if algorithm == "alphabeta":
        return AlphaBetaSearch(evaluator, move_generator, algorithm_name=algorithm_name)
    raise ValueError(f"Unsupported AI mode: {mode}")
