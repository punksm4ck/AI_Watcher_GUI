"""Turns a raw accessibility text dump into a possible limit-hit event."""
import re
from datetime import datetime

from config import TRACKED_ACCOUNTS, LIMIT_PHRASES

_LIMIT_RE = re.compile("|".join(re.escape(p) for p in LIMIT_PHRASES), re.IGNORECASE)

_TIME_RE = re.compile(
    r"""
    (?:limit\s*)?(?:resets?|until|at|on)\s*
    (
        (?:[A-Za-z]{3}\s+\d{1,2},\s*)?   # Month Day, (e.g. Sep 27,)
        \d{1,2}:\d{2}\s*(?:AM|PM|am|pm)   # HH:MM AM/PM
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _is_from_tracker_gui(text, start_idx, end_idx):
    """Ensures match isn't from our own tracker app GUI window."""
    window = text[max(0, start_idx - 100): min(len(text), end_idx + 100)]
    return bool(re.search(r'(?:MARK AVAILABLE|LOCKED|ONLINE|reset~|GEMINI EVENT LOG)', window, re.IGNORECASE))


def looks_like_limit_message(text):
    for m in _LIMIT_RE.finditer(text):
        if not _is_from_tracker_gui(text, m.start(), m.end()):
            return True
    return False


def extract_reset_time_raw(text):
    for line in text.splitlines():
        if any(k in line for k in ("reset", "until", "Limit", "out of free messages")):
            for m in _TIME_RE.finditer(line):
                val = m.group(1).strip()
                if val:
                    return val

    for m in _TIME_RE.finditer(text):
        if not _is_from_tracker_gui(text, m.start(), m.end()):
            val = m.group(1).strip()
            if val:
                return val
    return None


def try_parse_reset_time(raw, now=None):
    if not raw:
        return None
    now = now or datetime.now()
    formats = ["%b %d, %I:%M%p", "%b %d, %I:%M %p", "%I:%M%p", "%I:%M %p", "%I%p", "%I %p", "%H:%M"]

    cleaned = raw.upper().replace(".", "").replace("  ", " ").strip()
    cleaned_nospace = cleaned.replace(" ", "")

    for fmt in formats:
        for candidate_str in (cleaned, cleaned_nospace):
            try:
                parsed = datetime.strptime(candidate_str, fmt)
                candidate = now.replace(
                    month=parsed.month if parsed.month != 1900 else now.month,
                    day=parsed.day if parsed.day != 1900 else now.day,
                    hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0
                )
                if candidate < now:
                    candidate = candidate.replace(day=candidate.day + 1)
                return candidate.isoformat()
            except ValueError:
                continue
    return None


def detect_account(text):
    """
    Strictly disambiguates accounts, prioritizing longer/specific matches
    to prevent cross-triggering between tsannasardo and tsannasardo2.
    """
    # Check account 2 first (since account 1 is a substring prefix)
    if any(k in text for k in ("Thomas 2", "tsannasardo2", "Tsann2")):
        if "tsannasardo2@gmail.com" in TRACKED_ACCOUNTS:
            return "tsannasardo2@gmail.com"

    # Check account 1 explicitly ensuring '2' is absent
    if (any(k in text for k in ("Thomas 1", "tsannasardo1", "Tsann1")) or
        (re.search(r'\bThomas\b', text) and not re.search(r'\bThomas\s*2\b', text)) or
        (re.search(r'\bTsann1\b', text))):
        if "tsannasardo@gmail.com" in TRACKED_ACCOUNTS:
            if not re.search(r'tsannasardo2', text, re.IGNORECASE) and not re.search(r'Tsann2', text):
                return "tsannasardo@gmail.com"

    # Sort accounts by length descending so longer/specific emails match before shorter prefixes
    sorted_accounts = sorted(TRACKED_ACCOUNTS, key=len, reverse=True)
    for account in sorted_accounts:
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(account) + r'(?![a-zA-Z0-9])'
        if re.search(pattern, text, re.IGNORECASE):
            return account

    limit_match = None
    for m in _LIMIT_RE.finditer(text):
        if not _is_from_tracker_gui(text, m.start(), m.end()):
            limit_match = m
            break

    if not limit_match:
        return None

    limit_idx = limit_match.start()
    found = {}

    for account in sorted_accounts:
        if "punksm4ck" in account and "punksm4ck@" not in account:
            continue

        pattern = r'(?<![a-zA-Z0-9])' + re.escape(account) + r'(?![a-zA-Z0-9])'
        indices = [m.start() for m in re.finditer(pattern, text, re.IGNORECASE)]

        valid_indices = [idx for idx in indices if not _is_from_tracker_gui(text, idx, idx + len(account))]

        if valid_indices:
            min_dist = min(abs(idx - limit_idx) for idx in valid_indices)
            found[account] = {
                'distance': min_dist,
                'count': len(valid_indices)
            }

    if not found:
        return None

    def sort_key(acc):
        data = found[acc]
        try:
            order_idx = TRACKED_ACCOUNTS.index(acc)
        except ValueError:
            order_idx = 999
        return (data['distance'], -data['count'], order_idx)

    return sorted(found.keys(), key=sort_key)[0]
