

https://github.com/user-attachments/assets/bb4404e5-9138-4288-a428-345486b86f7e

<p align="center">
  <h1 align="center">Wallie</h1>
  <p align="center"><strong>The open-source AI streamer that actually feels alive.</strong></p>
  <p align="center">
    <a href="https://spontaneous-dodol-cabb7d.netlify.app/">Website</a> &nbsp;·&nbsp;
    <a href="#quick-start">Quick Start</a> &nbsp;·&nbsp;
    <a href="#features">Features</a> &nbsp;·&nbsp;
    <a href="#the-dashboard">Dashboard</a> &nbsp;·&nbsp;
    <a href="#architecture">Architecture</a> &nbsp;·&nbsp;
    <a href="#roadmap">Roadmap</a>
  </p>
  <p align="center">
    <img alt="License" src="https://img.shields.io/badge/license-MIT-blue.svg" />
    <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-brightgreen.svg" />
    <img alt="Platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg" />
  </p>
</p>

---

Every AI streamer you've seen has the same problem.

It says two sentences. Pauses. Says two more. Pauses. Describes your YouTube homepage like a screen reader. Forgets what it said thirty seconds ago. Ends every thought with "what do you guys think?" into a chat that doesn't exist. It's not a show — it's a tech demo on loop.

**Wallie is different.** It's an AI that actually streams — develops thoughts across minutes, reacts to your screen like a person who's been using that computer all day, remembers what it covered an hour ago, takes opinions and sticks with them, drifts between topics the way real conversations drift, and shuts up when there's nothing worth saying.

You design the streamer. Wallie runs the show.

```
   persona  ──┐
   topics   ──┤
   chat     ──┼──►  Wallie  ──►  Voice (TTS)  ──►  OBS / virtual cable  ──►  your stream
   vision   ──┤             ──►  Live2D avatar (VTube Studio)
   schedule ──┘
```

Pick the personality. Pick the voice. Pick the LLM. Pick the platform. Everything is swappable, everything is configurable from the browser, and the whole thing runs on your machine with your keys.

---

## Why another AI streamer?

Because the existing ones are toys.

They work for a 2-minute demo and fall apart on a real stream. Here's what actually goes wrong after 10 minutes:

| The problem | What usually happens | What Wallie does |
|---|---|---|
| **Repetition** | Says "that's interesting" every 30 seconds | Dedupe engine + phrase cooldown + rolling summary that tracks everything already said |
| **Short memory** | Forgets the topic from 5 minutes ago | Rolling summarizer compresses old turns into bullet notes, injected into every prompt |
| **Robotic vision** | "I can see a YouTube homepage with several videos" | First-person ownership + SKIP escape hatch — narrates nothing, reacts to what matters |
| **Question loops** | Every segment ends with "what do you think, chat?" | Question detector throttles after one; next prompt forces a statement ending |
| **No personality** | Generic helpful assistant voice | Full persona system: energy, humor style, catchphrases, backstory, opinions, taboo topics |
| **Choppy pacing** | 2 sentences → long pause → 2 sentences | Pipeline overlap + longer thought development eliminates dead air |
| **Broken threads** | Sets up a story, never delivers it | Open-thread tracker forces the next segment to pay off teases and answer its own questions |
| **Topic whiplash** | Jumps from AI to cooking to space with no bridge | Association-based topic drift with configurable style (rigid / natural / freeform) |

These aren't edge cases. They're the default behavior of most AI streamer projects. Wallie was built by hitting every one of these problems and refusing to ship until they were fixed.

---

## Features

### Bring your own everything

Six LLM providers. Three TTS engines. Three chat platforms. Mix and match per profile.

| LLM | TTS | Chat | Avatar |
|---|---|---|---|
| OpenAI | Fish Audio | Twitch | VTube Studio (Live2D) |
| Anthropic (Claude) | ElevenLabs | YouTube | — |
| Google (Gemini) | Piper (local, free) | Kick | — |
| Groq | — | — | — |
| OpenRouter | — | — | — |
| Ollama (local, free) | — | — | — |

Swap providers without changing code. Run a fully offline stream with Ollama + Piper, or go premium with Claude + ElevenLabs.

### Full persona design

Not just a name and a system prompt. You design a *character*:

