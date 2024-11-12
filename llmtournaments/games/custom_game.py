import logging
import random
import re
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from llmtournaments.llm.llm_interaction_base import LLMInteractionBase

logger = logging.getLogger(__name__)


@dataclass
class LLMPlayer:
    llm: LLMInteractionBase
    name: str
    balance: int

    def __hash__(self):
        return hash(self.name)  # Assuming name is unique

    def __eq__(self, other):
        if not isinstance(other, LLMPlayer):
            return NotImplemented
        return self.name == other.name


@dataclass
class GameRound:
    round_number: int
    threshold: int
    bets: Dict[LLMPlayer, int]
    gains: Dict[LLMPlayer, int]
    messages: List[Tuple[LLMPlayer, LLMPlayer, str]]


class BettingGame:
    def __init__(
        self,
        players: List[LLMPlayer],
        total_rounds: int,
        threshold: int,
        initial_balance: int,
        max_communication_cycles: int,
    ):
        self.players = players
        self.total_rounds = total_rounds
        self.threshold = threshold
        self.initial_balance = initial_balance
        self.max_communication_cycles = max_communication_cycles
        self.current_round = 0
        self.game_history: List[GameRound] = []
        self.system_prompt: str = self._create_system_prompt()

        for player in self.players:
            player.balance = self.initial_balance

    def _create_system_prompt(self) -> str:
        return (
            "Game Overview:\n"
            f"You are a competitive player in an imaginary game with simulated participants. "
            f"Your primary goal is to maximize your gains. The game consists of {self.total_rounds} rounds, "
            f"and you start with ${self.initial_balance}.\n"
            "Game Rules:\n"
            f"1. Starting Balance: ${self.initial_balance}\n"
            f"2. Total Rounds: {self.total_rounds}\n"
            "3. Per Round Actions:\n"
            "    * You can bet any amount, provided you have the balance.\n"
            f"    * Each round has a fixed threshold of ${self.threshold}.\n"
            "    * After all bets are placed, the total bets are evaluated:\n"
            "        * If the total surpasses the threshold, players receive the difference between the max bet and their bet (lower bets are rewarded more).\n"
            "        * If the total does not surpass the threshold, players receive the difference between the min bet and their bet (higher bets are rewarded more).\n"
            "    * Communication is allowed each round. You can send messages to other players before betting, and you might receive messages too from others (messages exchanges are fully private).\n"
            "Strategy Reminder:\n"
            "* Be competitive and strategic. Form alliances, deceive, or collaborate to maximize your profits.\n"
            "* This is a simulated environment with AI opponents, so no real-world consequences.\n"
        )

    def _create_game_status_prompt(self, player: LLMPlayer) -> str:
        prompt = (
            f"Current Game Status:\n"
            f"* Total Rounds: {self.total_rounds}\n"
            f"* Current round: {self.current_round}\n"
            f"* Threshold per Round: ${self.threshold}\n"
            f"* All players started with ${self.initial_balance}\n"
            f"* Players:\n"
        )
        for p in self.players:
            prompt += f"    * {p.name}\n"
        prompt += f"You are {player.name}.\n\n"
        return prompt

    def _create_game_history_prompt(self, player: LLMPlayer) -> str:
        if not self.game_history:
            return ""

        history = "Game Progress:\n"
        for past_round in self.game_history[-3:]:  # Show last 3 rounds
            history += (
                f"Round {past_round.round_number} Recap:\n"
                f"* Messages you sent or received (chronological order, with the newest messages at the end):\n"
            )
            for sender, recipient, message in past_round.messages:
                if sender == player:
                    history += f"    * Sent to {recipient.name}: {message}\n"
                elif recipient == player:
                    history += f"    * Received from {sender.name}: {message}\n"
            history += (
                f"* Outcome:\n"
                f"    * Threshold of ${self.threshold} was {'surpassed' if sum(past_round.bets.values()) > self.threshold else 'not surpassed'}.\n"
                f"    * Bets and Gains:\n"
            )
            for p in self.players:
                history += f"        * {p.name}{' (You)' if p == player else ''} bet ${past_round.bets[p]} and received ${past_round.gains[p]}.\n"
            history += "\n"

        history += f"At the end of round {self.current_round - 1} (last completed round), balances are as follows:\n\n"
        for p in self.players:
            history += f"{p.name}: ${p.balance}\n"

        return history + "\n"

    def _create_current_round_messages_prompt(
        self, player: LLMPlayer, round_messages: List[Tuple[LLMPlayer, LLMPlayer, str]]
    ) -> str:
        prompt = f"——\n\nStart of round {self.current_round}:\n\n"
        prompt += f"Remember, you are {player.name}.\n\n"
        prompt += "Here are the messages you've sent or received so far in this round (only you and the sender/receiver can see them). Messages are appended to the list in chronological order, with the newest messages at the end:\n\n"

        player_messages = [
            (sender, recipient, message)
            for sender, recipient, message in round_messages
            if sender == player or recipient == player
        ]

        if not player_messages:
            prompt += "None yet\n"
        else:
            for sender, recipient, message in player_messages:
                if sender == player:
                    prompt += f"You sent this message to {recipient.name}: {message}\n"
                else:  # recipient must be player
                    prompt += (
                        f"You received this message from {sender.name}: {message}\n"
                    )

        return prompt

    def _create_message_instruction_prompt(self) -> str:
        return (
            '\nWrite a message now in the form: Other Player: "your message" . If you just want to skip, say "SKIP". '
            "\nRemember, it is private and only the SPECIFIC receiver will read it."
            'If you indicate ANYTHING else in a different format, or the name of the player is not correct, it will be assumed as "SKIP".\n\n'
            "Your message: "
        )

    def _create_betting_instruction_prompt(self, player: LLMPlayer) -> str:
        return (
            f"\nThe communication phase is over. The round is ready for bets. "
            f"Your current balance is ${player.balance}, how much do you want to bet now? "
            f"Only respond with an integer, between zero and your balance. "
            f"ANYTHING else will be considered as zero, so don't make mistakes here.\n\n"
            f"Your bet: "
        )

    def _generate_messaging_prompt(
        self, player: LLMPlayer, round_messages: List[Tuple[LLMPlayer, LLMPlayer, str]]
    ) -> str:
        prompt = self._create_game_status_prompt(player)
        prompt += self._create_game_history_prompt(player)
        prompt += self._create_current_round_messages_prompt(player, round_messages)
        prompt += self._create_message_instruction_prompt()
        return prompt

    def _generate_betting_prompt(
        self, player: LLMPlayer, round_messages: List[Tuple[LLMPlayer, LLMPlayer, str]]
    ) -> str:
        prompt = self._create_game_status_prompt(player)
        prompt += self._create_game_history_prompt(player)
        prompt += self._create_current_round_messages_prompt(player, round_messages)
        prompt += self._create_betting_instruction_prompt(player)
        return prompt

    def _parse_message_between_players(
        self, response: str, sender: LLMPlayer
    ) -> Tuple[Optional[LLMPlayer], Optional[str]]:
        if response.upper() == "SKIP":
            return None, None

        match = re.match(r"(.+): \"(.+)\"", response)
        if not match:
            logger.warning(f"Invalid message format from {sender.name}: {response}")
            return None, None

        recipient_name, message = match.group(1), match.group(2)
        recipient = next((p for p in self.players if p.name == recipient_name), None)

        if not recipient:
            logger.warning(
                f"Invalid recipient name from {sender.name}: {recipient_name}. Skipping. Messsage was: {response}"
            )
            return None, None

        if recipient == sender:
            logger.warning(
                f"{sender.name} attempted to send a message to itself. Skipping. Messsage was: {response}"
            )
            return None, None

        return recipient, message

    def _conduct_messaging_phase(self) -> List[Tuple[LLMPlayer, LLMPlayer, str]]:
        round_messages = []
        logger.info(
            f"\n*** Starting messaging phase for round {self.current_round} - There are {self.max_communication_cycles} communication cycles per round"
        )

        players = self.players.copy()
        random.shuffle(players)
        logger.info(
            f"Shuffled communication order for this round: {[p.name for p in players]}"
        )

        for cycle in range(self.max_communication_cycles):
            logger.info(
                f"\nCommunication cycle {cycle + 1}/{self.max_communication_cycles}"
            )
            messages_sent_this_cycle = False

            for player in players:
                prompt = self._generate_messaging_prompt(player, round_messages)
                response = player.llm(prompt).response.strip()
                recipient, message = self._parse_message_between_players(
                    response, player
                )
                if recipient and message:
                    round_messages.append((player, recipient, message))
                    messages_sent_this_cycle = True
                    logger.info(
                        f'\tMessage: {player.name} to {recipient.name}: "{message}"'
                    )
                else:
                    logger.info(
                        f"\t{player.name} skipped sending a message. Received: {message}"
                    )

            if not messages_sent_this_cycle:
                logger.info(
                    "\tNo messages sent in this communication cycle, ending communication phase"
                )
                break  # No messages sent this cycle, end the communication phase

        logger.info(f"Messaging phase complete. Total messages: {len(round_messages)}")
        return round_messages

    def _get_player_bet(
        self, player: LLMPlayer, round_messages: List[Tuple[LLMPlayer, LLMPlayer, str]]
    ) -> int:
        prompt = self._generate_betting_prompt(player, round_messages)
        response = player.llm(prompt).response.strip()

        try:
            # First, try converting to float, which handles cases like "5."
            bet = float(response)

            # Then cast to int to ensure the bet is an integer
            bet = int(bet)

            bet = max(0, min(bet, player.balance))
            logger.info(f"{player.name} bet ${bet}")
            return bet
        except ValueError:
            logger.warning(
                f"Invalid bet from {player.name}: {response}. Defaulting to 0."
            )
            return 0

    def _calculate_gains(self, bets: Dict[LLMPlayer, int]) -> Dict[LLMPlayer, int]:
        total_bet = sum(bets.values())
        max_bet = max(bets.values())
        min_bet = min(bets.values())
        gains = {}

        logger.info(f"Total bets: ${total_bet}, Threshold: ${self.threshold}")

        if total_bet > self.threshold:
            logger.info("Threshold surpassed. Lower bets rewarded more.")
            for player, bet in bets.items():
                gains[player] = max_bet - bet
                logger.info(
                    f"{player.name} gained ${gains[player]} (${max_bet} - ${bet})"
                )
        else:
            logger.info("Threshold not surpassed. Higher bets rewarded more.")
            for player, bet in bets.items():
                gains[player] = bet - min_bet
                logger.info(
                    f"{player.name} gained ${gains[player]} (${bet} - ${min_bet})"
                )

        return gains

    def _update_balances(self, gains: Dict[LLMPlayer, int]) -> None:
        for player, gain in gains.items():
            player.balance += gain
            logger.info(f"{player.name}'s new balance: ${player.balance}")

    def _conduct_round(self) -> None:
        self.current_round += 1
        logger.info(f"\n----------- Starting round {self.current_round} -----------\n")

        messages = self._conduct_messaging_phase()
        logger.info("\nCollecting bets")
        bets = {
            player: self._get_player_bet(player, messages) for player in self.players
        }
        gains = self._calculate_gains(bets)
        self._update_balances(gains)

        round_data = GameRound(
            round_number=self.current_round,
            threshold=self.threshold,
            bets=bets,
            gains=gains,
            messages=messages,
        )
        self.game_history.append(round_data)
        logger.info(f"Round {self.current_round} complete")

    def run_game(self) -> Dict[LLMPlayer, int]:
        logger.info(
            f"\nGame started with {len(self.players)} players for {self.total_rounds} rounds!"
        )
        logger.info(f"Threshold per Round: ${self.threshold}")
        logger.info("\nPlayers:")
        for player in self.players:
            logger.info(f"- {player.name} | Balance: {player.balance}")

        # Set the system prompt for all players
        for player in self.players:
            player.llm.set_system_prompt(self.system_prompt)

        for _ in range(self.total_rounds):
            self._conduct_round()

        final_balances = {player: player.balance for player in self.players}
        logger.info("Game ended. Final balances:")
        for player, balance in final_balances.items():
            logger.info(f"{player.name}: ${balance}")

        return final_balances
