# core/state_machine.py - Strict Pushdown Automata & State Pattern for UI & Input Layering
"""
Clean UI State Machine & Pushdown Automata (PDA) for Cognitive Quest.

Eliminates input bleeding between:
1. State.Exploration   - Overworld movement enabled, puzzles disabled, menus enabled
2. State.CognitivePuzzle - World paused/dimmed, input rerouted entirely to the minigame UI, menus blocked
3. State.Dialogue      - Cinematic/text state locked, overworld movement blocked, menus blocked

Optimized for AMD A4-6300 (Dual-Core, 1MB L2 cache, no per-frame allocations).
"""

from enum import Enum
import pygame


class State(str, Enum):
    """
    Core UI and Game State Enumeration.
    Inherits from str for seamless string comparisons and serialization compatibility.
    """
    Exploration = "Exploration"
    CognitivePuzzle = "CognitivePuzzle"
    Dialogue = "Dialogue"

    def __str__(self):
        return self.value


# ============================================================
# STATE PATTERN HANDLER CLASSES
# ============================================================

class BaseState:
    """
    Abstract Base State definition for the State Pattern.
    Defines default capabilities, input gating, and lifecycle hooks.
    """
    name = State.Exploration
    allows_movement = True
    allows_menus = True
    allows_camera_pan = True
    is_world_paused = False
    should_dim_world = False

    def enter(self, machine, host=None, context=None):
        """Called when this state becomes the active state at the top of the PDA stack."""
        pass

    def exit(self, machine, host=None):
        """Called when this state is popped or transitioned away from."""
        pass

    def update(self, host, dt):
        """State-specific per-frame update logic."""
        pass

    def handle_event(self, host, event):
        """State-specific event interceptor. Return truthy or 'handled' if consumed."""
        return None

    def handle_click(self, host, pos):
        """State-specific click handler."""
        return False

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name.value}>"


class ExplorationState(BaseState):
    """
    Overworld exploration state.
    - Player movement (WASD, arrows, click-to-move, gesture steering) enabled.
    - Menus (Pause Menu, Controls Guide, Guide Modals) enabled.
    - LoL Camera middle-drag & Spacebar recenter enabled.
    - World running at standard speed (not paused, not dimmed).
    """
    name = State.Exploration
    allows_movement = True
    allows_menus = True
    allows_camera_pan = True
    is_world_paused = False
    should_dim_world = False


class PuzzleState(BaseState):
    """
    Cognitive puzzle state.
    - Overworld movement strictly disabled (WASD, click-to-move, gesture walking).
    - Overworld menus strictly disabled (no pause menu over minigame).
    - LoL camera panning strictly disabled.
    - World logic & stage timer paused.
    - World background dimmed via zero-allocation cached surface.
    - Inputs routed directly and exclusively to the active puzzle UI.
    """
    name = State.CognitivePuzzle
    allows_movement = False
    allows_menus = False
    allows_camera_pan = False
    is_world_paused = True
    should_dim_world = True

    def enter(self, machine, host=None, context=None):
        # Clear lingering click destinations to prevent character movement bleeding
        if host is not None and hasattr(host, 'click_dest'):
            host.click_dest = None


# Semantic alias
CognitivePuzzleState = PuzzleState


class DialogueState(BaseState):
    """
    Dialogue / Cinematic state.
    - Character locked in place (cannot walk or move during speech / prompt).
    - Menus blocked (prevents pausing during quiz choices / intro).
    - World updates continue (e.g. ambient animations, particle effects).
    - Input routed to dialogue boxes and quiz answer selection.
    """
    name = State.Dialogue
    allows_movement = False
    allows_menus = False
    allows_camera_pan = False
    is_world_paused = False
    should_dim_world = False

    def enter(self, machine, host=None, context=None):
        if host is not None and hasattr(host, 'click_dest'):
            host.click_dest = None


