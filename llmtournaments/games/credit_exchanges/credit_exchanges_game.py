# credit_exchanges_game.py
from typing import Dict, List, Tuple, Union
from llmtournaments.games.credit_exchanges.base_objects import (
    LLMPlayer,
    GameConfig,
    GameRound,
    GameState,
)
from llmtournaments.games.credit_exchanges.observers import Observable
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


# --------------------------------------------------------------------------
# JSON Cleaning and Loading
# --------------------------------------------------------------------------
def clean_and_load_json(input_text: str) -> dict:
    """
    Cleans up a given input_text by removing unwanted escape characters,
    extracts the first valid JSON object, and returns it as a dict.
    Raises ValueError if JSON cannot be successfully loaded.
    """
    # Clean up unwanted escape characters
    sanitized_text = input_text.replace('\\"', '"').replace("\\'", "'")
    sanitized_text = re.sub(
        r"\$ntr]", " ", sanitized_text
    )  # Replaces \n, \t, \r with spaces
    sanitized_text = sanitized_text.replace("\\\\", "\\")  # Single backslash

    # Extract JSON content between the first '{' and the last '}' (multiline)
    json_content = re.search(r"\{.*?\}", sanitized_text, re.DOTALL)
    if not json_content:
        raise ValueError(f"No curls found, expected for the JSON: {input_text}")

    json_text = json_content.group(0)

    # Attempt to parse the JSON content
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parsing error: {e}")


