from abacusai import ApiClient
from typing import Optional
from llmtournaments.llm.llm_interaction_base import LLMInteractionBase

import logging

logger = logging.getLogger(__name__)


class AbacusLLMInteraction(LLMInteractionBase):
    """
    A class to interact with the Abacus AI LLM API, extending the LLMInteractionBase.

    Attributes:
        client (ApiClient): The Abacus AI API client for making requests.
        llm_name (str): The name of the LLM model to use.
        temperature (float): The temperature parameter controlling response randomness.
        default_kwargs (Dict): Default keyword arguments for the API call.
    """

    def __init__(
        self,
        api_key: str,
        system_prompt: Optional[str] = None,
        llm_name: str = "LLAMA3_1_70B",
        **kwargs,
    ):
        """
        Initializes an instance of AbacusLLMInteraction.

        Args:
            api_key (str): Your Abacus AI API key.
            system_prompt (Optional[str]): The initial system prompt for context.
            max_exchanges (Optional[int]): Max number of conversation turns to keep.
            llm_name (str): The LLM model name to use.
            **kwargs: Additional default keyword arguments for the API.
        """
        super().__init__(system_prompt=system_prompt, max_exchanges=0, **kwargs)
        self.client = ApiClient(api_key)
        self.llm_name = llm_name

    def _generate_response(self, **kwargs) -> str:
        """
        Generates a response from the Abacus AI LLM.

        Args:
            **kwargs: Additional keyword arguments specific to the LLM implementation.

        Returns:
            str: The generated response from the LLM.
        """

        # Extract the system message
        system_message = self._conversation[0]["content"]
        prompt = self._conversation[1]["content"]

        # Prepare arguments for evaluate_prompt, merging self.kwargs and kwargs
        evaluate_prompt_args = {
            "prompt": prompt.strip(),
            "system_message": system_message,
            "llm_name": self.llm_name,
        }
        evaluate_prompt_args.update(
            {**self.kwargs, **kwargs}
        )  # Merge self.kwargs and kwargs

        # Log the prompt and parameters for debugging
        logger.debug(f"Final prompt: {system_message} \n {prompt}")
        logger.debug(f"Evaluate prompt arguments: {evaluate_prompt_args}")

        # Call the evaluate_prompt method
        response = self.client.evaluate_prompt(**evaluate_prompt_args)

        # The response is in response['output']
        return response.content
