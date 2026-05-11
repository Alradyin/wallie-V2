// =====================================================================
// Wallie dashboard — Alpine component
// =====================================================================

const SECTIONS = [
  { id: "identity",    label: "Identity",     ico: "🪪" },
  { id: "personality", label: "Personality",  ico: "🎭" },
  { id: "voice",       label: "Voice",        ico: "🎙" },
  { id: "topics",      label: "Topics",       ico: "📝" },
  { id: "vision",      label: "Vision",       ico: "👁" },
  { id: "chat",        label: "Chat",         ico: "💬" },
  { id: "avatar",      label: "Avatar",       ico: "🎴" },
  { id: "engine",      label: "Engine",       ico: "🧠" },
  { id: "secrets",     label: "API Keys",     ico: "🔑" },
];

const HUMOR_OPTIONS = [
  "ironic", "deadpan", "absurd", "observational",
  "self_deprecating", "roast", "wholesome", "chaotic",
];

const EMOTION_SLOTS = [
  "happy", "surprised", "laughing", "angry", "sad",
  "thinking", "smug", "eyeroll", "confused", "hype", "deadpan",
];

const MODEL_OPTIONS = {
  groq: [
    { id: "meta-llama/llama-4-maverick-17b-128e-instruct", label: "Llama 4 Maverick 17B", vision: true },
    { id: "meta-llama/llama-4-scout-17b-16e-instruct", label: "Llama 4 Scout 17B", vision: true },
    { id: "llama-3.3-70b-versatile", label: "Llama 3.3 70B", vision: false },
    { id: "llama-3.1-8b-instant", label: "Llama 3.1 8B (fast)", vision: false },
    { id: "gemma2-9b-it", label: "Gemma 2 9B", vision: false },
    { id: "mixtral-8x7b-32768", label: "Mixtral 8x7B", vision: false },
  ],
  openai: [
    { id: "gpt-4.1", label: "GPT-4.1", vision: true },
    { id: "gpt-4.1-mini", label: "GPT-4.1 Mini", vision: true },
    { id: "gpt-4.1-nano", label: "GPT-4.1 Nano", vision: true },
    { id: "gpt-4o", label: "GPT-4o", vision: true },
    { id: "gpt-4o-mini", label: "GPT-4o Mini", vision: true },
    { id: "o3-mini", label: "o3 Mini", vision: false },
  ],
  openrouter: [
    { id: "anthropic/claude-sonnet-4-6", label: "Claude Sonnet 4.6", vision: true },
    { id: "anthropic/claude-haiku-4-5", label: "Claude Haiku 4.5", vision: true },
    { id: "openai/gpt-4o", label: "GPT-4o", vision: true },
    { id: "openai/gpt-4.1", label: "GPT-4.1", vision: true },
    { id: "google/gemini-2.5-pro", label: "Gemini 2.5 Pro", vision: true },
    { id: "google/gemini-2.5-flash", label: "Gemini 2.5 Flash", vision: true },
    { id: "meta-llama/llama-3.3-70b-instruct", label: "Llama 3.3 70B", vision: false },
  ],
  anthropic: [
    { id: "claude-sonnet-4-6", label: "Claude Sonnet 4.6", vision: true },
    { id: "claude-opus-4-6", label: "Claude Opus 4.6", vision: true },
    { id: "claude-haiku-4-5", label: "Claude Haiku 4.5", vision: true },
  ],
  gemini: [
    { id: "gemini-2.5-pro", label: "Gemini 2.5 Pro", vision: true },
    { id: "gemini-2.5-flash", label: "Gemini 2.5 Flash", vision: true },
    { id: "gemini-2.0-flash", label: "Gemini 2.0 Flash", vision: true },
  ],
  ollama: [],
};

