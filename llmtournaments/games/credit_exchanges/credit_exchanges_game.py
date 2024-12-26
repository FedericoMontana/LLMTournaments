# credit_exchanges_game.py
from typing import Optional, Set, Dict, List, Tuple
from llmtournaments.games.credit_exchanges.base_objects import (
    LLMPlayer,
    GameConfig,
    GameRound,
    GameState,
)
from llmtournaments.games.credit_exchanges.observers import GameObserver
import logging
import random
import json
import re
from itertools import combinations

# Import the new PromptManager
from llmtournaments.games.credit_exchanges.prompt_manager import PromptManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JsonValidator:
    @staticmethod
    def clean_and_load_json(input_text):
        sanitized_text = input_text.replace('\\"', '"').replace("\\'", "'")
        sanitized_text = re.sub(
            r"\$ntr]", " ", sanitized_text
        )  # Replaces \n, \t, \r with spaces
        sanitized_text = sanitized_text.replace("\\\\", "\\")  # Single backslash

        # Step 2: Extract JSON content between first `{` and last `}` using DOTALL for multiline matching
        json_content = re.search(r"\{.*?\}", sanitized_text, re.DOTALL)
        if json_content:
            json_text = json_content.group(0)
        else:
            logger.error(
                f"No JSON content found in the input string. Got: {input_text}"
            )

        # Step 3: Attempt to load JSON

        return json.loads(json_text)

    @staticmethod
    def validate_transactions(
        json_str: str, sender_name: str, valid_players: Set[str]
    ) -> Dict[str, int]:
        try:
            data = JsonValidator.clean_and_load_json(json_str)

            if not isinstance(data, dict):
                logger.warning(f"Invalid transaction format from {sender_name}: {data}")
                return {}

            for recipient, amount in data.items():
                if recipient not in valid_players:
                    logger.warning(f"Invalid recipient from {sender_name}: {recipient}")
                    return {}
                if recipient == sender_name:
                    logger.warning(f"Self-transaction from {sender_name}")
                    return {}
                if not isinstance(amount, int) or amount < 0:
                    logger.warning(f"Invalid amount from {sender_name}: {amount}")
                    return {}

            return data

        except Exception as e:
            logger.warning(
                f"Invalid JSON from {sender_name}, got: {json_str}. Error: {str(e)}"
            )
            return {}

    @staticmethod
    def validate_message(
        json_str: str, sender_name: str, valid_players: Set[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        try:
            data = JsonValidator.clean_and_load_json(json_str)
            if not isinstance(data, dict):
                logger.warning(f"Invalid message format from {sender_name}: {data}")
                return None, None

            recipient = data.get("recipient")
            message = data.get("message")
            if not all(
                [
                    isinstance(recipient, str),
                    isinstance(message, str),
                    recipient in valid_players,
                    recipient != sender_name,
                    message.strip(),
                ]
            ):
                logger.warning(f"Invalid message data from {sender_name}")
                return None, None

            return recipient, message.strip()

        except Exception as e:
            logger.warning(
                f"Invalid JSON from {sender_name}, got: {json_str}. Error: {str(e)}"
            )
            return {}


class CreditExchangeGame:
    def __init__(self, players: List[LLMPlayer], config: GameConfig):
        self.game_state = GameState(players, config.initial_balance)
        self.game_config = config
        self.prompt_manager = PromptManager(self.game_config)
        self.observers: List[GameObserver] = []

        for player in players:
            player.llm.set_system_prompt(
                self.prompt_manager.create_system_prompt(player.name)
            )

    def add_observer(self, observer: GameObserver):
        self.observers.append(observer)

    def remove_observer(self, observer: GameObserver):
        self.observers.remove(observer)

    def notify_observers(self, method_name: str, *args, **kwargs):
        for observer in self.observers:
            method = getattr(observer, method_name, None)
            if callable(method):
                method(*args, **kwargs)

    def _conduct_messaging_phase(self) -> List[Tuple[LLMPlayer, LLMPlayer, str]]:
        ongoing_round_messages = []

        for cycle in range(self.game_config.max_communication_cycles):
            remaining_messages = self.game_config.max_communication_cycles - cycle
            player_order = random.sample(
                self.game_state.players, len(self.game_state.players)
            )

            for player in player_order:
                prompt = self.prompt_manager.generate_messaging_prompt(
                    player, self.game_state, ongoing_round_messages, remaining_messages
                )
                print(prompt)
                if player.name == "B":
                    print("\n------Message B -----")
                    print("++++")
                    print(ongoing_round_messages)
                    print("++++")
                    print(prompt)
                    print("---------------------------")

                response = player.llm(prompt).response
                recipient_player, message = None, response  # default for "SKIP" cases

                if response.strip().upper() != "SKIP":
                    recipient_name, message = JsonValidator.validate_message(
                        response, player.name, {p.name for p in self.game_state.players}
                    )
                    if recipient_name and message:
                        recipient_player = self.game_state.get_player_by_name(
                            recipient_name
                        )
                        ongoing_round_messages.append(
                            (player, recipient_player, message)
                        )

                # Notify observer once for each player iteration, with necessary details
                self.notify_observers(
                    "on_message_sent", player, recipient_player, message
                )

        # Notify observers at the end of all cycles
        self.notify_observers("on_round_messages_end", ongoing_round_messages)
        return ongoing_round_messages

    def _conduct_transaction_phase(
        self, ongoing_round_messages: List[Tuple[LLMPlayer, LLMPlayer, str]]
    ) -> Dict[LLMPlayer, Dict[LLMPlayer, int]]:
        transactions = {}

        for player in self.game_state.players:
            transactions[player] = {}  # Initialize empty transactions for player
            current_balance = self.game_state.get_balance(player)

            prompt = self.prompt_manager.generate_transaction_prompt(
                player, self.game_state, ongoing_round_messages
            )

            if player.name == "B":
                print("\n------Transaction B -----")
                print(prompt)
                print("---------------------------")

            response = player.llm(prompt).response

            if response.strip().upper() == "SKIP":
                self.notify_observers("on_transaction_made", player, None, None)
                continue

            player_transactions = JsonValidator.validate_transactions(
                response, player.name, {p.name for p in self.game_state.players}
            )

            # Check if total transactions exceed current balance
            total_amount = sum(player_transactions.values())
            if total_amount > current_balance:
                logger.error(
                    f"Transaction rejected: {player.name} attempted to send {total_amount} "
                    f"credits but only has {current_balance}"
                )
                continue

            for recipient_name, amount in player_transactions.items():
                recipient = self.game_state.get_player_by_name(recipient_name)
                transactions[player][recipient] = amount
                self.notify_observers("on_transaction_made", player, recipient, amount)

        self.notify_observers("on_round_transactions_end", transactions)
        return transactions

    def _process_transactions(
        self, transactions: Dict[LLMPlayer, Dict[LLMPlayer, int]]
    ) -> None:
        for sender, recipients in transactions.items():
            total_sent = sum(recipients.values())
            self.game_state.update_balance(sender, -total_sent)

            for recipient, amount in recipients.items():
                self.game_state.update_balance(recipient, amount)

        self._process_bonuses(transactions)

    def _process_bonuses(
        self, transactions: Dict[LLMPlayer, Dict[LLMPlayer, int]]
    ) -> None:
        for p1, p2 in combinations(self.game_state.players, 2):
            sent = transactions.get(p1, {}).get(p2, 0)
            received = transactions.get(p2, {}).get(p1, 0)

            bonus = min(sent, received)

            if bonus > 0:
                self.game_state.update_balance(p1, bonus)
                self.game_state.update_balance(p2, bonus)
                self.notify_observers("on_bonus_applied", p1, p2, bonus)

    def _conduct_round(self) -> None:
        self.game_state.increment_round()
        round_number = self.game_state.get_current_round()
        self.notify_observers("on_round_start", self.game_state, round_number)

        ongoing_round_messages = self._conduct_messaging_phase()
        transactions = self._conduct_transaction_phase(ongoing_round_messages)

        self.notify_observers(
            "on_transactions_processed", self.game_state, transactions
        )

        self._process_transactions(transactions)
        self.game_state.record_round(
            GameRound(
                round_number,
                transactions,
                ongoing_round_messages,
            )
        )

        self.notify_observers("on_round_end", self.game_state, round_number)

    def run_game(self) -> Dict[str, int]:
        self.notify_observers("on_game_start", self.game_config, self.game_state)

        for _ in range(self.game_config.total_rounds):
            self._conduct_round()

        final_balances = {
            player.name: self.game_state.get_balance(player)
            for player in self.game_state.players
        }

        self.notify_observers("on_game_end", self.game_state)

        return final_balances
