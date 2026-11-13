"""Domain enumerations shared by models, schemas, and services."""

from enum import StrEnum


class ImportStatus(StrEnum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AlertStatus(StrEnum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class Metric(StrEnum):
    REVENUE = "revenue"
    UNITS = "units"


class ComparisonPeriod(StrEnum):
    MONTH_OVER_MONTH = "month_over_month"
