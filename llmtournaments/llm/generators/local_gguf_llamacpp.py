# Implementation of the generator using llama_cpp interface
# this is for GGUF models from huggingface
# to see all the chat formats it supports: https://github.com/abetlen/llama-cpp-python/blob/main/llama_cpp/llama_chat_format.py

import logging
from typing import Optional
from llmtournaments.llm.llm_interaction_base import LLMInteractionBase
from llama_cpp import Llama

logger = logging.getLogger(__name__)


class Local_GGUF_LlamaCpp(LLMInteractionBase):
    """LLM Generator that uses a local Llama model for response generation."""

    def __init__(
        self,
        model_path: str,
        system_prompt: Optional[str] = None,
        max_exchanges: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize the LlamaCpp-based LLM generator.

        :param system_prompt: The initial system prompt or context for the conversation.
        :param model_path: Path to the local Llama model.
        :param max_exchanges: The maximum number of past conversation turns to keep.
        :param kwargs: Additional parameters for the Llama model.
        """
        super().__init__(system_prompt, max_exchanges)

        # Initialize the Llama model
        self.llm = Llama(
            model_path=model_path,
            # Read this about chat format: https://github.com/abetlen/llama-cpp-python/pull/1110
            # It's better to pass no parameter about chat_format, hoping the model has one in the GGUF
            # chat_format parameter is omitted as per the comment
            verbose=False,
            n_gpu_layers=-1,  # Utilize all available GPU layers
            **kwargs,
        )

    def _generate_response(self, **kwargs) -> str:
        """
        Generate a response from the Llama model based on the current conversation.

        :param kwargs: Additional parameters for the Llama `create_chat_completion` method.
        :return: The assistant's response as a string.
        """
        # Merge self.kwargs with the provided kwargs
        combined_kwargs = {**self.kwargs, **kwargs}

        # Generate the assistant's response using the Llama model
        llm_response = self.llm.create_chat_completion(
            self.conversation, **combined_kwargs
        )
        assistant_content = llm_response["choices"][0]["message"]["content"]

        return assistant_content
