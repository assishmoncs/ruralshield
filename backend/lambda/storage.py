import logging
from datetime import datetime, timezone
from decimal import Decimal

from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from config import AWS_REGION, TABLE_NAME

logger = logging.getLogger(__name__)
DYNAMODB_CONFIG = Config(connect_timeout=2, read_timeout=5, retries={"max_attempts": 3, "mode": "standard"})
MAX_STATISTICS_ITEMS = 10000


def _table():
    if not TABLE_NAME:
        return None
    import boto3

    return boto3.resource("dynamodb", region_name=AWS_REGION, config=DYNAMODB_CONFIG).Table(TABLE_NAME)


def save_scan(item):
    if not item.get("owner_id") or item.get("owner_id") == "anonymous":
        return False
    try:
        table = _table()
        if table is None:
            return False
        converted = {key: Decimal(str(value)) if isinstance(value, float) else value for key, value in item.items()}
        table.put_item(Item=converted)
        return True
    except (BotoCoreError, ClientError, TypeError, ValueError) as exc:
        logger.warning("dynamodb_save_failed error_type=%s", type(exc).__name__)
        return False


def list_history(owner_id, limit=50):
    if not owner_id or owner_id == "anonymous":
        return []
    try:
        table = _table()
        if table is None:
            return []
        from boto3.dynamodb.conditions import Key

        response = table.query(
            KeyConditionExpression=Key("owner_id").eq(owner_id),
            Limit=min(max(int(limit), 1), 100),
            ScanIndexForward=False,
        )
        return [item for item in response.get("Items", []) if item.get("input_type") in {"message", "url"}]
    except (BotoCoreError, ClientError, TypeError, ValueError) as exc:
        logger.warning("dynamodb_history_failed error_type=%s", type(exc).__name__)
        return []


def _all_history(owner_id, max_items=MAX_STATISTICS_ITEMS):
    if not owner_id or owner_id == "anonymous":
        return [], False
    try:
        table = _table()
        if table is None:
            return [], False
        from boto3.dynamodb.conditions import Key

        rows = []
        last_key = None
        truncated = False
        while len(rows) < max_items:
            kwargs = {
                "KeyConditionExpression": Key("owner_id").eq(owner_id),
                "ScanIndexForward": False,
                "Limit": min(250, max_items - len(rows)),
            }
            if last_key:
                kwargs["ExclusiveStartKey"] = last_key
            response = table.query(**kwargs)
            rows.extend(item for item in response.get("Items", []) if item.get("input_type") in {"message", "url"})
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
        if last_key:
            truncated = True
        return rows, truncated
    except (BotoCoreError, ClientError, TypeError, ValueError) as exc:
        logger.warning("dynamodb_statistics_failed error_type=%s", type(exc).__name__)
        return [], False


def statistics(owner_id):
    rows, truncated = _all_history(owner_id)
    total = len(rows)
    counts = {"SAFE": 0, "SUSPICIOUS": 0, "PHISHING": 0}
    categories = {}
    for row in rows:
        cls = row.get("classification")
        if cls in counts:
            counts[cls] += 1
        cat = row.get("scam_category") or "Other/Unknown"
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "total_scans": total,
        "safe": counts["SAFE"],
        "suspicious": counts["SUSPICIOUS"],
        "phishing": counts["PHISHING"],
        "phishing_percentage": round((counts["PHISHING"] / total * 100), 2) if total else 0,
        "scam_categories": categories,
        "recent_detections": rows[:10],
        "statistics_truncated": truncated,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def save_feedback(owner_id, scan_id, feedback):
    if not owner_id or owner_id == "anonymous" or not scan_id or feedback not in {"helpful", "incorrect"}:
        return False
    try:
        table = _table()
        if table is None:
            return False
        from boto3.dynamodb.conditions import Key

        response = table.query(
            KeyConditionExpression=Key("owner_id").eq(owner_id),
            Limit=100,
            ScanIndexForward=False,
        )
        target = next(
            (item for item in response.get("Items", []) if item.get("scan_id") == scan_id and item.get("input_type") in {"message", "url"}),
            None,
        )
        if not target:
            return False
        table.update_item(
            Key={"owner_id": owner_id, "scan_key": target["scan_key"]},
            UpdateExpression="SET feedback = :feedback, feedback_at = :timestamp",
            ExpressionAttributeValues={
                ":feedback": feedback,
                ":timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        return True
    except (BotoCoreError, ClientError, TypeError, ValueError) as exc:
        logger.warning("dynamodb_feedback_failed error_type=%s", type(exc).__name__)
        return False
