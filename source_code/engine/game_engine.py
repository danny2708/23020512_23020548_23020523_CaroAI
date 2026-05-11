from core.board import Board
from core.constants import HUMAN, AI
from core.rules import check_winner, check_draw
from engine.ai_runner import create_ai


class GameEngine:
    def __init__(self, size: int = 9, ai_mode: str = "alphabeta", depth: int = 2):
        self.board = Board(size=size)
        self.ai = create_ai(ai_mode)
        self.depth = depth

    def human_move(self, row: int, col: int) -> bool:
        return self.board.place_move(row, col, HUMAN)

    def ai_move(self):
        result = self.ai.search(self.board, self.depth)
        if result.best_move is not None:
            self.board.place_move(result.best_move[0], result.best_move[1], AI)
        return result

    def status(self) -> str:
        if check_winner(self.board, HUMAN):
            return "HUMAN_WIN"
        if check_winner(self.board, AI):
            return "AI_WIN"
        if check_draw(self.board):
            return "DRAW"
        return "ONGOING"
