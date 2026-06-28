"""
core/event_bus.py
A lightweight, in-memory Agent-to-Agent communication bus.

Every time one agent hands off work to another (Coordinator -> PaperReader,
PaperReader -> FactChecker, etc.) it publishes an AgentMessage here. The
Streamlit "Architecture" page and the terminal logs both read from this
same bus, so what you see in the UI is the *actual* communication trace,
not a fake animation.
"""
from __future__ import annotations

import threading
from typing import Callable

from core.config import get_logger
from core.models import AgentMessage

logger = get_logger("event_bus")


class EventBus:
    def __init__(self) -> None:
        self._messages: list[AgentMessage] = []
        self._lock = threading.Lock()
        self._subscribers: list[Callable[[AgentMessage], None]] = []

    def publish(self, message: AgentMessage) -> None:
        with self._lock:
            self._messages.append(message)
        logger.info(
            "[%s -> %s] (%s) %s",
            message.sender.value,
            message.receiver.value,
            message.stage.value,
            message.summary,
        )
        for sub in self._subscribers:
            try:
                sub(message)
            except Exception:  # subscribers must never break the pipeline
                logger.exception("Event bus subscriber raised an exception")

    def subscribe(self, callback: Callable[[AgentMessage], None]) -> None:
        self._subscribers.append(callback)

    def history(self) -> list[AgentMessage]:
        with self._lock:
            return list(self._messages)

    def clear(self) -> None:
        with self._lock:
            self._messages.clear()


# A single process-wide bus. Streamlit re-imports modules across reruns but
# keeps module-level state per session process, which is sufficient here;
# the UI layer also mirrors messages into st.session_state for persistence
# across reruns within a session.
event_bus = EventBus()
