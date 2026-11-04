# Cognitive Maze - Developer & Agent Guidelines

## Target Hardware Constraint
> [!IMPORTANT]
> **Primary Target System: AMD A4-6300 APU (Dual-Core, 2 Threads, 3.7 GHz, 1MB L2 Cache, 0MB L3 Cache, Radeon HD 8370D Integrated Graphics).**
> All features, camera tracking, rendering, audio, and distribution builds must strictly run at 60 FPS without stuttering on this low-spec hardware.

Detailed rules are documented in [.agents/rules/hardware_target.md](file:///.agents/rules/hardware_target.md):
- **Core Budget**: 2 CPU threads max (Main Pygame thread + Camera/AI thread). Never busy-wait.
- **MediaPipe Sizing**: Always downsample frames to 320x240 for hand tracking with `num_hands=1`.
- **Memory & Cache**: Avoid per-frame allocations in hot loops; keep data structures compact to fit in 1MB L2 cache.
- **Surface Memoization**: Cache rendered fonts, transformed sprites, and map surfaces. Always use `.convert()` or `.convert_alpha()`.
- **Audio Mixing**: Pygame mixer initialized with `buffer=512`.

## Git & Version Control
- See [.agents/rules/git.md](file:///.agents/rules/git.md). Never run `git push` automatically without explicit user request.
