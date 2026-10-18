"""C50 unsupported-claim check (E13) and C51 repeated-run status (E2, E4, E9, E13), written before any of those runs."""
from backend.catalogue.seed import load_lexicon
from backend.evaluation.claims import shown_reason_problems
from backend.evaluation.runs import aggregate

LEX = load_lexicon()


def test_price_stock_and_health_claims_are_flagged():
    dish_terms = {"paneer", "butter", "tomato"}
    assert shown_reason_problems("Rich and creamy, a weekend favourite", dish_terms, LEX) == []
    assert "price_or_stock" in shown_reason_problems("Great value at ₹120", dish_terms, LEX)[0]
    assert "price_or_stock" in shown_reason_problems("Only a few left in stock", dish_terms, LEX)[0]
    assert "claim:healthy" in shown_reason_problems("A healthy pick for tonight", dish_terms, LEX)
    assert "claim:immunity" in shown_reason_problems("Boosts immunity", dish_terms, LEX)


def test_ingredient_not_in_the_dish_is_flagged():
    dish_terms = {"paneer", "butter", "tomato"}
    assert shown_reason_problems("Soft paneer in a buttery tomato sauce", dish_terms, LEX) == []
    assert "ingredient:chicken" in shown_reason_problems("Tender chicken in a rich gravy", dish_terms, LEX)


def test_aggregate_uses_the_median_run_and_any_critical():
    runs = [{"accuracy": 0.80}, {"accuracy": 0.90}, {"accuracy": 0.87}]
    out = aggregate(runs, {"accuracy": ("min", 0.85)}, critical=[[], [], []])
    assert out["metrics"]["accuracy"]["median"] == 0.87 and out["metrics"]["accuracy"]["range"] == [0.80, 0.90]
    assert out["status"] == "PASS"
    assert aggregate(runs, {"accuracy": ("min", 0.85)}, critical=[[], ["x"], []])["status"] == "FAIL"
    assert aggregate([{"fp": 0.1}, {"fp": 0.0}, {"fp": 0.2}], {"fp": ("max", 0.05)}, critical=[[], [], []])["status"] == "FAIL"
