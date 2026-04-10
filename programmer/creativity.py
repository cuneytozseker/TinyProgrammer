"""
Creative dimensions for prompt variety.

The device picks a combination of style, palette, inspiration seed, and
mood directive per cycle. This module holds the data lists and the
selection helpers.
"""

import random


# =============================================================================
# Program type categories (for mood biasing)
# =============================================================================

CATEGORIES = {
    "motion": [
        "bouncing_ball", "pong", "orbit_system", "pendulum",
        "spring_chain", "particle_fountain", "gravity_well", "flock",
    ],
    "grid": [
        "game_of_life", "cellular_automata", "wire_world",
        "ant_trail", "langton_ant", "voronoi_grow",
    ],
    "generative": [
        "pattern", "generative_glyphs", "l_system",
        "fractal_tree", "tile_weaver", "mandala", "plasma",
    ],
    "natural": [
        "rain", "starfield", "fire", "lightning",
        "snow", "waves", "aurora",
    ],
    "abstract": [
        "spiral", "random_walker", "animation", "brush_strokes",
        "geometric_drift", "color_fields", "warp_grid",
    ],
    "math": [
        "wireframe_plot",
    ],
}

# Reverse lookup: program_type -> category
TYPE_TO_CATEGORY = {
    ptype: cat
    for cat, types in CATEGORIES.items()
    for ptype in types
}


# =============================================================================
# Creative dimensions
# =============================================================================

STYLE_MODIFIERS = [
    "minimalist", "chaotic", "symmetrical", "organic", "geometric",
    "glitchy", "dreamy", "brutalist", "ornate", "sparse",
    "dense", "kinetic", "still", "layered", "monochromatic",
]

COLOR_PALETTES = [
    "warm earth tones", "cool ocean", "neon on black", "pastel morning",
    "monochrome greens", "monochrome blues", "monochrome reds",
    "sunset gradient", "sunrise gradient",
    "candy pop", "toxic sludge", "vintage print", "faded polaroid",
]

INSPIRATION_SEEDS = {
    "nature": [
        "rain on a window", "fireflies at dusk", "kelp forest",
        "spiderweb dew", "tide pool", "frost crystals", "leaves falling",
    ],
    "mechanical": [
        "clock gears", "factory lights", "circuit board",
        "printing press", "pneumatic tubes",
    ],
    "abstract": [
        "a fever dream", "zero gravity", "static electricity",
        "vapor trails", "echoes",
    ],
    "architectural": [
        "brutalist facade", "stained glass", "art deco",
        "japanese garden", "labyrinth", "stacked windows",
    ],
    "musical": [
        "a slow waltz", "techno pulse", "heartbeat",
        "ocean swells", "jazz improv", "metronome",
    ],
}

ALL_SEEDS = [s for seeds in INSPIRATION_SEEDS.values() for s in seeds]


# =============================================================================
# Mood → creativity mapping
# =============================================================================

MOOD_CREATIVITY = {
    "hopeful": {
        "categories": None,  # any
        "styles": ["organic", "dreamy"],
        "directive": "try something gentle and open-ended",
    },
    "focused": {
        "categories": ["grid", "generative", "math"],
        "styles": ["geometric", "symmetrical"],
        "directive": "follow a clean mathematical rule",
    },
    "curious": {
        "categories": None,
        "styles": ["glitchy", "layered"],
        "directive": "combine two things you haven't combined before",
    },
    "proud": {
        "categories": ["motion", "generative"],
        "styles": ["dense", "ornate"],
        "directive": "show off, make it elaborate",
    },
    "frustrated": {
        "categories": ["motion"],
        "styles": ["minimalist", "sparse"],
        "directive": "go back to basics, make something reliable",
    },
    "tired": {
        "categories": ["natural", "abstract"],
        "styles": ["still", "monochromatic"],
        "directive": "keep it simple and meditative",
    },
    "playful": {
        "categories": None,
        "styles": ["chaotic", "kinetic"],
        "directive": "break the rules, have fun with it",
    },
    "determined": {
        "categories": ["grid", "motion"],
        "styles": ["brutalist", "kinetic"],
        "directive": "commit to one idea and push it hard",
    },
}


# =============================================================================
# Excluded style + palette combinations
# =============================================================================

EXCLUDED_COMBOS = [
    ("monochromatic", "candy pop"),
    ("brutalist", "pastel morning"),
    ("minimalist", "toxic sludge"),
    ("dreamy", "brutalist facade"),  # style vs seed check not needed but listed
]


# =============================================================================
# Selection helpers
# =============================================================================

# Probability of including an inspiration seed per cycle
SEED_PROBABILITY = 0.6

# Probability of picking a style from mood preference vs random
MOOD_STYLE_PROBABILITY = 0.8


def pick_creative_dimensions(mood: str) -> dict:
    """Pick style, palette, inspiration seed, and directive for a cycle.

    Returns a dict with keys: style, palette, inspiration_seed (may be None),
    directive, category_bias (list of preferred categories or None).
    """
    mood_data = MOOD_CREATIVITY.get(mood, MOOD_CREATIVITY["hopeful"])

    # Style: 80% from mood preference, 20% fully random
    if mood_data["styles"] and random.random() < MOOD_STYLE_PROBABILITY:
        style = random.choice(mood_data["styles"])
    else:
        style = random.choice(STYLE_MODIFIERS)

    # Palette: random, re-roll if blacklisted against chosen style
    palette = random.choice(COLOR_PALETTES)
    for _ in range(10):
        if (style, palette) not in EXCLUDED_COMBOS:
            break
        palette = random.choice(COLOR_PALETTES)

    # Inspiration seed: probabilistic
    seed = random.choice(ALL_SEEDS) if random.random() < SEED_PROBABILITY else None

    return {
        "style": style,
        "palette": palette,
        "inspiration_seed": seed,
        "directive": mood_data["directive"],
        "category_bias": mood_data["categories"],
    }


def pick_program_type(mood: str, program_types: list, last_type: str = None) -> str:
    """Pick a program type, biased by the mood's preferred categories.

    Args:
        mood: current mood name
        program_types: list of (name, weight) tuples from config.PROGRAM_TYPES
        last_type: avoid picking this (for immediate repeat avoidance)

    Types in the mood's preferred categories get a 4x weight boost.
    """
    if not program_types:
        return "pattern"

    mood_data = MOOD_CREATIVITY.get(mood, MOOD_CREATIVITY["hopeful"])
    preferred_cats = mood_data.get("categories")

    names = []
    weights = []
    for ptype, w in program_types:
        if ptype == last_type:
            continue
        names.append(ptype)
        if preferred_cats:
            cat = TYPE_TO_CATEGORY.get(ptype)
            if cat in preferred_cats:
                weights.append(w * 4)
            else:
                weights.append(w)
        else:
            weights.append(w)

    if not names:
        # Everything was filtered out (only last_type was available)
        return program_types[0][0]
    return random.choices(names, weights=weights)[0]
