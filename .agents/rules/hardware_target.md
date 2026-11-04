# Target Hardware Specification: AMD A4-6300 APU

## Hardware Profile
- **Processor**: AMD A4-6300 APU (Dual-Core, 2 Threads, 3.7 GHz base / 3.9 GHz boost, Piledriver 32nm).
- **Cache**: 1MB L2 cache total (shared between 2 cores), **0MB L3 cache**.
- **Integrated GPU**: AMD Radeon HD 8370D (128 Radeon shader cores, DirectX 11, shared DDR3 system memory).
- **Memory**: Typically 4GB to 8GB DDR3 (memory bandwidth is shared between CPU and iGPU).
- **Operating System**: Windows 64-bit.

## Strict Architectural & Performance Rules
All code additions, refactorings, optimizations, and features MUST strictly comply with these hardware constraints:

1. **Dual-Core Threading Budget**:
   - There are ONLY 2 physical cores / 2 threads available.
   - Core allocation:
     - Core 1: Pygame main loop (event handling, physics/game logic, screen rendering).
     - Core 2: OpenCV camera capture & MediaPipe hand tracking inference thread.
   - **Never** spawn uncontrolled thread pools, background worker storms, or busy-wait loops (`while True: pass`).
   - Use non-blocking locks (`threading.Lock`) and small thread sleeps (`time.sleep(0.002-0.005)`) in worker loops to yield CPU execution slices.

2. **MediaPipe Inference Throttling & Sizing**:
   - **Max Resolution**: Never feed 640×480 or higher frames into MediaPipe. Always downscale inference frames to 320×240 (`cv2.INTER_LINEAR` or `cv2.INTER_NEAREST`).
   - **Single Hand Only**: Maintain `num_hands=1` / `max_num_hands=1`.
   - **Lightweight Models**: Use `model_complexity=0` for legacy Solutions API or the compact `hand_landmarker.task` with minimal thresholding.
   - **Direct Memory Re-use**: Avoid creating new NumPy arrays or allocating extra buffers per camera frame.

3. **L2 Cache Sensitivity (1MB L2, No L3)**:
   - With only 1MB L2 cache and no L3 cache, memory thrashing and large object allocations cause severe CPU pipeline stalls.
   - Keep per-frame hot-loop data structures minimal and flat.
   - Avoid instantiating new objects, dictionaries, or lists within `update()` and `draw()` functions every frame.

4. **Pygame Rendering & Asset Memoization**:
   - **Zero Per-Frame File I/O**: Never load images or sounds inside game loops (`pygame.image.load`, `pygame.mixer.Sound`). All assets must be loaded and converted during screen initialization or preloaded.
   - **Convert Surfaces**: Always call `.convert()` or `.convert_alpha()` on loaded Pygame surfaces so the pixel format matches the display surface, avoiding expensive CPU blit conversions.
   - **Text Memoization**: Never call `font.render()` every frame for static or slowly-changing strings. Cache rendered text surfaces.
   - **Surface Scaling**: Cache scaled sprites/textures instead of calling `pygame.transform.scale()` or `pygame.transform.smoothscale()` inside `draw()` loops.

5. **Audio Buffer Latency**:
   - Initialize Pygame mixer with low buffer sizes (e.g. `buffer=512`) to prevent audio crackle and keep CPU mixing overhead minimal.

6. **Standalone Build Packaging**:
   - Exclude unnecessary heavy packages (PyTorch, TensorFlow, Pandas, Matplotlib, SciPy, Jupyter) from PyInstaller builds to keep binary size compact and minimize RAM footprint.
