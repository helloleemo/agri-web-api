from app.modules.order_statuses.constants import OrderStatusCode


def build_customer_order_status_email(order, status_name):
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
	body = (
		f"{intro}\n\n"
		f"訂單編號：{order.order_no}\n"
		f"目前狀態：{status_name} ({order.order_status_code})\n"
		f"收件人：{order.customer_name or order.orderer_name or '-'}\n"
		f"聯絡信箱：{order.customer_email}\n"
		f"更新時間：{order.updated_at.isoformat() if order.updated_at else ''}\n"
	)
	return subject, body


def build_admin_order_status_email(order, status_name):
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