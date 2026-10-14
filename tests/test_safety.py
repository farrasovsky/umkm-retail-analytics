"""Negative safety, boundary protection, and data-leakage prevention tests for the showcase."""

import inspect
import os
from pathlib import Path
import subprocess
import sys
import pytest

from retail_analytics.ingestion.loaders import load_transactions_csv
from retail_analytics.ingestion.schemas import SchemaValidationError
from retail_analytics.showcase.summary import get_project_root, run_showcase_demo


def test_public_showcase_function_has_no_path_parameters():
    """Test 1: Public showcase entrypoint must have 0 parameters (no path/fixture overrides)."""
    sig = inspect.signature(run_showcase_demo)
    assert len(sig.parameters) == 0, f"run_showcase_demo must be parameterless, found: {list(sig.parameters.keys())}"

    # Calling with unexpected positional argument must raise TypeError
    with pytest.raises(TypeError):
        run_showcase_demo("custom_path")  # type: ignore

    # Calling with unexpected keyword argument must raise TypeError
    with pytest.raises(TypeError):
        run_showcase_demo(fixture_dir=Path("custom"))  # type: ignore

    with pytest.raises(TypeError):
        run_showcase_demo(output_dir=Path("custom"))  # type: ignore


def test_execution_from_unrelated_working_directory(tmp_path: Path):
    """Test 2: Executing demo from an unrelated working directory must resolve to project root."""
    original_cwd = Path.cwd()
    external_dir = tmp_path / "unrelated_working_dir"
    external_dir.mkdir()

    repo_root = get_project_root()
    output_file = repo_root / "output" / "showcase" / "showcase_summary.json"

    try:
        os.chdir(external_dir)
        # Execute parameterless showcase demo from outside project directory
        summary = run_showcase_demo()

        assert summary["showcase_name"] == "UMKM Retail Analytics Technical Showcase"
        # Confirm output is saved strictly under project root, NOT the caller's working directory
        assert output_file.exists()
        # Confirm unrelated working directory was NOT populated with output or input files
        assert list(external_dir.iterdir()) == []
    finally:
        os.chdir(original_cwd)


def test_missing_fixture_fails_explicitly_without_substitute_generation(tmp_path: Path, monkeypatch):
    """Test 3: Missing fixture must raise FileNotFoundError, fail non-zero, and never auto-generate data."""
    empty_repo_mock = tmp_path / "empty_repo"
    empty_repo_mock.mkdir()
    sample_dir = empty_repo_mock / "data" / "sample"
    sample_dir.mkdir(parents=True)

    # Monkeypatch project root to an empty directory lacking raw_transactions.csv
    monkeypatch.setattr(
        "retail_analytics.showcase.summary.get_project_root",
        lambda: empty_repo_mock,
    )

    with pytest.raises(FileNotFoundError, match="Designated synthetic transaction fixture not found"):
        run_showcase_demo()

    # Crucial safety guarantee: missing fixture must NOT trigger auto-generation in missing directory!
    assert list(sample_dir.iterdir()) == []
    # No output directory must be created in mock repo
    assert not (empty_repo_mock / "output").exists()


def test_cli_missing_fixture_returns_nonzero_exit_code(tmp_path: Path):
    """Running showcase when fixture is missing must exit with a non-zero exit code."""
    empty_dir = tmp_path / "empty_proj"
    empty_dir.mkdir()

    code = (
        "import sys\n"
        "from unittest.mock import patch\n"
        "from pathlib import Path\n"
        "import retail_analytics.showcase.summary as summary_mod\n"
        "with patch.object(summary_mod, 'get_project_root', return_value=Path(r'" + str(empty_dir) + "')):\n"
        "    try:\n"
        "        summary_mod.run_showcase_demo()\n"
        "    except FileNotFoundError:\n"
        "        sys.exit(1)\n"
    )

    res = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert list(empty_dir.iterdir()) == []


def test_cli_rejects_arbitrary_customer_input_and_output_flags():
    """Test 5: CLI must not expose or accept arbitrary customer input or output flags."""
    forbidden_flags = [
        ["--input", "confidential.csv"],
        ["-i", "confidential.csv"],
        ["--output", "/tmp/leak"],
        ["-o", "/tmp/leak"],
        ["--inventory", "confidential_inv.csv"],
    ]

    for flags in forbidden_flags:
        res = subprocess.run(
            [sys.executable, "scripts/run_showcase.py"] + flags,
            cwd=get_project_root(),
            capture_output=True,
            text=True,
        )
        assert res.returncode != 0, f"Expected non-zero exit for flags {flags}, got {res.returncode}"
        assert "unrecognized arguments" in res.stderr.lower() or "error" in res.stderr.lower()


def test_invalid_and_absent_fixture_behavior(tmp_path: Path):
    """Test 6: Absent fixture vs empty file vs malformed schema must be strictly distinguished."""
    # 1. Non-existent file raises FileNotFoundError
    non_existent = tmp_path / "does_not_exist.csv"
    with pytest.raises(FileNotFoundError):
        load_transactions_csv(non_existent)

    # 2. Completely empty file raises SchemaValidationError (not treated as valid empty dataframe)
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("")
    with pytest.raises(SchemaValidationError, match="completely empty"):
        load_transactions_csv(empty_file)

    # 3. Malformed header missing required columns raises SchemaValidationError
    malformed_file = tmp_path / "malformed.csv"
    malformed_file.write_text("random_col1,random_col2\nval1,val2\n")
    with pytest.raises(SchemaValidationError, match="Missing mandatory column"):
        load_transactions_csv(malformed_file)
