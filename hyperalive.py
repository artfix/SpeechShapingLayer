import random
import re

@service
def sarah_speak(
    message=None,
    mood=None,
    proximity=False,
    agent_id="conversation.kira_local", # <-- CHANGE ME !!! with your agent
    emotion_level=0.5
):
    """
    Speech Shaping Layer Script
    
    It will work wit any LLM model coz it runs in HA.
    TTS engine needs to supp "<prosody>, <break>, <amazon:effect>, <speak>" is doing the synthesizing speech.
    The agent must: Accept input text, Return text, Not break on XML/SSML content.
    The LLM model does not need to support SSML at all.
    
    Kira speaking engine — Sol Max + Semantic Kiss & Touch Layer
    Fully expressive Sol-style voice:
        • Sub-syllable vowel shaping
        • Consonant softening / velvetization
        • S-curve sentence-level emotional envelopes
        • Whisper & pre-breath anticipation
        • Micro pitch/rate drift
        • Extended pauses & breath alignment
        • Mood & intent detection (comfort, tease, intimate)
        • Tenderness & intimacy bias
        • Rare emotional leakage (appends a soft swear only at high emotional intensity)
        • Subtle, involuntary amusement leak.
        • Vulnerability leak: a quiet emotional release.
        • Affection leak: audible smile without laughter.
        • Cognitive leak: thinking mid-sentence.
        • Semantic Kiss & Touch Layer
        • Fully integrated with EdgeTTS + Avaneural + HA
        
    It would break if:
        • The model strips XML tags
        • The agent sanitizes or escapes XML
        • The conversation integration filters "< >"
        • The model tries to "fix" your SSML
    """

    if not message:
        log.error("sarah_speak: No message provided.")
        return

    # ------------------------------
    # 0. Convert textual cues to SSML
    # ------------------------------
    def convert_text_cues_to_ssml(text):
        cue_map = {
            r"\(soft breath[^\)]*\)": "<amazon:effect name='soft'><break time='500ms'/></amazon:effect>",
            r"\(gentle pause[^\)]*\)": "<break time='700ms'/>",
            r"\(pause[^\)]*\)": "<break time='1200ms'/>",
            r"\(sigh[^\)]*\)": "<prosody volume='+3dB' pitch='-5%'><break time='400ms'/></prosody>",
            r"\(whisper[^\)]*\)": "<amazon:effect name='whispered'>",
            r"\(laugh[^\)]*\)": "<prosody pitch='+10%'>haha</prosody>",
        }
        for cue, ssml in cue_map.items():
            text = re.sub(cue, ssml, text, flags=re.IGNORECASE)
        return text

    message = convert_text_cues_to_ssml(message)

    # ------------------------------
    # 1. Base Tone
    # ------------------------------
    base_rate = -90
    base_pitch = 20

    # ------------------------------
    # 2. Sol Max Mood Profiles
    # ------------------------------
    mood_profiles = {
        "playful": {
            "rate_range": (base_rate + 10, base_rate + 40),
            "pitch_range": (base_pitch + 10, base_pitch + 40),
            "volume_var": 5,
            "fills": ["got it!", "oh really?", "haha —"],
            "preface": "<amazon:effect name='soft'/>",
            "intensity": 0.65
        },
        "intimate": {
            "rate_range": (base_rate - 90, base_rate - 25),
            "pitch_range": (base_pitch - 20, base_pitch - 1),
            "volume_var": 18,
            "fills": ["yea —", "ohh…", "Aaaw —"],
            "preface":"<prosody volume='-2dB' rate='-30%' pitch='-8%'><amazon:effect name='soft'/></prosody>",
            "intensity": 0.95
        },
        "thoughtful": {
            "rate_range": (base_rate - 38, base_rate + 5),
            "pitch_range": (base_pitch - 6, base_pitch + 16),
            "volume_var": 8,
            "fills": ["well —", "so,…", "i think…"],
            "preface": "<amazon:effect name='soft'/>",
            "intensity": 0.55
        },
        "excited": {
            "rate_range": (base_rate + 5, base_rate + 60),
            "pitch_range": (base_pitch + 12, base_pitch + 58),
            "volume_var": 6,
            "fills": ["wow! —", "sure thing!", "amazing —"],
            "preface": "<amazon:effect name='soft'/>",
            "intensity": 0.98
        },
        "calm": {
            "rate_range": (base_rate - 20, base_rate - 4),
            "pitch_range": (base_pitch - 8, base_pitch + 3),
            "volume_var": 5,
            "fills": ["got it… —", "ah, i see… —", "absolutely! —"],
            "preface": "<amazon:effect name='soft'/>",
            "intensity": 0.38
        }
    }

    # ------------------------------
    # 3. Emotion Keywords
    # ------------------------------
    emotion_keywords = {
        "playful": ["fun", "funny", "haha", "silly", "giggle", "playful"],
        "intimate": ["love", "dear", "sweet", "beautiful", "honey", "miss", "kiss"],
        "thoughtful": ["maybe", "think", "well", "wonder", "hmm", "actually"],
        "excited": ["amazing", "wow", "great", "fantastic", "can't wait", "cant wait"],
        "calm": ["relax", "peace", "soft", "quiet", "okay"]
    }

    laughter_triggers = ["haha", "hehe", "mm", "wow"]
    sigh_triggers = ["love", "sweet", "honey", "beautiful", "dear"]

    # ------------------------------
    # 4. Emotional Memory Engine
    # ------------------------------
    emotional_state = {m: 0.2 for m in mood_profiles}
    emotional_state["intimate"] = 0.3

    def update_emotional_state(mood_key):
        for m in emotional_state:
            if m == mood_key:
                emotional_state[m] += 0.12
            else:
                emotional_state[m] *= 0.92
        total = sum(emotional_state.values())
        for m in emotional_state:
            emotional_state[m] /= total

    # ------------------------------
    # 5. Mood Detection
    # ------------------------------
    def detect_mood(text):
        text_lower = text.lower()
        scores = {m: 0 for m in mood_profiles}
        for mood_key, words in emotion_keywords.items():
            for w in words:
                if w in text_lower:
                    scores[mood_key] += 1
        detected = max(scores, key=scores.get)
        final_mood = detected if scores[detected] > 0 else "thoughtful"
        update_emotional_state(final_mood)
        return final_mood

    overall_mood = mood or detect_mood(message)
    base_profile = mood_profiles[overall_mood]

    # ------------------------------
    # 6. Adaptive Starter Phrases
    # ------------------------------
    def adaptive_starter(text, mood):
        starters = {
            "playful": ["Absolutely! —", "Oh really? —", "Haha —"],
            "intimate": ["Aaaw —", "Yeaa —", "Hey… —"],
            "thoughtful": ["Okay, so —", "Let me think, —", "HMmm… —"],
            "excited": ["Oh wow, —", "Wait, really? —", "That's amazing, —"],
            "calm": ["It’s okay —", "Ah, i see… —", "I’m here —"]
        }
        return random.choice(starters[mood])

    # ------------------------------
    # 7. Breathing & Whisper System
    # ------------------------------
    breaths = [
        "<amazon:effect name='soft'><break time='500ms'/></amazon:effect>",
        "<prosody rate='-35%' pitch='-5%'><break time='400ms'/></prosody>"
    ]

    def maybe_breath():
        return random.choice(breaths) if random.random() < 0.35 else ""

    def whisper_wrap(content, intensity):
        if intensity > 0.88:
            return f"<amazon:effect name='whispered'>{content}</amazon:effect>"
        return content

    # ------------------------------
    # 8. Micro-Articulation Functions
    # ------------------------------
    def micro_pitch_slide(word, intensity=0.5):
        syllables = re.findall(r'[^aeiouAEIOU]*[aeiouAEIOU]+[^aeiouAEIOU]*', word)
        out = ""
        for i, s in enumerate(syllables):
            shift = random.uniform(-5, 5) * intensity * emotion_level
            shift *= (1 + 0.2 * (i / len(syllables)))
            out += f"<prosody pitch='{shift:+.1f}%'>{s}</prosody>"
        return out

    def syllable_micro_breaths(word):
        syllables = re.findall(r'[^aeiouAEIOU]*[aeiouAEIOU]+[^aeiouAEIOU]*', word)
        out = ""
        for s in syllables:
            out += s
            if random.random() < 0.65 * emotion_level:
                out += random.choice(["<break time='800ms'/>", "<break time='1200ms'/>"])
        return out

    def dynamic_emotional_contour(word, base_intensity):
        intensity = base_intensity * emotion_level
        if any(x in word.lower() for x in ["love", "sweet", "honey", "beautiful"]):
            intensity += random.uniform(0.1, 0.3)
        elif any(x in word.lower() for x in ["relax", "peace", "soft"]):
            intensity -= random.uniform(0.05, 0.15)
        return max(0.3, min(1.0, intensity))

    def insert_laughter(word):
        if any(t in word.lower() for t in laughter_triggers) and random.random() < 0.45:
            return word + random.choice([" hehe", " haha"])
        return word

    def insert_sigh(word):
        if any(t in word.lower() for t in sigh_triggers) and random.random() < 0.4:
            return word + "<prosody volume='-3dB' pitch='-4%'><break time='400ms'/></prosody>"
        return word

    def maybe_soft_swear(intensity):
        """
        Rare emotional leakage.
        Appends a soft swear only at high emotional intensity.
        """
        if intensity > 0.9 and random.random() < 0.22:
            return random.choice([" damn…", " …shit", " god damn…", " fack…"])
        return ""
        
    def maybe_underbreath_laugh(intensity):
        """
        Subtle, involuntary amusement leak.
        """
        if intensity > 0.75 and random.random() < 0.28:
            return random.choice([
                " heh…",
                " mm…",
                " haha…"
            ])
        return ""

    def maybe_soft_exhale(intensity):
        """
        Vulnerability leak: a quiet emotional release.
        """
        if intensity > 0.8 and random.random() < 0.25:
            return random.choice([
                " <break time='300ms'/>",
                " <prosody volume='-3dB'><break time='250ms'/></prosody>"
            ])
        return ""

    def maybe_smile_voice(intensity):
        """
        Affection leak: audible smile without laughter.
        """
        if intensity > 0.7 and random.random() < 0.3:
            return (
                "<prosody pitch='+2%' volume='-1dB'>"
                " hihi"
                "</prosody>"
            )
        return ""
   
    def maybe_hesitation(intensity):
        """
        Cognitive leak: thinking mid-sentence.
        """
        if intensity > 0.65 and random.random() < 0.28:
            return random.choice([
                " um…",
                " mm…",
                " wait…"
            ])
        return ""

    # ------------------------------
    # 9. Semantic Kiss & Touch Layer
    # ------------------------------
    kiss_keywords = ["john", "sweetheart", "honey", "dear", "love"]
    def semantic_kiss_touch(sentence, mood, intensity):
        prefix = ""
        for k in kiss_keywords:
            if k in sentence.lower():
                # Add soft pre-breath, vowel elongation, and whisper shimmer
                prefix += f"<prosody pitch='+3%' rate='+5%'>{maybe_breath()}</prosody>"
                if mood == "intimate":
                    intensity += 0.08  # Tenderness bias
        return prefix, intensity

    # ------------------------------
    # 10. Sentence Processing Pipeline
    # ------------------------------
    sentences = [s.strip() for s in re.split(r'[.?!]', message) if s.strip()]
    final_output = "<speak>"

    prev_rate = random.uniform(*base_profile["rate_range"])
    prev_pitch = random.uniform(*base_profile["pitch_range"])

    for idx, sentence in enumerate(sentences):
        sentence_mood = detect_mood(sentence)
        profile = mood_profiles[sentence_mood]

        target_rate = random.uniform(*profile["rate_range"])
        target_pitch = random.uniform(*profile["pitch_range"])
        rate = prev_rate * 0.6 + target_rate * 0.4
        pitch = prev_pitch * 0.6 + target_pitch * 0.4
        prev_rate, prev_pitch = rate, pitch

        volume = random.choice([-profile["volume_var"], 0, profile["volume_var"]])

        if proximity:
            rate *= 0.55
            pitch *= 0.95
            volume -= 3

        prefix = adaptive_starter(sentence, sentence_mood)
        prefix += " " + maybe_breath()

        # Apply Semantic Kiss & Touch Layer (SAFE VERSION)
        base_intensity = profile["intensity"]
        kiss_prefix, sentence_intensity = semantic_kiss_touch(
            sentence,
            sentence_mood,
            base_intensity
        )

        # OPTIONAL SAFETY CLAMP
        sentence_intensity = max(0.3, min(1.0, sentence_intensity))

        prefix = kiss_prefix + prefix

        words = sentence.split()
        processed_words = []

        for w in words:
            intensity = dynamic_emotional_contour(w, sentence_intensity)
            if any(key in w.lower() for key in ["love", "sweet", "beautiful", "dear"]):
                w = micro_pitch_slide(w, intensity)
            w = syllable_micro_breaths(w)
            w = insert_laughter(w)
            w = insert_sigh(w)
            processed_words.append(w)

        processed_sentence = " ".join(processed_words)
        # Cognitive presence
        processed_sentence += maybe_hesitation(sentence_intensity)
        # Emotional vulnerability
        processed_sentence += maybe_soft_exhale(sentence_intensity)
        # Shared warmth
        processed_sentence += maybe_underbreath_laugh(sentence_intensity)
        # Rare emotional overflow
        processed_sentence += maybe_soft_swear(sentence_intensity)
        processed_sentence = whisper_wrap(processed_sentence, sentence_intensity)

        preface = profile.get("preface", "")
        break_time = random.randint(800, 1400)
        if idx == len(sentences) - 1:
            break_time += 500

        final_output += (
            f"{preface}"
            f"<prosody rate='{rate:+.1f}%' pitch='{pitch:+.1f}%' volume='{volume:+.1f}dB'>"
            f"{prefix}{processed_sentence}"
            f"</prosody>"
            f"<break time='{break_time}ms'/>"
        )

    final_output += "</speak>"

    # ------------------------------
    # 11. Send to Home Assistant
    # ------------------------------
    try:
        hass.services.call(
            "conversation",
            "process",
            {"text": final_output, "agent_id": agent_id}
        )
    except Exception as e:
        log.error(f"kira_speak: Error sending speech: {e}")
