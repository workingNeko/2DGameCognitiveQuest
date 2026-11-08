# Changelog — Cognitive Maze

All notable **Changes & Improvements** and **Bug Fixes** for each version of **Cognitive Maze** are documented in this file.

---

## [v1.2.4] — 2026-11-09
### Changes & Improvements
- **100% Automatic One-Click In-App Updater**: Replaced manual/browser update flows with a single **`⬇ Update & Restart`** action inside the game that downloads, verifies, silently installs in-place (`/SILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS`), and automatically relaunches `CognitiveMaze.exe` with zero web browser redirects or manual setup wizard steps.
- **Exact Installation Folder Targeting**: Automatic updates detect the exact folder from which `CognitiveMaze.exe` was launched (including Desktop or portable directories via `/DIR`) and upgrade that copy directly.
- **Copyright & Metadata Compliance**: Updated application metadata, leaderboard headers, installer publisher/version resources, and release notes to reflect independent educational software authorship without institutional trademark or endorsement claims.

### Bug Fixes
- **Interrupted Wi-Fi Download Recovery & Integrity Validation**: Added HTTP `Range` byte-resume retries (up to 3 attempts), exact `Content-Length` verification, and HTML captive-portal rejection (`_is_valid_installer_file`) so dropped school Wi-Fi connections never execute truncated installers.
- **Version Badge Formatting & Font Memoization**: Fixed duplicate `vv` version prefix rendering (`vv1.2.3` -> `v1.2.4`) in Settings and Main Menu footer pills, and cached footer pill font instances to avoid per-frame `SysFont` overhead on AMD A4-6300 hardware.
- **Clean Webcam & Save Shutdown Handoff**: Ensured student progress saves are flushed and DirectShow camera handles (`cap.release()`) are closed prior to update installation so the relaunched game acquires the camera immediately.
- **User Save & Audio Settings Preservation**: Protected `db\saves\*` (`onlyifdoesntexist`) in `installer.iss` so custom volume settings and local student progress are never overwritten during upgrades.

---

## [v1.2.3] — 2026-11-09
### Changes & Improvements
- **Quarter 3 Sun Temple Fraction Match Mini-Game**: Replaced multi-step Quarter 3 guardian puzzles with a streamlined single-round, 4-card visual fraction matching mini-game (`1/2`, `1/3`, `2/3`, `1/4`, `3/4`) across `map7`, `map8`, and `map9`, supporting closed-fist drag, mouse drag, and two-tap matching.
- **Vercel Grading Portal Sync & Summative Assessment Mapping**: Solidified 100-point assessment mapping across Quarter 1, Quarter 2, Quarter 3, and Summative Assessment with idempotent stage saving and automatic high-score replacement.
- **AMD A4-6300 APU Build & Rendering Optimization**: Eliminated ~96 MB of duplicate bundled assets (reducing installer size from ~151 MB to ~109 MB) and pre-baked `.convert_alpha()` puzzle/UI surfaces for locked 60 FPS performance.
- **UI Cleanup**: Simplified Settings version label display.

### Bug Fixes
- **Crash-Safe Student Reset Recovery**: Added Write-Ahead Log (`pending_student_restore.json`) protection so power or network interruptions during new-activity resets never strand student records.
- **Cloud Question LaTeX Sanitization**: Fixed raw LaTeX expressions (`\frac`, `\times`, escaped currency symbols) appearing unformatted in live cloud-synced quiz prompts.
- **Autosave Frame-Time Stalls**: Offloaded synchronous disk `fsync` writes from the 60 FPS Pygame main loop to prevent micro-stutters on Dual-Core Radeon HD 8370D systems.

---