- **Identity** — name, handle, pronouns, age range, origin, archetype, backstory
- **Voice** — energy level (chill → unhinged), humor style (pick multiple: ironic, deadpan, absurd, observational, roast...), profanity level, formality
- **Flavor** — catchphrases, running gags, banned words, favorite topics, taboo topics
- **Opinions** — strong opinions toggle, admit uncertainty, break the fourth wall
- **Extra notes** — free text for anything the structured fields miss

Save multiple personas. Switch between them with a dropdown.

### Hours-long sessions without decay

The single biggest technical challenge. Most AI chatbots break down after 20 minutes because the context window fills up.

Wallie's approach:
- **Rolling summarizer** — every ~14 segments, a background LLM call compresses older history into tight bullet notes
- **Session notes** — that compressed memory is injected into every system prompt, so the streamer knows what it already said
- **Cross-session memory** — key facts and viewer interactions persist across streams
- **Dedupe engine** — paraphrase-aware similarity check (bigram + trigram Jaccard) catches the model repeating itself in different words

### Organic pacing

Real streamers don't talk at a constant rate. They get excited, they pause to think, they go on tangents, they settle into a flow.

- **Mood engine** — arousal, valence, focus, and talkativity drift slowly over the stream. High arousal = faster, warmer output. Low talkativity = silence beats. Mood state feeds into the avatar for reactive animation.
- **Attention engine** — vision events are filtered through a probabilistic decision layer. Not every screen change gets a deep reaction. Some get a glance. Some get ignored. Some trigger a personal tangent.
- **Silence beats** — the streamer holds natural pauses when the mood says to. Dead air handled by design, not by accident.
- **Pipeline overlap** — next segment starts generating while current audio is still playing. No awkward 3-second gaps between thoughts.

### Vision that isn't narration

Screen reactions are the hardest part to get right. Wallie's approach:

- **First-person ownership** — Wallie owns whatever is on screen. Gaming: "I just got bodied by that boss", not "the character is fighting a boss". Browsing: "let me pull this up", not "the user is browsing". Never third-person, never narration.
- **SKIP escape hatch** — if there's nothing specific to name, the model outputs `SKIP` and stays quiet. No more narrating generic UIs.
- **Activity adaptation** — detects scrolling, typing, app-switching, video playback and adjusts reactions accordingly. Typing → ignore. App switch → react. Rapid browsing → wait until user settles. Each activity type gets context-aware prompting.
- **Attention engine** — not every screen change gets the same treatment. DEEP reactions (22%), quick GLANCEs (28%), personal TANGENTs (5%), deliberate IGNOREs (27%), and SILENCE beats (18%). Streak fatigue prevents reacting the same way twice in a row.
- **Scene memory** — remembers what it last said about the current screen. Dedupe threshold at 0.65 with per-sentence comparison catches paraphrased repetition.

### Live2D avatar with emotion

Not just a mouth that opens and closes. Six animation layers run simultaneously over a single WebSocket, so the avatar feels like a person — not a puppet.

- **Viseme lip sync** — spectral analysis of PCM audio estimates mouth shape in real-time. Front vowels (A/E/I) spread the mouth wide, back vowels (O/U) round it. Combined with RMS amplitude for jaw openness, attack/release envelope, noise floor gating, and a speaking smile baseline. The result: the avatar's mouth actually forms different shapes per sound, not just open/close.
- **Blink** — periodic natural eye blinks (~3.8s interval) with random variation and occasional double-blinks. Blink rate adapts to mood: sleepy = more blinks, alert = fewer
- **Body motion** — slow torso sway on BodyAngleX/Y/Z, lower amplitude and longer period than head movement, so the avatar breathes even when silent
- **Idle motion** — head sway and eye darts when not speaking. Eye-dart frequency increases when the streamer's mood focus drops (scattered attention)
- **11 expression slots** — happy, surprised, laughing, angry, sad, thinking, smug, eyeroll, confused, hype, deadpan
- **Keyword-driven emotions** — sentence content automatically triggers matching expressions (21 regex patterns, first match wins)
- **Expression auto-mapping** — on connect, Wallie discovers VTS hotkeys and matches them to empty expression slots by name. No manual configuration needed for models with standard hotkey names
- **Mood-reactive avatar** — the MoodEngine's arousal/valence/focus feed directly into the avatar. Arousal scales idle and body sway amplitude (0.5×–1.6×). Valence shifts brow position and adds a resting smile when the streamer is in a good mood. Focus modulates eye-dart frequency
- **Event cues** — super chat → hype face, screen change → surprised look + upward glance, thinking pause → thinking expression, chat message → head turn toward "the chat"

