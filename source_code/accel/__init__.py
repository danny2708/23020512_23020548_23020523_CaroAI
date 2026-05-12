try:
    from accel.caro_accel import (
        check_winner_at_codes,
        check_winner_full_codes,
        evaluate_codes,
        quick_move_score_codes,
    )

    CYTHON_AVAILABLE = True
except ImportError:
    CYTHON_AVAILABLE = False
    check_winner_at_codes = None
    check_winner_full_codes = None
    evaluate_codes = None
    quick_move_score_codes = None
