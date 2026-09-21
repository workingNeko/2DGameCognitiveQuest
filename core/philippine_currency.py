# core/philippine_currency.py - Real Philippine Currency Definitions & Visual Renderer

import os
import pygame
import math
import random

# ============================================================
# PHILIPPINE CURRENCY DATASET (Real New Generation Currency)
# Excludes sub-peso centavos (5¢, 25¢, 1¢) to focus on active Peso denominations
# ============================================================

PHILIPPINE_CURRENCY = {
    # ---------------- Banknotes ----------------
    "bill_20": {
        "id": "bill_20",
        "name": "20 Peso Bill",
        "tagalog_name": "Dalawampung Piso",
        "symbol": "₱20",
        "value_text": "₱20",
        "value": 20,
        "value_peso": 20.0,
        "type": "banknote",
        "main_color": (234, 88, 12),       # Orange
        "color_accent": (234, 88, 12),
        "light_color": (251, 146, 60),
        "dark_color": (154, 52, 18),
        "portrait": "Manuel L. Quezon",
        "landmark": "Malacañang Palace & Banaue Rice Terraces",
        "color_hint": "Orange Banknote"
    },
    "bill_50": {
        "id": "bill_50",
        "name": "50 Peso Bill",
        "tagalog_name": "Limampung Piso",
        "symbol": "₱50",
        "value_text": "₱50",
        "value": 50,
        "value_peso": 50.0,
        "type": "banknote",
        "main_color": (225, 29, 72),       # Red / Pink
        "color_accent": (225, 29, 72),
        "light_color": (251, 113, 133),
        "dark_color": (159, 18, 57),
        "portrait": "Sergio Osmeña",
        "landmark": "First Philippine Assembly & Taal Lake",
        "color_hint": "Pink / Red Banknote"
    },
    "bill_100": {
        "id": "bill_100",
        "name": "100 Peso Bill",
        "tagalog_name": "Sandaang Piso",
        "symbol": "₱100",
        "value_text": "₱100",
        "value": 100,
        "value_peso": 100.0,
        "type": "banknote",
        "main_color": (124, 58, 237),      # Violet / Purple
        "color_accent": (124, 58, 237),
        "light_color": (192, 132, 252),
        "dark_color": (91, 33, 182),
        "portrait": "Manuel A. Roxas",
        "landmark": "Bangko Sentral ng Pilipinas & Mayon Volcano",
        "color_hint": "Purple / Violet Banknote"
    },
    "bill_200": {
        "id": "bill_200",
        "name": "200 Peso Bill",
        "tagalog_name": "Dalawandaang Piso",
        "symbol": "₱200",
        "value_text": "₱200",
        "value": 200,
        "value_peso": 200.0,
        "type": "banknote",
        "main_color": (22, 163, 74),       # Green
        "color_accent": (22, 163, 74),
        "light_color": (74, 222, 128),
        "dark_color": (20, 83, 45),
        "portrait": "Diosdado P. Macapagal",
        "landmark": "EDSA People Power II & Chocolate Hills",
        "color_hint": "Green Banknote"
    },
    "bill_500": {
        "id": "bill_500",
        "name": "500 Peso Bill",
        "tagalog_name": "Limandaang Piso",
        "symbol": "₱500",
        "value_text": "₱500",
        "value": 500,
        "value_peso": 500.0,
        "type": "banknote",
        "main_color": (202, 138, 4),       # Yellow / Gold
        "color_accent": (202, 138, 4),
        "light_color": (250, 204, 21),
        "dark_color": (113, 63, 18),
        "portrait": "Corazon & Benigno Aquino Jr.",
        "landmark": "EDSA People Power I & Underground River",
        "color_hint": "Yellow / Gold Banknote"
    },
    "bill_1000": {
        "id": "bill_1000",
        "name": "1000 Peso Bill",
        "tagalog_name": "Sanlibong Piso",
        "symbol": "₱1000",
        "value_text": "₱1000",
        "value": 1000,
        "value_peso": 1000.0,
        "type": "banknote",
        "main_color": (2, 132, 199),       # Cyan / Blue
        "color_accent": (2, 132, 199),
        "light_color": (56, 189, 248),
        "dark_color": (7, 89, 133),
        "portrait": "Jose Abad Santos, Vicente Lim, Josefa Llanes Escoda",
        "landmark": "Tubbataha Reefs Natural Park",
        "color_hint": "Blue / Cyan Banknote"
    },

    # ---------------- Coins ----------------
    "coin_1": {
        "id": "coin_1",
        "name": "1 Piso Coin",
        "tagalog_name": "Isang Piso",
        "symbol": "₱1",
        "value_text": "₱1",
        "value": 1.0,
        "value_peso": 1.0,
        "type": "coin",
        "style": "silver",
        "main_color": (148, 163, 184),     # Silver/Nickel
        "color_accent": (148, 163, 184),
        "light_color": (241, 245, 249),
        "dark_color": (71, 85, 105),
        "portrait": "Jose Rizal",
        "landmark": "Waling-waling Orchid / BSP",
        "color_hint": "Silver Coin with Jose Rizal"
    },
    "coin_5": {
        "id": "coin_5",
        "name": "5 Piso Coin",
        "tagalog_name": "Limang Piso",
        "symbol": "₱5",
        "value_text": "₱5",
        "value": 5.0,
        "value_peso": 5.0,
        "type": "coin",
        "style": "silver_ring",
        "main_color": (148, 163, 184),     # Nickel Plated
        "color_accent": (148, 163, 184),
        "light_color": (248, 250, 252),
        "dark_color": (71, 85, 105),
        "portrait": "Andres Bonifacio",
        "landmark": "Tayabak Vine / BSP",
        "color_hint": "Silver Coin with Andres Bonifacio"
    },
    "coin_10": {
        "id": "coin_10",
        "name": "10 Piso Coin",
        "tagalog_name": "Sampung Piso",
        "symbol": "₱10",
        "value_text": "₱10",
        "value": 10.0,
        "value_peso": 10.0,
        "type": "coin",
        "style": "silver_mabini",
        "main_color": (148, 163, 184),     # Silver
        "color_accent": (148, 163, 184),
        "light_color": (248, 250, 252),
        "dark_color": (51, 65, 85),
        "portrait": "Apolinario Mabini",
        "landmark": "Kapa-kapa Plant / BSP",
        "color_hint": "Silver Coin with Apolinario Mabini"
    },
    "coin_20": {
        "id": "coin_20",
        "name": "20 Piso Coin",
        "tagalog_name": "Dalawampung Piso",
        "symbol": "₱20",
        "value_text": "₱20",
        "value": 20.0,
        "value_peso": 20.0,
        "type": "coin",
        "style": "bimetal_gold",
        "main_color": (217, 119, 6),       # Bimetallic Gold outer ring, Silver core
        "color_accent": (217, 119, 6),
        "light_color": (251, 191, 36),
        "dark_color": (146, 64, 14),
        "portrait": "Manuel L. Quezon",
        "landmark": "Nilad Flower / Malacañang Palace",
        "color_hint": "Bimetallic Coin (Gold Ring & Silver Core)"
    }
}

