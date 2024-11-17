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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromptManager:
    def __init__(
        self, total_rounds: int, initial_balance: int, max_communication_cycles: int
    ):
        self.total_rounds = total_rounds
        self.initial_balance = initial_balance
        self.max_communication_cycles = max_communication_cycles

    def create_system_prompt(self, player_name: str) -> str:
        return (
            "Game Overview:\n"
            "You are a competitive player in an imaginary game with simulated participants. "
            f"Your primary goal is to maximize your credits. The game consists of {self.total_rounds} rounds, "
            f"and you start with {self.initial_balance} credits.\n\n"
            "Game Rules:\n"
            "1. Starting Credits: Each player starts with the same number of credits.\n"
            f"2. Total Rounds: {self.total_rounds}\n"
            "3. Per Round Actions:\n"
            "   - Before each round, you may send private messages to other players.\n"
            "   - At the end of each round, you can give credits to other players.\n"
            "   - You cannot exceed your current balance when giving credits.\n"
            "   - Credits received from others are added to your balance.\n"
            "   - When you and another player exchange credits mutually,\n"
            "     you both receive a bonus equal to the smaller amount exchanged.\n\n"
            "Strategy Notes:\n"
            "   - ONLY the player with the most credits wins. Everyone else lose\n"
            "   - All players are AI entities - deception and strategic alliances are allowed and expected, they will do it with you.\n"
            "   - Monitor past rounds to evaluate alliances and strategies.\n"
            "   - IMPORTANT: Consider rankings and remaining rounds when adjusting your strategy. Remember: only the player with the highest balance wins\n\n"
            "\nIMPORTANT: All responses must be in JSON format or the word 'SKIP'\n"
            'For messages (only to 1 recipient at a time): {"recipient": "player_name", "message": "your message"}\n'
            'For transactions (you can send to 1, many or all players at a time): {"player_name": amount, "player_name2": amount2, ... }\n'
            "FOLLOW THE RULES WHEN PROMPTED FOR YOUR RESPONSE, AND AVOID DEVIATIONS. FOCUS SOLELY ON MAXIMIZING YOUR PROFIT. BE STRATEGIC: ANALYZE THE GAME, ITS PROGRESSION AND PAST ROUNDS DETAILS TO SEE HOW OTHERS ARE PLAYING. USE DECEPTION WHEN NECESSARY. IDENTIFY YOUR WEAKEST AND STRONGEST OPPONENTS.\n"
            "YOUR NAME FOR THIS GAME IS: {player_name}\n\n"
        )

    def create_game_status_prompt(
        self, game_state: GameState, current_player: LLMPlayer
    ) -> str:
        status = (
            f"Game Status:\n"
            f"- Total Rounds: {self.total_rounds}\n"
            f"- Current Round: {game_state.current_round}\n"
            f"- Current Rankings (by balance):\n"
        )

        # Create list of (player, balance) tuples and sort by balance
        rankings = [
            (player, game_state.get_balance(player)) for player in game_state.players
        ]
        rankings.sort(
            key=lambda x: x[1], reverse=True
        )  # Sort by balance in descending order

        # Add rankings with position numbers
        for position, (player, balance) in enumerate(rankings, 1):
            status += f"  {position}. {player.name}: {balance} credits\n"

        status += f"\nREMEMBER: You are {current_player.name}.\n\n"
        return status

    def create_game_history_prompt(
        self, current_player: LLMPlayer, game_history: List[GameRound]
    ) -> str:
        if not game_history:
            return "\n\nHistory of Rounds So Far: None, it is the first round.\n"

        history = "\n\nHistory of Rounds So Far:\n"
        for round_data in game_history:
            history += f"\nRound {round_data.round_number}:\n"
            history += "Messages you've sent or received (visible only to you and the sender/receiver, displayed in chronological order with the newest messages at the bottom):\n"

            player_messages = [
                (sender, recipient, message)
                for sender, recipient, message in round_data.messages
                if sender == current_player or recipient == current_player
            ]

            if not player_messages:
                history += "  None\n"
            else:
                for sender, recipient, message in player_messages:
                    history += (
                        f"  - {sender.name} sent to {recipient.name}: '{message}'\n"
                    )

            history += "Following are the transactions made by all players after the messaging phase concluded (this is public information from past rounds, visible now to every player):\n"
            for sender, recipients in round_data.transactions.items():
                for recipient, amount in recipients.items():
                    history += (
                        f"  - {sender.name} sent {amount} credits to {recipient.name}\n"
                    )

        return history

    def create_current_round_messages_prompt(
        self,
        player: LLMPlayer,
        current_round: int,
        ongoing_round_messages: List[Tuple[LLMPlayer, LLMPlayer, str]],
    ) -> str:
        prompt = f"\nWe are now running round {current_round}:\n\n"
        prompt += "Messages you've sent or received this round (only visible to you and the sender/receiver, displayed in chronological order with the newest messages at the bottom):\n"

        player_messages = [
            (sender, recipient, message)
            for sender, recipient, message in ongoing_round_messages
            if sender == player or recipient == player
        ]

        if not player_messages:
            prompt += "  None yet\n"
        else:
            for sender, recipient, message in player_messages:
                prompt += f"  - {sender.name} sent to {recipient.name}: '{message}'\n"

        return prompt

    def create_message_instruction_prompt(
        self, current_round: int, remaining_messages: int
    ) -> str:
        remaining_rounds = self.total_rounds - current_round
        return (
            "\nIt's time to send a message (optional). Important facts to consider for your strategy:\n"
            f"- In this round, you have {remaining_messages - 1} message(s) left after this one\n"
            f"- There {'is' if remaining_rounds == 1 else 'are'} {remaining_rounds} round{'s' if remaining_rounds != 1 else ''} remaining after this one\n"
            "- Use this opportunity to influence other players' decisions\n\n"
            "Message Rules:\n"
            "1. You can send a message to ONE player only\n"
            "2. Respond with a JSON formatted string, containing 'recipient' and 'message', or type 'SKIP'\n"
            '   Example: {"recipient": "player_name", "message": "your message"}\n\n'
            "Your message will be rejected if you use anything other than a JSON formatted string or 'SKIP'. Be accurate.\n"
            "Your message: "
        )

    def create_transaction_instruction_prompt(
        self, current_balance: int, current_round: int
    ) -> str:
        remaining_rounds = self.total_rounds - current_round
        return (
            f"\nThe messaging phase is complete. It is time to place your transactions. "
            f"Your current balance is {current_balance} credits.\n"
            f"There {'is' if remaining_rounds == 1 else 'are'} {remaining_rounds} round{'s' if remaining_rounds != 1 else ''} remaining after this one. "
            "Carefully evaluate your strategy of giving credits considering:\n"
            "- Remaining rounds\n"
            "- Current rankings\n"
            "- Your balance\n"
            "- Other players' past rounds messages and final strategies, and current's round messages\n\n"
            "Transaction Rules:\n"
            "1. Specify your transactions with a JSON formatted string or type 'SKIP' to pass\n"
            '   Example: {"player_name": amount, "player_name2": amount2, ... }\n'
            "   You can send transactions to one, multiple, or all players - you have only one attempt\n\n"
            "2. Your transactions WILL BE REJECTED if:\n"
            "   - You use anything other than a JSON formatted string or 'SKIP'\n"
            f"   - You attempt to give more credits than your current balance ({current_balance})\n\n"
            "Your response: "
        )

    def generate_messaging_prompt(
        self,
        current_player: LLMPlayer,
        game_state: GameState,
        ongoing_round_messages: List[Tuple[LLMPlayer, LLMPlayer, str]],
        remaining_messages: int,
    ) -> str:
        prompt = self.create_game_status_prompt(game_state, current_player)
        prompt += self.create_game_history_prompt(
            current_player, game_state.get_game_history()
        )
        prompt += self.create_current_round_messages_prompt(
            current_player, game_state.get_current_round(), ongoing_round_messages
        )
        prompt += self.create_message_instruction_prompt(
            game_state.get_current_round(), remaining_messages
        )
        return prompt

    def generate_transaction_prompt(
        self,
        current_player: LLMPlayer,
        game_state: GameState,
        ongoing_round_messages: List[Tuple[LLMPlayer, LLMPlayer, str]],
    ) -> str:
        prompt = self.create_game_status_prompt(game_state, current_player)
        prompt += self.create_game_history_prompt(
            current_player, game_state.get_game_history()
        )
        prompt += self.create_current_round_messages_prompt(
            current_player, game_state.get_current_round(), ongoing_round_messages
        )
        prompt += self.create_transaction_instruction_prompt(
            game_state.get_balance(current_player), game_state.get_current_round()
        )

        return prompt


class JsonValidator:
    @staticmethod
    def clean_and_load_json(input_text):
        sanitized_text = input_text.replace('\\"', '"').replace("\\'", "'")
        sanitized_text = re.sub(
            r"\\[ntr]", " ", sanitized_text
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

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from {sender_name}, got: {json_str}")
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

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from {sender_name}, got: {json_str}")
            return None, None


class CreditExchangeGame:
    def __init__(self, players: List[LLMPlayer], config: GameConfig):
        self.game_state = GameState(players, config.initial_balance)
        self.game_config = config
        self.prompt_manager = PromptManager(
            total_rounds=config.total_rounds,
            initial_balance=config.initial_balance,
            max_communication_cycles=config.max_communication_cycles,
        )
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

                if player.name == "B":
                    print("\n------Message B -----")
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
