"""
Base class for interacting with Large Language Models (LLMs).

This module defines abstract classes and data structures to facilitate
interaction with various LLM implementations while maintaining a conversation
history and handling responses.

Classes:
LLMResponse: Encapsulates the LLM's response and the time taken to generate it.
LLMInteractionBase: Abstract base class providing a common interface for LLM interactions.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict

# Configure the logger for this module
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    """
    Represents a response from a Large Language Model (LLM).

    Attributes:
        response (str): The actual text response from the LLM.
        generation_time (float): The time taken to generate the response in seconds.
    """

    response: str
    generation_time: float


class LLMInteractionBase(ABC):
    """
    Abstract base class for interacting with Large Language Models (LLMs).

    Provides a common interface for interacting with different LLM implementations.
    Subclasses must implement the `_generate_response` method.
    """

    DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        max_exchanges: Optional[int] = None,
        **kwargs,
    ) -> None:
        """
        Initializes an instance of LLMInteractionBase.

        Args:
            system_prompt (Optional[str]): The initial system prompt to set the context for the conversation.
                                           If None, a default prompt is used.
            max_exchanges (Optional[int]): The maximum number of conversation turns to keep in history.
                                           If None, the entire history is retained.
            **kwargs: Additional keyword arguments to store for later use.

        Raises:
            ValueError: If max_exchanges is negative.
        """
        if max_exchanges is not None and max_exchanges < 0:
            raise ValueError("max_exchanges must be non-negative or None.")

        self._conversation: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt or self.DEFAULT_SYSTEM_PROMPT}
        ]
        self.max_exchanges: Optional[int] = max_exchanges
        self.kwargs = kwargs  # Store additional keyword arguments

        logger.debug(
            f"Initializing LLMInteractionBase with system_prompt: '{self._conversation[0]['content']}' "
            f"and max_exchanges: {max_exchanges}, additional params: {kwargs}"
        )

    def set_system_prompt(self, system_prompt: str) -> None:
        """
        Sets or updates the system prompt for the conversation.

        Args:
            system_prompt (str): The system prompt to set or update.
        """
        self._conversation[0] = {"role": "system", "content": system_prompt}
        logger.debug(f"System prompt updated to: '{system_prompt}'")

    @abstractmethod
    def _generate_response(self, **kwargs) -> str:
        """
        Generates a response from the LLM.

        Subclasses must implement this method to handle the actual interaction with the specific LLM.

        Args:
            **kwargs: Additional keyword arguments specific to the LLM implementation. These will overwrite the ones in init.

        Returns:
            str: The generated response from the LLM.

        Raises:
            NotImplementedError: If not implemented by the subclass.
        """
        raise NotImplementedError(
            "Subclasses must implement the _generate_response method."
        )

    def __call__(self, user_input: str, **kwargs) -> LLMResponse:
        """
        Sends a user message to the LLM and returns the response.

        Args:
            user_input (str): The user's message.
            **kwargs: Additional keyword arguments to pass to the underlying LLM implementation.

        Returns:
            LLMResponse: An object containing the LLM's response and generation time.
        """
        logger.debug(f"Received user input: '{user_input}'")
        self._conversation.append({"role": "user", "content": user_input})

        start_time = time.perf_counter()

        try:
            logger.debug(f"Sending to the model: {self._conversation}")

            response = self._generate_response(**kwargs)

            generation_time = time.perf_counter() - start_time
            logger.debug(
                f"Generated response ({generation_time:.4f} seconds): '{response}'"
            )
        except Exception:
            raise

        self._conversation.append({"role": "assistant", "content": response})
        self._truncate_messages()

        return LLMResponse(response=response, generation_time=generation_time)

    def _truncate_messages(self) -> None:
        """Truncates the conversation history based on max_exchanges."""
        if self.max_exchanges is not None:
            num_messages_to_keep = (
                self.max_exchanges * 2
            )  # Each exchange has 2 messages

            if num_messages_to_keep == 0:
                # Keep only the system prompt
                self._conversation = self._conversation[:1]
            else:
                # Exclude the system prompt and take the last N messages
                last_messages = self._conversation[1:][-num_messages_to_keep:]
                self._conversation = self._conversation[:1] + last_messages
            logger.debug(
                f"Conversation history truncated to the last {self.max_exchanges} exchanges."
            )

    @property
    def conversation(self) -> List[Dict[str, str]]:
        """
        Returns a copy of the current conversation history.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the conversation history.
        """
        return self._conversation.copy()
