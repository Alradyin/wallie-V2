"""Scene memory and user behavior tracking for vision reactions."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Optional

from .scene_classifier import ScreenActivity


@dataclass
class SceneMemory:
    last_description: str = ""
    recent_descriptions: Deque[str] = field(default_factory=lambda: deque(maxlen=5))
    last_scene_hash: Optional[Any] = None
    scene_started_at: float = field(default_factory=time.time)
    scene_change_count: int = 0

    def record_scene_change(self, h: Any) -> None:
        self.last_scene_hash = h
        self.scene_started_at = time.time()
        self.scene_change_count = 0

    def record_delta(self) -> None:
        self.scene_change_count += 1

    def record_spoken(self, text: str) -> None:
        if text:
            self.last_description = text
            self.recent_descriptions.append(text)

    @property
    def recent_context(self) -> str:
        if not self.recent_descriptions:
            return ""
        return " | ".join(self.recent_descriptions)

    def is_same_scene(self, h: Any, threshold: int) -> bool:
        if self.last_scene_hash is None:
            return False
        try:
            return abs(h - self.last_scene_hash) < threshold
        except Exception:
            return False

    def scene_age_sec(self) -> float:
        return time.time() - self.scene_started_at


@dataclass
class UserBehaviorTracker:
    _recent_activities: Deque[ScreenActivity] = field(
        default_factory=lambda: deque(maxlen=20)
    )
    _activity_timestamps: Deque[float] = field(
        default_factory=lambda: deque(maxlen=20)
    )
    current_pattern: str = "starting"
    _last_active_change_ts: float = field(default_factory=time.time)
    _recent_scroll_dirs: Deque[str] = field(
        default_factory=lambda: deque(maxlen=6)
    )
    _settled_count: int = 0
    _prev_activity: ScreenActivity = ScreenActivity.STATIC

    def record_activity(
        self,
        activity: ScreenActivity,
        pattern: str = "",
        scroll_direction: str = "",
    ) -> None:
        now = time.time()
        self._recent_activities.append(activity)
        self._activity_timestamps.append(now)

        if pattern:
            self.current_pattern = pattern

        if activity == ScreenActivity.SCROLL and scroll_direction:
            self._recent_scroll_dirs.append(scroll_direction)

        if activity in (ScreenActivity.STATIC, ScreenActivity.MICRO):
            self._settled_count += 1
        else:
            self._settled_count = 0
            self._last_active_change_ts = now

        self._prev_activity = activity

    @property
    def settled_seconds(self) -> float:
        return time.time() - self._last_active_change_ts

    @property
    def is_settled(self) -> bool:
        return self._settled_count >= 4 and self.settled_seconds > 8.0

    @property
    def is_rapid_browsing(self) -> bool:
        if len(self._recent_activities) < 4:
            return False
        recent = list(self._recent_activities)[-5:]
        active_count = sum(
            1 for a in recent
            if a in (ScreenActivity.SCROLL, ScreenActivity.NAVIGATION, ScreenActivity.APP_SWITCH)
        )
        return active_count >= 3

    @property
    def is_watching_media(self) -> bool:
        if len(self._recent_activities) < 3:
            return False
        recent = list(self._recent_activities)[-4:]
        return sum(1 for a in recent if a == ScreenActivity.MEDIA_PLAYING) >= 3

    @property
    def is_typing(self) -> bool:
        if len(self._recent_activities) < 2:
            return False
        recent = list(self._recent_activities)[-3:]
        return sum(1 for a in recent if a == ScreenActivity.TYPING) >= 2

    @property
    def scroll_direction(self) -> str:
        if not self._recent_scroll_dirs:
            return ""
        recent = list(self._recent_scroll_dirs)[-3:]
        if len(set(recent)) == 1:
            return recent[0]
        return recent[-1] if recent else ""

    @property
    def browsing_pace(self) -> float:
        if len(self._activity_timestamps) < 3:
            return 0.0
        recent = list(self._recent_activities)[-8:]
        active = sum(
            1 for a in recent
            if a not in (ScreenActivity.STATIC, ScreenActivity.MICRO)
        )
        return min(1.0, active / max(1, len(recent)))

    def transition_detected(self) -> Optional[str]:
        if len(self._recent_activities) < 2:
            return None
        prev = self._prev_activity
        curr = list(self._recent_activities)[-1]

        if curr == ScreenActivity.APP_SWITCH:
            return "switched_app"
        if curr == ScreenActivity.NAVIGATION and prev != ScreenActivity.NAVIGATION:
            return "navigated"
        if curr == ScreenActivity.SCROLL and prev not in (ScreenActivity.SCROLL,):
            return "started_scrolling"
        if curr == ScreenActivity.STATIC and self._settled_count == 4:
            return "settled_down"
        if curr == ScreenActivity.MEDIA_PLAYING and prev != ScreenActivity.MEDIA_PLAYING:
            return "started_watching"
        if curr == ScreenActivity.TYPING and prev != ScreenActivity.TYPING:
            return "started_typing"
        return None

    def adaptation_hint(self) -> str:
        if self.is_rapid_browsing:
            return (
                "You're quickly flipping through things — browsing, looking "
                "for something. Don't commit to any one thing until you land "
                "on something that catches your eye."
            )
        if self.is_typing:
            return (
                "You're typing something right now. If you mention it, keep it "
                "brief and natural — 'let me type this real quick' or similar."
            )
        if self.is_watching_media:
            return (
                "Active content on screen — could be a game you're playing or a video you're watching. "
                "Look at the image and react accordingly. "
                "Don't narrate or describe — react with opinions, jokes, or feelings."
            )
        if self.is_settled:
            settled = self.settled_seconds
            if settled > 30:
                return (
                    "You've been on this for a while now. Find a fresh angle or "
                    "move on — don't repeat what you already said about it."
                )
            return (
                "You've settled on this. Take your time with it — no need to "
                "rush to the next thing."
            )

        recent = list(self._recent_activities)[-1] if self._recent_activities else ScreenActivity.STATIC
        if recent == ScreenActivity.SCROLL:
            d = self.scroll_direction
            if d:
                return f"You're scrolling {d} through the content."
            return "You're scrolling through the content."
        if recent == ScreenActivity.NAVIGATION:
            return "You just navigated to something new."
        if recent == ScreenActivity.APP_SWITCH:
            return "You just switched to a different app/window."
        return ""
