"""Runtime configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PROFILES_DIR = BASE_DIR / "profiles"
STATE_FILE = BASE_DIR / ".wallie_state.json"


# -------------------------------------------------------------------
# Secrets
# -------------------------------------------------------------------
class Secrets(BaseModel):
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    groq_api_key: str = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    openrouter_api_key: str = Field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))

    fish_api_key: str = Field(default_factory=lambda: os.getenv("FISH_API_KEY", ""))
    elevenlabs_api_key: str = Field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))

    youtube_api_key: str = Field(default_factory=lambda: os.getenv("YOUTUBE_API_KEY", ""))
    youtube_client_secret_file: str = Field(
        default_factory=lambda: os.getenv("YOUTUBE_CLIENT_SECRET_FILE", "scripts/client_secret.json")
    )
    youtube_live_chat_id: str = Field(default_factory=lambda: os.getenv("YOUTUBE_LIVE_CHAT_ID", ""))

    twitch_oauth_token: str = Field(default_factory=lambda: os.getenv("TWITCH_OAUTH_TOKEN", ""))
    twitch_channel: str = Field(default_factory=lambda: os.getenv("TWITCH_CHANNEL", ""))
    twitch_nick: str = Field(default_factory=lambda: os.getenv("TWITCH_NICK", ""))

    kick_channel: str = Field(default_factory=lambda: os.getenv("KICK_CHANNEL", ""))


# -------------------------------------------------------------------
# Persona
# -------------------------------------------------------------------
Profanity = Literal["none", "mild", "heavy"]
Formality = Literal["street", "casual", "formal"]
SentenceLength = Literal["short", "medium", "mixed"]
HumorStyle = Literal[
    "ironic", "deadpan", "absurd", "observational",
    "self_deprecating", "roast", "wholesome", "chaotic",
]
Energy = Literal["chill", "warm", "hyped", "unhinged"]


class PersonaConfig(BaseModel):
    name: str = "Wallie"
    handle: str = "@wallie"
    language: str = "en"
    pronouns: str = "they/them"
    age_range: str = "early 20s"
    origin: str = "somewhere online"
    archetype: str = "variety streamer"
    backstory: str = (
        "A chronically online streamer who has seen every weird corner of the internet "
        "and is mildly amused by all of it."
    )

    energy: Energy = "warm"
    humor_style: list[HumorStyle] = Field(default_factory=lambda: ["ironic", "observational"])
    profanity: Profanity = "mild"
    formality: Formality = "casual"
    sentence_length: SentenceLength = "short"
    catchphrases: list[str] = Field(default_factory=list)
    running_gags: list[str] = Field(default_factory=list)
    banned_words: list[str] = Field(default_factory=list)
    extra_style_notes: str = ""

    strong_opinions: bool = True
    admit_uncertainty: bool = True
    break_fourth_wall: bool = False  # Can reference being on a stream
    favorite_topics: list[str] = Field(default_factory=list)
    taboo_topics: list[str] = Field(default_factory=list)

    address_style: Literal["by_name", "generic", "crowd"] = "by_name"
    reply_length: Literal["snappy", "medium", "longer"] = "snappy"
    react_to_highlights_hype: bool = True

    vision_first_person: bool = True
    vision_commentary_density: Literal["sparse", "balanced", "dense"] = "balanced"
    vision_interests: list[str] = Field(default_factory=list)
    vision_boring_signals: list[str] = Field(default_factory=lambda: [
        "google homepage", "new tab", "loading", "blank page",
        "desktop", "login screen", "settings",
    ])

    entertainer_mode: bool = True
    audience_hook_rate: float = 0.30
    anecdote_seeds: list[str] = Field(default_factory=list)
    personal_beat_rate: float = 0.35


# -------------------------------------------------------------------
# Other subsystems
# -------------------------------------------------------------------
class LLMConfig(BaseModel):
    provider: Literal["openai", "groq", "openrouter", "anthropic", "gemini", "ollama"] = "groq"
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.85
    top_p: float = 0.95
    max_tokens: int = 350
    presence_penalty: float = 0.3
    frequency_penalty: float = 0.4
    vision_capable: bool = False
    allow_vision_skip: bool = True
    ollama_base_url: str = "http://localhost:11434"
    ollama_keep_alive: str = "5m"


class TTSConfig(BaseModel):
    provider: Literal["fish", "elevenlabs", "piper"] = "fish"
    voice_id: str = ""
    sample_rate: int = 24000
    el_model_id: str = "eleven_turbo_v2_5"
    el_stability: float = 0.45
    el_similarity_boost: float = 0.75
    el_style: float = 0.0
    fish_latency_mode: Literal["normal", "balanced"] = "balanced"
    piper_model_path: str = ""
    piper_length_scale: float = 1.0


class VisionConfig(BaseModel):
    enabled: bool = False
    source: Literal["monitor"] = "monitor"
    monitor_index: int = 1
    interval_sec: float = 3.0
    min_change_threshold: int = 8
    max_edge_px: int = 768
    llm_max_edge_px: int = 512
    llm_jpeg_quality: int = 50
    scene_change_threshold: int = 20
    min_emit_interval_sec: float = 8.0
    max_frame_age_sec: float = 5.0
    idle_variance_threshold: float = 15.0
    enrich_monologue: bool = False
    enrich_probability: float = 0.08

    organic_vision: bool = False
    organicity: float = 0.75
    never_interrupt_speech: bool = True
    min_vision_react_interval_sec: float = 20.0
    micro_change_threshold: int = 4
    idle_check_interval_sec: float = 45.0
    min_engagement_for_react: float = 0.35
    startup_delay_sec: float = 5.0


class ChatConfig(BaseModel):
    youtube_enabled: bool = False
    twitch_enabled: bool = False
    kick_enabled: bool = False
    reply_probability: float = 0.35
    min_reply_interval_sec: float = 8.0
    max_message_age_sec: float = 45.0


class TopicConfig(BaseModel):
    mode: Literal["list", "ai_picks"] = "ai_picks"
    topics: list[str] = Field(default_factory=lambda: [
        "Artificial intelligence and the future",
        "Strange decisions from tech companies",
        "Absurd observations from everyday life",
    ])
    switch_min_sec: float = 90.0
    switch_chance: float = 0.15
    drift_style: Literal["rigid", "natural", "freeform"] = "natural"


class OrchestratorConfig(BaseModel):
    segment_target_sec: float = 12.0
    dedupe_window: int = 8
    dedupe_threshold: float = 0.65
    prebuffer: bool = True
    max_words_per_sentence: int = 22

    segment_sentences_min: int = 3
    segment_sentences_max: int = 6
    max_audio_lookahead_sec: float = 8.0

    session_duration_min: float = 0.0
    outro_seconds: float = 30.0

    recent_verbatim_turns: int = 24
    summarize_every_n: int = 14
    max_messages: int = 200
    max_chars: int = 60000

    organic_enabled: bool = True
    silence_beat_min_sec: float = 2.0
    silence_beat_max_sec: float = 5.5
    silence_beat_ceiling: float = 0.35
    min_inter_segment_gap_sec: float = 0.35
    breathing_gap_max_sec: float = 2.5
    post_vision_silence_sec: float = 3.0

    enable_breaks: bool = True
    break_every_min: float = 8.0
    break_every_jitter: float = 0.35
    break_min_sec: float = 4.0
    break_max_sec: float = 12.0


class AvatarConfig(BaseModel):
    enabled: bool = False
    vts_host: str = "127.0.0.1"
    vts_port: int = 8001

    param_mouth_open:  str = "MouthOpen"
    param_mouth_smile: str = "MouthSmile"
    param_mouth_form:  str = "ParamMouthForm"
    param_face_x:      str = "FaceAngleX"
    param_face_y:      str = "FaceAngleY"
    param_face_z:      str = "FaceAngleZ"
    param_eye_x:       str = "EyeLeftX"
    param_eye_y:       str = "EyeLeftY"
    param_brows:       str = "Brows"

    lipsync_gain:    float = 4.0
    lipsync_ceiling: float = 0.85
    lipsync_floor:   float = 0.02
    lipsync_attack:  float = 0.65
    lipsync_release: float = 0.30
    speaking_smile:  float = 0.15

    enable_viseme_lipsync: bool = True
    viseme_smoothing:      float = 0.35

    enable_idle_motion: bool = True
    idle_sway_amplitude: float = 4.0
    idle_sway_period_sec: float = 6.0
    enable_eye_darts: bool = True
    eye_dart_interval_sec: float = 4.5

    expr_happy:      str = ""
    expr_surprised:  str = ""
    expr_laughing:   str = ""
    expr_angry:      str = ""
    expr_sad:        str = ""
    expr_thinking:   str = ""
    expr_smug:       str = ""
    expr_eyeroll:    str = ""
    expr_confused:   str = ""
    expr_hype:       str = ""
    expr_deadpan:    str = ""

    enable_blink:          bool = True
    param_eye_open_left:   str = "EyeOpenLeft"
    param_eye_open_right:  str = "EyeOpenRight"
    blink_interval_sec:    float = 3.8
    blink_hold_sec:        float = 0.045
    double_blink_chance:   float = 0.15

    enable_body_motion:    bool = True
    param_body_x:          str = "BodyAngleX"
    param_body_y:          str = "BodyAngleY"
    param_body_z:          str = "BodyAngleZ"
    body_sway_amplitude:   float = 2.5
    body_sway_period_sec:  float = 9.0

    enable_mood_link:      bool = True
    mood_idle_min_scale:   float = 0.5
    mood_idle_max_scale:   float = 1.6
    mood_brow_min:         float = -0.4
    mood_brow_max:         float = 0.3
    mood_smile_max:        float = 0.20

    auto_map_expressions:  bool = True


class AppConfig(BaseModel):
    profile_name: str = "default"
    persona: PersonaConfig = Field(default_factory=PersonaConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    chat: ChatConfig = Field(default_factory=ChatConfig)
    topics: TopicConfig = Field(default_factory=TopicConfig)
    orchestrator: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    avatar: AvatarConfig = Field(default_factory=AvatarConfig)


# -------------------------------------------------------------------
# Profiles (multi-persona support)
# -------------------------------------------------------------------
@dataclass
class Runtime:
    config: AppConfig
    secrets: Secrets
    base_dir: Path = BASE_DIR


def _ensure_dirs() -> None:
    PROFILES_DIR.mkdir(exist_ok=True)


def _active_profile_name() -> str:
    _ensure_dirs()
    if STATE_FILE.exists():
        try:
            import json
            return json.loads(STATE_FILE.read_text(encoding="utf-8")).get("active", "default")
        except Exception:
            pass
    return "default"


def _set_active_profile_name(name: str) -> None:
    import json
    STATE_FILE.write_text(json.dumps({"active": name}), encoding="utf-8")


def _profile_path(name: str) -> Path:
    safe = "".join(c for c in name if c.isalnum() or c in "-_") or "default"
    return PROFILES_DIR / f"{safe}.yaml"


def list_profiles() -> list[str]:
    _ensure_dirs()
    return sorted(p.stem for p in PROFILES_DIR.glob("*.yaml"))


def load_profile(name: Optional[str] = None) -> AppConfig:
    name = name or _active_profile_name()
    path = _profile_path(name)
    if not path.exists():
        cfg = AppConfig(profile_name=name)
        save_profile(cfg, name)
        _set_active_profile_name(name)
        return cfg
    try:
        import yaml  # type: ignore
        data: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        data["profile_name"] = name
        return AppConfig(**data)
    except ModuleNotFoundError:
        import json
        data = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
        data["profile_name"] = name
        return AppConfig(**data)


def save_profile(cfg: AppConfig, name: Optional[str] = None) -> None:
    _ensure_dirs()
    name = name or cfg.profile_name or "default"
    cfg = cfg.model_copy(update={"profile_name": name})
    path = _profile_path(name)
    data = cfg.model_dump()
    try:
        import yaml  # type: ignore
        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    except ModuleNotFoundError:
        import json
        path.with_suffix(".json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def activate_profile(name: str) -> AppConfig:
    cfg = load_profile(name)
    _set_active_profile_name(name)
    return cfg


def delete_profile(name: str) -> bool:
    path = _profile_path(name)
    if path.exists():
        path.unlink()
        if _active_profile_name() == name:
            remaining = list_profiles()
            _set_active_profile_name(remaining[0] if remaining else "default")
        return True
    return False


def clone_profile(src: str, dst: str) -> AppConfig:
    cfg = load_profile(src)
    save_profile(cfg, dst)
    return load_profile(dst)


def get_runtime() -> Runtime:
    return Runtime(config=load_profile(), secrets=Secrets())


def load_config(*_args, **_kwargs) -> AppConfig:
    return load_profile()


def save_config(cfg: AppConfig, *_args, **_kwargs) -> None:
    save_profile(cfg)
