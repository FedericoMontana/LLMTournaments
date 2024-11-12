from llmtournaments.games.credit_exchanges.base_objects import (
    LLMPlayer,
    GameState,
    GameConfig,
)
from typing import Dict, List, Tuple
from tabulate import tabulate
from colorama import Fore, Style
import colorama
import time


class GameObserver:
    def on_game_start(self, game_config: GameConfig, game_state: GameState):
        pass

    def on_round_start(self, game_state: GameState, round_number: int):
        pass

    def on_message_sent(self, sender: LLMPlayer, recipient: LLMPlayer, message: str):
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

    def on_round_messages_end(self, messages: List[Tuple[LLMPlayer, LLMPlayer, str]]):
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

    def _print_separator(self, char="─", length=50):
        print(f"{self.INFO}{char * length}{self.RESET}")

    def _print_header(self, text: str):
        self._print_separator()
        print(f"{self.HEADER}{text}{self.RESET}")
        self._print_separator()

    def on_game_start(self, game_config: GameConfig, game_state: GameState):
        print("\n" * 2)
        self._print_header("🎮 GAME STARTED 🎮")

        # Display game configuration
        print(f"\n{self.HEADER}📋 Game Configuration:{self.RESET}")
        print(f"{self.INFO}Players ({len(game_state.players)}):{self.RESET}")
        for player in game_state.players:
            print(
                f"   • {player.name} (Starting balance: {game_state.get_balance(player)} credits)"
            )

        print(f"\n{self.INFO}Total Rounds: {game_config.total_rounds}{self.RESET}")
        print(
            f"\n{self.INFO}Total Message Cycles per round: {game_config.max_communication_cycles}{self.RESET}"
        )

        # Game rules summary
        print(f"\n{self.HEADER}🎯 Game Rules:{self.RESET}")
        print(
            f"{self.INFO}• Players can send messages and make transactions each round"
        )
        print("• Transactions between players affect their credit balance")
        print("• Bonuses are awarded for successful cooperation")
        print("• Rankings are updated after each round")
        print(f"• Final standings determined by total credits{self.RESET}")

        self._print_separator()
        time.sleep(0.5)  # Add dramatic pause

    def on_round_start(self, game_state: GameState, round_number: int):
        print("\n")
        self._print_header(f"📍 ROUND {round_number} 📍")

    def on_message_sent(self, sender: LLMPlayer, recipient: LLMPlayer, message: str):
        if recipient is None:
            print(
                f"{self.WARNING}💬 {sender.name} → (No recipient specified):{self.RESET}"
            )
            print(f"   {message}")

            return

        print(f"{self.INFO}💬 {sender.name} → {recipient.name}:{self.RESET}")
        print(f"   {message}")

    def on_transaction_made(self, sender: LLMPlayer, recipient: LLMPlayer, amount: int):
        if recipient is None:
            print(
                f"{self.WARNING}💸 {sender.name} skips - no transaction sent {self.RESET}"
            )
            return
        print(
            f"{self.SUCCESS}💸 {sender.name} sends {amount} credits to {recipient.name}{self.RESET}"
        )

    def on_bonus_applied(self, player1: LLMPlayer, player2: LLMPlayer, bonus: int):
        print(
            f"{self.IMPORTANT}🎁 Bonus applied between {player1.name} and {player2.name}: "
            f"{bonus} credits{self.RESET}"
        )

    def on_transactions_processed(
        self,
        game_state: GameState,
        transactions: Dict[LLMPlayer, Dict[LLMPlayer, int]],
    ):
        self._print_transaction_matrix(game_state, transactions)

    def on_round_messages_end(self, messages: List[Tuple[LLMPlayer, LLMPlayer, str]]):
        print(f"\n{self.INFO}📨 Messages phase concluded{self.RESET}")

    def on_round_transactions_end(
        self, transactions: Dict[LLMPlayer, Dict[LLMPlayer, int]]
    ):
        print(f"\n{self.INFO}💰 Transactions phase concluded{self.RESET}")

    def on_round_end(self, game_state: GameState, round_number: int):
        self._print_rankings(game_state)

    def on_game_end(self, game_state: GameState):
        self._print_header("🏁 GAME COMPLETED 🏁")

        # Create table data for final balances
        final_balances = [
            [player.name, game_state.get_balance(player)]
            for player in game_state.players
        ]
        final_balances.sort(key=lambda x: x[1], reverse=True)

        # Add color coding to balances
        colored_balances = [
            [
                f"{self.IMPORTANT}{name}{self.RESET}",
                f"{self.SUCCESS}{balance} credits{self.RESET}",
            ]
            for name, balance in final_balances
        ]

        print("\n📊 Final Results:")
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

        print(f"\n{self.HEADER}🏆 Current Rankings:{self.RESET}")

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

        # Create matrix data
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

        # Create headers with arrows
        headers = [f"{self.HEADER}TO ↓{self.RESET}"] + [
            f"{self.HEADER}{name}{self.RESET}" for name in player_names
        ]

        # Add FROM column with arrows
        matrix_data = [
            [f"{self.HEADER}FROM {player.name} →{self.RESET}"] + row
            for player, row in zip(game_state.players, matrix_data)
        ]

        print(
            f"\n{self.IMPORTANT}📊 Transaction Matrix - Round {game_state.get_current_round()}{self.RESET}"
        )
        print(
            tabulate(
                matrix_data, headers=headers, tablefmt="fancy_grid", stralign="center"
            )
        )

        # Print summary statistics
        total_transactions = sum(
            transactions.get(sender, {}).get(recipient, 0)
            for sender in game_state.players
            for recipient in game_state.players
            if sender != recipient
        )

        print(f"\n{self.HEADER}📈 Round Summary:{self.RESET}")
        summary_data = [
            [
                "Total Transactions",
                f"{self.SUCCESS}{total_transactions} credits{self.RESET}",
            ],
            ["Active Players", f"{self.INFO}{len(game_state.players)}{self.RESET}"],
        ]
        print(tabulate(summary_data, tablefmt="simple", stralign="left"))
