# core/dynamic_quiz_manager.py
"""
Dynamic Quiz & Station Manager for Cognitive Quest 2D.
Enables dynamic game adjustment when questions are added, updated, or removed in the webapp:
- Automatically provisions map coordinates for additional station NPCs
- Distributes dynamic stations evenly across walkable map terrain
- Ensures all questions correspond to distinct in-game NPCs
"""

import math

# Maximum questions that the game can handle per quarter and in the summative assessment (Strict upper ceiling: 15)
MAX_QUESTIONS_PER_QUARTER = 15


def validate_and_clamp_questions(questions, quarter_num=None, max_allowed=MAX_QUESTIONS_PER_QUARTER):
    """
    Error handler and dynamic validator for cloud-supplied quiz questions.
    - Enforces strict upper capacity limit: accepts up to `max_allowed` (15 questions max)
      from Quarter 1 to Summative Assessment.
    - If webapp provides > 15 questions, logs an explicit warning/error handler notice
      and safely clamps to the first 15 questions.
    - Validates that each item is a valid dictionary with required question content.
    - Filters out malformed, None, or empty question entries to prevent runtime crashes.
    
    Returns:
        list of validated question dicts, clamped to at most `max_allowed` (15).
    """
    if not questions or not isinstance(questions, (list, tuple)):
        return []

    stage_name = (
        f"Quarter {quarter_num}"
        if quarter_num in (1, 2, 3)
        else ("Summative Assessment" if quarter_num == 4 else f"Stage {quarter_num or 'Unknown'}")
    )

    # 1. Validate structure of each question entry
    valid_questions = []
    for idx, q in enumerate(questions):
        if not isinstance(q, dict):
            print(f"[QUESTION FORMAT ERROR] {stage_name}: Question #{idx + 1} is not a valid dict (type={type(q).__name__}). Skipping.")
            continue
        # Require non-empty question text or prompt
        q_text = str(q.get("question") or q.get("text") or q.get("prompt") or "").strip()
        if not q_text:
            print(f"[QUESTION FORMAT ERROR] {stage_name}: Question #{idx + 1} has empty text/prompt. Skipping.")
            continue
        valid_questions.append(q)

    # 2. Strict capacity check & error handler for webapp providing > 15 questions
    raw_count = len(valid_questions)
    if raw_count > max_allowed:
        print(
            f"[QUESTION OVERFLOW HANDLER] {stage_name}: Web app provided {raw_count} questions, "
            f"exceeding safe maximum capacity of {max_allowed}. "
            f"Clamping and safely accepting first {max_allowed} questions only."
        )
        return valid_questions[:max_allowed]

    return valid_questions


def allocate_dynamic_stations(
    game_map,
    existing_stations,
    needed_count,
    forbidden_tiles=None,
    walkable_chars=None
):
    """
    Dynamically expands station coordinates on the map if `needed_count` > `len(existing_stations)`.
    Enforces a strict upper ceiling of MAX_QUESTIONS_PER_QUARTER (15 questions max).
    Uses farthest-point sampling on walkable tiles to place new NPCs cleanly without crowding.
    
    Returns:
        dict or list: matching the input format with at most MAX_QUESTIONS_PER_QUARTER stations.
    """
    # Enforce maximum 15 questions per quarter / summative assessment
    needed_count = min(needed_count, MAX_QUESTIONS_PER_QUARTER)

    was_list = isinstance(existing_stations, (list, tuple))
    res_stations = {}
    if isinstance(existing_stations, dict):
        res_stations = dict(existing_stations)
    elif isinstance(existing_stations, (list, tuple)):
        for idx, item in enumerate(existing_stations, start=1):
            if isinstance(item, (tuple, list)) and len(item) == 2 and isinstance(item[1], (tuple, list)):
                res_stations[item[0]] = item[1]
            else:
                res_stations[idx] = item

    if needed_count <= len(res_stations):
        return list(res_stations.values()) if was_list else res_stations

    if forbidden_tiles is None:
        forbidden_tiles = set()
    else:
        forbidden_tiles = set(forbidden_tiles)

    if walkable_chars is None:
        walkable_chars = {"G", "#", "1", "2", "3", "4", "5", "6", "7", "8", "9", "P", "B", "r", "l", "u", "d"}

    # Avoid occupied station tiles
    occupied_tiles = set(res_stations.values()) | forbidden_tiles

    rows = len(game_map)
    if rows == 0:
        return list(res_stations.values()) if was_list else res_stations
    cols = max(len(r) for r in game_map)

    # 1. Identify all valid walkable candidate tiles
    candidates = []
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    for y in range(rows):
        row_str = game_map[y]
        for x in range(len(row_str)):
            tile_char = row_str[x]
            if tile_char not in walkable_chars:
                continue
            if (x, y) in occupied_tiles:
                continue

            # Ensure candidate has at least one walkable adjacent tile so player can stand next to it
            has_walkable_neighbor = False
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= ny < rows and 0 <= nx < len(game_map[ny]):
                    if game_map[ny][nx] in walkable_chars and (nx, ny) not in occupied_tiles:
                        has_walkable_neighbor = True
                        break

            if has_walkable_neighbor:
                candidates.append((x, y))

    if not candidates:
        return list(res_stations.values()) if was_list else res_stations

    # 2. Assign extra stations using deterministic spatial dispersion
    num_to_add = needed_count - len(res_stations)
    existing_ids = sorted(res_stations.keys())
    next_id = (max(existing_ids) + 1) if existing_ids else 1

    current_station_positions = list(res_stations.values())

    for _ in range(num_to_add):
        if not candidates:
            break

        best_candidate = None
        best_score = -1.0

        if not current_station_positions:
            # Pick center-most tile
            cx, cy = cols / 2.0, rows / 2.0
            best_candidate = min(candidates, key=lambda c: math.hypot(c[0] - cx, c[1] - cy))
        else:
            # Pick candidate that maximizes minimum distance to all placed stations
            for cand in candidates:
                min_dist = min(math.hypot(cand[0] - pos[0], cand[1] - pos[1]) for pos in current_station_positions)
                # Deterministic tie-breaker using coordinates
                score = min_dist * 1000.0 - (cand[1] * 0.1 + cand[0] * 0.001)
                if score > best_score:
                    best_score = score
                    best_candidate = cand

        if best_candidate is not None:
            res_stations[next_id] = best_candidate
            current_station_positions.append(best_candidate)
            occupied_tiles.add(best_candidate)
            candidates.remove(best_candidate)
            next_id += 1

    return list(res_stations.values()) if was_list else res_stations
