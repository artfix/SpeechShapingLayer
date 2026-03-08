import random
import re

@service(supports_response="True")
def kira_speak(
    message=None,
    starter_mood=None,  # Only affects first sentence
    proximity=False,
    agent_id="conversation.kira_local",
    emotion_level=1.0
):
    """
    Speech Shaping Layer Script
    
    It will work wit any LLM model coz it runs in HA.
    TTS engine needs to supp "<prosody>, <break>, <amazon:effect>, <speak>" is doing the synthesizing speech.
    The agent must: Accept input text, Return text, Not break on XML/SSML content.
    The LLM model does not need to support SSML at all.
    
    Kira speaking engine — Sol Max + Semantic Kiss & Touch Layer for edge-tts avaNeural
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
        log.error("kira_speak: No message provided.")
        return

    # ------------------------------
    # 0. Convert textual cues to SSML
    # ------------------------------
    def convert_text_cues_to_ssml(text):
        cue_map = {
            r"\(soft breath[^\)]*\)": "<prosody volume='-15%' rate='-10%'><break time='500ms'/></prosody>",
            r"\(gentle pause[^\)]*\)": "<break time='700ms'/>",
            r"\(pause[^\)]*\)": "<break time='1200ms'/>",
            r"\(sigh[^\)]*\)": "<prosody volume='+3dB' pitch='-5%'><break time='400ms'/></prosody>",
            r"\(whisper[^\)]*\)": "<prosody volume='-50%' rate='-20%' pitch='-10%'>",
            r"\(laugh[^\)]*\)": "<prosody pitch='+10%'>haha</prosody>",
        }
        for cue, ssml in cue_map.items():
            text = re.sub(cue, ssml, text, flags=re.IGNORECASE)
        return text

    message = convert_text_cues_to_ssml(message)

    # Validate emotion_level
    if emotion_level <= 0:
        emotion_level = 0.1
        log.warning("kira_speak: emotion_level too low, set to 0.1")
    elif emotion_level > 2.0:
        emotion_level = 2.0
        log.warning("kira_speak: emotion_level too high, capped at 2.0")
        
    # Escape XML special characters
    message = (message.replace('&', '&amp;')
                     .replace('<', '&lt;')
                     .replace('>', '&gt;')
                     .replace('"', '&quot;')
                     .replace("'", '&apos;'))

    # ------------------------------
    # 1. Base Tone
    # ------------------------------
    base_rate = -15
    base_pitch = 0

    # ------------------------------
    # 2. Sol Max Mood Profiles
    # ------------------------------
    mood_profiles = {
        "playful": {
            "rate_range": (base_rate + 80, base_rate + 120),  # Super fast, bouncy
            "pitch_range": (base_pitch + 70, base_pitch + 110),  # Very high, giggly
            "volume_var": 20,  # Wild volume swings
            "fills": ["hehe —", "oh really?! —", "silly you —", "haha wait —"],
            "preface": "<prosody volume='+2dB' rate='+15%' pitch='+10%'>",
            "intensity": 1.0
        },
        "intimate": {
            "rate_range": (base_rate - 70, base_rate - 40),  # Very slow, deliberate
            "pitch_range": (base_pitch - 50, base_pitch - 30),  # Low, warm, chest voice
            "volume_var": -12,  # Consistently softer
            "fills": ["mmm —", "hey you… —", "i've been thinking… —", "come here… —"],
            "preface": "<prosody volume='-6dB' rate='-40%' pitch='-15%'><amazon:effect name='soft'/></prosody>",
            "intensity": 1.0
        },
        "thoughtful": {
            "rate_range": (base_rate - 40, base_rate - 20),  # Slow, measured
            "pitch_range": (base_pitch - 20, base_pitch),  # Mid-low, contemplative
            "volume_var": -5,  # Slightly quieter
            "fills": ["hmm… —", "you know… —", "i wonder… —", "maybe… —"],
            "preface": "<prosody rate='-25%' pitch='-5%'>",
            "intensity": 0.8
        },
        "excited": {
            "rate_range": (base_rate + 100, base_rate + 140),  # Extremely fast
            "pitch_range": (base_pitch + 80, base_pitch + 120),  # Very high, breathless
            "volume_var": 25,  # Loud and dynamic
            "fills": ["OH! —", "wait wait —", "omg —", "guess what?! —"],
            "preface": "<prosody volume='+5dB' rate='+25%' pitch='+15%'>",
            "intensity": 1.0
        },
        "calm": {
            "rate_range": (base_rate - 30, base_rate - 10),  # Slow, steady
            "pitch_range": (base_pitch - 10, base_pitch + 5),  # Neutral, grounded
            "volume_var": -8,  # Quiet and consistent
            "fills": ["it's okay… —", "shh… —", "i'm here… —", "just breathe… —"],
            "preface": "<prosody volume='-4dB' rate='-20%' pitch='-3%'><amazon:effect name='soft'/></prosody>",
            "intensity": 0.6
        },
        # NEW MOOD: Angry
        "angry": {
            "rate_range": (base_rate + 40, base_rate + 70),  # Fast but clipped
            "pitch_range": (base_pitch - 40, base_pitch - 20),  # Very low, growly
            "volume_var": 30,  # Can get LOUD
            "fills": ["ugh —", "seriously?! —", "for fack's sake —", "damn it —"],
            "preface": "<prosody volume='+8dB' rate='+15%' pitch='-20%'>",
            "intensity": 1.0
        },
        # NEW MOOD: Sad
        "sad": {
            "rate_range": (base_rate - 60, base_rate - 35),  # Very slow
            "pitch_range": (base_pitch - 50, base_pitch - 30),  # Very low, hollow
            "volume_var": -15,  # Barely audible sometimes
            "fills": ["oh… —", "i know… —", "it hurts… —", "why… —"],
            "preface": "<prosody volume='-10dB' rate='-45%' pitch='-20%'><amazon:effect name='soft'/></prosody>",
            "intensity": 0.9
        }
    }

    # ------------------------------
    # 2.5 Mood-Specific Scaling Factors
    # ------------------------------
    MOOD_SCALING = {
        "playful": {
            "underbreath_laugh": 1.4,      # Laughs scale a lot
            "playful_vocal": 1.5,          # Giggles scale even more
            "soft_swear": 0.3,             # Almost no swears
            "frustrated_sigh": 0.2,        # Never frustrated
            "hesitation": 0.6,             # Less hesitation
            "excited_vocal": 0.8,          # Some excited sounds
            "soft_exhale": 0.5,            # Less vulnerability
            "vulnerable_tremor": 0.2,      # Very rare
            "sad_vocal": 0.1,              # Almost no sadness
            "max_underbreath_laugh": 0.9,  # Cap at 90%
            "max_playful_vocal": 0.9,      # Cap at 90%
            "max_soft_swear": 0.3,         # Cap low
            "max_frustrated_sigh": 0.2     # Cap very low
        },
        "intimate": {
            "underbreath_laugh": 0.7,      # Soft, intimate laughs
            "playful_vocal": 0.3,          # Rare giggles
            "soft_swear": 1.1,             # Occasional intimate swears
            "frustrated_sigh": 0.3,        # Rare frustration
            "hesitation": 1.3,             # More thoughtful pauses
            "soft_exhale": 1.5,            # Much more vulnerability
            "vulnerable_tremor": 1.4,      # Voice breaks more
            "sad_vocal": 0.8,              # Can get emotional
            "excited_vocal": 0.4,          # Rare excitement
            "max_underbreath_laugh": 0.5,  # Cap soft laughs
            "max_soft_swear": 0.3,         # Cap swears low
            "max_soft_exhale": 0.8,        # Can be very vulnerable
            "max_vulnerable_tremor": 0.7   # Voice can break
        },
        "thoughtful": {
            "underbreath_laugh": 0.6,      # Occasional soft laughs
            "playful_vocal": 0.4,          # Rare giggles
            "soft_swear": 0.5,             # Very rare swears
            "frustrated_sigh": 0.4,        # Some frustration
            "hesitation": 1.5,             # LOTS of hesitation
            "soft_exhale": 1.1,            # Some vulnerability
            "vulnerable_tremor": 0.5,      # Rare voice breaks
            "sad_vocal": 0.6,              # Can be contemplative/sad
            "excited_vocal": 0.3,          # Rare excitement
            "max_hesitation": 0.8,         # Cap hesitation
            "max_underbreath_laugh": 0.4   # Cap laughs low
        },
        "excited": {
            "underbreath_laugh": 1.5,      # Laughs A LOT
            "playful_vocal": 1.5,          # Lots of playful sounds
            "excited_vocal": 1.6,          # Squeals! 
            "soft_swear": 1.2,             # Excited swears
            "frustrated_sigh": 0.2,        # No frustration
            "hesitation": 0.3,             # Almost no hesitation
            "soft_exhale": 0.5,            # Less vulnerability
            "vulnerable_tremor": 0.2,      # No voice breaks
            "sad_vocal": 0.1,              # No sadness
            "max_underbreath_laugh": 0.9,  # Cap at 90%
            "max_playful_vocal": 0.9,      # Cap at 90%
            "max_excited_vocal": 0.9,      # Cap at 90%
            "max_soft_swear": 0.6          # Some swears ok
        },
        "calm": {
            "underbreath_laugh": 0.4,      # Soft occasional laughs
            "playful_vocal": 0.3,          # Rare playful
            "soft_swear": 0.2,             # Almost no swears
            "frustrated_sigh": 0.2,        # No frustration
            "hesitation": 0.8,             # Some hesitation
            "soft_exhale": 1.2,            # Calm, peaceful exhales
            "vulnerable_tremor": 0.3,      # Rare voice breaks
            "sad_vocal": 0.3,              # Rare sadness
            "excited_vocal": 0.2,          # No excitement
            "max_soft_exhale": 0.7,        # Calm breaths
            "max_underbreath_laugh": 0.3   # Very soft laughs
        },
        "angry": {
            "underbreath_laugh": 0.1,      # Almost no laughs
            "playful_vocal": 0.1,          # No playfulness
            "soft_swear": 1.5,             # LOTS of swears
            "frustrated_sigh": 1.6,        # Extreme frustration
            "growl": 1.7,                  # Growls scale most
            "hesitation": 0.4,             # Less hesitation
            "soft_exhale": 0.8,            # Sharp exhales
            "vulnerable_tremor": 0.2,      # No vulnerability
            "sad_vocal": 0.2,              # No sadness
            "excited_vocal": 0.3,          # Rare
            "max_soft_swear": 0.9,         # Can swear a LOT
            "max_frustrated_sigh": 0.9,    # Very frustrated
            "max_growl": 0.8,              # Can growl a lot
            "max_underbreath_laugh": 0.1   # Almost never laughs
        },
        "sad": {
            "underbreath_laugh": 0.1,      # No laughs
            "playful_vocal": 0.1,          # No playfulness
            "soft_swear": 0.4,             # Rare soft swears
            "frustrated_sigh": 0.5,        # Some frustration through tears
            "sad_vocal": 1.6,              # LOTS of crying sounds
            "vulnerable_tremor": 1.5,      # Voice breaks constantly
            "hesitation": 1.3,             # Broken, hesitant speech
            "soft_exhale": 1.2,            # Sobbing breaths
            "excited_vocal": 0.1,          # No excitement
            "max_sad_vocal": 0.9,          # Can sob heavily
            "max_vulnerable_tremor": 0.8,  # Voice breaks a lot
            "max_hesitation": 0.7,         # Very hesitant
            "max_soft_exhale": 0.7,        # Sobbing breaths
            "max_underbreath_laugh": 0.1   # Never laughs
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
        "calm": ["relax", "peace", "soft", "quiet", "okay"],
        # NEW: Angry keywords
        "angry": ["angry", "mad", "frustrated", "annoyed", "hate", "stupid", "damn", "hell"],
        # NEW: Sad keywords
        "sad": ["sad", "sorry", "unfortunate", "depressing", "cry", "heartbroken", "lonely"]
    }

    laughter_triggers = ["haha", "hehe", "mm", "wow"]
    sigh_triggers = ["love", "sweet", "honey", "beautiful", "dear"]

    # ------------------------------
    # 3.5 Kira's Natural Personality Bias
    # ------------------------------
    # Kira's core personality influences mood detection
    personality_bias = {
        "playful": 0.1,     # Slightly playful by default
        "intimate": 0.15,   # A bit more affectionate
        "thoughtful": 0.05,  # Occasionally reflective
        "excited": 0.05,     # Can get excited
        "calm": 0.1,         # Generally calm
        "angry": 0.0,        # Only from keywords
        "sad": 0.0           # Only from keywords
    }
    
    def detect_mood_with_personality(text):
        # Get keyword-based scores
        text_lower = text.lower()
        scores = {m: 0 for m in mood_profiles}
        
        # Add keyword matches
        for mood_key, words in emotion_keywords.items():
            for w in words:
                if w in text_lower:
                    scores[mood_key] += 1
        
        # Add personality bias (Kira's natural tendencies)
        for mood, bias in personality_bias.items():
            scores[mood] += bias
        
        # Find dominant mood
        detected = max(scores, key=scores.get)
        final_mood = detected if scores[detected] > 0 else "calm"
        update_emotional_state(final_mood)
        return final_mood

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
        if total > 0:
            for m in emotional_state:
                emotional_state[m] /= total
        else:
            # Fallback - should never happen but just in case
            for m in emotional_state:
                emotional_state[m] = 1.0 / len(emotional_state)

    # ------------------------------
    # 6. Adaptive Starter Phrases
    # ------------------------------
    def adaptive_starter(text, mood):
        starters = {
            "playful": ["Absolutely! —", "Oh really? —", "Haha —"],
            "intimate": ["Aaaw —", "Yeaa —", "Hey… —"],
            "thoughtful": ["Okay, so —", "Let me think, —", "HMmm… —"],
            "excited": ["Oh wow, —", "Wait, really? —", "That's amazing, —"],
            "calm": ["It’s okay —", "Ah, I see… —", "I’m here —"],
            # NEW: Angry starters
            "angry": ["Ugh —", "Facking Seriously?! —", "For crying out loud —"],
            # NEW: Sad starters
            "sad": ["Oh no… —", "That's so sad… —", "I'm sorry… —"]
        }
        return random.choice(starters[mood])

    # ------------------------------
    # 7. Breathing & Whisper System
    # ------------------------------
    breaths = [
        "<prosody volume='-15%' rate='-10%'><break time='500ms'/></prosody>",
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
            if random.random() < 0.25 * emotion_level:
                out += random.choice(["<break time='800ms'/>", "<break time='1200ms'/>"])
        return out

    def dynamic_emotional_contour(word, base_intensity):
        intensity = base_intensity * emotion_level
        if any(x in word.lower() for x in ["love", "sweet", "honey", "beautiful"]):
            intensity += random.uniform(0.1, 0.3)
        elif any(x in word.lower() for x in ["relax", "peace", "soft"]):
            intensity -= random.uniform(0.05, 0.15)
        return max(0.3, intensity)  # <-- Only floor, no ceiling!

    def insert_laughter(word):
        if any(t in word.lower() for t in laughter_triggers) and random.random() < 0.45:
            return word + random.choice([" hehe", " haha"])
        return word

    def insert_sigh(word):
        if any(t in word.lower() for t in sigh_triggers) and random.random() < 0.4:
            return word + "<prosody volume='-3dB' pitch='-4%'><break time='400ms'/></prosody>"
        return word

    # ------------------------------
    # NEW: Mood-Specific Probability Scaling
    # ------------------------------
    def get_scaled_probability(effect, mood, base_prob, current_intensity, emotion_level):
        """
        Scale a probability based on mood, intensity, and emotion_level
        """
        # Get mood-specific scaling factor (default 1.0 if not specified)
        scaling = MOOD_SCALING.get(mood, {}).get(effect, 1.0)
        
        # Get mood-specific max cap (default 0.9 if not specified)
        max_cap = MOOD_SCALING.get(mood, {}).get(f"max_{effect}", 0.9)
        
        # Calculate scaled probability
        # Multiply base by emotion_level, scaling factor, and current intensity
        scaled = base_prob * emotion_level * scaling * current_intensity
        
        # Cap it
        return min(scaled, max_cap)

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
                    # Only prevent negatives, let highs go wild for dramatic effect!
                    intensity = max(0.1, intensity)                    
        return prefix, intensity

    # ------------------------------
    # 10. Sentence Processing Pipeline
    # ------------------------------
    sentences = [s.strip() for s in re.split(r'[.?!]', message) if s.strip()]
    final_output = "<speak>"

    # Initialize rate and pitch based on first sentence
    if sentences:
        first_mood = starter_mood if starter_mood else detect_mood_with_personality(sentences[0])
        first_profile = mood_profiles[first_mood]
        prev_rate = random.uniform(*first_profile["rate_range"])
        prev_pitch = random.uniform(*first_profile["pitch_range"])
    else:
        prev_rate = base_rate
        prev_pitch = base_pitch
#--------------------------------------------------------
    for idx, sentence in enumerate(sentences):
        sentence_mood = detect_mood_with_personality(sentence)
        profile = mood_profiles[sentence_mood]

        target_rate = random.uniform(*profile["rate_range"])
        target_pitch = random.uniform(*profile["pitch_range"])
        rate = prev_rate * 0.1 + target_rate * 0.9  # 90% new mood immediately!
        pitch = prev_pitch * 0.1 + target_pitch * 0.9
        prev_rate, prev_pitch = rate, pitch

        volume = random.choice([-profile["volume_var"], 0, profile["volume_var"]])

        if proximity:
            # Slower, softer, more intimate
            rate *= 0.55
            pitch *= 0.95
            volume -= 3
            
            # Add gentle pre-breath for first sentence in proximity
            if idx == 0:
                prefix = "<prosody volume='-2dB'><break time='400ms'/></prosody>"
            else:
                prefix = ""
            
            # Increase chance of intimate starter phrases
            intimate_starters = ["hey…", "come close…", "listen…", "you know…"]
            if random.random() < 0.5:
                prefix += random.choice(intimate_starters) + " "
        else:
            prefix = ""

        # Add adaptive starter (non-proximity) or enhance proximity starter
        if proximity:
            prefix += " " + maybe_breath()
        else:
            prefix = adaptive_starter(sentence, sentence_mood) + " " + maybe_breath()

        # Apply Semantic Kiss & Touch Layer
        kiss_prefix, modified_intensity = semantic_kiss_touch(
            sentence,
            sentence_mood,
            profile["intensity"]
        )
        
        # Update the intensity for THIS sentence only
        current_intensity = max(0.3, modified_intensity)  # No ceiling!
        prefix = kiss_prefix + prefix
#--------------------------------------------------------------------------

        words = sentence.split()
        processed_words = []

        for w in words:
            intensity = dynamic_emotional_contour(w, current_intensity)
            if any(key in w.lower() for key in ["love", "sweet", "beautiful", "dear"]):
                w = micro_pitch_slide(w, intensity)
            w = syllable_micro_breaths(w)
            w = insert_laughter(w)
            w = insert_sigh(w)
            processed_words.append(w)

        processed_sentence = " ".join(processed_words)
        
        # Proximity whisper chance
        if proximity and random.random() < 0.6:  # 40% chance to whisper in proximity
            processed_sentence = f"<amazon:effect name='whispered'>{processed_sentence}</amazon:effect>"
            current_intensity *= 0.9  # Softer intensity for whispers

        # Cognitive presence
        processed_sentence += maybe_hesitation(current_intensity)
        # Emotional vulnerability
        processed_sentence += maybe_soft_exhale(current_intensity)
        
        # Mood-specific vocalizations with scaling
        if sentence_mood == "playful":
            # Playful vocal
            playful_prob = get_scaled_probability("playful_vocal", sentence_mood, 0.45, current_intensity, emotion_level)
            if random.random() < playful_prob:
                processed_sentence += random.choice([
                    " <prosody pitch='+15%'>hehe</prosody>",
                    " <prosody rate='+20%' pitch='+10%'>*giggle*</prosody>",
                    " <prosody volume='-10%' pitch='+5%'>tee hee</prosody>",
                    " <prosody pitch='+25%' rate='+15%'>haha!</prosody>"
                ])
            
            # Underbreath laugh
            laugh_prob = get_scaled_probability("underbreath_laugh", sentence_mood, 0.4, current_intensity, emotion_level)
            if random.random() < laugh_prob:
                processed_sentence += random.choice([" heh…", " mm…", " haha…", " *giggle*"])
                
        elif sentence_mood == "excited":
            # Excited vocal
            excited_prob = get_scaled_probability("excited_vocal", sentence_mood, 0.5, current_intensity, emotion_level)
            if random.random() < excited_prob:
                processed_sentence += random.choice([
                    " <prosody pitch='+30%' rate='+25%'>whee!</prosody>",
                    " <prosody volume='+5dB' pitch='+20%'>*squeak*</prosody>",
                    " <prosody rate='+30%' pitch='+25%'>eep!</prosody>",
                    " <prosody pitch='+35%' volume='+4dB'>yaaay!</prosody>"
                ])
            
            # Underbreath laugh
            laugh_prob = get_scaled_probability("underbreath_laugh", sentence_mood, 0.4, current_intensity, emotion_level)
            if random.random() < laugh_prob:
                processed_sentence += random.choice([" heh…", " mm…", " haha…", " *giggle*"])
                
        elif sentence_mood == "intimate":
            # Soft exhale
            exhale_prob = get_scaled_probability("soft_exhale", sentence_mood, 0.25, current_intensity, emotion_level)
            if random.random() < exhale_prob:
                processed_sentence += random.choice([
                    " <break time='300ms'/>",
                    " <prosody volume='-3dB'><break time='250ms'/></prosody>"
                ])
            
            # Underbreath laugh (soft for intimate)
            laugh_prob = get_scaled_probability("underbreath_laugh", sentence_mood, 0.3, current_intensity, emotion_level)
            if random.random() < laugh_prob:
                processed_sentence += random.choice([" mm…", " heh…"])
                
        elif sentence_mood == "angry":
            # Frustrated sigh
            sigh_prob = get_scaled_probability("frustrated_sigh", sentence_mood, 0.4, current_intensity, emotion_level)
            if random.random() < sigh_prob:
                processed_sentence += random.choice([
                    " ugh…",
                    " <prosody pitch='-15%' volume='+3dB'>grrr…</prosody>",
                    " mmph…"
                ])
            
            # Double chance for angry (your original design)
            if random.random() < sigh_prob:
                processed_sentence += random.choice([
                    " <prosody rate='+10%' pitch='-10%'>ugh!</prosody>",
                    " <prosody volume='+2dB'>*sharp exhale*</prosody>"
                ])
            
            # Growl
            growl_prob = get_scaled_probability("growl", sentence_mood, 0.3, current_intensity, emotion_level)
            if random.random() < growl_prob:
                processed_sentence += " <prosody pitch='-20%' rate='-15%'>grrr…</prosody>"
                
        elif sentence_mood == "sad":
            # Sad vocal
            sad_prob = get_scaled_probability("sad_vocal", sentence_mood, 0.35, current_intensity, emotion_level)
            if random.random() < sad_prob:
                processed_sentence += random.choice([
                    " <prosody pitch='-20%' volume='-30%'>*sniff*</prosody>",
                    " <prosody rate='-40%' pitch='-25%'>oh…</prosody>",
                    " <prosody volume='-40%'>*quiet sob*</prosody>",
                    " <prosody volume='-35%' pitch='-10%'>*tiny cry*</prosody>"
                ])
            
            # Vulnerable tremor
            tremor_prob = get_scaled_probability("vulnerable_tremor", sentence_mood, 0.25, current_intensity, emotion_level)
            if random.random() < tremor_prob:
                processed_sentence += random.choice([
                    " <break time='400ms'/>",
                    " <prosody volume='-2dB'>…</prosody>",
                    " i just…"
                ])
                
        else:  # calm, thoughtful
            # Soft exhale
            exhale_prob = get_scaled_probability("soft_exhale", sentence_mood, 0.2, current_intensity, emotion_level)
            if random.random() < exhale_prob:
                processed_sentence += random.choice([
                    " <break time='300ms'/>",
                    " <prosody volume='-3dB'><break time='250ms'/></prosody>"
                ])
            
            # Hesitation
            hesitation_prob = get_scaled_probability("hesitation", sentence_mood, 0.28, current_intensity, emotion_level)
            if random.random() < hesitation_prob:
                processed_sentence += random.choice([
                    " um…",
                    " mm…",
                    " wait…"
                ])

        # Soft swear with mood-specific scaling
        if sentence_mood not in ["calm", "thoughtful"]:
            swear_prob = get_scaled_probability("soft_swear", sentence_mood, 0.35, current_intensity, emotion_level)
            if random.random() < swear_prob:
                processed_sentence += random.choice([" damn…", " …shit", " god damn…", " fack…", " hell…"])
            
        processed_sentence = whisper_wrap(processed_sentence, current_intensity)

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
    # DEBUG: Log the SSML to see what's being sent
    # ------------------------------
    log.info(f"DEBUG - Final SSML: {final_output}")

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
        log.error(f"kira_emotional_speak: Error sending speech: {e}")
