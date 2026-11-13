import hashlib
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from app.services.validation_service import validate_frame
from app.utils.csv_utils import parse_csv
from scripts.generate_sample_data import DEFAULT_END_MONTH, generate, write_csv
from scripts.seed import BRANDS, REGIONS

SAMPLE = Path(__file__).resolve().parents[2] / "sample-data" / "pharma_sales_sample.csv"
HEADER = "sales_date,brand_name,region_name,quantity,revenue"


def _by_pair_and_month(rows: list[dict]) -> dict[tuple[str, str], dict[str, Decimal]]:
    values: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(dict)
    for row in rows:
        values[(row["brand_name"], row["region_name"])][row["sales_date"][:7]] = Decimal(
            row["revenue"]
        )
    return values


def test_generator_is_reproducible(tmp_path: Path) -> None:
    first = generate(DEFAULT_END_MONTH)
    second = generate(DEFAULT_END_MONTH)

    assert first == second

    first_path = tmp_path / "first.csv"
    second_path = tmp_path / "second.csv"
    write_csv(first, first_path)
    write_csv(second, second_path)

    assert first_path.read_bytes() == second_path.read_bytes()
    assert hashlib.sha256(first_path.read_bytes()).hexdigest() == hashlib.sha256(
        second_path.read_bytes()
    ).hexdigest()


def test_committed_sample_matches_generator(tmp_path: Path) -> None:
    generated_path = tmp_path / "generated.csv"
    write_csv(generate(DEFAULT_END_MONTH), generated_path)

    assert SAMPLE.exists()
    assert generated_path.read_bytes() == SAMPLE.read_bytes()


def test_committed_sample_matches_csv_contract() -> None:
    content = SAMPLE.read_bytes()
    assert content.splitlines()[0].decode("utf-8") == HEADER

    frame = parse_csv(content)
    brands = {name.casefold(): index for index, (name, _) in enumerate(BRANDS, 1)}
    regions = {name.casefold(): index for index, (name, _) in enumerate(REGIONS, 1)}
    result = validate_frame(frame, brands, regions)

    assert result.total_rows == 240
    assert result.accepted_rows == 240
    assert result.rejected_rows == 0
    assert result.errors == []


def test_committed_sample_has_expected_shape() -> None:
    rows = generate(DEFAULT_END_MONTH)

    assert len(rows) == 240
    assert {row["brand_name"] for row in rows} == {name for name, _ in BRANDS}
    assert {row["region_name"] for row in rows} == {name for name, _ in REGIONS}
    assert {row["sales_date"] for row in rows} == {
        f"2025-{month:02d}-01" for month in range(11, 13)
    } | {f"2026-{month:02d}-01" for month in range(1, 11)}
    assert all(int(row["quantity"]) >= 0 for row in rows)
    assert all(Decimal(row["revenue"]) >= 0 for row in rows)


def test_seeded_declines_and_growth_events() -> None:
    rows = generate(DEFAULT_END_MONTH)
    changes = {}
    for pair, months in _by_pair_and_month(rows).items():
        previous = months["2026-09"]
        current = months["2026-10"]
        changes[pair] = (current - previous) / previous * Decimal("100")

    assert changes[("Cardioval", "Chennai")] <= Decimal("-20")
    assert changes[("Neurozen", "Coimbatore")] <= Decimal("-20")
    assert changes[("Glucofine", "Madurai")] >= Decimal("30")
    assert changes[("Oncovera", "Trichy")] >= Decimal("30")

    seeded_pairs = {
        ("Cardioval", "Chennai"),
        ("Neurozen", "Coimbatore"),
        ("Glucofine", "Madurai"),
        ("Oncovera", "Trichy"),
    }
    normal_changes = [
        change for pair, change in changes.items() if pair not in seeded_pairs
    ]
    assert len(normal_changes) == 16
    assert all(abs(change) < Decimal("10") for change in normal_changes)

    declines = [pair for pair, change in changes.items() if change <= Decimal("-20")]
    growth = [pair for pair, change in changes.items() if change >= Decimal("30")]
    assert len(declines) >= 2
    assert 1 <= len(growth) <= 2
