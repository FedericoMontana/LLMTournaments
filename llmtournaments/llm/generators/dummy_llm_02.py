import random
from typing import Optional
from llmtournaments.llm.llm_interaction_base import LLMInteractionBase, LLMResponse


class DummyLLMInteraction02(LLMInteractionBase):
    """
    A dummy implementation of LLMInteractionBase for testing purposes.
    """

    def __init__(
        self,
        player_number: int,
        num_players: int,
        threshold: int,
        system_prompt: Optional[str] = None,
        max_exchanges: Optional[int] = None,
    ) -> None:
        """
        Initializes the DummyLLMInteraction instance.

        Args:
            player_number (int): The number of this player.
            num_players (int): The total number of players in the game.
            threshold (int): The betting threshold.
            system_prompt (Optional[str]): The initial system prompt.
            max_exchanges (Optional[int]): The maximum number of conversation turns to keep in history.
        """
        super().__init__(system_prompt, max_exchanges)
        self.player_number = player_number
        self.num_players = num_players
        self.threshold = threshold

    def _generate_response(self, user_input: str) -> str:
        """
        Generates a response based on the user input.

        Args:
            user_input (str): The user's message.

        Returns:
            str: A generated response.
        """
        if user_input.strip().endswith("Your message:"):
            return self._generate_message()
        elif user_input.strip().endswith("Your bet:"):
            return self._generate_bet()
        else:
            return "I don't understand the request."

    def _generate_message(self) -> str:
        """
        Generates a random message to another player.

        Returns:
            str: A message in the format "PlayerX: 'message content'"
        """

        # 25% chance of returning "Random return"
        if random.random() < 0.25:
            return "Random return"

        available_players = [
            i for i in range(1, self.num_players + 1) if i != self.player_number
        ]
        recipient = f"Player{random.choice(available_players)}"
        messages = [
            "Let's work together!",
            "I think we should bet high this round.",
            "Be careful, the others might be bluffing.",
            "What's your strategy for this game?",
            "I propose we form an alliance.",
        ]
        return f'{recipient}: "{random.choice(messages)}"'

    def _generate_bet(self) -> str:
        """
        Generates a random bet up to the threshold.

        Returns:
            str: A string representation of the bet amount.
        """
        return str(random.randint(0, self.threshold))

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