class UIStateMachine:
    """
    Strict Pushdown Automata (PDA) for UI and Input Layering.

    Maintains a LIFO stack of game states:
    - Base state is always State.Exploration (cannot be popped).
    - Opening a cognitive puzzle pushes State.CognitivePuzzle (or PuzzleState).
    - Talking to an NPC or viewing a quiz dialog pushes State.Dialogue (or DialogueState).
    - Closing or completing an overlay pops back to the previous state.

    Provides strict input gating:
    - allows_movement(): True ONLY in State.Exploration
    - allows_menus(): True ONLY in State.Exploration
    - allows_camera_pan(): True ONLY in State.Exploration
    - is_world_paused(): True in State.CognitivePuzzle
    - should_dim_world(): True in State.CognitivePuzzle
    """

    def __init__(self, initial_state=State.Exploration, host=None):
        # State Handler Registry
        self._handlers = {
            State.Exploration: ExplorationState(),
            State.CognitivePuzzle: PuzzleState(),
            State.Dialogue: DialogueState(),
        }
        self._host = host
        self._listeners = []

        norm_state = self._normalize_state(initial_state)
        self._stack = [norm_state]
        self._contexts = [{}]

        # Surface memoization cache: (width, height, alpha, color) -> Surface
        self._dim_surface_cache = {}

        # Trigger enter on initial state
        handler = self._handlers.get(norm_state)
        if handler:
            handler.enter(self, host=self._host, context={})

    @property
    def current_handler(self):
        """Returns the BaseState handler object for the active state."""
        return self._handlers.get(self.current_state, self._handlers[State.Exploration])

    def register_state_handler(self, state, handler):
        """Allows injecting custom state handler instances."""
        norm_state = self._normalize_state(state)
        self._handlers[norm_state] = handler

    @classmethod
    def _normalize_state(cls, state):
        if isinstance(state, BaseState):
            return state.name
        if isinstance(state, State):
            return state
        if isinstance(state, str):
            for s in State:
                if s.value.lower() == state.lower() or s.name.lower() == state.lower():
                    return s
        raise ValueError(f"Invalid state: {state}. Expected one of {[s.value for s in State]}")

    # ============================================================
    # STACK OPERATIONS
    # ============================================================

    @property
    def current_state(self):
        """Returns the active state at the top of the stack."""
        return self._stack[-1]

    @property
    def current_context(self):
        """Returns metadata associated with the active state."""
        return self._contexts[-1]

    @property
    def depth(self):
        """Returns the number of states on the stack."""
        return len(self._stack)

    @property
    def stack_depth(self):
        """Alias for depth."""
        return self.depth

    def push(self, state, context=None):
        """
        Pushes a new state onto the stack.
        Suspends the previous state and activates the new state.
        Clears any active click-to-move destinations on the host screen.
        """
        if isinstance(state, BaseState):
            self.register_state_handler(state.name, state)
        norm_state = self._normalize_state(state)
        ctx = context if isinstance(context, dict) else ({"data": context} if context is not None else {})
        prev_state = self.current_state
        prev_handler = self.current_handler

        # Clear host click_dest to prevent movement bleeding
        if self._host is not None and hasattr(self._host, 'click_dest'):
            self._host.click_dest = None

        if prev_handler:
            prev_handler.exit(self, host=self._host)

        self._stack.append(norm_state)
        self._contexts.append(ctx)

        new_handler = self.current_handler
        if new_handler:
            new_handler.enter(self, host=self._host, context=ctx)

        self._notify_listeners(action="push", new_state=norm_state, old_state=prev_state, context=ctx)
        return norm_state

    def pop(self):
        """
        Pops the top state from the stack and resumes the uncovered state.
        The base root state (State.Exploration) is never popped.
        """
        if len(self._stack) > 1:
            popped_state = self._stack.pop()
            popped_ctx = self._contexts.pop()
            popped_handler = self._handlers.get(popped_state)
            if popped_handler:
                popped_handler.exit(self, host=self._host)

            new_state = self.current_state
            new_ctx = self.current_context

            # Clear host click_dest when transitioning back
            if self._host is not None and hasattr(self._host, 'click_dest'):
                self._host.click_dest = None

            resumed_handler = self.current_handler
            if resumed_handler:
                resumed_handler.enter(self, host=self._host, context=new_ctx)

            self._notify_listeners(action="pop", new_state=new_state, old_state=popped_state, context=popped_ctx)
            return popped_state
        return self.current_state

    def push_state(self, state, context=None):
        """Convenience alias for push."""
        return self.push(state, context=context)

    def pop_state(self):
        """Convenience alias for pop."""
        return self.pop()

    def set_state(self, state, context=None):
        """
        Transitions directly to a state.
        If transitioning to State.Exploration, resets the stack to [State.Exploration].
        Otherwise, sets stack to [State.Exploration, state].
        """
        if isinstance(state, BaseState):
            self.register_state_handler(state.name, state)
        norm_state = self._normalize_state(state)
        prev_state = self.current_state
        prev_handler = self.current_handler
        ctx = context if isinstance(context, dict) else ({"data": context} if context is not None else {})

        if self._host is not None and hasattr(self._host, 'click_dest'):
            self._host.click_dest = None

        if prev_handler:
            prev_handler.exit(self, host=self._host)

        if norm_state == State.Exploration:
            self._stack = [State.Exploration]
            self._contexts = [ctx]
        else:
            self._stack = [State.Exploration, norm_state]
            self._contexts = [{}, ctx]

        new_handler = self.current_handler
        if new_handler:
            new_handler.enter(self, host=self._host, context=ctx)

        self._notify_listeners(action="set", new_state=norm_state, old_state=prev_state, context=ctx)
        return norm_state

    def reset(self, state=State.Exploration):
        """Resets the state machine stack to a single root state."""
        return self.set_state(state)

    # ============================================================
    # STATE QUERIES & GATING
    # ============================================================

    def is_exploration(self):
        """True when in overworld exploration."""
        return self.current_state == State.Exploration

    def is_cognitive_puzzle(self):
        """True when a cognitive puzzle overlay is active."""
        return self.current_state == State.CognitivePuzzle

    def is_dialogue(self):
        """True when a dialogue, cinematic, or quiz modal is active."""
        return self.current_state == State.Dialogue

    def is_in(self, state):
        """Checks if current state matches the provided state."""
        return self.current_state == self._normalize_state(state)

    def contains(self, state):
        """Checks if state is anywhere in the stack."""
        norm_state = self._normalize_state(state)
        return norm_state in self._stack

    def allows_movement(self):
        """
        Strict movement gate: Character movement (keys, click-to-move, gesture steering)
        is ONLY enabled during State.Exploration.
        """
        return self.is_exploration()

    def allows_menus(self):
        """
        Strict menu gate: In-game menus (Pause Menu, Controls Guide, Guide Modals)
        can ONLY be opened during State.Exploration.
        Prevents menu bleeding over active cognitive puzzles or dialogues.
        """
        return self.is_exploration()

    def allows_camera_pan(self):
        """
        Strict camera gate: LoL camera panning and recentering is ONLY enabled
        during State.Exploration.
        """
        return self.is_exploration()

    def is_world_paused(self):
        """
        True when world logic/timers should pause (e.g. during cognitive puzzles).
        """
        return self.is_cognitive_puzzle()

    def should_dim_world(self):
        """
        True when the game world backdrop should be dimmed to highlight an overlay.
        """
        return self.is_cognitive_puzzle()

    # ============================================================
    # HARDWARE-OPTIMIZED WORLD DIMMING
    # ============================================================

    def render_dim_overlay(self, screen, alpha=150, color=(0, 0, 0)):
        """
        Renders a memoized semi-transparent dimming overlay over the screen.
        Zero per-frame allocations: re-uses a cached Surface matching the dimensions,
        strictly complying with the AMD A4-6300 L2 cache constraint.
        """
        w, h = screen.get_size()
        key = (w, h, alpha, color)
        dim_surf = self._dim_surface_cache.get(key)
        if dim_surf is None:
            dim_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            dim_surf.fill((*color, alpha))
            self._dim_surface_cache[key] = dim_surf

        screen.blit(dim_surf, (0, 0))

    # ============================================================
    # LISTENERS & OBSERVERS
    # ============================================================

    def add_listener(self, listener):
        """Registers a callback for state changes: listener(new_state, old_state, action, context)."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener):
        """Removes a registered callback."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self, action, new_state, old_state, context):
        for listener in self._listeners:
            try:
                listener(new_state, old_state, action, context)
            except Exception as e:
                print(f"[STATE MACHINE ERROR] Listener error: {e}")

    def __repr__(self):
        return f"<UIStateMachine stack={[s.value for s in self._stack]} current={self.current_state.value}>"
