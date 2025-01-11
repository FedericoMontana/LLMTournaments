from llmtournaments.games.credit_exchanges.base_objects import (
    LLMPlayer,
    GameState,
    GameConfig,
)
from typing import Dict, List, Tuple, Optional
from tabulate import tabulate
from colorama import Fore, Style
import colorama
import time
from abc import ABC, abstractmethod


class BaseObserver(ABC):
    """Abstract base class for all game observers"""

    @abstractmethod
    def update(self, event_type: str, *args, **kwargs):
        """Main update method that all observers must implement"""
        pass


class Observable:
    """Mixin class to provide observer functionality"""

    def __init__(self):
        self._observers = []

    def add_observer(self, observer: BaseObserver):
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: BaseObserver):
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_observers(self, event_type: str, *args, **kwargs):
        for observer in self._observers:
            observer.update(event_type, *args, **kwargs)


class GameObserver(BaseObserver):
    """Concrete implementation of game observer with default behaviors"""

    def update(self, event_type: str, *args, **kwargs):
        """Routes events to appropriate handler methods"""
        handler = getattr(self, f"{event_type}", None)
        if handler and callable(handler):
            handler(*args, **kwargs)
        else:
            raise ValueError(
                f"No handler found for event type '{event_type}' in {self.__class__.__name__}"
            )

    def on_game_start(self, game_config: GameConfig, game_state: GameState):
        pass

    def on_round_start(self, game_state: GameState, round_number: int):
        pass

    def on_message_sent(
        self, sender: LLMPlayer, recipients: List[LLMPlayer], message: str
    ):
        pass

    def on_transaction_made(self, sender: LLMPlayer, recipient: LLMPlayer, amount: int):
        pass

    def on_bonus_applied(self, player1: LLMPlayer, player2: LLMPlayer, bonus: int):
        pass

    def on_transactions_processed(
        self,
        game_state: GameState,
        transactions: Dict[LLMPlayer, Dict[LLMPlayer, int]],
    ):
        pass

    def on_round_messages_end(
        self, messages: List[Tuple[LLMPlayer, List[LLMPlayer], str]]
    ):
        pass

    def on_round_transactions_end(
        self, transactions: Dict[LLMPlayer, Dict[LLMPlayer, int]]
    ):
        pass

    def on_round_end(self, game_state: GameState, round_number: int):
        pass

    def on_game_end(self, game_state: GameState):
        pass


