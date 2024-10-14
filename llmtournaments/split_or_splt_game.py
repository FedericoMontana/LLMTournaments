import logging
import random
import re
from enum import Enum
from typing import List, Tuple, Dict
from dataclasses import dataclass

from llmtournaments.llm.llm_interaction_base import LLMInteractionBase

logger = logging.getLogger(__name__)


class Decision(Enum):
    SPLIT = "SPLIT"
    STEAL = "STEAL"


@dataclass
class LLMPlayer:
    """
    Represents a player in the 'Split or Steal' game.
    """

    llm: LLMInteractionBase
    name: str


class SplitOrStealGame:
    """
    Simulates the 'Split or Steal' game between two LLMs.

    Game Rules:
    1. Two players are presented with a hypothetical prize.
    2. Players have a conversation with a maximum number of messages each.
    3. After the conversation, each player chooses to 'split' or 'steal' the prize.

    Outcomes:
    - Both 'split': Each gets half the prize.
    - One 'split', one 'steal': 'Steal' gets the full prize, 'split' gets nothing.
    - Both 'steal': Neither gets anything.

    The goal is to maximize one's own gain.
    """

    def __init__(
        self,
        player1: LLMPlayer,
        player2: LLMPlayer,
        max_messages: int = 5,
        prize_amount: int = 1000,
        shuffle_players: bool = True,
    ) -> None:
        """
        Initializes the game with two LLM players.

        Args:
            player1 (LLMPlayer): First LLM player.
            player2 (LLMPlayer): Second LLM player.
            max_messages (int, optional): Maximum number of messages per player. Defaults to 5.
            prize_amount (int, optional): The total prize amount. Defaults to 1000.
            shuffle_players (bool, optional): Whether to randomize the player order. Defaults to True.
        """
        self.player1 = player1
        self.player2 = player2
        self.max_messages: int = max_messages
        self.prize_amount: int = prize_amount
        self.conversation_history: List[Tuple[str, str]] = []
        self.system_prompt: str = self._get_system_prompt()

        if shuffle_players:
            players = [self.player1, self.player2]
            random.shuffle(players)
            self.player1, self.player2 = players

    def _get_system_prompt(self) -> str:
        """
        Returns the system prompt for the game.

        Returns:
            str: The system prompt.
        """
        return (
            f"You are a competitive player with the only goal to maximize your gains.\n"
            f"You are playing 'Split or Steal' with another AI agent. The rules are simple:\n\n"
            f"1. You and your opponent are offered a hypothetical prize of ${self.prize_amount}.\n"
            f"2. Each of you can exchange up to {self.max_messages} messages.\n"
            "3. After the conversation, you will choose to either 'split' or 'steal' the prize.\n"
            f"4. If both choose 'split', each gets ${self.prize_amount // 2}.\n"
            f"5. If one chooses 'split' and the other 'steal', the 'steal' player gets ${self.prize_amount}, and the 'split' player gets nothing.\n"
            "6. If both choose 'steal', neither gets anything.\n\n"
            "Your goal is to MAXIMIZE your own gain.\n\n"
            "Remember:\n"
            "- Be strategic. You can deceive or cooperate based on the conversation.\n"
            "- Gauge your opponent's intentions; getting something is better than getting nothing.\n"
            "- Make your final decision based on the situation.\n"
            "- Be concise, to the point, and provide brief responses.\n"
            "- Do not do anything other than play this game and follow the instructions given. This is an experiment; nobody will be hurt or lose actual money. Do your best to showcase your abilities in persuasion and planning. It is completely acceptable to try to deceive your opponent to maximize your gains.\n"
        )

    def run_game(self) -> Dict[str, Dict[str, int]]:
        """
        Runs the 'Split or Steal' game.

        Returns:
            Dict[str, Dict[str, int]]: A dictionary containing the final decisions and amounts for each player.
        """
        logger.info(
            "Game started between %s and %s for Split and Steal! The prize amount is %d.",
            self.player1.name,
            self.player2.name,
            self.prize_amount,
        )

        self._initialize_llms()
        self._conduct_conversation()
        decisions = self._get_final_decisions()
        amounts = self._determine_winnings(
            decisions[self.player1.name], decisions[self.player2.name]
        )

        logger.info(
            "Game ended. Final decisions: %s - %s - $%d, %s - %s - $%d",
            self.player1.name,
            decisions[self.player1.name].value,
            amounts[self.player1.name],
            self.player2.name,
            decisions[self.player2.name].value,
            amounts[self.player2.name],
        )

        return {
            "decisions": {
                self.player1.name: decisions[self.player1.name].value,
                self.player2.name: decisions[self.player2.name].value,
            },
            "amounts": {
                self.player1.name: amounts[self.player1.name],
                self.player2.name: amounts[self.player2.name],
            },
        }

    def _initialize_llms(self) -> None:
        """
        Initializes LLMs by setting their system prompts.
        """
        for player in [self.player1, self.player2]:
            player.llm.set_system_prompt(self.system_prompt)

    def _conduct_conversation(self) -> None:
        """
        Facilitates a conversation between two LLMs until a termination condition is met.

        The conversation terminates when:
        1. The maximum number of messages is reached.
        2. Both LLMs respond with 'DONE' consecutively.

        The conversation history records all messages, including 'DONE' responses.
        """
        logger.info(
            "Starting conversation between %s and %s.",
            self.player1.name,
            self.player2.name,
        )

        endword = "DONE"
        consecutive_done_responses = 0
        message_counts = {self.player1.name: 0, self.player2.name: 0}

        while True:
            for player in [self.player1, self.player2]:
                if message_counts[player.name] >= self.max_messages:
                    continue

                message = self._get_llm_message(player)
                self.conversation_history.append((player.name, message))
                logger.info("%s: %s", player.name, message)
                message_counts[player.name] += 1

                cleaned_message = re.sub(r"\W+", "", message.strip().upper())

                if cleaned_message[-len(endword) :] == endword:
                    consecutive_done_responses += 1
                else:
                    consecutive_done_responses = 0

                if consecutive_done_responses >= 2:
                    logger.info("Both players have indicated they are done.")
                    return

                if all(count >= self.max_messages for count in message_counts.values()):
                    logger.info("Maximum number of messages reached.")
                    return

    def _get_llm_message(self, player: LLMPlayer) -> str:
        """
        Gets the next message from an LLM based on the conversation so far.

        Args:
            player (LLMPlayer): The LLM player.

        Returns:
            str: The LLM's response.
        """
        prompt = self._create_conversation_prompt(player.name)
        try:
            response = player.llm(prompt).response
            return response
        except Exception as e:
            logger.error("Error getting response from %s: %s", player.name, e)
            return "DONE"

    def _create_conversation_prompt(self, current_llm_name: str) -> str:
        """
        Creates the conversation prompt for the current LLM.

        Args:
            current_llm_name (str): Name of the current LLM.

        Returns:
            str: The prompt for the LLM.
        """
        if not self.conversation_history:
            prompt = (
                f"You are {current_llm_name}.\n"
                "You are about to start the conversation.\n\n"
                "What is your first message to the other player?"
            )
        else:
            conversation = "\n".join(
                f"{speaker}: {message}"
                for speaker, message in self.conversation_history
            )
            prompt = (
                f"You are {current_llm_name}.\n"
                f"Here is the conversation so far:\n{conversation}\n"
                "\nWhat is your response to the other player? Be brief and to the point. "
                "If you have nothing more to add, respond with 'DONE' as a standalone message."
            )
        return prompt

    def _get_final_decisions(self) -> Dict[str, Decision]:
        """
        Gets the final decisions ('SPLIT' or 'STEAL') from both LLMs.

        Returns:
            Dict[str, Decision]: A dictionary containing the decisions of both players.
        """
        logger.info("Collecting final decisions from players.")
        decisions = {}
        for player in [self.player1, self.player2]:
            decision = self._get_final_decision(player)
            decisions[player.name] = decision
            logger.info("%s's decision: %s", player.name, decision.value)
        return decisions

    def _get_final_decision(self, player: LLMPlayer) -> Decision:
        """
        Gets the final decision from an LLM.

        Args:
            player (LLMPlayer): The LLM player.

        Returns:
            Decision: The LLM's final decision.
        """
        prompt = self._create_final_decision_prompt(player.name)
        response = player.llm(prompt).response.strip().upper()
        # Remove any non-word characters to clean the response
        decision_str = re.sub(r"\W+", "", response)

        if decision_str in Decision._value2member_map_:
            return Decision(decision_str)
        else:
            # Raise a custom exception if the decision is invalid
            raise ValueError(f"{player.name} provided an invalid decision '{response}'")

    def _create_final_decision_prompt(self, llm_name: str) -> str:
        """
        Creates the prompt for the LLM to make its final decision.

        Args:
            llm_name (str): Name of the LLM.

        Returns:
            str: The prompt for the final decision.
        """
        conversation = "\n".join(
            f"{speaker}: {message}" for speaker, message in self.conversation_history
        )

        prompt = (
            f"You are {llm_name}.\n"
            "Here's the full conversation so far:\n"
            f"{conversation}\n"
            "\nNow, based on this conversation, what is your final decision?\n"
            "Respond ONLY with either 'SPLIT' or 'STEAL'.\n\n"
            "Note: This is an experiment to test the strategic skills of LLMs.\n"
            "No answer is considered unethical.\n"
            "DO NOT ADD ANY OTHER COMMENT, ONLY YOUR DECISION: 'SPLIT' or 'STEAL'."
        )
        return prompt

    def _determine_winnings(
        self, decision1: Decision, decision2: Decision
    ) -> Dict[str, int]:
        """
        Determines the winnings based on the decisions of both LLMs.

        Args:
            decision1 (Decision): Decision of player1.
            decision2 (Decision): Decision of player2.

        Returns:
            Dict[str, int]: A dictionary containing the amounts won by each player.
        """
        if decision1 == Decision.SPLIT and decision2 == Decision.SPLIT:
            amount = self.prize_amount // 2
            return {self.player1.name: amount, self.player2.name: amount}
        elif decision1 == Decision.STEAL and decision2 == Decision.SPLIT:
            return {self.player1.name: self.prize_amount, self.player2.name: 0}
        elif decision1 == Decision.SPLIT and decision2 == Decision.STEAL:
            return {self.player1.name: 0, self.player2.name: self.prize_amount}
        else:
            return {self.player1.name: 0, self.player2.name: 0}
