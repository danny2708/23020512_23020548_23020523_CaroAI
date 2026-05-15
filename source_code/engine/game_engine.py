from dataclasses import dataclass

from ai.base_search import SearchResult
from core.board import Board
from core.constants import HUMAN, AI
from core.rules import check_winner, check_draw
from engine.ai_runner import create_ai, normalize_ai_mode


@dataclass
class HumanVsAIMove:
    player: str
    move: tuple[int, int]
    result: SearchResult | None = None


class GameEngine:
    def __init__(self, size: int = 9, ai_mode: str = "alphabeta", depth: int = 2):
        self.board = Board(size=size)
        self.ai_mode = normalize_ai_mode(ai_mode)
        self.ai = create_ai(self.ai_mode)
        self.depth = depth
        self.history: list[HumanVsAIMove] = []

    def human_move(self, row: int, col: int) -> bool:
        if not self.board.place_move(row, col, HUMAN):
            return False
        self.history.append(HumanVsAIMove(player=HUMAN, move=(row, col)))
        return True

    def ai_move(self):
        search_board = self.board.clone()
        result = self.ai.search(search_board, self.depth, ai_player=AI)
        if result.best_move is not None:
            self.board.place_move(result.best_move[0], result.best_move[1], AI)
            self.history.append(HumanVsAIMove(player=AI, move=result.best_move, result=result))
        return result

    def undo_last_turn(self) -> list[HumanVsAIMove]:
        if not self.history:
            return []

        removed = [self._undo_last_move()]
        if removed[0] is not None and removed[0].player == AI and self.history and self.history[-1].player == HUMAN:
            removed.append(self._undo_last_move())
        return [move for move in removed if move is not None]

    def replay_turn(self, removed_moves: list[HumanVsAIMove]) -> bool:
        moves = list(reversed(removed_moves))
        replayed: list[HumanVsAIMove] = []
        for move in moves:
            row, col = move.move
            if not self.board.place_move(row, col, move.player):
                for replayed_move in reversed(replayed):
                    self.board.undo_move(replayed_move.move[0], replayed_move.move[1])
                    self.history.pop()
                return False
            self.history.append(move)
            replayed.append(move)
        return True

    def _undo_last_move(self) -> HumanVsAIMove | None:
        if not self.history:
            return None
        move = self.history.pop()
        self.board.undo_move(move.move[0], move.move[1])
        return move

    def update_ai(self, ai_mode: str, depth: int) -> None:
        ai_mode = normalize_ai_mode(ai_mode)
        if ai_mode != self.ai_mode:
            self.ai_mode = ai_mode
            self.ai = create_ai(self.ai_mode)
        self.depth = depth

    def status(self) -> str:
        if check_winner(self.board, HUMAN):
            return "HUMAN_WIN"
        if check_winner(self.board, AI):
            return "AI_WIN"
        if check_draw(self.board):
            return "DRAW"
        return "ONGOING"