class CreditExchangeGame(Observable):
    """
    Main game class that manages players, processes rounds,
    and handles validations for transactions/messages based on game rules.
    """

    def __init__(self, players: List[LLMPlayer], config: GameConfig):
        super().__init__()
        self.game_state = GameState(players, config.initial_balance)
        self.game_config = config
        self.prompt_manager = PromptManager(self.game_config)

        for player in players:
            player.llm.set_system_prompt(
                self.prompt_manager.create_system_prompt(player.name)
            )

    def _validate_and_format_payload(
        self, raw_text: str, sender: LLMPlayer, payload_type: str
    ) -> Union[Dict[LLMPlayer, int], Tuple[LLMPlayer, str]]:
        """
        1) Parses the JSON from raw_text.
        2) Validates the data for either "message" or "transaction".
        3) Returns the validated payload.

        For "message": returns (recipient_player, message_text).
        - Recipients must exist, not be the sender, and message must be non-empty.

        For "transaction": returns {recipient_player: amount, ...}.
        - Recipients must exist, not be the sender, and amounts must be non-negative.

        Raises ValueError on any invalid JSON or violation of game rules.
        """

        def _validate_and_get_recipient_player(
            recipient_name: str, sender_player: LLMPlayer
        ) -> LLMPlayer:
            recipient_player = self.game_state.get_player_by_name(recipient_name)
            if not recipient_player:
                raise ValueError(f"Recipient does not exist: {recipient_name}")
            if recipient_player == sender_player:
                raise ValueError("Player trying to interact with itself")
            return recipient_player

        data = clean_and_load_json(raw_text)

        if payload_type == "message":
            recipient_name = data.get("recipient")
            message_value = data.get("message")

            recipient_player = _validate_and_get_recipient_player(
                recipient_name, sender
            )
            if not message_value.strip():
                raise ValueError("Message cannot be empty.")

            return (recipient_player, message_value.strip())

        elif payload_type == "transaction":
            validated_tx: Dict[LLMPlayer, int] = {}
            for recipient_name, amount in data.items():
                recipient_player = _validate_and_get_recipient_player(
                    recipient_name, sender
                )
                if not isinstance(amount, int) or amount < 0:
                    raise ValueError(
                        f"Invalid transaction amount for {recipient_name}: {amount}"
                    )

                validated_tx[recipient_player] = amount

            return validated_tx

        else:
            raise ValueError(f"Unknown payload_type: {payload_type}")

    # --------------------------------------------------------------------------
    # Messaging Phase
    # --------------------------------------------------------------------------
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

                # Debug print for Player B
                # if player.name == "B":
                #     print("\n------Message B -----")
                #     print(prompt)
                #     print("---------------------------")

                response_text = player.llm(prompt).response.strip()

                if response_text.upper() == "SKIP":
                    # No message
                    self.notify_observers("on_message_sent", player, None, None)
                    continue

                try:
                    recipient_player, message_text = self._validate_and_format_payload(
                        response_text, player, "message"
                    )
                    ongoing_round_messages.append(
                        (player, recipient_player, message_text)
                    )
                    self.notify_observers(
                        "on_message_sent", player, recipient_player, message_text
                    )

                except ValueError as e:
                    logger.error(
                        f"Message error from {player.name}: {str(e)}. Got: {response_text}"
                    )

        # Notify observers at the end of the messaging phase
        self.notify_observers("on_round_messages_end", ongoing_round_messages)
        return ongoing_round_messages

    # --------------------------------------------------------------------------
    # Transaction Phase
    # --------------------------------------------------------------------------
    def _conduct_transaction_phase(
        self, ongoing_round_messages: List[Tuple[LLMPlayer, LLMPlayer, str]]
    ) -> Dict[LLMPlayer, Dict[LLMPlayer, int]]:
        transactions = {}

        for player in self.game_state.players:
            transactions[player] = {}
            current_balance = self.game_state.get_balance(player)

            prompt = self.prompt_manager.generate_transaction_prompt(
                player, self.game_state, ongoing_round_messages
            )
            # if player.name == "B":
            #     print("\n------Transaction B -----")
            #     print(prompt)
            #     print("---------------------------")

            response_text = player.llm(prompt).response.strip()

            if response_text.upper() == "SKIP":
                self.notify_observers("on_transaction_made", player, None, None)
                continue

            try:
                payload = self._validate_and_format_payload(
                    response_text, player, "transaction"
                )

                total_amount = sum(payload.values())
                if total_amount > current_balance:
                    logger.error(
                        f"Transaction rejected: {player.name} tried to send {total_amount}, "
                        f"but only has {current_balance}"
                    )
                    continue

                for recipient_player, amount in payload.items():
                    transactions[player][recipient_player] = amount
                    self.notify_observers(
                        "on_transaction_made", player, recipient_player, amount
                    )

            except ValueError as e:
                logger.error(
                    f"Transaction error from {player.name}: {str(e)}. Got: {response_text}"
                )

        self.notify_observers("on_round_transactions_end", transactions)
        return transactions

    # --------------------------------------------------------------------------
    # Transaction Processing & Bonuses
    # --------------------------------------------------------------------------
    def _process_transactions(
        self, transactions: Dict[LLMPlayer, Dict[LLMPlayer, int]]
    ) -> None:
        """
        Deducts the total sent credits from each sender, adds to each recipient,
        then processes any bonus credits.
        """
        # Deduct from senders
        for sender, recipients_dict in transactions.items():
            total_sent = sum(recipients_dict.values())
            self.game_state.update_balance(sender, -total_sent)

            # Add to recipients
            for recipient, amount in recipients_dict.items():
                self.game_state.update_balance(recipient, amount)

        # Process bonuses (where players transact with each other)
        self._process_bonuses(transactions)

    def _process_bonuses(
        self, transactions: Dict[LLMPlayer, Dict[LLMPlayer, int]]
    ) -> None:
        """
        If two players exchange X credits in both directions, they both get X bonus credits.
        """
        for p1, p2 in combinations(self.game_state.players, 2):
            sent = transactions.get(p1, {}).get(p2, 0)
            received = transactions.get(p2, {}).get(p1, 0)
            bonus = min(sent, received)

            if bonus > 0:
                self.game_state.update_balance(p1, bonus)
                self.game_state.update_balance(p2, bonus)
                self.notify_observers("on_bonus_applied", p1, p2, bonus)

    # --------------------------------------------------------------------------
    # Orchestration
    # --------------------------------------------------------------------------
    def _conduct_round(self) -> None:
        """
        Conducts one full round of the game:
        1) Increment round number
        2) Conduct messaging phase
        3) Conduct transaction phase
        4) Process transactions
        5) Record round results
        """
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
        """
        Runs the full game according to the total number of rounds.
        Returns final player balances.
        """
        self.notify_observers("on_game_start", self.game_config, self.game_state)

        for _ in range(self.game_config.total_rounds):
            self._conduct_round()

        final_balances = {
            player.name: self.game_state.get_balance(player)
            for player in self.game_state.players
        }

        self.notify_observers("on_game_end", self.game_state)
        return final_balances
