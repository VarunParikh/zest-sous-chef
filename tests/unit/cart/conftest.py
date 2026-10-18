import pytest

from backend.cart.models import Cart, CartDish, CartLine
from backend.catalogue.store import load_store

BUTTER = "b055-5af3aded"  # packs 100 g, 200 g, 500 g
PANEER = "b054-09ede858"  # packs 200 g, 500 g


@pytest.fixture(scope="session")
def store():
    return load_store()


def line(lid, cd, variant, qty, item="butter", unit="g", **kw):
    return CartLine(line_id=lid, cart_dish_id=cd, ingredient_name=item, need_qty=qty, need_unit=unit,
                    variant_id=variant, **kw)


def cart(*dishes) -> Cart:
    """cart(("cd_1", [line...]), ("cd_2", [line...]))"""
    return Cart(dishes=[CartDish(cart_dish_id=cd, dish_id=None, name=cd, source="text", lines=ls) for cd, ls in dishes])


def lines(c: Cart) -> dict[str, CartLine]:
    return {ln.line_id: ln for d in c.dishes for ln in d.lines}
