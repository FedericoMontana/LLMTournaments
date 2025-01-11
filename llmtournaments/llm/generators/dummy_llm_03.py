import random
from typing import Optional, List
from llmtournaments.llm.llm_interaction_base import LLMInteractionBase, LLMResponse
import json


class DummyLLMInteractionForCreditExchanges(LLMInteractionBase):
    """
    A dummy implementation of LLMInteractionBase for testing the CreditExchangeGame.
    """

    def __init__(
        self,
        player_name: str,
        other_players: List[str],
        initial_balance: int,
        system_prompt: Optional[str] = None,
        max_exchanges: Optional[int] = None,
    ) -> None:
        """
        Initializes the DummyLLMInteraction instance.

        Args:
            player_name (str): The name of this player.
            other_players (List[str]): List of names of other players in the game.
            initial_balance (int): Initial balance of the player.
            system_prompt (Optional[str]): The initial system prompt.
            max_exchanges (Optional[int]): The maximum number of conversation turns to keep in history.
        """
        super().__init__(system_prompt, max_exchanges)
        self.player_name = player_name
        self.other_players = other_players
        self.balance = initial_balance

    def _generate_response(self, user_input: str) -> str:
        """
        Generates a response based on the user input, distinguishing between messaging and transaction phases.

        Args:
            user_input (str): The user's message.

        Returns:
            str: A generated response.
        """
        if user_input.strip().endswith("Your message:"):
            return self._generate_message_response()
        elif user_input.strip().endswith("Your response:"):
            return self._generate_transaction_response()
        else:
            return "SKIP"

    def _generate_message_response(self) -> str:
        """
        Generates a random message response to send to one or more other players.

        Returns:
            str: A JSON formatted string with recipients and a message.
        """
        if random.random() < 0.1:  # 10% chance to skip sending a message
            return "SKIP"

        num_recipients = random.randint(1, len(self.other_players))
        recipients = random.sample(self.other_players, num_recipients)
        message = random.choice(
            [
                "Let's collaborate this round.",
                "How about a truce?",
                "Watch out for the big moves!",
                "Let's maximize our profits together!",
                "Thinking of forming an alliance?",
            ]
        )
        return json.dumps({"recipients": recipients, "message": message})

    def _generate_transaction_response(self) -> str:
        """
        Generates a random transaction response with possible credit exchanges,
        ensuring that the sum of all transactions does not exceed the player's balance.

        Returns:
            str: A JSON formatted string with transactions to other players.
        """
        available_players = list(self.other_players)
        random.shuffle(available_players)

        transactions = {}
        remaining_balance = self.balance

        for recipient in available_players:
            if remaining_balance <= 0:
                break

            max_amount = min(remaining_balance, 15)  # Cap each transaction
            if (
                max_amount > 0 and random.random() < 0.6
            ):  # 60% chance to send a transaction
                amount = random.randint(1, max_amount)
                transactions[recipient] = amount
                remaining_balance -= amount

        return json.dumps(transactions) if transactions else "SKIP"

    def __call__(self, user_input: str, **kwargs) -> LLMResponse:
        """
        Overrides the base class method to provide dummy responses.

        Args:
            user_input (str): The user's message.
            **kwargs: Additional keyword arguments (ignored in this implementation).

        Returns:
            LLMResponse: An object containing the generated response and a random generation time.
        """
        response = self._generate_response(user_input)
        dummy_generation_time = random.uniform(0.1, 1)
        return LLMResponse(response=response, generation_time=dummy_generation_time)
