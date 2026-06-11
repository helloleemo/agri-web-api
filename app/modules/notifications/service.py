import json
import logging
import os
import urllib.error
import urllib.request


logger = logging.getLogger(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_NOTIFICATION_TARGET_IDS = [
	target.strip()
	for target in os.getenv("LINE_NOTIFICATION_TARGET_IDS", "").split(",")
	if target.strip()
]
LINE_PUSH_API_URL = os.getenv("LINE_PUSH_API_URL", "https://api.line.me/v2/bot/message/push")


def get_line_notification_targets() -> list[str]:
	return list(LINE_NOTIFICATION_TARGET_IDS)


def send_line_message(target_id: str, message: str) -> None:
	if not LINE_CHANNEL_ACCESS_TOKEN:
		logger.warning("LINE_CHANNEL_ACCESS_TOKEN is not configured. LINE message to %s was not sent.", target_id)
		logger.warning("LINE message content for %s:\n%s", target_id, message)
		return

	payload = json.dumps({
		"to": target_id,
		"messages": [{"type": "text", "text": message}],
	}).encode("utf-8")
	request = urllib.request.Request(
		LINE_PUSH_API_URL,
		data=payload,
		headers={
			"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
			"Content-Type": "application/json",
		},
		method="POST",
	)

	try:
		with urllib.request.urlopen(request, timeout=10):
			return
	except urllib.error.HTTPError as exc:
		logger.error(
			"Failed to send LINE message to %s (status=%s): %s",
			target_id,
			exc.code,
			exc.read().decode("utf-8", errors="ignore"),
		)
	except Exception:
		logger.exception("Unexpected error while sending LINE message to %s", target_id)


def build_order_summary_message(
	order_no: str,
	status_name: str,
	order_status_code: int,
	customer_email: str,
	customer_name: str | None,
	created_at: str,
	updated_at: str,
	items: list[dict[str, object]],
) -> str:
	lines = [
		"[訂單狀態更新]",
		f"訂單編號：{order_no}",
		f"狀態：{status_name} ({order_status_code})",
		f"顧客姓名：{customer_name or '-'}",
		f"顧客信箱：{customer_email}",
		f"建立時間：{created_at}",
		f"更新時間：{updated_at}",
		"訂單明細：",
	]

	for index, item in enumerate(items, start=1):
		product_name = str(item.get("product_name") or "未知商品")
		quantity = item.get("quantity")
		lines.append(f"{index}. {product_name} x {quantity}")

	return "\n".join(lines)