### The dashboard

Everything is configured from the browser. No YAML files. No terminal commands after setup.

```
┌──────────────────────────────────────────────────────────────┐
│ ◤ WALLIE   Profile: marlow ▾  ⊕ ⎘ 🗑      ● LIVE  Stop  ‹  │
├──────────┬───────────────────────────────┬───────────────────┤
│          │                               │   LIVE STATUS     │
│ Identity │  Section editor               │ ┌───────────────┐ │
│ Personal.│                               │ │ Current topic  │ │
│ Voice    │  (each section has its own    │ │ Now saying...  │ │
│ Avatar   │   editor with live controls)  │ │ Open threads   │ │
│ Topics   │                               │ │ Recent angles  │ │
│ Vision   │  Test ▶ monologue / chat / vis│ │ Session memory │ │
│ Chat     │  Output preview + ▶ speak this│ │ Mood state     │ │
│ Engine   │                               │ │ WebSocket log  │ │
│ API Keys │                               │ └───────────────┘ │
└──────────┴───────────────────────────────┴───────────────────┘
```

Three columns: navigation, section editor, live status. Test any configuration change instantly with the preview buttons before going live.

<p align="center">
  <img src="docs/images/dashboard-identity.png" alt="Dashboard — Identity" width="100%" />
  <br /><br />
  <img src="docs/images/dashboard-personality.png" alt="Dashboard — Personality" width="100%" />
</p>

---

## Quick start

### One-click setup

Clone and double-click. No Python knowledge needed.

**Windows:**
```
git clone https://github.com/Alradyin/wallie-V2.git
cd wallie-V2
```
Double-click **`install.bat`** → then **`start.bat`**. Dashboard opens at `http://127.0.0.1:8765`.

> `start.bat` auto-installs on first run — you can skip `install.bat` entirely.

**macOS / Linux:**
```bash
git clone https://github.com/Alradyin/wallie-V2.git
cd wallie-V2
chmod +x start.sh
./start.sh
```

That's it. Everything else happens in the browser.

### Pick your budget

| Path | LLM | TTS | Cost/hour | Quality |
|---|---|---|---|---|
| **Free** | Gemini 2.5 Flash | Piper (local) | $0 | Good for testing |
| **Cheap & fast** | Groq (Llama 3.3 70B) | Fish Audio | ~$1.50 | Best balance |
| **Premium** | Claude Sonnet | ElevenLabs | ~$6.50 | Best quality + vision |

All configured from the dashboard. Add your API keys → pick provider → pick model → Start.

<details>
<summary><strong>Piper (free TTS) setup</strong></summary>

Piper runs locally — no API key needed. One extra terminal command to download a voice:

```bash
# In your wallie directory, with venv active:
pip install piper-tts onnxruntime
python scripts/download_piper_voice.py en_US-amy-medium
```

Then in the dashboard: Voice → provider: `piper`, path: `voices/en_US-amy-medium.onnx`.
</details>

<details>
<summary><strong>Vision setup (screen reactions)</strong></summary>

Requires a vision-capable LLM. In the dashboard:

1. **Engine** → toggle "Vision capable" ON
2. Use a vision model: `claude-sonnet-4-5`, `gpt-4o`, `gemini-2.5-pro`, or `llama-4-scout` on Groq
3. **Vision** section → toggle ON, adjust frame interval and sensitivity

The SKIP escape hatch is always active — no configuration needed.
</details>

<details>
<summary><strong>Chat platform setup</strong></summary>

