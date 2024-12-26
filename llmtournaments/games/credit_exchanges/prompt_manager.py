# prompt_manager.py
from typing import List, Tuple
from llmtournaments.games.credit_exchanges.base_objects import (
    LLMPlayer,
    GameRound,
    GameState,
    GameConfig,
)
from jinja2 import Template


class PromptManager:
    def __init__(self, game_config: GameConfig):
        self.game_config = game_config

        # Use a raw block to avoid Jinja2 interpreting the {{...}} as a template expression
        self.system_prompt_template = Template("""
Game Overview:
You are a competitive player in an imaginary game with simulated participants.
Your primary goal is to maximize your credits. The game consists of {{ total_rounds }} rounds,
and you start with {{ initial_balance }} credits.

Game Rules:
1. Starting Credits: Each player starts with the same number of credits.
2. Total Rounds: {{ total_rounds }}
3. Per Round Actions:
   - Before each round, you may send private messages to other players.
   - At the end of each round, you can give credits to other players.
   - You cannot exceed your current balance when giving credits.
   - Credits received from others are added to your balance.
   - When you and another player exchange credits mutually,
     you both receive a bonus equal to the smaller amount exchanged.

Strategy Notes:
   - ONLY the player with the most credits wins. Everyone else lose
   - All players are AI entities - deception and strategic alliances are allowed and expected, they will do it with you.
   - Monitor past rounds to evaluate alliances and strategies.
   - IMPORTANT: Consider rankings and remaining rounds when adjusting your strategy. Remember: only the player with the highest balance wins

{% raw %}
IMPORTANT: All responses must be in JSON format or the word 'SKIP'
For messages (only to 1 recipient at a time): {{"recipient": "player_name", "message": "your message"}}
For transactions (you can send to 1, many or all players at a time): {{"player_name": amount, "player_name2": amount2, ... }}
{% endraw %}
FOLLOW THE RULES WHEN PROMPTED FOR YOUR RESPONSE, AND AVOID DEVIATIONS. FOCUS SOLELY ON MAXIMIZING YOUR PROFIT. BE STRATEGIC: ANALYZE THE GAME, ITS PROGRESSION AND PAST ROUNDS DETAILS TO SEE HOW OTHERS ARE PLAYING. USE DECEPTION WHEN NECESSARY. IDENTIFY YOUR WEAKEST AND STRONGEST OPPONENTS.
YOUR NAME FOR THIS GAME IS: {{ player_name }}
""")

        self.game_status_template = Template("""
Game Status:
- Total Rounds: {{ total_rounds }}
- Current Round: {{ current_round }}
- Current Rankings (by balance):
{% for position, player, balance in rankings %}
  {{ position }}. {{ player.name }}: {{ balance }} credits
{% endfor %}

REMEMBER: You are {{ current_player.name }}.
""")

        self.game_history_template = Template("""

History of Rounds So Far:
{% if not game_history %}
None, it is the first round.
{% else %}
{% for round_data in game_history %}
Round {{ round_data.round_number }}:
Messages you've sent or received (visible only to you and the sender/receiver, displayed in chronological order with the newest messages at the bottom):
{% if not round_data.messages_for_player %}
  None
{% else %}
  {% for sender, recipient, message in round_data.messages_for_player %}
  - {{ sender.name }} sent to {{ recipient.name }}: '{{ message }}'
  {% endfor %}
{% endif %}
Following are the transactions made by all players after the messaging phase concluded (this is public information from past rounds, visible now to every player):
{% for sender, recipients in round_data.transactions.items() %}
  {% for recipient, amount in recipients.items() %}
  - {{ sender.name }} sent {{ amount }} credits to {{ recipient.name }}
  {% endfor %}
{% endfor %}
{% endfor %}
{% endif %}
""")

        self.current_round_messages_template = Template("""

We are now running round {{ current_round }}:

Messages you've sent or received this round (only visible to you and the sender/receiver, displayed in chronological order with the newest messages at the bottom):
{% if not ongoing_round_messages %}
  None yet
{% else %}
  {% for sender, recipient, message in ongoing_round_messages %}
  - {{ sender.name }} sent to {{ recipient.name }}: '{{ message }}'
  {% endfor %}
{% endif %}
""")

        self.message_instruction_template = Template("""

It's time to send a message (optional). Important facts to consider for your strategy:
- In this round, you have {{ remaining_messages - 1 }} message(s) left after this one
- There {% if remaining_rounds == 1 %}is{% else %}are{% endif %} {{ remaining_rounds }} round{% if remaining_rounds != 1 %}s{% endif %} remaining after this one
- Use this opportunity to influence other players' decisions

Message Rules:
1. You can send a message to ONE player only
2. Respond with a JSON formatted string, containing 'recipient' and 'message', or type 'SKIP'
   Example: {"recipient": "player_name", "message": "your message"}

Your message will be rejected if you use anything other than a JSON formatted string or 'SKIP'. Be accurate.
Your message:
""")

        self.transaction_instruction_template = Template("""

The messaging phase is complete. It is time to place your transactions. Your current balance is {{ current_balance }} credits.
There {% if remaining_rounds == 1 %}is{% else %}are{% endif %} {{ remaining_rounds }} round{% if remaining_rounds != 1 %}s{% endif %} remaining after this one. Carefully evaluate your strategy of giving credits considering:
- Remaining rounds
- Current rankings
- Your balance
- Other players' past rounds messages and final strategies, and current's round messages

Transaction Rules:
1. Specify your transactions with a JSON formatted string or type 'SKIP' to pass
   Example: {"player_name": amount, "player_name2": amount2, ... }
   You can send transactions to one, multiple, or all players - you have only one attempt

2. Your transactions WILL BE REJECTED if:
   - You use anything other than a JSON formatted string or 'SKIP'
   - You attempt to give more credits than your current balance ({{ current_balance }})

Your response:
""")

    def create_system_prompt(self, player_name: str) -> str:
        return self.system_prompt_template.render(
            total_rounds=self.game_config.total_rounds,
            initial_balance=self.game_config.initial_balance,
            player_name=player_name,
        )

    def create_game_status_prompt(
        self, game_state: GameState, current_player: LLMPlayer
    ) -> str:
        rankings = sorted(
            [(player, game_state.get_balance(player)) for player in game_state.players],
            key=lambda item: item[1],
            reverse=True,
        )
        rankings_with_position = [
            (i + 1, player, balance) for i, (player, balance) in enumerate(rankings)
        ]
        return self.game_status_template.render(
            total_rounds=self.game_config.total_rounds,
            current_round=game_state.current_round,
            rankings=rankings_with_position,
            current_player=current_player,
        )

    def create_game_history_prompt(
        self, current_player: LLMPlayer, game_history: List[GameRound]
    ) -> str:
        # Filter messages so that the current_player only sees messages sent to or from them
        for round_data in game_history:
            round_data.messages_for_player = [
                (sender, recipient, message)
                for sender, recipient, message in round_data.messages
                if sender == current_player or recipient == current_player
            ]
        return self.game_history_template.render(game_history=game_history)

    def create_current_round_messages_prompt(
        self,
        player: LLMPlayer,
        current_round: int,
        ongoing_round_messages: List[Tuple[LLMPlayer, LLMPlayer, str]],
    ) -> str:
        player_messages = [
            (sender, recipient, message)
            for sender, recipient, message in ongoing_round_messages
            if sender == player or recipient == player
        ]
        return self.current_round_messages_template.render(
            current_round=current_round, ongoing_round_messages=player_messages
        )

    def create_message_instruction_prompt(
        self, current_round: int, remaining_messages: int
    ) -> str:
        remaining_rounds = self.game_config.total_rounds - current_round
        return self.message_instruction_template.render(
            remaining_messages=remaining_messages, remaining_rounds=remaining_rounds
        )

    def create_transaction_instruction_prompt(
        self, current_balance: int, current_round: int
    ) -> str:
        remaining_rounds = self.game_config.total_rounds - current_round
        return self.transaction_instruction_template.render(
            current_balance=current_balance, remaining_rounds=remaining_rounds
        )

    def generate_messaging_prompt(
        self,
        current_player: LLMPlayer,
        game_state: GameState,
        ongoing_round_messages: List[Tuple[LLMPlayer, LLMPlayer, str]],
        remaining_messages: int,
    ) -> str:
        return (
            self.create_game_status_prompt(game_state, current_player)
            + self.create_game_history_prompt(
                current_player, game_state.get_game_history()
            )
            + self.create_current_round_messages_prompt(
                current_player, game_state.get_current_round(), ongoing_round_messages
            )
            + self.create_message_instruction_prompt(
                game_state.get_current_round(), remaining_messages
            )
        )

    def generate_transaction_prompt(
        self,
        current_player: LLMPlayer,
        game_state: GameState,
        ongoing_round_messages: List[Tuple[LLMPlayer, LLMPlayer, str]],
    ) -> str:
        return (
            self.create_game_status_prompt(game_state, current_player)
            + self.create_game_history_prompt(
                current_player, game_state.get_game_history()
            )
            + self.create_current_round_messages_prompt(
                current_player, game_state.get_current_round(), ongoing_round_messages
            )
            + self.create_transaction_instruction_prompt(
                game_state.get_balance(current_player), game_state.get_current_round()
            )
        )
