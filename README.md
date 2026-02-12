# SpeechShapingLayer
## Speech Shaping Layer script for Home Assistant 

### This script is for PERSONAL USE

# Let`s go
- SpeechShapingLayer script is NOT dependent on the LLM model.
- It will work with any model that accepts plain text and returns plain text.

But let’s break it down properly.

# 🧠 What Script Actually Does
1. Takes a message
2. Converts it into SSML
3. Wraps everything in: ```<speak> ... </speak>```

5. Sends it to:
```
hass.services.call(
    "conversation",
    "process",
    {"text": final_output, "agent_id": agent_id}
)
```

So the LLM is only receiving:
```<speak>...SSML...</speak>```

The AI model is NOT generating the SSML, the script is generating it.

# ✅ Install in Home Assistant

- Make sure you have installed ```Pyscript``` from HACS, in your HA
- Download python script hyperalive.py from here and place it in your ```/homeassistant/pyscript``` folder.
- Click on script to edit inside and modify this agent line to yours ```agent_id="conversation.kira_local",``` ( mine is called `conversation.kira_local`) this need to be replaced with your current agent.
- After replace restart HA, the script will start working with the agent set inside

# 🔎 So What Determines Compatibility?

Compatibility depends entirely on:

1️⃣ The Home Assistant conversation integration

and

2️⃣ The agent you selected (agent_id)

Example:
agent_id="conversation.kira_local"

# RuLL: 
The agent must:

- Accept input text

- Return text

- Not break on XML/SSML content

# ✅ Will It Work With:

It will work with ollama

- Ollama models accept raw text

- They don’t reject XML

- They will just treat <speak> as text

The script does NOT require model-side SSML understanding.

# 🚨 Important Detail

The LLM is NOT synthesizing speech.

EdgeTTS (or whatever TTS backend you use) is the one that must support: 
```<prosody>

<break>

<amazon:effect>

<speak>
```
If your TTS supports SSML → you’re fine.

The LLM model does NOT need to support SSML at all.

# 🎯 When Would It NOT Work?

It would break if:

- The model strips XML tags

- The agent sanitizes or escapes XML

- The conversation integration filters ```< >```

- The model tries to "fix" your SSML

Example of breaking behavior:
If the model rewrites:

```<speak>Hello</speak>```


into:

```Sure! <speak>Hello</speak>```


That would corrupt your output.

# ⚠️ Only Avoid

Models that:

- Auto-format output heavily

- Add markdown formatting

- Insert explanations automatically

- Sanitize XML

But most instruct models behave.

# 🧠 Big Clarification

Script is a speech shaping layer.

It does NOT depend on:

- Model intelligence

- Model size

- Model architecture

- Model training data

It only depends on:

- Whether HA conversation agent passes the text through correctly.


_____________________________________________________________________________________________________________

# 🎛️ Kira Voice Cheat Sheet: emotion_level vs Features

| `emotion_level` | Intensity multiplier | Expected Behavior    | Soft Swears | Laughter / Giggles | Whispers / Sighs | Micro-breaths / Prosody            |
| --------------- | -------------------- | -------------------- | ----------- | ------------------ | ---------------- | ---------------------------------- |
| **0.2**         | Very low             | Almost deadpan       | Very rare   | Almost none        | Almost none      | Very subtle                        |
| **0.4**         | Low                  | Quiet & calm         | Rare        | Occasional         | Occasional       | Slight pitch / rate variation      |
| **0.5**         | Moderate             | Mildly expressive    | Sometimes   | Sometimes          | Sometimes        | Noticeable, still subtle           |
| **0.7**         | Balanced             | Natural, lively      | Occasional  | Frequent           | Frequent         | Clear pitch slides & micro-breaths |
| **0.85**        | High                 | Very expressive      | Likely      | Frequent           | Frequent         | Strong prosody variations          |
| **1.0**         | Maximum              | Full emotional range | Often       | Very frequent      | Very frequent    | Strongest pitch, rate, breaths     |

# 🧩 How It Works Internally

- `sentence_intensity = base_intensity * emotion_level` → scales everything per sentence.

- Thresholds for random features ( like swears >0.9, underbreath laugh >0.75 ) are applied after scaling.

- Micro-breaths, prosody shifts, pitch slides are multiplied directly by `emotion_level`.

- Semantic Kiss & Touch Layer can still add small increments (+0.08–0.12) per sentence, but with `0.7` it stays realistic.

# ✅ Recommendation

- Use 0.7 as default → balanced, expressive voice for normal HA interactions

- Drop to 0.4–0.5 for quiet, subtle moods (like “calm”)

- Raise to 0.85–1.0 if you want “playful” or “intimate” mode with swears, giggles, and full expressivity

_____________________________________________________________________________________________________________

<img width="710" height="943" alt="Screenshot 2026-02-12 125123" src="https://github.com/user-attachments/assets/3a8f3aa0-0ea5-4aa3-a395-1b4461fb8c57" />

_____________________________________________________________________________________________________________

[Hope you will enjoy it]