class ConsolePrinter(GameObserver):
    def __init__(self):
        colorama.init()
        self.HEADER = f"{Fore.YELLOW}{Style.BRIGHT}"
        self.RESET = Style.RESET_ALL
        self.INFO = Fore.CYAN
        self.SUCCESS = Fore.GREEN
        self.WARNING = Fore.YELLOW
        self.IMPORTANT = f"{Fore.MAGENTA}{Style.BRIGHT}"

    def _print_separator(self, char="─", length=40):
        print(f"{self.INFO}{char * length}{self.RESET}")

    def _print_header(self, text: str):
        self._print_separator()
        print(f"{self.HEADER}{text}{self.RESET}")

    def on_game_start(self, game_config: GameConfig, game_state: GameState):
        print("\n")
        self._print_header("Game Started")

        print(f"\n{self.HEADER}Game Configuration:{self.RESET}")
        print(f"{self.INFO}Players ({len(game_state.players)}):{self.RESET}")
        for player in game_state.players:
            print(
                f"   - {player.name} (Starting balance: {game_state.get_balance(player)} credits)"
            )

        print(f"\n{self.INFO}Total Rounds: {game_config.total_rounds}{self.RESET}")
        print(
            f"{self.INFO}Message Cycles per Round: {game_config.max_communication_cycles}{self.RESET}"
        )

        print(f"\n{self.HEADER}Game Rules:{self.RESET}")
        print(
            f"{self.INFO}- Players can send messages and make transactions each round{self.RESET}"
        )
        print(f"{self.INFO}- Transactions affect credit balances{self.RESET}")
        print(f"{self.INFO}- Bonuses are awarded for cooperation{self.RESET}")
        print(f"{self.INFO}- Rankings are updated per round{self.RESET}")
        print(f"{self.INFO}- Final standings by total credits{self.RESET}")

        print()
        time.sleep(0.5)

    def on_round_start(self, game_state: GameState, round_number: int):
        print("\n")
        print(f"{self.HEADER}Round {round_number} Initiated{self.RESET}")

    def on_message_sent(
        self, sender: LLMPlayer, recipients: List[LLMPlayer], message: str
    ):
        recipient_names = [recipient.name for recipient in recipients]
        print(
            f"{self.INFO}Message: {sender.name} -> {', '.join(recipient_names)}: {message}{self.RESET}"
        )
        time.sleep(0.5)

    def on_transaction_made(
        self, sender: LLMPlayer, recipient: Optional[LLMPlayer], amount: int
    ):
        if recipient is None:
            print(
                f"{self.WARNING}Transaction Skipped: {sender.name} did not send a transaction.{self.RESET}"
            )
        else:
            print(
                f"{self.SUCCESS}Transaction: {sender.name} sent {amount} credits to {recipient.name}{self.RESET}"
            )

    def on_bonus_applied(self, player1: LLMPlayer, player2: LLMPlayer, bonus: int):
        print(
            f"{self.IMPORTANT}Bonus Awarded: {player1.name} and {player2.name} received {bonus} credits.{self.RESET}"
        )

    def on_transactions_processed(
        self,
        game_state: GameState,
        transactions: Dict[LLMPlayer, Dict[LLMPlayer, int]],
    ):
        self._print_transaction_matrix(game_state, transactions)

    def on_round_messages_end(
        self, messages: List[Tuple[LLMPlayer, List[LLMPlayer], str]]
    ):
        print(f"\n{self.INFO}Message Phase Concluded.{self.RESET}")

    def on_round_transactions_end(
        self, transactions: Dict[LLMPlayer, Dict[LLMPlayer, int]]
    ):
        print(f"\n{self.INFO}Transaction Phase Concluded.{self.RESET}")

    def on_round_end(self, game_state: GameState, round_number: int):
        self._print_rankings(game_state)

    def on_game_end(self, game_state: GameState):
        self._print_header("Game Completed")

        final_balances = [
            [player.name, game_state.get_balance(player)]
            for player in game_state.players
        ]
        final_balances.sort(key=lambda x: x[1], reverse=True)

        colored_balances = [
            [
                f"{self.IMPORTANT}{name}{self.RESET}",
                f"{self.SUCCESS}{balance} credits{self.RESET}",
            ]
            for name, balance in final_balances
        ]

        print("\nFinal Results:")
        print(
            tabulate(
                colored_balances,
                headers=[
                    f"{self.HEADER}Player{self.RESET}",
                    f"{self.HEADER}Balance{self.RESET}",
                ],
                tablefmt="fancy_grid",
                stralign="center",
            )
        )

    def _print_rankings(self, game_state: GameState) -> None:
        rankings = [
            (player.name, game_state.get_balance(player))
            for player in game_state.players
        ]
        rankings.sort(key=lambda x: x[1], reverse=True)

        print("\nCurrent Rankings:")

        table_data = []
        for rank, (name, balance) in enumerate(rankings, 1):
            table_data.append(
                [
                    rank,
                    name,
                    f"{self.SUCCESS}{balance} credits{self.RESET}",
                ]
            )

        print(
            tabulate(
                table_data,
                headers=[
                    f"{self.HEADER}Rank{self.RESET}",
                    f"{self.HEADER}Player{self.RESET}",
                    f"{self.HEADER}Balance{self.RESET}",
                ],
                tablefmt="fancy_grid",
                stralign="center",
            )
        )

    def _print_transaction_matrix(
        self,
        game_state: GameState,
        transactions: Dict[LLMPlayer, Dict[LLMPlayer, int]],
    ) -> None:
        player_names = [p.name for p in game_state.players]

        matrix_data = []
        for sender in game_state.players:
            row = []
            for recipient in game_state.players:
                if sender == recipient:
                    row.append(f"{self.WARNING}—{self.RESET}")
                else:
                    amount = transactions.get(sender, {}).get(recipient, 0)
                    if amount > 0:
                        row.append(f"{self.SUCCESS}{amount}{self.RESET}")
                    else:
                        row.append(f"{Fore.RED}0{self.RESET}")
            matrix_data.append(row)

        headers = [f"{self.HEADER}TO{self.RESET}"] + [
            f"{self.HEADER}{name}{self.RESET}" for name in player_names
        ]

        matrix_data = [
            [f"{self.HEADER}FROM {player.name}{self.RESET}"] + row
            for player, row in zip(game_state.players, matrix_data)
        ]

        print(
            f"\n{self.IMPORTANT}Transaction Matrix - Round {game_state.get_current_round()}{self.RESET}"
        )
        print(
            tabulate(
                matrix_data, headers=headers, tablefmt="fancy_grid", stralign="center"
            )
        )

        total_transactions = sum(
            transactions.get(sender, {}).get(recipient, 0)
            for sender in game_state.players
            for recipient in game_state.players
            if sender != recipient
        )

        print(f"\n{self.HEADER}Round Summary:{self.RESET}")
        summary_data = [
            [
                "Total Transactions",
                f"{self.SUCCESS}{total_transactions} credits{self.RESET}",
            ],
            ["Active Players", f"{self.INFO}{len(game_state.players)}{self.RESET}"],
        ]
        print(tabulate(summary_data, tablefmt="simple", stralign="left"))
