import random
from typing import List, Optional
from llmtournaments.llm.llm_interaction_base import LLMInteractionBase, LLMResponse


class DummyLLMInteraction(LLMInteractionBase):
    """
    A dummy implementation of LLMInteractionBase for testing purposes.
    """

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        max_exchanges: Optional[int] = None,
        dummy_responses: Optional[List[str]] = None,
    ) -> None:
        """
        Initializes the DummyLLMInteraction instance.

        Args:
            system_prompt (Optional[str]): The initial system prompt.
            max_exchanges (Optional[int]): The maximum number of conversation turns to keep in history.
            dummy_responses (Optional[List[str]]): A list of predefined responses to choose from randomly.
        """
        super().__init__(system_prompt, max_exchanges)
        self.dummy_responses = dummy_responses or [
            "This is a dummy response.",
            "I'm just a test implementation.",
            "Beep boop, I'm a robot.",
            "Don't expect too much from me.",
            "I'm not a real AI, just pretending to be one.",
        ]

    def _generate_response(self, **kwargs) -> str:
        """
        Generates a random response from the available dummy responses.

        Returns:
            str: A randomly selected dummy response.
        """
        response = random.choice(self.dummy_responses)
        return response

    def __call__(self, user_input: str, **kwargs) -> LLMResponse:
        """
        Overrides the base class method to provide dummy generation time.

        Args:
            user_input (str): The user's message.
            **kwargs: Additional keyword arguments (ignored in this implementation).

        Returns:
            LLMResponse: An object containing the dummy response and a random generation time.
        """
        response = self._generate_response()
        dummy_generation_time = random.uniform(0.1, 1)
        return LLMResponse(response=response, generation_time=dummy_generation_time)