**Twitch:** Add OAuth token from [twitchtokengenerator.com](https://twitchtokengenerator.com) (chat:read scope). Or leave empty for anonymous read-only.

**YouTube:** Drop `client_secret.json` in `scripts/`. First run opens browser for Google OAuth consent.

**Kick:** Just enter the channel slug. No auth needed (public Pusher WebSocket).
</details>

<details>
<summary><strong>VTube Studio avatar</strong></summary>

1. Run VTube Studio with API enabled (Settings → API → Enable)
2. In the dashboard: Avatar → toggle ON
3. First connect triggers a plugin approval popup in VTS — click Allow
4. Expression slots are **auto-mapped** from your model's hotkeys on connect. Override manually if needed
5. Adjust lipsync gain/ceiling for your voice. Viseme lip sync (spectral mouth shape) is enabled by default — disable it in Avatar config if your model doesn't have a `ParamMouthForm` parameter
6. Blink, body motion, and mood-reactive behaviour are enabled by default — tweak or disable per-feature in config

Works with any Live2D model that has standard parameters (`MouthOpen`, `EyeOpenLeft/Right`, `FaceAngleX/Y/Z`, `BodyAngleX/Y/Z`).
</details>

<details>
<summary><strong>OBS output routing</strong></summary>

Wallie outputs audio through your system's default audio device. To route it into OBS:

**Windows:** Install [VB-CABLE](https://vb-audio.com/Cable/). Set CABLE Input as default playback. In OBS: Audio Input Capture → CABLE Output.

**macOS:** Use [BlackHole](https://existential.audio/blackhole/) the same way.

**Linux:** PipeWire / PulseAudio loopback (`pw-loopback`).
</details>

---

## Architecture

```
  Screen ────► Vision ───┐
  (mss + pHash)          │
                         ▼
  Chat ─────────►  Orchestrator  ◄──── Persona + Topics + Mood
  (YT/Twitch/Kick)      │
                         │  intent → system prompt + user message
                         ▼
                   LLM (streaming)     ← 5 providers
                         │
                         │  token stream
                         ▼
                  SentenceStreamer      ← splits tokens into TTS-ready sentences
                         │
                         ▼
                   TTS pipeline        ← 3 providers, parallel pre-fire
                         │
                         │  PCM16 audio
                         ▼
                    AudioPlayer ──────► VTube Studio (viseme lipsync + blink + body + expressions)
                         │                    ▲
                         │              Mood Engine (arousal/valence/focus)
                         │
                         ▼
                  speakers / OBS / virtual cable
```

**One pipeline. One conversation history. No competing buffers.** This is the defining design choice. Early prototypes had parallel generation paths and went insane — the streamer would repeat itself, contradict itself, and lose all continuity. Everything goes through one orchestrator, one set of messages, one output path.

**Intent priority:** highlight chat (barge in) → vision event → ordinary chat → monologue. Higher-priority intents preempt lower ones.

**Continuity machinery:**
- Rolling summary of older turns → injected into system prompt
- Open-thread tracker → forces the next segment to resolve dangling questions and teases
- Phrase cooldown → prevents catchphrase spam
- Theme tracker → blocks repeated angles

### Project structure

```
wallie-v2/
├── wallie.py              # entrypoint
├── config.py              # pydantic models, profile management
├── core/
│   ├── orchestrator.py    # the single pipeline
│   ├── persona.py         # prompt engineering
│   ├── context.py         # conversation history + rolling summary
│   ├── attention.py       # vision reaction decisions
│   ├── mood.py            # slow-evolving emotional state
│   └── memory_store.py    # cross-session persistent memory
├── llm/                   # 5 LLM provider adapters
├── tts/                   # 3 TTS provider adapters
├── audio/                 # sounddevice player with alignment safety
├── vision/                # screen capture + change detection + activity classification
├── chat/                  # YouTube, Twitch, Kick monitors
├── avatar/                # VTube Studio WebSocket client
├── dashboard/             # FastAPI + Alpine.js (no build step)
├── profiles/              # saved persona profiles (YAML)
└── scripts/               # setup utilities
```

---

## Provider compatibility

### LLM

| Provider | Streaming | Vision | Notes |
|---|---|---|---|
| **Groq** | ✅ | ✅ (Llama-4) | Fastest inference. Free tier. |
| **OpenAI** | ✅ | ✅ (GPT-4o) | Strong vision. Premium pricing. |
| **OpenRouter** | ✅ | ✅ (varies) | One key, many models. |
| **Anthropic** | ✅ | ✅ (Claude 4) | Best character/IP recognition. |
| **Gemini** | ✅ | ✅ (2.5 family) | Free tier (50 req/min). |
| **Ollama** | ✅ | ✅ (llava, etc.) | Fully local. No API key. |

### TTS

| Provider | Streaming | Cloning | Cost |
|---|---|---|---|
| **Fish Audio** | ✅ | ✅ | ~$15/M chars |
| **ElevenLabs** | ✅ | ✅ | ~$30/M chars |
| **Piper** | ✅ (local) | ❌ | $0 |

---

## Security

- API keys stored in `.env` with restricted permissions (`chmod 600` on POSIX)
- Dashboard never exposes raw keys — only masked previews (`sk-•••xyz`)
- Dashboard binds to `127.0.0.1` only — not accessible from the network
- Atomic writes prevent `.env` corruption
- Provider error messages scrubbed of key-shaped strings before display
- Allowed env variables are hard-coded — the UI cannot write arbitrary keys

**Do not expose the dashboard to a public network without a reverse proxy with authentication.**

---

## Troubleshooting

<details>
<summary><strong>Audio becomes static</strong></summary>

Hit the **reset audio** button in the dashboard top bar. If it recurs, check logs — usually a TTS provider returning non-PCM data (detected and aborted automatically in most cases).
</details>

<details>
<summary><strong>AI describes generic UI ("I see a YouTube page")</strong></summary>

The SKIP escape hatch depends on the model. Smaller models (Llama-4 Scout, Gemini Flash) are worse at following it. Upgrade to Claude Sonnet or GPT-4o for better vision, or set commentary density to `sparse`.
</details>

<details>
<summary><strong>AI keeps asking questions to chat</strong></summary>

The question throttle is automatic (forces statements after one question-ending). If it persists, raise frequency penalty to 0.5–0.7 in Engine settings.
</details>

<details>
<summary><strong>Avatar mouth doesn't move</strong></summary>

Check that the `MouthOpen` parameter name matches your model (some use `ParamMouthOpen` or `MouthOpenY`). Override in Avatar → Parameter mapping.
</details>

<details>
<summary><strong>Avatar mouth moves but shape looks wrong</strong></summary>

Viseme lip sync drives `ParamMouthForm` for mouth shape (wide ↔ round). If your model uses a different parameter name, update it in Avatar → Parameters → Mouth form. If your model doesn't support mouth form at all, disable "Spectral mouth shape" in the Viseme section — lipsync will fall back to volume-only (open/close).
</details>

<details>
<summary><strong>Avatar doesn't blink</strong></summary>

Check that your model has `EyeOpenLeft` / `EyeOpenRight` parameters (some use `ParamEyeLOpen` / `ParamEyeROpen`). Override the parameter names in Avatar config. Blink can be disabled with `enable_blink: false`.
</details>

<details>
<summary><strong>Expressions don't fire</strong></summary>

Expression slots need to match VTS hotkey names or IDs. If auto-mapping didn't find your hotkeys (naming mismatch), map them manually in the dashboard or set `expr_happy`, `expr_sad`, etc. in your profile. Use the dashboard's "Discover hotkeys from VTS" to see available names.
</details>

<details>
<summary><strong>TTS returns 401</strong></summary>

Verify the key in API Keys — the masked preview should match your provider dashboard. Hit "test" to confirm.
</details>

---

## Roadmap

What's coming next:

- **Hearing** — real-time audio input so Wallie can listen and react to game audio, music, voice chat, and stream alerts. Not just eyes — ears too.
- **Streaming avatar backend (HeyGen)** — realistic-looking avatars as an alternative to Live2D
- **First-run wizard** — guided setup that walks you through provider choice → key entry → first stream
- **Docker image** — `docker run wallie` with a volume for config
- **Cost meter** — running spend tally in the live drawer
- **OBS WebSocket integration** — scene switching tied to stream events
- **Voice cloning UI** — upload reference audio, create a voice from the dashboard

If any of these matter to you — open an issue, or better yet, a PR.

---

## Contributing

Issues and PRs welcome. Ground rules:

- **Code is English-only.** Comments, logs, variables — all English. UI can be localized.
- **Single pipeline, single history.** Don't add parallel generation paths. That road has been walked.
- **Lazy imports for optional deps.** Groq users shouldn't need `anthropic` installed.
- Run `python scripts/_import_check.py` before submitting.

---

## License

MIT. See [LICENSE](LICENSE).

---

<p align="center">
  <strong>Wallie is built for people who want their AI streamer to feel like a real show, not a tech demo.</strong>
  <br />
  Star the repo. Try the $0 path. Tell us what broke.
</p>
