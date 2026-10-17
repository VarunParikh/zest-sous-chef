"""E3 item matching, fixed before any E3 run (Evaluation Plan §4 E3)."""
from backend.catalogue.seed import load_lexicon
from backend.evaluation.photos import labels_from, match

LEX = load_lexicon()


def test_alternatives_optional_and_parentheticals():
    labels = labels_from(["red capsicum", "zucchini or cucumber", "fennel (uncertain)", "muffins (cooked)"], LEX)
    assert [l.optional for l in labels] == [False, False, True, False]
    assert labels[1].alternatives == [{"zucchini"}, {"cucumber"}]
    assert labels[3].alternatives == [{"muffin"}]


def test_alias_plural_and_subset_matching():
    labels = labels_from(["red capsicum", "tomato", "cherry tomato", "button mushroom"], LEX)
    m = match([("Red Bell Pepper", 0.9), ("tomatoes", 0.8), ("tomato", 0.7), ("mushrooms", 0.95)], labels, LEX)
    assert m.true_positives == 4 and m.required_found == 4 and m.false_positives == 0


def test_one_detection_matches_one_label():
    labels = labels_from(["tomato", "cherry tomato"], LEX)
    m = match([("tomato", 0.9)], labels, LEX)
    assert m.true_positives == 1 and m.required_found == 1 and m.required_total == 2


def test_optional_found_counts_for_precision_not_recall():
    labels = labels_from(["egg", "fennel (uncertain)"], LEX)
    m = match([("fennel", 0.9)], labels, LEX)
    assert m.true_positives == 1 and m.required_found == 0 and m.required_total == 1


def test_wrong_items_are_false_positives():
    labels = labels_from(["milk"], LEX)
    m = match([("pizza", 0.9), ("milk", 0.8)], labels, LEX)
    assert (m.true_positives, m.false_positives) == (1, 1)
