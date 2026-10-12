from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_URL = (
    "https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json"
)
WORKFLOW_FILE = Path(".github/workflows/daily-commit.yml")
VERSION_CONFIG = Path("config/python-version.json")
PYPROJECT_FILE = Path("pyproject.toml")
STABLE_VERSION_RE = re.compile(r"^3\.\d+\.\d+$")
WORKFLOW_VERSION_RE = re.compile(r'(python-version:\s*["\'])([^"\']+)(["\'])')
PYPROJECT_TARGET_RE = re.compile(r'(ci-python-version\s*=\s*")([^"]+)(")')


@dataclass(frozen=True)
class PythonVersionSync:
    updated: bool
    current_minor: str
    latest_minor: str
    latest_full: str
    changed_files: tuple[Path, ...]


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def _to_minor(version: str) -> str:
    major, minor, *_ = version.split(".")
    return f"{major}.{minor}"


def fetch_latest_stable_python() -> tuple[str, str]:
    request = urllib.request.Request(MANIFEST_URL, headers={"User-Agent": "daily-git-commit"})
    with urllib.request.urlopen(request, timeout=30) as response:
        manifest = json.load(response)

    stable_versions = [
        entry["version"]
        for entry in manifest
        if entry.get("stable") and STABLE_VERSION_RE.fullmatch(str(entry.get("version", "")))
    ]
    if not stable_versions:
        raise RuntimeError("No stable Python versions found in actions manifest.")

    latest_full = max(stable_versions, key=_version_key)
    return _to_minor(latest_full), latest_full


def read_configured_minor(root: Path) -> str:
    config_path = root / VERSION_CONFIG
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            minor = str(data.get("minor", "")).strip()
            if minor and minor != "3.x":
                return minor
        except (json.JSONDecodeError, OSError):
            pass

    pyproject_path = root / PYPROJECT_FILE
    if pyproject_path.exists():
        match = PYPROJECT_TARGET_RE.search(pyproject_path.read_text(encoding="utf-8"))
        if match and match.group(2) != "3.x":
            return match.group(2)

    workflow = root / WORKFLOW_FILE
    if workflow.exists():
        match = WORKFLOW_VERSION_RE.search(workflow.read_text(encoding="utf-8"))
        if match:
            configured = match.group(2)
            if STABLE_VERSION_RE.fullmatch(configured):
                return _to_minor(configured)
            if configured != "3.x":
                return configured

    return "3.14"


def _write_version_config(root: Path, minor: str, full_version: str) -> Path:
    config_path = root / VERSION_CONFIG
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "minor": minor,
        "full_version": full_version,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": MANIFEST_URL,
    }
    config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return config_path


def _update_workflow(root: Path, minor: str) -> Path | None:
    workflow = root / WORKFLOW_FILE
    if not workflow.exists():
        return None
    text = workflow.read_text(encoding="utf-8")
    match = WORKFLOW_VERSION_RE.search(text)
    if match and match.group(2) == "3.x":
        return None
    updated = WORKFLOW_VERSION_RE.sub(
        lambda match: f"{match.group(1)}{minor}{match.group(3)}",
        text,
        count=1,
    )
    if updated != text:
        workflow.write_text(updated, encoding="utf-8")
        return workflow
    return None


def _update_pyproject(root: Path, minor: str) -> Path | None:
    pyproject = root / PYPROJECT_FILE
    if not pyproject.exists():
        return None

    text = pyproject.read_text(encoding="utf-8")
    if PYPROJECT_TARGET_RE.search(text):
        updated = PYPROJECT_TARGET_RE.sub(
            lambda match: f'{match.group(1)}{minor}{match.group(3)}',
            text,
            count=1,
        )
    elif "[tool.daily_commit]" in text:
        updated = text.replace(
            "[tool.daily_commit]\n",
            f'[tool.daily_commit]\nci-python-version = "{minor}"\n',
        )
    else:
        updated = text.rstrip() + f'\n\n[tool.daily_commit]\nci-python-version = "{minor}"\n'

    pyproject.write_text(updated, encoding="utf-8")
    return pyproject


def sync_python_version(root: Path) -> PythonVersionSync:
    current_minor = read_configured_minor(root)

    try:
        latest_minor, latest_full = fetch_latest_stable_python()
    except (urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Python version check skipped: {exc}")
        return PythonVersionSync(False, current_minor, current_minor, current_minor, ())

    if _version_key(latest_minor) <= _version_key(current_minor):
        print(f"Python version up to date ({current_minor}). Latest available: {latest_minor}.")
        return PythonVersionSync(False, current_minor, latest_minor, latest_full, ())

    changed: list[Path] = [
        _write_version_config(root, latest_minor, latest_full),
    ]
    pyproject = _update_pyproject(root, latest_minor)
    if pyproject is not None:
        changed.append(pyproject)

    # Note: GITHUB_TOKEN in GitHub Actions cannot push changes touching .github/workflows/*.
    # The CI workflow uses python-version: "3.x" with check-latest: true.
    # Therefore, we never modify or stage workflow files during GitHub Actions CI.
    is_ci = os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI") == "true"
    if not is_ci:
        workflow = _update_workflow(root, latest_minor)
        if workflow is not None:
            changed.append(workflow)

    print(f"Python version updated: {current_minor} -> {latest_minor} ({latest_full})")
    return PythonVersionSync(True, current_minor, latest_minor, latest_full, tuple(changed))