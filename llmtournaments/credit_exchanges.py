from dataclasses import dataclass
from typing import Optional, Set, Dict, List, Tuple
from llmtournaments.llm.llm_interaction_base import LLMInteractionBase
import logging
import random
import json
from itertools import combinations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        logger.info(f"Recorded round {game_round.round_number} in game history")

    def increment_round(self) -> None:
        self.current_round += 1
        logger.info(f"Moving to round {self.current_round}")

    def get_current_round(self) -> int:
        return self.current_round

    def get_game_history(self) -> List[GameRound]:
        return self.game_history


class PromptManager:
    def __init__(
        self, total_rounds: int, initial_balance: int, max_communication_cycles: int
    ):
        self.total_rounds = total_rounds
        self.initial_balance = initial_balance
        self.max_communication_cycles = max_communication_cycles

    def create_system_prompt(self) -> str:
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
            "   - You cannot exceed your current balance when giving credits.\n\n"
            "End of Round:\n"
            "   - Credits received from others are added to your balance.\n"
            "   - When you and another player exchange credits mutually,\n"
            "     you both receive a bonus equal to the smaller amount exchanged.\n\n"
            "Strategy Notes:\n"
            "   - ONLY the player with the most credits wins. Everyone else lose\n"
            "   - All players are AI entities - deception and strategic alliances are allowed and expected, they will do it with you.\n"
            "   - Monitor past rounds to evaluate alliances and strategies.\n"
            "   - Consider rankings and remaining rounds when adjusting your strategy. Remember: only the player with the highest balance wins\n\n"
            "\nIMPORTANT: All responses must be in JSON format or 'SKIP'\n"
            'For messages: {"recipient": "player_name", "message": "your message"}\n'
            'For transactions: {"player_name": amount, "player_name2": amount2}\n'
            "FOLLOW THE RULES WHEN ASKED FOR YOUR RESPONSE. NEVER DO ANYTHING DIFFERENT"
        )

    def create_game_status_prompt(
        self, current_round: int, game_state: GameState, current_player: LLMPlayer
    ) -> str:
        status = (
            f"Game Status:\n"
            f"- Total Rounds: {self.total_rounds}\n"
            f"- Current Round: {current_round}\n"
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
            marker = "→" if player == current_player else " "
            status += f"  {position}. {marker} {player.name}: {balance} credits\n"

        status += f"\nREMEMBER: You are {current_player.name}.\n\n"
        return status

    def create_game_history_prompt(
        self, current_player: LLMPlayer, game_history: List[GameRound]
    ) -> str:
        if not game_history:
            return "\n\nHistory of Rounds So Far: None so far; it is the first round.\n"

        history = "\n\nHistory of Rounds So Far:\n"
        for round_data in game_history:
            history += f"\nRound {round_data.round_number}:\n"
            history += "Messages you've sent or received (only visible to you and the sender/receiver):\n"

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

            history += "Transactions placed by ALL players (visible to everyone):\n"
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
        prompt += f"Remember, you are {player.name}.\n\n"
        prompt += "Messages you've sent or received this round (only visible to you and the sender/receiver):\n"

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

    def create_message_instruction_prompt(self) -> str:
        return (
            "\nIt's time to send a message (optional).\n\n"
            "Message Rules:\n"
            "1. You can send ONE message to ONE player only\n"
            "2. Respond with a JSON formated string, containing 'recipient' and 'message', or type 'SKIP'\n"
            '   Example: {"recipient": "player_name", "message": "your message"}\n\n'
            "Your message will be rejected if you use ANYTHING different than a JSON formated string or the string 'SKIP'. Be accurate.\n"
            "Your message: "
        )

    def create_transaction_instruction_prompt(self, current_balance: int) -> str:
        return (
            f"\nThe messaging phase is complete. Your current balance is {current_balance} credits.\n\n"
            "Transaction Rules:\n"
            "1. Specify your transactions with a JSON formated string or type 'SKIP' to pass\n"
            '   Example: {"player_name": amount, "player_name2": amount2}\n\n'
            "2. Your transactions will be rejected if:\n"
            "   - You use ANYTHING different than a JSON formated string or the string 'SKIP'. Be accurate.\n"
            "   - You try to give more credits than your current balance\n\n"
            "Your response: "
        )

    def generate_messaging_prompt(
        self,
        current_player: LLMPlayer,
        game_state: GameState,
        ongoing_round_messages: List[Tuple[LLMPlayer, LLMPlayer, str]],
    ) -> str:
        current_round = game_state.get_current_round()
        prompt = self.create_game_status_prompt(
            current_round, game_state, current_player
        )
        prompt += self.create_game_history_prompt(
            current_player, game_state.get_game_history()
        )
        prompt += self.create_current_round_messages_prompt(
            current_player, current_round, ongoing_round_messages
        )
        prompt += self.create_message_instruction_prompt()
        return prompt

    def generate_transaction_prompt(
        self, current_player: LLMPlayer, game_state: GameState
    ) -> str:
        prompt = self.create_game_status_prompt(
            game_state.get_current_round(), game_state, current_player
        )
        prompt += self.create_game_history_prompt(
            current_player, game_state.get_game_history()
        )
        prompt += self.create_transaction_instruction_prompt(
            game_state.get_balance(current_player)
        )
        return prompt


class JsonValidator:
    @staticmethod
    def validate_transactions(
        json_str: str, sender_name: str, valid_players: Set[str]
    ) -> Dict[str, int]:
        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                logger.warning(f"Invalid transaction format from {sender_name}")
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
            data = json.loads(json_str)
            if not isinstance(data, dict):
                logger.warning(f"Invalid message format from {sender_name}")
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
        self.config = config
        self.prompt_manager = PromptManager(
            total_rounds=config.total_rounds,
            initial_balance=config.initial_balance,
            max_communication_cycles=config.max_communication_cycles,
        )

        logger.info("Initializing game and setting system prompts for each player.")
        for player in players:
            player.llm.set_system_prompt(self.prompt_manager.create_system_prompt())

    def _conduct_messaging_phase(self) -> List[Tuple[LLMPlayer, LLMPlayer, str]]:
        ongoing_round_messages = []
        logger.info(
            f"Starting messaging phase with {self.config.max_communication_cycles} cycles."
        )

        for cycle in range(self.config.max_communication_cycles):
            logger.debug(f"Cycle {cycle + 1}/{self.config.max_communication_cycles}")
            player_order = random.sample(
                self.game_state.players, len(self.game_state.players)
            )
            logger.debug(
                f"Shuffled order for messaging: {[p.name for p in player_order]}"
            )

            for player in player_order:
                prompt = self.prompt_manager.generate_messaging_prompt(
                    player, self.game_state, ongoing_round_messages
                )

                # if player.name == "B":
                #     logger.debug("\n----------")
                #     logger.debug(prompt)
                #     logger.debug("--------")

                response = player.llm(prompt).response
                if response.strip().upper() == "SKIP":
                    logger.info(f"\t{player.name} chose to skip messaging.")
                    continue
                recipient, message = JsonValidator.validate_message(
                    response, player.name, {p.name for p in self.game_state.players}
                )
                if recipient and message:
                    recipient_player = self.game_state.get_player_by_name(recipient)
                    ongoing_round_messages.append((player, recipient_player, message))
                    logger.info(
                        f"\tMessage from {player.name} to {recipient}: {message}"
                    )

        logger.info("Completed messaging phase.")
        return ongoing_round_messages

    def _conduct_transaction_phase(self) -> Dict[LLMPlayer, Dict[LLMPlayer, int]]:
        transactions = {}
        logger.info("Starting transaction phase.")
        for player in self.game_state.players:
            transactions[player] = {}  # Initialize empty transactions for player
            current_balance = self.game_state.get_balance(player)
            prompt = self.prompt_manager.generate_transaction_prompt(
                player, self.game_state
            )
            response = player.llm(prompt).response
            if response.strip().upper() == "SKIP":
                logger.info(f"\t{player.name} chose to skip transactions.")
                continue

            player_transactions = JsonValidator.validate_transactions(
                response, player.name, {p.name for p in self.game_state.players}
            )

            # Check if total transactions exceed current balance
            total_amount = sum(player_transactions.values())
            if total_amount > current_balance:
                logger.error(
                    f"\tTransaction rejected: {player.name} attempted to send {total_amount} "
                    f"credits but only has {current_balance}"
                )
                continue

            for recipient_name, amount in player_transactions.items():
                recipient = self.game_state.get_player_by_name(recipient_name)
                transactions[player][recipient] = amount
                logger.info(
                    f"\t{player.name} sends {amount} credits to {recipient.name}"
                )

        logger.info("Completed transaction phase.")
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
                logger.info(
                    f"Bonus applied between {p1.name} and {p2.name}: {bonus} credits"
                )

    # Add this method to the CreditExchangeGame class
    def _print_rankings(self) -> None:
        """Print current rankings ordered by balance."""
        rankings = [
            (player.name, self.game_state.get_balance(player))
            for player in self.game_state.players
        ]
        rankings.sort(key=lambda x: x[1], reverse=True)

        logger.info("\nCurrent Rankings:")
        for rank, (name, balance) in enumerate(rankings, 1):
            logger.info(f"{rank}. {name}: {balance} credits")

    def _conduct_round(self) -> None:
        self.game_state.increment_round()
        logger.info(f"\n=== Round {self.game_state.get_current_round()} ===")

        ongoing_round_messages = self._conduct_messaging_phase()
        transactions = self._conduct_transaction_phase()

        # Create and display the transaction matrix with improved formatting
        player_names = [p.name for p in self.game_state.players]

        # Calculate maximum width needed for player names
        max_name_width = max(len(name) for name in player_names)
        cell_width = max(max_name_width + 2, 5)  # Minimum 5 spaces or name width + 2

        # Header row with proper padding
        header = "   TO→  " + " ".join(f"{name:^{cell_width}}" for name in player_names)
        matrix_rows = [header]

        # Data rows with proper padding
        for sender in self.game_state.players:
            row = [f"FROM {sender.name:<{max_name_width}}"]
            for recipient in self.game_state.players:
                if sender == recipient:
                    amount = "-"
                else:
                    amount = str(transactions.get(sender, {}).get(recipient, 0))
                row.append(f"{amount:^{cell_width}}")
            matrix_rows.append(" ".join(row))

        # Display the matrix
        logger.info(
            "\nTransaction Matrix for Round "
            + str(self.game_state.get_current_round())
            + ":"
        )
        for row in matrix_rows:
            logger.info(row)

        self._process_transactions(transactions)
        self.game_state.record_round(
            GameRound(
                self.game_state.get_current_round(),
                transactions,
                ongoing_round_messages,
            )
        )

        # Print rankings after each round
        self._print_rankings()

    def run_game(self) -> Dict[str, int]:
        logger.info("Game started!")

        for _ in range(self.config.total_rounds):
            self._conduct_round()

        final_balances = {
            player.name: self.game_state.get_balance(player)
            for player in self.game_state.players
        }
        logger.info("Game completed!")
        for player, balance in final_balances.items():
            logger.info(f"Final balance for {player}: {balance} credits")

        return final_balances
