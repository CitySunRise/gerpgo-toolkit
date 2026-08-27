#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TEXT_SUFFIXES = {
    "",
    ".cfg",
    ".example",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
BLOCKED_SUFFIXES = {".csv", ".har", ".key", ".log", ".pem", ".xls", ".xlsx"}
BLOCKED_NAME_PARTS = {"cookie", "credential", "download", "export", "profile", "session"}
ALLOW_EMAIL_DOMAINS = {"example.invalid", "users.noreply.github.com"}

PATTERNS = {
    "private key": re.compile("-----" + r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    "cloud access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "credential in URL": re.compile(r"https?://[^\s/:]+:[^\s/@]+@"),
    "bearer credential": re.compile(
        r"(?i)authorization\s*[:=]\s*[\"']?bearer\s+[A-Za-z0-9._~+/=-]{12,}"
    ),
    "session header": re.compile(r"(?i)x-auth-token\s*[:=]\s*[\"'][A-Za-z0-9._~+/=-]{12,}"),
    "macOS home path": re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    "Windows home path": re.compile(r"[A-Za-z]:\\Users\\[A-Za-z0-9._-]+\\"),
    "ASIN-like identifier": re.compile(r"\bB0[A-Z0-9]{8}\b"),
    "private network address": re.compile(
        r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|"
        r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
    ),
    "mainland China phone number": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
}
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
CREDENTIAL_ASSIGNMENT_RE = re.compile(
    r"(?i)(?:app[_-]?id|app[_-]?key|password|username|access[_-]?token|x-auth-token)"
    r"[\"']?\s*[:=]\s*[\"']([A-Za-z0-9._~+/=-]{8,})"
)
ENV_CREDENTIAL_RE = re.compile(
    r"(?im)^GERPGO_(?:OPENAPI_APP_ID|OPENAPI_APP_KEY|WEB_USERNAME|WEB_PASSWORD)="
    r"([^\s#]+)"
)
SAFE_VALUE_PREFIXES = ("DEMO", "EXAMPLE", "GERPGO_", "REDACTED", "UNDEFINED")


def git_paths(staged: bool) -> list[Path]:
    if staged:
        command = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"]
    else:
        command = ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
    completed = subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
    return [ROOT / item.decode() for item in completed.stdout.split(b"\0") if item]


def scan(paths: list[Path]) -> list[str]:
    findings: list[str] = []
    for path in paths:
        if not path.is_file() or ".git" in path.parts:
            continue
        relative = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        lower_name = path.name.lower()
        if path.suffix.lower() in BLOCKED_SUFFIXES:
            findings.append(f"{relative}: blocked artifact type {path.suffix}")
            continue
        if (
            path.name != ".env.example"
            and any(part in lower_name for part in BLOCKED_NAME_PARTS)
            and path.suffix.lower() not in {".py", ".md"}
        ):
            findings.append(f"{relative}: sensitive-looking filename")
        if path.suffix.lower() not in TEXT_SUFFIXES and not path.name.startswith("."):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        findings.extend(scan_text(str(relative), text))
    return findings


def scan_text(label: str, text: str) -> list[str]:
    findings: list[str] = []
    for risk, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(f"{label}:{line}: {risk}")
    for match in EMAIL_RE.finditer(text):
        if match.group(1).lower() not in ALLOW_EMAIL_DOMAINS:
            line = text.count("\n", 0, match.start()) + 1
            findings.append(f"{label}:{line}: email address")
    for match in CREDENTIAL_ASSIGNMENT_RE.finditer(text):
        if not match.group(1).upper().startswith(SAFE_VALUE_PREFIXES):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(f"{label}:{line}: credential-like assignment")
    for match in ENV_CREDENTIAL_RE.finditer(text):
        if not match.group(1).upper().startswith(SAFE_VALUE_PREFIXES):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(f"{label}:{line}: credential-like environment value")
    return findings


def scan_archives(paths: list[Path]) -> list[str]:
    findings: list[str] = []
    for path in paths:
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                for member in archive.infolist():
                    if not member.is_dir():
                        findings.extend(
                            _scan_archive_member(path, member.filename, archive.read(member))
                        )
            continue
        if tarfile.is_tarfile(path):
            with tarfile.open(path) as archive:
                for member in archive.getmembers():
                    if not member.isfile():
                        continue
                    extracted = archive.extractfile(member)
                    if extracted is not None:
                        findings.extend(_scan_archive_member(path, member.name, extracted.read()))
            continue
        findings.append(f"{path}: unsupported archive type")
    return findings


def _scan_archive_member(archive: Path, member: str, content: bytes) -> list[str]:
    suffix = Path(member).suffix.lower()
    if suffix in BLOCKED_SUFFIXES:
        return [f"{archive}!{member}: blocked artifact type {suffix}"]
    if suffix not in TEXT_SUFFIXES and not Path(member).name.startswith("."):
        return []
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return []
    return scan_text(f"{archive}!{member}", text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan repository files for privacy risks.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true", help="Scan staged files only.")
    mode.add_argument("--all", action="store_true", help="Scan tracked and untracked files.")
    mode.add_argument("--archive", nargs="+", type=Path, help="Scan wheel, ZIP, or tar archives.")
    args = parser.parse_args()
    paths = git_paths(staged=args.staged) if not args.archive else []
    findings = scan(paths) if not args.archive else scan_archives(args.archive)
    if findings:
        print("Privacy scan blocked:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    checked = len(args.archive) if args.archive else len(paths)
    label = "archives" if args.archive else "files"
    print(f"Privacy scan passed: {checked} {label} checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