function emptyCfg() {
  return {
    profile_name: "default",
    persona: {
      name: "", handle: "", language: "en", pronouns: "", age_range: "", origin: "", archetype: "",
      backstory: "",
      energy: "warm", humor_style: ["ironic", "observational"],
      profanity: "mild", formality: "casual", sentence_length: "short",
      catchphrases: [], running_gags: [], banned_words: [],
      extra_style_notes: "",
      strong_opinions: true, admit_uncertainty: true, break_fourth_wall: false,
      favorite_topics: [], taboo_topics: [],
      address_style: "by_name", reply_length: "snappy", react_to_highlights_hype: true,
      vision_first_person: true, vision_commentary_density: "balanced",
    },
    llm: { provider: "groq", model: "", temperature: 0.85, top_p: 0.95, max_tokens: 500, presence_penalty: 0.3, frequency_penalty: 0.4, vision_capable: false, ollama_base_url: "http://localhost:11434", ollama_keep_alive: "5m" },
    tts: { provider: "fish", voice_id: "", sample_rate: 24000, el_model_id: "eleven_turbo_v2_5", el_stability: 0.45, el_similarity_boost: 0.75, el_style: 0.0, fish_latency_mode: "balanced" },
    vision: { enabled: false, source: "monitor", monitor_index: 1, interval_sec: 3.0, min_change_threshold: 8, max_edge_px: 768, startup_delay_sec: 5 },
    chat: { youtube_enabled: false, twitch_enabled: false, kick_enabled: false, reply_probability: 0.35, min_reply_interval_sec: 8.0, max_message_age_sec: 45.0 },
    topics: { mode: "ai_picks", topics: [], switch_min_sec: 90, switch_chance: 0.15 },
    orchestrator: {
      segment_target_sec: 12,
      dedupe_window: 8,
      dedupe_threshold: 0.78,
      prebuffer: true,
      session_duration_min: 0,
      outro_seconds: 30,
      recent_verbatim_turns: 24,
      summarize_every_n: 14,
      max_messages: 200,
      max_chars: 60000,
    },
    avatar: {
      enabled: false,
      vts_host: "127.0.0.1",
      vts_port: 8001,
      param_mouth_open: "MouthOpen",
      param_mouth_smile: "MouthSmile",
      param_face_x: "FaceAngleX",
      param_face_y: "FaceAngleY",
      param_face_z: "FaceAngleZ",
      param_eye_x: "EyeLeftX",
      param_eye_y: "EyeLeftY",
      param_brows: "Brows",
      lipsync_gain: 4.0,
      lipsync_ceiling: 0.85,
      lipsync_floor: 0.02,
      lipsync_attack: 0.65,
      lipsync_release: 0.30,
      speaking_smile: 0.15,
      param_mouth_form: "ParamMouthForm",
      enable_viseme_lipsync: true,
      viseme_smoothing: 0.35,
      enable_idle_motion: true,
      idle_sway_amplitude: 4.0,
      idle_sway_period_sec: 6.0,
      enable_eye_darts: true,
      eye_dart_interval_sec: 4.5,
      expr_happy: "", expr_surprised: "", expr_laughing: "",
      expr_angry: "", expr_sad: "", expr_thinking: "",
      expr_smug: "", expr_eyeroll: "", expr_confused: "",
      expr_hype: "", expr_deadpan: "",
    },
  };
}

