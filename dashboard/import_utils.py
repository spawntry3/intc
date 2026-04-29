import csv
import io
import re
from datetime import date, datetime

from django.db import transaction

from .models import CollegeAnalyticsSettings, InstagramPost, Review


MONTH_RU = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]


def _detect_delimiter(sample_line: str, default: str = ",") -> str:
    semi = sample_line.count(";")
    comma = sample_line.count(",")
    if semi == 0 and comma == 0:
        return default
    return ";" if semi > comma else ","


def _parse_date(value: str) -> date:
    if value is None:
        raise ValueError("Empty date")
    s = str(value).strip()
    if not s:
        raise ValueError("Empty date")

    try:
        return date.fromisoformat(s)
    except Exception:
        pass

    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y.%m.%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue

    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        raise ValueError(f"Unsupported date format: {s}")


def _normalize_sentiment(value: str) -> str:
    if value is None:
        raise ValueError("Sentiment is empty")
    s = str(value).strip().lower()
    mapping = {
        "positive": "positive",
        "положительный": "positive",
        "позитивный": "positive",
        "negative": "negative",
        "отрицательный": "negative",
        "негативный": "negative",
        "neutral": "neutral",
        "нейтральный": "neutral",
        "neutralnyy": "neutral",
        "нейтральный ": "neutral",
        "нейтральная": "neutral",
    }

    return mapping.get(s, mapping.get(s.replace("–", "-"), None) or _maybe_short_map(s))


def _maybe_short_map(s: str):
    if s in ("pos", "p", "good", "+"):
        return "positive"
    if s in ("neg", "n", "bad", "-"):
        return "negative"
    if s in ("neu", "neutral", "0"):
        return "neutral"
    raise ValueError(f"Unknown sentiment: {s}")


def _extract_hashtags(text: str) -> str:
    if not text:
        return ""
    tags = re.findall(r"#([\w_]+)", str(text))
    if not tags:
        return ""
    return " ".join([f"#{t}" for t in tags])


def import_reviews_csv(*, csv_bytes: bytes, source: str, mode: str, delimiter_choice: str):
    decoded = csv_bytes.decode("utf-8-sig", errors="replace")
    lines = decoded.splitlines()
    if not lines:
        raise ValueError("CSV is empty")
    delimiter = _detect_delimiter(lines[0], default=",") if delimiter_choice == "auto" else delimiter_choice

    reader = csv.DictReader(io.StringIO(decoded), delimiter=delimiter)
    required = {"author", "text", "sentiment", "date"}
    header = set((reader.fieldnames or []))
    missing = required - header
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}. Got: {', '.join(sorted(header))}")

    seen = set()
    imported = 0
    skipped = 0
    error_examples = []

    with transaction.atomic():
        if mode == "replace_source":
            Review.objects.filter(source=source).delete()

        for row in reader:
            try:
                author = (row.get("author") or "").strip()
                text = (row.get("text") or "").strip()
                if not author or not text:
                    skipped += 1
                    continue

                sent = _normalize_sentiment(row.get("sentiment"))
                d = _parse_date(row.get("date"))
                rating_raw = (row.get("rating") or "").strip() if row.get("rating") else ""
                likes_raw = (row.get("likes") or "").strip() if row.get("likes") else ""

                rating = float(rating_raw) if rating_raw else None
                likes = int(likes_raw) if likes_raw else 0

                key = (source, author, text[:200], d.isoformat(), sent, rating or "")
                if key in seen:
                    skipped += 1
                    continue
                seen.add(key)

                Review.objects.create(
                    source=source,
                    author=author,
                    text=text,
                    rating=rating,
                    sentiment=sent,
                    date=d,
                    likes=likes,
                )
                imported += 1
            except Exception as e:
                skipped += 1
                if len(error_examples) < 5:
                    error_examples.append(str(e))

    return {"imported": imported, "skipped": skipped, "errors": error_examples}


def import_instagram_posts_csv(*, csv_bytes: bytes, mode: str, delimiter_choice: str):
    settings = CollegeAnalyticsSettings.load()
    followers_default = settings.instagram_followers or 1

    decoded = csv_bytes.decode("utf-8-sig", errors="replace")
    lines = decoded.splitlines()
    if not lines:
        raise ValueError("CSV is empty")
    delimiter = _detect_delimiter(lines[0], default=",") if delimiter_choice == "auto" else delimiter_choice

    reader = csv.DictReader(io.StringIO(decoded), delimiter=delimiter)
    required = {"post_id", "caption", "likes", "comments", "date"}
    header = set((reader.fieldnames or []))
    missing = required - header
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}. Got: {', '.join(sorted(header))}")

    imported = 0
    updated = 0
    skipped = 0
    error_examples = []

    with transaction.atomic():
        if mode == "replace_source":
            InstagramPost.objects.all().delete()

        for row in reader:
            try:
                post_id = (row.get("post_id") or "").strip()
                if not post_id:
                    skipped += 1
                    continue

                caption = (row.get("caption") or "").strip()
                likes = int((row.get("likes") or "0").strip() or "0")
                comments = int((row.get("comments") or "0").strip() or "0")
                d = _parse_date(row.get("date"))

                image_url = (row.get("image_url") or "").strip() if "image_url" in (reader.fieldnames or []) else ""
                post_url = (
                    (row.get("post_url") or "").strip()
                    if "post_url" in (reader.fieldnames or [])
                    else f"https://www.instagram.com/p/{post_id}/"
                )

                hashtags = (row.get("hashtags") or "").strip() if "hashtags" in (reader.fieldnames or []) else ""
                if not hashtags:
                    hashtags = _extract_hashtags(caption)

                engagement_raw = (row.get("engagement_rate") or "").strip() if "engagement_rate" in (reader.fieldnames or []) else ""
                engagement_rate = (
                    float(engagement_raw)
                    if engagement_raw
                    else round((likes + comments) / followers_default * 100, 2)
                )

                defaults = {
                    "caption": caption,
                    "likes": likes,
                    "comments": comments,
                    "date": d,
                    "image_url": image_url,
                    "post_url": post_url,
                    "hashtags": hashtags,
                    "engagement_rate": engagement_rate,
                }

                _, created = InstagramPost.objects.update_or_create(post_id=post_id, defaults=defaults)
                if created:
                    imported += 1
                else:
                    updated += 1
            except Exception as e:
                skipped += 1
                if len(error_examples) < 5:
                    error_examples.append(str(e))

    return {"imported": imported, "updated": updated, "skipped": skipped, "errors": error_examples}

