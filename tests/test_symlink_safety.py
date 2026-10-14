"""Regression tests for symbolic-link attacks on the showcase fixture and output paths.

Each test builds an isolated temporary project layout and monkeypatches the internal
project-root locator. The real committed fixture and report are never modified.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil

import pytest

import retail_analytics.showcase.summary as summary_mod
from retail_analytics.showcase.summary import (
    ShowcaseIntegrityError,
    ShowcasePathError,
    get_project_root,
    run_showcase_demo,
)

REAL_ROOT = get_project_root()
FIXTURES = ("raw_transactions.csv", "product_master.csv")


def _require_symlinks(tmp_path: Path) -> None:
    probe_target = tmp_path / "_probe_target"
    probe_target.write_text("x")
    probe_link = tmp_path / "_probe_link"
    try:
        os.symlink(probe_target, probe_link)
    except (OSError, NotImplementedError) as err:
        pytest.skip(f"Symbolic links cannot be created on this platform/user: {err}")
    finally:
        if probe_link.is_symlink():
            probe_link.unlink()
        probe_target.unlink()


def _make_project(base: Path) -> Path:
    """Create a temporary project with byte-identical copies of the committed fixtures."""
    project = base / "project"
    sample = project / "data" / "sample"
    sample.mkdir(parents=True)
    for name in FIXTURES:
        shutil.copy2(REAL_ROOT / "data" / "sample" / name, sample / name)
    return project


@pytest.fixture
def temp_project(tmp_path: Path, monkeypatch) -> Path:
    _require_symlinks(tmp_path)
    project = _make_project(tmp_path)
    monkeypatch.setattr(summary_mod, "get_project_root", lambda: project)
    return project


def _external_copy(tmp_path: Path) -> Path:
    """External directory holding byte-identical fixture copies (so only the symlink check can stop it)."""
    external = tmp_path / "external_data"
    external.mkdir()
    for name in FIXTURES:
        shutil.copy2(REAL_ROOT / "data" / "sample" / name, external / name)
    return external


def test_normal_run_in_temp_project_writes_only_to_output_showcase(temp_project: Path):
    summary = run_showcase_demo()
    assert summary["data_quality_audit"]["raw_rows"] == 1788
    out_dir = temp_project / "output" / "showcase"
    assert sorted(p.name for p in out_dir.iterdir()) == ["quarantined_sample.csv", "showcase_summary.json"]
    assert sorted(p.name for p in temp_project.iterdir()) == ["data", "output"]


def test_symlinked_fixture_file_is_rejected(temp_project: Path, tmp_path: Path):
    external = _external_copy(tmp_path)
    fixture = temp_project / "data" / "sample" / "raw_transactions.csv"
    fixture.unlink()
    os.symlink(external / "raw_transactions.csv", fixture)

    with pytest.raises(ShowcasePathError, match="Symbolic link rejected"):
        run_showcase_demo()

    assert not (temp_project / "output").exists()
    assert sorted(p.name for p in external.iterdir()) == sorted(FIXTURES)


def test_symlinked_fixture_parent_directory_is_rejected(temp_project: Path, tmp_path: Path):
    external = _external_copy(tmp_path)
    sample_dir = temp_project / "data" / "sample"
    shutil.rmtree(sample_dir)
    os.symlink(external, sample_dir, target_is_directory=True)

    with pytest.raises(ShowcasePathError, match="Symbolic link rejected"):
        run_showcase_demo()

    assert not (temp_project / "output").exists()


def test_symlinked_data_directory_is_rejected(temp_project: Path, tmp_path: Path):
    external_root = tmp_path / "external_root"
    shutil.copytree(temp_project / "data", external_root / "data")
    shutil.rmtree(temp_project / "data")
    os.symlink(external_root / "data", temp_project / "data", target_is_directory=True)

    with pytest.raises(ShowcasePathError, match="Symbolic link rejected"):
        run_showcase_demo()

    assert not (temp_project / "output").exists()


def test_symlinked_output_showcase_directory_is_rejected(temp_project: Path, tmp_path: Path):
    external_out = tmp_path / "external_out"
    external_out.mkdir()
    (temp_project / "output").mkdir()
    os.symlink(external_out, temp_project / "output" / "showcase", target_is_directory=True)

    with pytest.raises(ShowcasePathError, match="Symbolic link rejected in output path"):
        run_showcase_demo()

    assert list(external_out.iterdir()) == []
    assert [p.name for p in (temp_project / "output").iterdir()] == ["showcase"]


def test_symlinked_output_parent_directory_is_rejected(temp_project: Path, tmp_path: Path):
    external_out = tmp_path / "external_output_root"
    external_out.mkdir()
    os.symlink(external_out, temp_project / "output", target_is_directory=True)

    with pytest.raises(ShowcasePathError, match="Symbolic link rejected in output path"):
        run_showcase_demo()

    assert list(external_out.iterdir()) == []


def test_symlinked_output_file_is_not_followed(temp_project: Path, tmp_path: Path):
    outside_file = tmp_path / "outside.json"
    outside_file.write_text("original")
    out_dir = temp_project / "output" / "showcase"
    out_dir.mkdir(parents=True)
    os.symlink(outside_file, out_dir / "showcase_summary.json")

    with pytest.raises(ShowcasePathError, match="Symbolic link rejected for output file"):
        run_showcase_demo()

    assert outside_file.read_text() == "original"


def test_substituted_fixture_content_fails_integrity_check(tmp_path: Path, monkeypatch):
    project = _make_project(tmp_path)
    monkeypatch.setattr(summary_mod, "get_project_root", lambda: project)
    fixture = project / "data" / "sample" / "raw_transactions.csv"
    fixture.write_text(
        "transaction_id,transaction_date,sku,quantity,unit_price\n"
        "TXN-EXT-1,2026-05-01,SKU-X,1,100000\n"
    )

    with pytest.raises(ShowcaseIntegrityError, match="integrity check failed"):
        run_showcase_demo()

    assert not (project / "output").exists()


def test_missing_product_master_fails_explicitly(tmp_path: Path, monkeypatch):
    project = _make_project(tmp_path)
    monkeypatch.setattr(summary_mod, "get_project_root", lambda: project)
    (project / "data" / "sample" / "product_master.csv").unlink()

    with pytest.raises(FileNotFoundError, match="product master fixture not found"):
        run_showcase_demo()

    assert sorted(p.name for p in (project / "data" / "sample").iterdir()) == ["raw_transactions.csv"]
    assert not (project / "output").exists()


def test_manifest_matches_committed_fixtures():
    """The source-controlled digests must describe the committed synthetic fixtures."""
    from retail_analytics.showcase.fixture_manifest import EXPECTED_FIXTURE_SHA256

    for name, expected in EXPECTED_FIXTURE_SHA256.items():
        assert summary_mod._sha256_of(REAL_ROOT / "data" / "sample" / name) == expected