function formatHMS(seconds) {
  if (seconds === null || seconds === undefined) return "—";
  seconds = Math.max(0, Math.round(seconds));
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const pad = (n) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`;
}

function app() {
  return {
    sections: SECTIONS,
    humorOptions: HUMOR_OPTIONS,
    section: "identity",

    cfg: emptyCfg(),
    profiles: [],
    activeProfile: "default",

    running: false,
    status: {},
    logs: [],
    _nextLogId: 1,
    _ws: null,

    drawerOpen: true,
    saveMsg: "",
    testing: false,
    testResult: "",
    voiceTestText: "",
    avatarTestExpr: "",
    avatarTestMsg: "",
    visionTestResult: "",
    visionTestMeta: "",
    emotionSlots: EMOTION_SLOTS,
    avatarStatus: { enabled: false, connected: false },
    avatarHotkeys: [],
    avatarHotkeysFetched: false,
    // Secrets UI state. Raw values live ONLY inside `secretEdits`, keyed by env
    // name; cleared the moment we save / cancel so they don't linger in memory.
    secrets: [],
    secretEdits: {},     // env -> draft value (only set while editing)
    secretShow: {},      // env -> whether the input is unmasked while editing
    secretMsg: {},       // env -> "saved" / "tested ✓" / error text
    secretBusy: {},      // env -> bool (test in flight)

    async init() {
      await this.loadProfiles();
      await this.loadConfig();
      await this.refreshStatus();
      await this.loadSecrets();
      this.connectWs();
      setInterval(() => this.refreshStatus(), 2000);
      setInterval(() => this.refreshAvatarStatus(), 3000);
    },

    // ----- secrets -----
    async loadSecrets() {
      try {
        const r = await fetch("/api/secrets");
        const data = await r.json();
        this.secrets = data.secrets || [];
      } catch (e) { console.warn("loadSecrets:", e); }
    },

    secretsByKind(kind) {
      return (this.secrets || []).filter(s => s.kind === kind);
    },

    envToProvider(env) {
      // OPENAI_API_KEY → openai, ELEVENLABS_API_KEY → elevenlabs, etc.
      const m = {
        OPENAI_API_KEY: "openai",
        GROQ_API_KEY: "groq",
        OPENROUTER_API_KEY: "openrouter",
        ANTHROPIC_API_KEY: "anthropic",
        GEMINI_API_KEY: "gemini",
        FISH_API_KEY: "fish",
        ELEVENLABS_API_KEY: "elevenlabs",
      };
      return m[env] || "";
    },

    startEditSecret(env) {
      this.secretEdits[env] = "";
      this.secretShow[env] = false;
    },

    cancelEditSecret(env) {
      // Wipe the draft from memory immediately — no traces in component state.
      delete this.secretEdits[env];
      delete this.secretShow[env];
      delete this.secretMsg[env];
    },

    async saveSecret(env) {
      const value = this.secretEdits[env] ?? "";
      try {
        const r = await fetch("/api/secrets", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ env, value }),
        });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        // Wipe draft NOW — server confirmed the write, we don't need it anymore.
        delete this.secretEdits[env];
        delete this.secretShow[env];
        this.secretMsg[env] = value ? "saved" : "cleared";
        await this.loadSecrets();
        setTimeout(() => { delete this.secretMsg[env]; }, 1800);
      } catch (e) {
        this.secretMsg[env] = `error: ${e}`;
      }
    },

    async testProviderKey(provider, env) {
      this.secretBusy[env] = true;
      this.secretMsg[env] = "testing…";
      try {
        const r = await fetch("/api/secrets/test", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ provider }),
        });
        const data = await r.json();
        this.secretMsg[env] = data.ok ? `✓ ${data.preview || "ok"}` : `✗ ${data.error || "failed"}`;
      } catch (e) {
        this.secretMsg[env] = `✗ ${e}`;
      } finally {
        this.secretBusy[env] = false;
        setTimeout(() => { delete this.secretMsg[env]; }, 4000);
      }
    },

    // ----- avatar -----
    async refreshAvatarStatus() {
      try {
        const r = await fetch("/api/avatar/status");
        this.avatarStatus = await r.json();
      } catch { this.avatarStatus = { enabled: false, connected: false }; }
    },

    async fetchHotkeys() {
      this.avatarHotkeysFetched = true;
      try {
        const r = await fetch("/api/avatar/hotkeys");
        const data = await r.json();
        this.avatarHotkeys = data.hotkeys || [];
        if (this.avatarHotkeys.length === 0) {
          this.avatarTestMsg = "no hotkeys returned (model has none defined?)";
          setTimeout(() => (this.avatarTestMsg = ""), 3000);
        }
      } catch (e) {
        this.avatarTestMsg = "fetch failed: " + e;
        setTimeout(() => (this.avatarTestMsg = ""), 3000);
      }
    },

    async testEmotion(slot) {
      try {
        const r = await fetch("/api/test/expression", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ expression: slot }),
        });
        const data = await r.json();
        this.avatarTestMsg = r.ok ? `→ ${slot}` : data.detail || "failed";
      } catch (e) {
        this.avatarTestMsg = "error: " + e;
      }
      setTimeout(() => (this.avatarTestMsg = ""), 1800);
    },

    async testRawHotkey(name) {
      try {
        await fetch("/api/test/expression", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ expression: name }),
        });
        this.avatarTestMsg = `fired: ${name}`;
      } catch (e) {
        this.avatarTestMsg = "error: " + e;
      }
      setTimeout(() => (this.avatarTestMsg = ""), 1800);
    },

    async testLook(x, y) {
      try {
        await fetch("/api/test/avatar_look", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ x, y, hold_sec: 0.8 }),
        });
      } catch {}
    },

    async testVision() {
      await this.save();
      this.testing = true;
      this.visionTestResult = "capturing screen + sending to model...";
      this.visionTestMeta = "";
      try {
        const r = await fetch("/api/test/vision", { method: "POST" });
        const data = await r.json();
        if (r.ok) {
          this.visionTestResult = data.text || "(empty response)";
          this.visionTestMeta =
            `${data.provider}:${data.model} · frame ${data.frame_size?.join("×")} · ${(data.frame_bytes/1024).toFixed(1)} KB`;
        } else {
          this.visionTestResult = "ERROR: " + (data.detail || JSON.stringify(data));
        }
      } catch (e) {
        this.visionTestResult = "ERROR: " + e;
      } finally {
        this.testing = false;
      }
    },

    // ----- profiles -----
    async loadProfiles() {
      const r = await fetch("/api/profiles");
      const data = await r.json();
      this.profiles = data.profiles;
      this.activeProfile = data.active;
    },

    async switchProfile(name) {
      await fetch(`/api/profiles/${encodeURIComponent(name)}/activate`, { method: "PUT" });
      await this.loadConfig();
      await this.loadProfiles();
    },

    async promptNewProfile() {
      const name = prompt("New profile name:");
      if (!name) return;
      await fetch("/api/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      await this.loadProfiles();
      await this.loadConfig();
    },

    async promptCloneProfile() {
      const name = prompt(`Clone "${this.activeProfile}" as:`);
      if (!name) return;
      await fetch("/api/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, clone_from: this.activeProfile }),
      });
      await this.loadProfiles();
      await this.loadConfig();
    },

    async confirmDeleteProfile() {
      if (!confirm(`Delete profile "${this.activeProfile}"? This cannot be undone.`)) return;
      await fetch(`/api/profiles/${encodeURIComponent(this.activeProfile)}`, { method: "DELETE" });
      await this.loadProfiles();
      await this.loadConfig();
    },

    // ----- config I/O -----
    async loadConfig() {
      const r = await fetch("/api/config");
      const fetched = await r.json();
      // Merge into empty to ensure newly added fields exist.
      const base = emptyCfg();
      this.cfg = deepMerge(base, fetched);
    },

    async save() {
      const r = await fetch("/api/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(this.cfg),
      });
      this.saveMsg = r.ok ? "saved" : "fail";
      setTimeout(() => (this.saveMsg = ""), 1400);
    },

    // ----- orchestrator -----
    async refreshStatus() {
      try {
        const r = await fetch("/api/status");
        this.status = await r.json();
        this.running = !!this.status.running;
      } catch { this.running = false; }
    },

    async start() { await fetch("/api/start", { method: "POST" }); await this.refreshStatus(); },
    async stop()  { await fetch("/api/stop",  { method: "POST" }); await this.refreshStatus(); },

    async resetAudio() {
      try {
        await fetch("/api/audio/reset", { method: "POST" });
      } catch (e) { console.warn(e); }
    },

    // ----- live log -----
    connectWs() {
      const proto = location.protocol === "https:" ? "wss" : "ws";
      this._ws = new WebSocket(`${proto}://${location.host}/ws/events`);
      this._ws.onmessage = (ev) => {
        try {
          const entry = JSON.parse(ev.data);
          if (entry.type === "log") {
            entry.id = this._nextLogId++;
            this.logs.push(entry);
            if (this.logs.length > 400) this.logs.splice(0, this.logs.length - 400);
          }
        } catch {}
      };
      this._ws.onclose = () => setTimeout(() => this.connectWs(), 2000);
    },

    // ----- test strip -----
    async testPersona(kind) {
      // Save first so the server reads the latest persona.
      await this.save();
      this.testing = true;
      this.testResult = "…";
      try {
        const r = await fetch("/api/test/persona", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ kind }),
        });
        const data = await r.json();
        this.testResult = data.text || "(no response)";
      } catch (e) {
        this.testResult = `error: ${e}`;
      } finally {
        this.testing = false;
      }
    },

    async speakTest() {
      if (!this.testResult) return;
      await this._voice(this.testResult);
    },

    async testVoice() {
      if (!this.voiceTestText) return;
      await this._voice(this.voiceTestText);
    },

    async testExpression() {
      if (!this.avatarTestExpr) return;
      await this.save();
      this.testing = true;
      this.avatarTestMsg = "…";
      try {
        const r = await fetch("/api/test/expression", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ expression: this.avatarTestExpr }),
        });
        const data = await r.json();
        this.avatarTestMsg = data.ok ? "✓ triggered" : (data.detail || "failed");
      } catch (e) {
        this.avatarTestMsg = `error: ${e}`;
      } finally {
        this.testing = false;
        setTimeout(() => (this.avatarTestMsg = ""), 2500);
      }
    },

    async _voice(text) {
      await this.save();
      this.testing = true;
      try {
        await fetch("/api/test/voice", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
        });
      } finally {
        this.testing = false;
      }
    },

    // ----- helpers -----
    toggleInList(list, value) {
      const i = list.indexOf(value);
      if (i >= 0) list.splice(i, 1);
      else list.push(value);
    },

    modelOptions() {
      const provider = this.cfg.llm.provider;
      if (provider === "ollama") return [];
      const models = (MODEL_OPTIONS[provider] || []).slice();
      if (this.cfg.llm.model && !models.some(m => m.id === this.cfg.llm.model)) {
        models.unshift({ id: this.cfg.llm.model, label: this.cfg.llm.model, vision: this.cfg.llm.vision_capable, custom: true });
      }
      return models;
    },

    onModelSelect() {
      const models = MODEL_OPTIONS[this.cfg.llm.provider] || [];
      const selected = models.find(m => m.id === this.cfg.llm.model);
      if (selected) this.cfg.llm.vision_capable = selected.vision;
    },

    onProviderChange() {
      const models = MODEL_OPTIONS[this.cfg.llm.provider] || [];
      if (models.length > 0 && !models.some(m => m.id === this.cfg.llm.model)) {
        this.cfg.llm.model = models[0].id;
        this.cfg.llm.vision_capable = models[0].vision;
      }
    },

    formatHMS,
  };
}

// Chip input reusable component.
function chipInput(getList) {
  return {
    draft: "",
    model() { return getList() || []; },
    add() {
      const v = (this.draft || "").trim();
      if (!v) return;
      const list = getList();
      if (!list.includes(v)) list.push(v);
      this.draft = "";
    },
    remove(i) { getList().splice(i, 1); },
  };
}

// Deep merge: keys in 'override' replace keys in 'base'; arrays are taken whole from override.
function deepMerge(base, override) {
  if (override === null || override === undefined) return base;
  if (typeof base !== "object" || typeof override !== "object" || Array.isArray(base) || Array.isArray(override)) {
    return override;
  }
  const out = { ...base };
  for (const k of Object.keys(override)) {
    if (k in base && typeof base[k] === "object" && !Array.isArray(base[k]) && base[k] !== null) {
      out[k] = deepMerge(base[k], override[k]);
    } else {
      out[k] = override[k];
    }
  }
  return out;
}
