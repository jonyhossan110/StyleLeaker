from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import AnyStr, Dict, Optional


def ensure_directory(path: Path) -> Path:
    """Create a directory if it does not exist."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        temp_dir = Path(tempfile.mkdtemp(prefix='styleleaker_'))
        return temp_dir
    return path


def save_text_file(path: Path, content: str, encoding: str = 'utf-8') -> Path:
    """Save a text file to disk."""
    output_path = ensure_directory(path.parent)
    target_path = output_path / path.name
    try:
        target_path.write_text(content, encoding=encoding)
    except OSError as exc:
        fallback = Path(tempfile.mkdtemp(prefix='styleleaker_')) / path.name
        fallback.write_text(content, encoding=encoding)
        return fallback
    return target_path


def normalize_filename(name: str, default: str = 'asset') -> str:
    """Create a safe filename from a string."""
    sanitized = ''.join(ch for ch in name if ch.isalnum() or ch in ('-', '_', '.')).strip()
    return sanitized or default


def build_output_paths(base_output: Path, domain: str) -> Dict[str, Path]:
    """Build standard output directories for a target domain."""
    domain_path = ensure_directory(base_output / domain)
    return {
        'root': domain_path,
        'css': ensure_directory(domain_path / 'css'),
        'html': ensure_directory(domain_path / 'html'),
    }
