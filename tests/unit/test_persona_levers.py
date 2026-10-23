"""T-130 (C84, Personas v0.2): the personas shown in the app set their own weights; the rules that decide which dishes
are allowed (diet, faith, specialised diets) and gender are exactly as in v2.0.0, so eligibility is unchanged."""
from backend.api.sessions import load_presets
from backend.session.levers import LeverSet, offered

RULES_V2 = {  # persona: (gender, diet, faith, specialised diets), as released in v2.0.0
    "Meera Shah": ("Female", "Jain (No Root Veggies / Pure Veg)", "Jain (Strict Root-Free)", ["Standard / Balanced"]),
    "Rohan Deshmukh": ("Male", "Pure Veg (Strict)", "Hindu (Regular)", ["Standard / Balanced"]),
    "Imran Qureshi": ("Male", "Non-Veg / Flexitarian", "Muslim (Strict Halal Only)", ["Standard / Balanced"]),
    "Ananya Iyer": ("Female", "Pure Veg (Strict)", "Hindu (Shravan Month / Fasting Active)", ["Standard / Balanced"]),
    "Karan Malhotra": ("Male", "Non-Veg / Flexitarian", "None / Secular", ["Keto Diet", "High-Protein Fitness"]),
    "Priya Nair": ("Female", "Pure Veg (Strict)", "None / Secular", ["Vegan", "Gluten-Free"]),
    "Alex (Reviewer)": ("Unisex / Neutral", "Non-Veg / Flexitarian", "None / Secular", ["Standard / Balanced"]),
    "Lakshmi Pillai": ("Female", "Pure Veg (Strict)", "Hindu (Regular)", ["Intermittent Fasting / Low-GI"]),
    "Jordan Fernandes (control)": ("Unisex / Neutral", "Non-Veg / Flexitarian", "None / Secular", ["Standard / Balanced"]),
    "Rahul Verma": ("Male", "Non-Veg / Flexitarian", "None / Secular", ["Standard / Balanced"]),
    "Vikram Rao": ("Male", "Non-Veg / Flexitarian", "None / Secular", ["High-Protein Fitness"]),
}


def test_t130_each_shown_persona_sets_its_own_weights():
    presets, defaults = load_presets(), LeverSet().weights
    shown = {n: p for n, p in presets.items() if offered(n)}
    assert len(shown) == 8
    assert all(p.weights != defaults for p in shown.values()), [n for n, p in shown.items() if p.weights == defaults]


def test_t130_control_and_hidden_personas_keep_their_values():
    presets = load_presets()
    assert presets["Jordan Fernandes (control)"].model_dump(exclude={"gender"}) == LeverSet().model_dump(exclude={"gender"})
    assert presets["Alex (Reviewer)"] == LeverSet()
    assert presets["Vikram Rao"].weights == LeverSet().weights


def test_t130_rules_and_gender_unchanged_from_v2_0_0():
    presets = load_presets()
    assert set(presets) == set(RULES_V2)
    got = {n: (p.gender, p.diet, p.faith, sorted(p.specialized_diets)) for n, p in presets.items()}
    assert got == {n: (g, d, f, sorted(s)) for n, (g, d, f, s) in RULES_V2.items()}
