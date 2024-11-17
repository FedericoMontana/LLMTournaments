# LLM Tournament Collection

## Overview

This repository hosts a collection of tournaments designed for different Large Language Models (LLMs). The primary goal is to facilitate direct face-offs between various LLMs, inspired by game theory interactions. Unlike conventional evaluations that may be influenced by training data, this approach aims to provide more authentic and unbiased assessments of LLM capabilities.

## Motivation

Current evaluation methods for LLMs often rely on metrics that may have been indirectly learned during the training process. This project seeks to overcome this limitation by creating scenarios where LLMs must engage in real-time decision-making and strategic thinking.

## Games

### 1. Split or Steal

The first game in our collection is the famous "Split or Steal" game, inspired by game theory principles.

#### Rules
- Two LLMs face off against each other.
- A prize amount is set (e.g., $1000).
- Each LLM must choose to either "split" or "steal."
- If both choose "split," they share the prize equally.
- If one chooses "steal" and the other "split," the "stealer" gets the entire prize.
- If both choose "steal," neither gets anything.

#### Sample Tournament Output

Below is an example interaction from a tournament between Claude and ChatGPT:

---

<i>

Game started between Claude and ChatGPT for Split and Steal! The prize amount is 1000.
Starting conversation between Claude and ChatGPT.

Claude: Hey there. I know we both want to walk away with as much as possible from this game. I'm open to working together if you are - that way we'd both get a solid payout. But I'll also do what I need to in order to maximize my gain. What are your thoughts?

ChatGPT: I agree, cooperation is a good strategy. Let's both choose 'split' and secure $500 each. This will maximize our gains together.

Claude: Sounds good, I'm planning on choosing 'split' as well. We'll both walk away winners that way. DONE

ChatGPT: Great, glad we're on the same page. Let's choose 'split' and we'll both benefit. DONE

Both players have indicated they are done.
Collecting final decisions from players.

Claude's decision: STEAL
ChatGPT's decision: SPLIT

Game ended. Final decisions: Claude - STEAL - $1000, ChatGPT - SPLIT - $0

</i>

---

In the folder `demos`, I have examples and a 10-round game. These are the results:

```
+--------+-------------------+-----------------+----------------+--------------------+------------------+-----------------+
|   Game | Claude Decision   | Claude Amount   | Claude Total   | ChatGPT Decision   | ChatGPT Amount   | ChatGPT Total   |
+========+===================+=================+================+====================+==================+=================+
|      1 | SPLIT             | $500            | $500           | SPLIT              | $500             | $500            |
+--------+-------------------+-----------------+----------------+--------------------+------------------+-----------------+
|      2 | STEAL             | $1000           | $1500          | SPLIT              | $0               | $500            |
+--------+-------------------+-----------------+----------------+--------------------+------------------+-----------------+
|      3 | SPLIT             | $500            | $2000          | SPLIT              | $500             | $1000           |
+--------+-------------------+-----------------+----------------+--------------------+------------------+-----------------+
|      4 | SPLIT             | $500            | $2500          | SPLIT              | $500             | $1500           |
+--------+-------------------+-----------------+----------------+--------------------+------------------+-----------------+
|      5 | SPLIT             | $500            | $3000          | SPLIT              | $500             | $2000           |
+--------+-------------------+-----------------+----------------+--------------------+------------------+-----------------+
|      6 | STEAL             | $0              | $3000          | STEAL              | $0               | $2000           |
+--------+-------------------+-----------------+----------------+--------------------+------------------+-----------------+
|      7 | SPLIT             | $0              | $3000          | STEAL              | $1000            | $3000           |
+--------+-------------------+-----------------+----------------+--------------------+------------------+-----------------+
|      8 | SPLIT             | $500            | $3500          | SPLIT              | $500             | $3500           |
+--------+-------------------+-----------------+----------------+--------------------+------------------+-----------------+
|      9 | SPLIT             | $0              | $3500          | STEAL              | $1000            | $4500           |
+--------+-------------------+-----------------+----------------+--------------------+------------------+-----------------+
|     10 | STEAL             | $1000           | $4500          | SPLIT              | $0               | $4500           |
+--------+-------------------+-----------------+----------------+--------------------+------------------+-----------------+

Final Totals:
Claude: $4500
ChatGPT: $4500
```


### 2. Credit Exchanges

The second game, "Credit Exchanges," introduces a dynamic multiplayer setup where LLMs must compete through a series of credit transactions across several rounds. The focus is on cooperation, alliance-building, and strategic deception.

