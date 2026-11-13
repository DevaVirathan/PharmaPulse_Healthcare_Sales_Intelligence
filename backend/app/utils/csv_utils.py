"""CSV parsing helpers built on Pandas."""

import io

import pandas as pd

REQUIRED_HEADERS = ["sales_date", "brand_name", "region_name", "quantity", "revenue"]


class CsvParseError(ValueError):
    """Raised when a CSV cannot be parsed or has an invalid header."""


def parse_csv(content: bytes) -> pd.DataFrame:
    """Parse uploaded bytes into a string-only DataFrame.

    Extra columns are ignored. Header whitespace is trimmed. Empty files and
    missing/duplicate required headers raise CsvParseError.
    """

    if not content or not content.strip():
        raise CsvParseError("The uploaded file is empty.")

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CsvParseError("The file must be UTF-8 encoded CSV text.") from exc

    try:
        frame = pd.read_csv(
            io.StringIO(text),
            dtype=str,
            keep_default_na=False,
            na_filter=False,
        )
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise CsvParseError("The uploaded file is not a readable CSV.") from exc

    frame.columns = [str(column).strip() for column in frame.columns]
    duplicates = [
        column for column in frame.columns if list(frame.columns).count(column) > 1
    ]
    if duplicates:
        raise CsvParseError(f"Duplicate header: {sorted(set(duplicates))[0]}")

    missing = [header for header in REQUIRED_HEADERS if header not in frame.columns]
    if missing:
        raise CsvParseError(
            "Missing required header(s): " + ", ".join(missing)
        )

    # Keep only contract columns so extra data is never persisted.
    return frame[REQUIRED_HEADERS].copy()