## [v1.2.2] — 2026-11-07
### Changes & Improvements
- **Built-in Fullscreen Screenshot System (`F12` / `PrtScn` / `F2`)**: Added instant PNG capture to `Pictures\CognitiveMaze` plus direct Windows Clipboard DIB copy (`Ctrl + V` ready) and an on-screen HUD toast without Exclusive Fullscreen black-screen artifacts.
- **In-App Download Progress & Setup Handoff**: Added live percentage, `MB / MB`, and transfer speed tracking inside the Settings modal.
- **Custom Application Icon Integration**: Embedded "The Labyrinth Key" artwork across window titlebars, taskbar icons, desktop shortcuts, and setup binaries.

### Bug Fixes
- **Exclusive Fullscreen Capture Freeze**: Fixed Windows DWM black-frame capture issues when taking screenshots in hardware double-buffered fullscreen mode.
- **Installer File-Lock Conflicts**: Fixed `CognitiveMaze.exe` holding open file handles when launching an update installer by cleanly terminating Pygame prior to setup execution.

---

## [v1.2.1] — 2026-11-07
### Changes & Improvements
- **Streaming In-App Update Downloader**: Introduced background chunked installer streaming inside `UpdateManager` with CPU slice yielding for Dual-Core AMD A4-6300 APUs.
- **Low-Latency Camera Pipeline**: Enforced single-hand (`num_hands=1`) 320x240 MediaPipe inference and 1.0ms Windows kernel timer granularity (`timeBeginPeriod(1)`).

### Bug Fixes
- **Webcam Tracking Input Lag**: Fixed DirectShow frame-buffer backlog by flushing stale driver frames (`< 2ms` grab check), eliminating hand-cursor delay.
- **School Proxy SSL Verification Failures**: Fixed update-check connection errors behind educational firewalls and older Windows certificate stores via multi-tier SSL context fallback.

---

## [v1.2.0] — 2026-11-06
### Changes & Improvements
- **Windows Setup Installer & Portable Packaging**: Added Inno Setup low-privilege installer (`PrivilegesRequired=lowest`) for school lab PCs alongside standalone portable `.zip` builds.
- **3-Tier Update Discovery**: Added resilient GitHub Releases REST API -> Web Redirect -> Raw `version.json` update checking.

### Bug Fixes
- **Quarter 4 Raft Exit Movement Freeze**: Fixed player movement locking after disembarking from river rafts in Quarter 4.
- **Asset Path Resolution**: Fixed missing button/sprite fallbacks when launching from Windows startup shortcuts with `System32` working directories.
- **Quarter 3 Alignment**: Fixed visual layout alignment in Quarter 3 puzzle overlays.

---

## [v1.0.0] — 2026-11-04
### Changes & Improvements
- **Initial Standalone Release**: Complete 4-stage interactive 2D mathematics adventure covering Quarter 1, Quarter 2, Quarter 3, and Summative Assessment with MediaPipe webcam hand-gesture controls, keyboard/mouse support, universal pause menu, offline-resilient cloud question/grade synchronization, and AMD A4-6300 APU 60 FPS optimizations.

### Bug Fixes
- **Multi-Hand Background Interference**: Added palm-span proximity filtering and multi-hand HUD warnings so background bystanders do not hijack cursor tracking.
- **Offline Evaluation Queueing**: Fixed unprocessable cloud evaluation payloads blocking subsequent offline sync retries.

---

## Copyright & Legal Notice

**Copyright © 2026 Cognitive Maze Development Team. All rights reserved.**

- **Independent Educational Software**: *Cognitive Maze* is an independent academic and educational software project created to support Grade 2 mathematics practice and classroom instruction. It is **not** affiliated with, sponsored by, endorsed by, or an official publication of the Department of Education (DepEd), the Bangko Sentral ng Pilipinas (BSP), Nintendo, or any government agency or third-party trademark owner.
- **Educational Currency Illustrations**: Stylized depictions of Philippine banknotes and coins are specimen educational illustrations used strictly for teaching currency recognition and arithmetic.
- **Open-Source Software Notices**: This software incorporates open-source components licensed under their respective terms, including Python (PSF License), Pygame (LGPL v2.1), OpenCV (Apache License 2.0), NumPy (BSD License), and Google MediaPipe (Apache License 2.0).
