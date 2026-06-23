from app.modules.order_statuses.constants import OrderStatusCode


class _SafeDict(dict):
	def __missing__(self, key):
		return ""


def _get_item_field(item, field: str, default=None):
	if isinstance(item, dict):
		return item.get(field, default)
	return getattr(item, field, default)


def _get_item_product_label(item) -> str:
	product_name = _get_item_field(item, "product_name")
	if product_name:
		return str(product_name)

	product = _get_item_field(item, "product")
	if product is not None:
		if isinstance(product, dict):
			name = product.get("name")
		else:
			name = getattr(product, "name", None)
		if name:
			return str(name)

	product_id = _get_item_field(item, "product_id", "-")
	return str(product_id)


def _build_items_summary(items) -> str:
	lines = []
	for item in items:
		product_label = _get_item_product_label(item)
		unit = _get_item_field(item, "unit", "-") or "-"
		quantity = _get_item_field(item, "quantity", 0)
		lines.append(f"- {product_label} / {unit} x {quantity}")
	return "\n".join(lines)


def _build_email_context(order, status_name: str) -> dict[str, object]:
	items = getattr(order, "items", []) or []
	items_summary = _build_items_summary(items)

	return {
		"order_no": order.order_no,
		"status_name": status_name,
		"status_code": order.order_status_code,
		"customer_name": order.customer_name or order.orderer_name or "-",
		"customer_email": order.customer_email,
		"orderer_name": order.orderer_name or "-",
		"orderer_phone": order.orderer_phone or "-",
		"orderer_email": order.orderer_email or order.customer_email,
		"address": order.address or "-",
		"coupon_code": order.coupon_code or "",
		"delivery_method_label": getattr(order, "delivery_method_label", None) or "",
		"payment_method_label": getattr(order, "payment_method_label", None) or "",
		"subtotal_amount": order.subtotal_amount,
		"discount_amount": order.discount_amount,
		"shipping_fee": getattr(order, "shipping_fee", 0),
		"total_amount": order.total_amount,
		"bank_transfer_last5": order.bank_transfer_last5 or "",
		"items_count": len(items),
		"items_summary": items_summary,
		"created_at": order.created_at.isoformat() if getattr(order, "created_at", None) else "",
		"updated_at": order.updated_at.isoformat() if order.updated_at else "",
	}


def _render_template(template: str, context: dict[str, object]) -> str:
	return template.format_map(_SafeDict({k: str(v) for k, v in context.items()}))


def build_customer_order_status_email(order, status_name, subject_template: str | None = None, body_template: str | None = None):
	status_templates = {
		OrderStatusCode.ORDER_CREATED.value: (
			f"Mekarang訂購通知！訂單 {order.order_no} 已建立",
			"我們已收到您的訂單，待訂單確認後將發送繳費明細，請耐心等候。",
		),
		OrderStatusCode.ORDER_CONFIRMED_AND_PENDING_PAYMENT.value: (
			f"Mekarang訂購通知！訂單 {order.order_no} 已確認，請完成付款",
			(
				"您的訂單已確認，\n"
				"後續將依流程安排出貨。\n"
				"繳費明細如下：\n"
				f"訂單編號：{order.order_no}\n"
				f"收件人：{order.customer_name or order.orderer_name or '-'}\n"
				f"聯絡信箱：{order.customer_email}\n"
				f"總金額：{order.total_amount}\n"
				"請於7天內完成付款，逾期訂單將自動取消。\n"
				"如有任何問題，歡迎聯繫客服。\n"
			),
		),
		OrderStatusCode.PAID_AND_PREPARING.value: (
			f"訂單 {order.order_no} 備貨中",
			"我們已收到您的付款，訂單正在備貨中，完成後會通知您出貨。",
		),
		OrderStatusCode.SHIPPING.value: (
			f"訂單 {order.order_no} 已出貨",
			"您的訂單已出貨，請留意收件。",
		),
		OrderStatusCode.CANCELED.value: (
			f"訂單 {order.order_no} 已取消",
			"您的訂單已取消；若這不是您預期的結果，請聯繫客服。",
		),
		OrderStatusCode.DELIVERED.value: (
			f"訂單 {order.order_no} 已送達",
			"您的訂單已送達，感謝您的訂購。",
		),
		OrderStatusCode.REFUNDED.value: (
			f"訂單 {order.order_no} 已退款",
			"您的退款已處理完成，款項將依原付款方式返還，請留意帳戶入帳。",
		),
		OrderStatusCode.OTHER.value: (
			f"訂單 {order.order_no} 狀態更新",
			"您的訂單狀態已更新，如有疑問請聯繫客服。",
		),
	}
	subject, intro = status_templates.get(
		order.order_status_code,
		(f"訂單 {order.order_no} 狀態更新", "您的訂單狀態已更新。"),
	)
	context = _build_email_context(order, status_name)
	if subject_template:
		subject = _render_template(subject_template, context)
	if body_template:
		return subject, _render_template(body_template, context)

	body = (
		f"{intro}\n\n"
		f"訂單編號：{order.order_no}\n"
		f"目前狀態：{status_name} ({order.order_status_code})\n"
		f"收件人：{order.customer_name or order.orderer_name or '-'}\n"
		f"聯絡信箱：{order.customer_email}\n"
		f"更新時間：{order.updated_at.isoformat() if order.updated_at else ''}\n"
	)
	return subject, body


