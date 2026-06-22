import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.carts.model import Cart, CartItem
from app.modules.carts.schema import CartItemInput, CartItemResponse, CartResponse
from app.modules.images.model import Image
from app.modules.products.model import Product, ProductUnits
from app.modules.units.model import Unit


def _get_cart_query(user_id: uuid.UUID):
    return (
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(
            selectinload(Cart.items)
            .selectinload(CartItem.product)
            .selectinload(Product.images),
            selectinload(Cart.items).selectinload(CartItem.unit_ref),
        )
    )


def get_or_create_cart(db: Session, user_id: uuid.UUID) -> Cart:
    cart = db.scalar(_get_cart_query(user_id))
    if cart is None:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.flush()
        # reload with relationships
        db.refresh(cart)
    return cart


def _build_item_response(db: Session, item: CartItem) -> CartItemResponse:
    product = item.product
    unit_ref = item.unit_ref

    # get unit price from product_units if unit is specified
    unit_price: int | None = getattr(product, "price", None)
    if item.unit_id and product:
        pu_price = db.scalar(
            select(ProductUnits.price).where(
                ProductUnits.product_id == item.product_id,
                ProductUnits.unit_id == item.unit_id,
            )
        )
        if pu_price is not None:
            unit_price = pu_price

    # get primary image URL
    image_url: str | None = None
    if product and product.images:
        primary = next((img for img in product.images if img.is_primary), None)
        image_url = (primary or product.images[0]).file_url

    return CartItemResponse(
        id=item.id,
        product_id=item.product_id,
        unit_id=item.unit_id,
        quantity=item.quantity,
        product_name=getattr(product, "name", None),
        unit_name=getattr(unit_ref, "name", None),
        unit_price=unit_price,
        image_url=image_url,
    )


def get_cart(db: Session, user_id: uuid.UUID) -> CartResponse:
    cart = get_or_create_cart(db, user_id)
    items = [_build_item_response(db, item) for item in cart.items]
    return CartResponse(id=cart.id, items=items)


def sync_cart(db: Session, user_id: uuid.UUID, payload_items: list[CartItemInput]) -> CartResponse:
    cart = get_or_create_cart(db, user_id)

    # delete all existing items
    for existing_item in list(cart.items):
        db.delete(existing_item)
    db.flush()

    # insert new items
    for item_in in payload_items:
        new_item = CartItem(
            cart_id=cart.id,
            product_id=item_in.product_id,
            unit_id=item_in.unit_id,
            quantity=item_in.quantity,
        )
        db.add(new_item)

    db.flush()

    # reload cart with updated items and relationships
    cart = db.scalar(_get_cart_query(user_id))
    if cart is None:
        return CartResponse(id=cart.id if cart else uuid.uuid4(), items=[])

    items = [_build_item_response(db, item) for item in cart.items]
    return CartResponse(id=cart.id, items=items)
