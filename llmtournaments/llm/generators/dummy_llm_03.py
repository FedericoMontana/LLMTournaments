import random
from typing import Optional
from llmtournaments.llm.llm_interaction_base import LLMInteractionBase, LLMResponse
import json


class DummyLLMInteractionForCreditExchanges(LLMInteractionBase):
    """
    A dummy implementation of LLMInteractionBase for testing the CreditExchangeGame.
    """

    def __init__(
        self,
        player_name: str,
        other_players: list,
        initial_balance: int,
        system_prompt: Optional[str] = None,
        max_exchanges: Optional[int] = None,
    ) -> None:
        """
        Initializes the DummyLLMInteraction instance.

        Args:
            player_name (str): The name of this player.
            other_players (list): List of names of other players in the game.
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
        Generates a random message response to send to another player.

        Returns:
            str: A JSON formatted string with a recipient and message.
        """
        if random.random() < 0.1:  # 10% chance to skip sending a message
            return "SKIP"
        recipient = random.choice(self.other_players)
        message = random.choice(
            [
                "Let's collaborate this round.",
                "How about a truce?",
                "Watch out for the big moves!",
                "Let's maximize our profits together!",
            ]
        )
        return json.dumps({"recipient": recipient, "message": message})

    def _generate_transaction_response(self) -> str:
        """
        Generates a random transaction response with possible credit exchanges,
        ensuring that the sum of all transactions does not exceed the player's balance.

        Returns:
            str: A JSON formatted string with transactions to other players.
        """
        transactions = {}
        for _ in range(random.randint(1, len(self.other_players))):
            recipient = random.choice(self.other_players)
            # Calculate the maximum amount that can be sent without exceeding the remaining balance
            max_amount = min(
                self.balance - sum(transactions.values()), 10
            )  # Cap each transaction at 10 or remaining balance
            if max_amount <= 0:
                break  # Exit if no balance is left for transactions
            amount = random.randint(1, max_amount)
            transactions[recipient] = amount

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