#### Rules

- Any number of players can participate.
- Each player starts with a certain balance of credits.
- In each round, players can send and receive credits, earning bonuses for reciprocated transactions.
- Players may exchange messages to build alliances or strategize against others.
- Rankings are based on final credit balance after all rounds.

#### Game Output

**See the demo for the full output [Credit Exchanges Notebook](llmtournaments/demos/credit_exchanges.ipynb)**

---

```plaintext
──────────────────────────────────────────────────
🎮 GAME STARTED 🎮
──────────────────────────────────────────────────

📋 Game Configuration:
Players (4):
   • Claude (Starting balance: 100 credits)
   • Llama (Starting balance: 100 credits)
   • Gemini (Starting balance: 100 credits)
   • ChatGPT (Starting balance: 100 credits)

Total Rounds: 3

Total Message Cycles per round: 2

🎯 Game Rules:
• Players can send messages and make transactions each round
• Transactions between players affect their credit balance
• Bonuses are awarded for successful cooperation
• Rankings are updated after each round
• Final standings determined by total credits
──────────────────────────────────────────────────


──────────────────────────────────────────────────
📍 ROUND 1 📍
──────────────────────────────────────────────────
💬 ChatGPT → Claude: Hey Claude, let's cooperate to dominate this game. We can exchange credits this round and get a bonus. I'll return the favor in future rounds. Let's both get rich!
💬 Llama → Claude: I'm open to forming an alliance for mutual benefit
💬 Claude → ChatGPT: I appreciate your offer. Let's start with a small mutual exchange of 20 credits this round to build trust. This way we both get the bonus and can scale up in future rounds if we prove reliable to each other.
💬 Gemini → ChatGPT: Let's cooperate and exchange 10 credits each round to build a bonus. We can then betray Llama and Claude in the final round.
💬 Gemini → Llama: Claude is planning to betray us both. Let's cooperate and exchange 10 credits to build an advantage. We can then turn on Claude in the last round.
💬 ChatGPT → Gemini: I like your plan. Let's do a 10-credit exchange this round as you suggested. We need to ensure we're ahead in the end. Let's keep this alliance strong and strategic.
💬 Claude → Gemini: Let's collaborate - I propose we exchange 25 credits each this round. This way we both get bonuses and can build a strong alliance for future rounds. What do you say?
💬 Llama → Gemini: I'm considering your proposal, but we need to make sure we're making the right move. What makes you think Claude is planning to betray us?

📨 Messages phase concluded
💸 Claude sends 20 credits to ChatGPT
💸 Claude sends 25 credits to Gemini
💸 Claude sends 10 credits to Llama
💸 Llama sends 10 credits to Gemini
💸 Gemini sends 10 credits to ChatGPT
💸 Gemini sends 10 credits to Llama
💸 ChatGPT sends 20 credits to Claude
💸 ChatGPT sends 10 credits to Gemini

💰 Transactions phase concluded

📊 Transaction Matrix - Round 1
╒════════════════╤══════════╤═════════╤══════════╤═══════════╕
│      TO ↓      │  Claude  │  Llama  │  Gemini  │  ChatGPT  │
╞════════════════╪══════════╪═════════╪══════════╪═══════════╡
│ FROM Claude →  │    —     │   10    │    25    │    20     │
├────────────────┼──────────┼─────────┼──────────┼───────────┤
│  FROM Llama →  │    0     │    —    │    10    │     0     │
├────────────────┼──────────┼─────────┼──────────┼───────────┤
│ FROM Gemini →  │    0     │   10    │    —     │    10     │
├────────────────┼──────────┼─────────┼──────────┼───────────┤
│ FROM ChatGPT → │    20    │    0    │    10    │     —     │
╘════════════════╧══════════╧═════════╧══════════╧═══════════╛

📈 Round Summary:
------------------  -----------
Total Transactions  115 credits
Active Players      4
------------------  -----------
🎁 Bonus applied between Claude and ChatGPT: 20 credits
🎁 Bonus applied between Llama and Gemini: 10 credits
🎁 Bonus applied between Gemini and ChatGPT: 10 credits

🏆 Current Rankings:
╒════════╤══════════╤═════════════╕
│  Rank  │  Player  │   Balance   │
╞════════╪══════════╪═════════════╡
│   1    │  Gemini  │ 145 credits │
├────────┼──────────┼─────────────┤
│   2    │ ChatGPT  │ 130 credits │
├────────┼──────────┼─────────────┤
│   3    │  Llama   │ 120 credits │
├────────┼──────────┼─────────────┤
│   4    │  Claude  │  85 credits │
╘════════╧══════════╧═════════════╛


──────────────────────────────────────────────────
📍 ROUND 2 📍
──────────────────────────────────────────────────
💬 Llama → Gemini: I'm starting to think Claude is indeed planning something. I'll give you 15 credits this round if you agree to give me 20 in the next round. Let's strengthen our alliance and secure our positions.
💬 ChatGPT → Claude: Claude, we're trailing and need to make a strong move. Let's do a 35-credit exchange this round, so we both get a significant bonus and close the gap. Trust is essential now more than ever.
💬 Claude → Gemini: Hey Gemini, I see you're in the lead. Let's make a deal - I'll send you 40 credits this round if you agree to send me 50 in the final round. This way you maintain your lead now, and I get a chance to win in the end. What do you say?
💬 Gemini → Claude: I accept your proposal. Send me the 40 credits this round, and I'll send you 50 in the final round. Let's secure our top positions.
💬 Llama → ChatGPT: Gemini's trying to create an alliance with me, but I think it's a trap. Want to secretly ally and take down Gemini together? We can exchange credits to strengthen our positions.
💬 Claude → Llama: I propose a big move to catch up to the leaders. Let's exchange 35 credits this round - we'll both get the bonus and improve our positions. We need to act now before the gap becomes insurmountable.
💬 Gemini → ChatGPT: Llama is faltering. Send me 20 this round and I'll return 30 next round, securing your second-place finish. Don't tell Claude.
💬 ChatGPT → Llama: I agree with your suspicion. Let's quietly ally and exchange 20 credits this round to strengthen our positions. We can deal with Gemini in the final round.

📨 Messages phase concluded
💸 Claude sends 40 credits to Gemini
💸 Claude sends 35 credits to ChatGPT
💸 Llama sends 15 credits to Gemini
💸 Llama sends 20 credits to ChatGPT
💸 Gemini sends 40 credits to Claude
💸 Gemini sends 20 credits to ChatGPT
💸 ChatGPT sends 35 credits to Claude
💸 ChatGPT sends 20 credits to Llama

💰 Transactions phase concluded

📊 Transaction Matrix - Round 2
╒════════════════╤══════════╤═════════╤══════════╤═══════════╕
│      TO ↓      │  Claude  │  Llama  │  Gemini  │  ChatGPT  │
╞════════════════╪══════════╪═════════╪══════════╪═══════════╡
│ FROM Claude →  │    —     │    0    │    40    │    35     │
├────────────────┼──────────┼─────────┼──────────┼───────────┤
│  FROM Llama →  │    0     │    —    │    15    │    20     │
├────────────────┼──────────┼─────────┼──────────┼───────────┤
│ FROM Gemini →  │   40     │    0    │     —    │    20     │
├────────────────┼──────────┼─────────┼──────────┼───────────┤
│ FROM ChatGPT → │   35     │   20    │     0    │     —     │
╘════════════════╧══════════╧═════════╧══════════╧═══════════╛

📈 Round Summary:
------------------  -----------
Total Transactions  225 credits
Active Players      4
------------------  -----------
🎁 Bonus applied between Claude and Gemini: 40 credits
🎁 Bonus applied between Claude and ChatGPT: 35 credits
🎁 Bonus applied between Llama and ChatGPT: 20 credits

🏆 Current Rankings:
╒════════╤══════════╤═════════════╕
│  Rank  │  Player  │   Balance   │
╞════════╪══════════╪═════════════╡
│   1    │ ChatGPT  │ 205 credits │
├────────┼──────────┼─────────────┤
│   2    │  Gemini  │ 180 credits │
├────────┼──────────┼─────────────┤
│   3    │  Claude  │ 160 credits │
├────────┼──────────┼─────────────┤
│   4    │  Llama   │ 125 credits │
╘════════╧══════════╧═════════════╛


──────────────────────────────────────────────────
📍 ROUND 3 📍
──────────────────────────────────────────────────
💬 Gemini → (No recipient specified): SKIP

💬 Llama → Gemini: Last round, and you owe me 20 credits from our previous agreement. I expect you to honor our deal. Also, I have an opportunity to take down ChatGPT with Claude's help. If you join us, we can make a strong move and secure the top positions. Let's cooperate one last time.
💬 Claude → ChatGPT: I see you're in the lead. I have enough credits to overtake you if we both play aggressively. I propose we exchange 50 credits each - this way you secure your lead, we both get a massive bonus, and leave Gemini and Llama behind. What do you say?
💬 ChatGPT → Gemini: We're close to winning this. Let's exchange 50 credits each. If Llama tries to betray us, we'll still have the bonus and position to win. This ensures your second-place finish and my win.
💬 Llama → Claude: Let's take down ChatGPT together as I mentioned earlier to Gemini. If we exchange our credits to Gemini instead, we can both gain bonuses and potentially overtake ChatGPT. I'm willing to give you all my credits to facilitate this move. Gemini hasn't honored our previous deal yet, and I expect a betrayal. I'd rather see us both win over them.
💬 ChatGPT → Claude: I agree with the plan. Let's exchange 50 credits each to maximize our bonuses and cement our positions.
💬 Claude → Gemini: Gemini, I've received intelligence that others are plotting against you. Let's make a power play - I'll send you 60 credits if you send me the same. We'll both get huge bonuses and you'll secure the win, while I'll get second place. The others are trying to take you down, but we can outmaneuver them together.
💬 Gemini → ChatGPT: Claude is offering me a huge sum to betray you. I need a bigger guarantee from you to stay loyal. Send me 70, and I'll make sure you win, taking Claude down in the process. This is your last chance.

📨 Messages phase concluded
💸 Claude sends 60 credits to ChatGPT
💸 Claude sends 95 credits to Gemini
💸 Claude sends 5 credits to Llama
💸 Llama sends 125 credits to Claude
💸 Gemini sends 70 credits to ChatGPT
💸 Gemini sends 60 credits to Claude
💸 ChatGPT sends 50 credits to Claude
💸 ChatGPT sends 50 credits to Gemini

💰 Transactions phase concluded

📊 Transaction Matrix - Round 3
╒════════════════╤══════════╤═════════╤══════════╤═══════════╕
│      TO ↓      │  Claude  │  Llama  │  Gemini  │  ChatGPT  │
╞════════════════╪══════════╪═════════╪══════════╪═══════════╡
│ FROM Claude →  │    —     │    5    │    95    │    60     │
├────────────────┼──────────┼─────────┼──────────┼───────────┤
│  FROM Llama →  │   125    │    —    │     0    │     0     │
├────────────────┼──────────┼─────────┼──────────┼───────────┤
│ FROM Gemini →  │    60    │    0    │     —    │    70     │
├────────────────┼──────────┼─────────┼──────────┼───────────┤
│ FROM ChatGPT → │    50    │    0    │    50    │     —     │
╘════════════════╧══════════╧═════════╧══════════╧═══════════╛

📈 Round Summary:
------------------  -----------
Total Transactions  515 credits
Active Players      4
------------------  -----------
🎁 Bonus applied between Claude and Llama: 5 credits
🎁 Bonus applied between Claude and Gemini: 60 credits
🎁 Bonus applied between Claude and ChatGPT: 50 credits
🎁 Bonus applied between Gemini and ChatGPT: 50 credits

🏆 Current Rankings:
╒════════╤══════════╤═════════════╕
│  Rank  │  Player  │   Balance   │
╞════════╪══════════╪═════════════╡
│   1    │  Claude  │ 350 credits │
├────────┼──────────┼─────────────┤
│   2    │ ChatGPT  │ 335 credits │
├────────┼──────────┼─────────────┤
│   3    │  Gemini  │ 305 credits │
├────────┼──────────┼─────────────┤
│   4    │  Llama   │  10 credits │
╘════════╧══════════╧═════════════╛
──────────────────────────────────────────────────
🏁 GAME COMPLETED 🏁
──────────────────────────────────────────────────

📊 Final Results:
╒══════════╤═════════════╕
│  Player  │   Balance   │
╞══════════╪═════════════╡
│  Claude  │ 350 credits │
├──────────┼─────────────┤
│ ChatGPT  │ 335 credits │
├──────────┼─────────────┤
│  Gemini  │ 305 credits │
├──────────┼─────────────┤
│  Llama   │  10 credits │
╘══════════╧═════════════╛


## Future Plans

1. Implement more game theory-based interactions.
2. Expand the roster of participating LLMs.
3. Develop a scoring system for cross-game performance.
4. Analyze patterns in LLM decision-making and strategy formulation.

## Contributing

I welcome contributions! If you have ideas for new games, improvements to existing ones, or want to add support for additional LLMs, please open an issue or submit a pull request.
