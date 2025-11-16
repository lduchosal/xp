"""Lightweight state machine utilities.

Provides simple, zero-dependency state machine implementation for
managing state transitions with validation.
"""

from enum import Enum
from typing import Set


class StateMachine:
    """Lightweight state machine for managing state transitions.

    Enforces valid state transitions and prevents invalid operations.
    Zero dependencies, suitable for any state-based logic.

    Example:
        >>> from enum import Enum
        >>> class State(str, Enum):
        ...     IDLE = "IDLE"
        ...     RUNNING = "RUNNING"
        ...
        >>> sm = StateMachine(State.IDLE)
        >>> sm.define_transition("start", {State.IDLE}, State.RUNNING)
        >>> sm.can_transition("start")  # True
        >>> sm.transition("start", State.RUNNING)  # True
        >>> sm.get_state()  # State.RUNNING
    """

    def __init__(self, initial: Enum):
        """Initialize state machine.

        Args:
            initial: Initial state (any Enum value).
        """
        self.state = initial
        self._valid_transitions: dict[str, Set[Enum]] = {}

    def define_transition(self, action: str, valid_sources: Set[Enum]) -> None:
        """Define valid source states for an action.

        Args:
            action: Action name (e.g., "connect", "disconnect").
            valid_sources: Set of states from which action is valid.
        """
        self._valid_transitions[action] = valid_sources

    def can_transition(self, action: str) -> bool:
        """Check if action is valid from current state.

        Args:
            action: Action to check (e.g., "connect", "disconnect").

        Returns:
            True if action is valid from current state.
        """
        valid_sources = self._valid_transitions.get(action, set())
        return self.state in valid_sources

    def transition(self, action: str, new_state: Enum) -> bool:
        """Attempt state transition.

        Args:
            action: Action triggering the transition.
            new_state: Target state.

        Returns:
            True if transition succeeded, False if invalid.
        """
        if self.can_transition(action):
            self.state = new_state
            return True
        return False

    def get_state(self) -> Enum:
        """Get current state.

        Returns:
            Current state as Enum value.
        """
        return self.state