# Surface cache
_SURFACE_CACHE = {}


def get_currency_info(currency_id):
    """Retrieve metadata dictionary for a currency ID."""
    return PHILIPPINE_CURRENCY.get(currency_id, None)


def get_randomized_quarter2_currency_pool(map_name="map4.txt", count=5, num_items=None, pool_size=None):
    """
    Returns a freshly randomized 5-item selection of real Philippine currency
    sampled without replacement across every map in Quarter 2.
    """
    target_count = num_items or pool_size or count or 5
    available_keys = list(PHILIPPINE_CURRENCY.keys())
    
    # Randomly select target_count distinct items from the 10 available currencies
    sampled_keys = random.sample(available_keys, min(target_count, len(available_keys)))
    random.shuffle(sampled_keys)
    return [PHILIPPINE_CURRENCY[k] for k in sampled_keys]


def load_real_currency_surface(currency_id, width=None, height=None):
    """Loads and scales authentic Philippine currency image from assets/images/currency/."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    img_path = os.path.join(base_dir, "assets", "images", "currency", f"{currency_id}.png")
    if not os.path.exists(img_path):
        img_path = os.path.join("assets", "images", "currency", f"{currency_id}.png")
    
    if not os.path.exists(img_path):
        return None
    try:
        surf = pygame.image.load(img_path).convert_alpha()
        if width is not None and height is not None:
            surf = pygame.transform.smoothscale(surf, (int(width), int(height)))
        return surf
    except Exception:
        return None


def render_banknote_surface(currency_info, width=170, height=86):
    """Renders authentic real Philippine banknote image with polished card border."""
    key = (currency_info["id"], "real_bill", width, height)
    if key in _SURFACE_CACHE:
        return _SURFACE_CACHE[key]

    real_img = load_real_currency_surface(currency_info["id"], width, height)
    if real_img:
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        # Clean rounded backing
        pygame.draw.rect(surf, (15, 23, 42, 220), (0, 0, width, height), border_radius=6)
        surf.blit(real_img, (0, 0))
        # Sleek accent outline
        accent = currency_info.get("main_color", (218, 165, 32))
        pygame.draw.rect(surf, accent, (0, 0, width, height), 2, border_radius=6)
        _SURFACE_CACHE[key] = surf
        return surf

    # Procedural Vector Fallback
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    main_col = currency_info["main_color"]
    light_col = currency_info["light_color"]
    dark_col = currency_info["dark_color"]
    symbol = currency_info["symbol"]
    
    rect = pygame.Rect(0, 0, width, height)
    pygame.draw.rect(surf, main_col, rect, border_radius=8)
    inner_rect = rect.inflate(-6, -6)
    pygame.draw.rect(surf, (255, 255, 255, 100), inner_rect, 1, border_radius=6)
    pygame.draw.rect(surf, dark_col, rect, 2, border_radius=8)

    val_font = pygame.font.SysFont("Impact", max(16, int(height * 0.38)))
    val_surf = val_font.render(symbol, True, (255, 255, 255))
    surf.blit(val_surf, (8, 6))

    _SURFACE_CACHE[key] = surf
    return surf


def render_coin_surface(currency_info, size_or_w=86, height=None):
    """Renders authentic real Philippine coin image."""
    if height is not None:
        size = min(int(size_or_w), int(height))
    elif isinstance(size_or_w, (tuple, list)):
        size = min(int(size_or_w[0]), int(size_or_w[1]))
    else:
        size = int(size_or_w)

    key = (currency_info["id"], "real_coin", size)
    if key in _SURFACE_CACHE:
        return _SURFACE_CACHE[key]

    real_img = load_real_currency_surface(currency_info["id"], size, size)
    if real_img:
        _SURFACE_CACHE[key] = real_img
        return real_img

    # Procedural Vector Fallback
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    radius = int(size * 0.46)
    main_col = currency_info["main_color"]
    symbol = currency_info["symbol"]

    pygame.draw.circle(surf, main_col, (cx, cy), radius)
    pygame.draw.circle(surf, (255, 255, 255), (cx, cy), radius, 2)
    font_size = max(11, int(radius * 0.72))
    v_font = pygame.font.SysFont("Impact", font_size)
    txt_surf = v_font.render(symbol, True, (15, 23, 42))
    surf.blit(txt_surf, txt_surf.get_rect(center=(cx, cy)))

    _SURFACE_CACHE[key] = surf
    return surf


def render_currency_token(currency_info, width=170, height=86):
    """Universal token renderer displaying real banknote/coin images with clear denomination badges."""
    if currency_info.get("type") in ["banknote", "bill"]:
        return render_banknote_surface(currency_info, width, height)
    else:
        # Render real coin centered inside a stylish display card with metadata
        card_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        card_rect = pygame.Rect(0, 0, width, height)
        pygame.draw.rect(card_surf, (30, 41, 59, 230), card_rect, border_radius=10)
        pygame.draw.rect(card_surf, currency_info["main_color"], card_rect, 2, border_radius=10)
        
        # Render real coin on left
        coin_size = min(height - 10, int(width * 0.44))
        coin_img = render_coin_surface(currency_info, coin_size)
        card_surf.blit(coin_img, (8, (height - coin_size) // 2))
        
        # Details on right
        t_font = pygame.font.SysFont("Arial", 12, bold=True)
        s_font = pygame.font.SysFont("Arial", 10)
        
        name_surf = t_font.render(currency_info["name"], True, (255, 255, 255))
        tag_surf = s_font.render(currency_info.get("tagalog_name", ""), True, (254, 240, 138))
        hint_surf = s_font.render(currency_info.get("portrait", ""), True, (148, 163, 184))
        
        card_surf.blit(name_surf, (coin_size + 14, 12))
        card_surf.blit(tag_surf, (coin_size + 14, 30))
        card_surf.blit(hint_surf, (coin_size + 14, 48))
        
        return card_surf
