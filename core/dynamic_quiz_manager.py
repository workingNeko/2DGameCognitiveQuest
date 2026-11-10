# core/dynamic_quiz_manager.py
"""
Dynamic Quiz & Station Manager for Cognitive Quest 2D.
Enables dynamic game adjustment when questions are added, updated, or removed in the webapp:
- Automatically provisions map coordinates for additional station NPCs
- Distributes dynamic stations evenly across walkable map terrain
- Ensures all questions correspond to distinct in-game NPCs
"""

import math

# Maximum questions that the game can handle per quarter and in the summative assessment
MAX_QUESTIONS_PER_QUARTER = 10


def allocate_dynamic_stations(
    game_map,
    existing_stations,
    needed_count,
    forbidden_tiles=None,
    walkable_chars=None
):
    """
    Dynamically expands station coordinates on the map if `needed_count` > `len(existing_stations)`.
    Enforces a strict upper ceiling of MAX_QUESTIONS_PER_QUARTER (10 questions max).
    Uses farthest-point sampling on walkable tiles to place new NPCs cleanly without crowding.
    
    Returns:
        dict or list: matching the input format with at most MAX_QUESTIONS_PER_QUARTER stations.
    """
    # Enforce maximum 10 questions per quarter / summative assessment
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
