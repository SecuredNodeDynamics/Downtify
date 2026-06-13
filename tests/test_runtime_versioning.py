from __future__ import annotations

from downtify.versioning import (
    bump_patch,
    bump_runtime_version,
    highest_version,
    read_runtime_version,
)


def test_bump_patch_increments_third_version_part():
    assert bump_patch('2.9.0') == '2.9.1'


def test_runtime_version_persists_increment(tmp_path):
    version_file = tmp_path / 'app-version'

    assert bump_runtime_version('2.9.0', version_file) == '2.9.1'
    assert bump_runtime_version('2.9.0', version_file) == '2.9.2'
    assert version_file.read_text(encoding='utf-8').strip() == '2.9.2'


def test_runtime_version_uses_newer_code_version_after_upgrade(tmp_path):
    version_file = tmp_path / 'app-version'
    version_file.write_text('2.9.9\n', encoding='utf-8')

    assert read_runtime_version('3.0.0', version_file) == '3.0.0'
    assert bump_runtime_version('3.0.0', version_file) == '3.0.1'


def test_highest_version_compares_numeric_parts():
    assert highest_version('2.10.0', '2.9.99') == '2.10.0'