def build_admin_order_status_email(order, status_name, subject_template: str | None = None, body_template: str | None = None):
	status_templates = {
		OrderStatusCode.ORDER_CREATED.value: (
			f"[Admin] 新訂單 {order.order_no}",
			"系統收到新訂單，請確認後續處理流程。",
		),
		OrderStatusCode.ORDER_CONFIRMED_AND_PENDING_PAYMENT.value: (
			f"[Admin] 訂單 {order.order_no} 已確認待付款",
			"訂單目前待付款，請視需要追蹤付款狀況。",
		),
		OrderStatusCode.PAID_AND_PREPARING.value: (
			f"[Admin] 訂單 {order.order_no} 備貨中",
			"訂單已完成付款並進入備貨流程。",
		),
		OrderStatusCode.SHIPPING.value: (
			f"[Admin] 訂單 {order.order_no} 已出貨",
			"訂單已出貨，請追蹤物流與送達狀態。",
		),
		OrderStatusCode.CANCELED.value: (
			f"[Admin] 訂單 {order.order_no} 已取消",
			"訂單已取消，請確認是否需要後續退款或庫存調整。",
		),
		OrderStatusCode.DELIVERED.value: (
			f"[Admin] 訂單 {order.order_no} 已送達",
			"訂單已送達，可視需要進行結案追蹤。",
		),
		OrderStatusCode.REFUNDED.value: (
			f"[Admin] 訂單 {order.order_no} 已退款",
			"訂單退款已處理，請確認退款金額與方式是否正確。",
		),
		OrderStatusCode.OTHER.value: (
			f"[Admin] 訂單 {order.order_no} 狀態更新（其他）",
			"訂單狀態已被標記為其他，請確認處理情況。",
		),
	}
	subject, intro = status_templates.get(
		order.order_status_code,
		(f"[Admin] 訂單 {order.order_no} 狀態更新", "訂單狀態已更新。"),
	)
	context = _build_email_context(order, status_name)
	if subject_template:
		subject = _render_template(subject_template, context)
	if body_template:
		return subject, _render_template(body_template, context)

	body = (
		f"{intro}\n\n"
		f"訂單編號：{order.order_no}\n"
		f"目前狀態：{status_name} ({order.order_status_code})\n"
		f"下單人：{order.orderer_name or '-'} / {order.orderer_email or order.customer_email}\n"
		f"顧客：{order.customer_name or '-'} / {order.customer_email}\n"
		f"總金額：{order.total_amount}\n"
		f"更新時間：{order.updated_at.isoformat() if order.updated_at else ''}\n"
	)
	return subject, body


def build_admin_bank_transfer_last5_email(order):
	subject = f"[Admin] 訂單 {order.order_no} 已提交匯款後五碼"
	body = (
		"顧客已提交匯款帳號後五碼，請至後台確認。\n\n"
		f"訂單編號：{order.order_no}\n"
		f"顧客：{order.customer_name or order.orderer_name or '-'} / {order.customer_email}\n"
		f"後五碼：{order.bank_transfer_last5 or '-'}\n"
		f"目前狀態：{order.order_status_code}\n"
	)
	return subject, body