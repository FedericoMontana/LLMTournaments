from dataclasses import dataclass
from llmtournaments.llm.llm_interaction_base import LLMInteractionBase
from typing import Optional, Dict, List, Tuple


@dataclass
class GameConfig:
    total_rounds: int
    initial_balance: int
    max_communication_cycles: int

    @classmethod
    def from_dict(cls, config_dict: dict) -> "GameConfig":
        return cls(
            total_rounds=config_dict["total_rounds"],
            initial_balance=config_dict["initial_balance"],
            max_communication_cycles=config_dict["max_communication_cycles"],
        )


@dataclass
class LLMPlayer:
    llm: LLMInteractionBase
    name: str

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, LLMPlayer):
            return NotImplemented
        return self.name == other.name


@dataclass
class GameRound:
    round_number: int
    transactions: Dict[LLMPlayer, Dict[LLMPlayer, int]]
    messages: List[Tuple[LLMPlayer, LLMPlayer, str]]


class GameState:
    def __init__(self, players: List[LLMPlayer], initial_balance: int):
        self.players = players
        self.player_balances: Dict[LLMPlayer, int] = {
            player: initial_balance for player in players
        }
        self.game_history: List[GameRound] = []
        self.current_round = 0

    def get_player_by_name(self, name: str) -> Optional[LLMPlayer]:
        return next((player for player in self.players if player.name == name), None)

    def get_balance(self, player: LLMPlayer) -> int:
        return self.player_balances[player]

    def update_balance(self, player: LLMPlayer, amount: int) -> None:
        self.player_balances[player] += amount

    def record_round(self, game_round: GameRound) -> None:
        self.game_history.append(game_round)

    def increment_round(self) -> None:
        self.current_round += 1

    def get_current_round(self) -> int:
        return self.current_round

    def get_game_history(self) -> List[GameRound]:
        return self.game_history
