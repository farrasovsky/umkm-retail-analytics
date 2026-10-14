"""Ingestion module for loading and validating source retail datasets."""

from .loaders import load_inventory_csv, load_product_master_csv, load_transactions_csv
from .schemas import (
    INVENTORY_REQUIRED_COLUMNS,
    PRODUCT_MASTER_REQUIRED_COLUMNS,
    TRANSACTION_REQUIRED_COLUMNS,
    SchemaValidationError,
    validate_inventory_schema,
    validate_product_master_schema,
    validate_transaction_schema,
)

__all__ = [
    "load_transactions_csv",
    "load_inventory_csv",
    "load_product_master_csv",
    "TRANSACTION_REQUIRED_COLUMNS",
    "INVENTORY_REQUIRED_COLUMNS",
    "PRODUCT_MASTER_REQUIRED_COLUMNS",
    "SchemaValidationError",
    "validate_transaction_schema",
    "validate_inventory_schema",
    "validate_product_master_schema",
]

