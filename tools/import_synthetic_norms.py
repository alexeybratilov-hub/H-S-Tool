from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.db import init_db
from ot_agent.regulatory_db import (
    chunk_exists,
    create_source,
    init_regulatory_schema,
    source_exists,
    add_chunk,
)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)

    return digest.hexdigest()


def _read_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Manifest root must be a JSON object.")

    return data


def _resolve_relative_path(raw_path: str) -> Path:
    path = Path(raw_path)

    if path.is_absolute():
        return path

    return BASE_DIR / path


def validate_manifest(manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    prepared_sources: list[dict[str, Any]] = []

    sources = manifest.get("sources")

    if not isinstance(sources, list):
        errors.append("manifest.sources must be a list.")
        return prepared_sources, errors, warnings

    source_ids: set[str] = set()

    for source_index, source in enumerate(sources, start=1):
        entity = f"source #{source_index}"

        if not isinstance(source, dict):
            errors.append(f"{entity}: item is not an object.")
            continue

        source_id = _clean(source.get("source_id"))
        title = _clean(source.get("title"))

        if not source_id:
            errors.append(f"{entity}: source_id is empty.")
        elif source_id in source_ids:
            errors.append(f"{entity}: duplicate source_id={source_id}.")
        else:
            source_ids.add(source_id)
            entity = f"source {source_id}"

        if not title:
            errors.append(f"{entity}: title is empty.")

        file_path_raw = _clean(source.get("file_path"))
        file_path: Path | None = None

        if file_path_raw:
            file_path = _resolve_relative_path(file_path_raw)

            if not file_path.exists():
                errors.append(f"{entity}: file_path does not exist: {file_path_raw}")
            else:
                source["sha256"] = _sha256(file_path)
        else:
            warnings.append(f"{entity}: file_path is empty.")

        chunks = source.get("chunks")

        if not isinstance(chunks, list) or not chunks:
            errors.append(f"{entity}: chunks must be a non-empty list.")
            continue

        chunk_ids: set[str] = set()
        prepared_chunks: list[dict[str, Any]] = []

        for chunk_index, chunk in enumerate(chunks, start=1):
            chunk_entity = f"{entity}, chunk #{chunk_index}"

            if not isinstance(chunk, dict):
                errors.append(f"{chunk_entity}: item is not an object.")
                continue

            chunk_id = _clean(chunk.get("chunk_id"))

            if not chunk_id:
                errors.append(f"{chunk_entity}: chunk_id is empty.")
            elif chunk_id in chunk_ids:
                errors.append(f"{chunk_entity}: duplicate chunk_id={chunk_id}.")
            else:
                chunk_ids.add(chunk_id)
                chunk_entity = f"{entity}, chunk {chunk_id}"

            text_file_raw = _clean(chunk.get("text_file"))
            text_inline = _clean(chunk.get("text"))

            if text_file_raw:
                text_path = _resolve_relative_path(text_file_raw)

                if not text_path.exists():
                    errors.append(f"{chunk_entity}: text_file does not exist: {text_file_raw}")
                    continue

                text_content = text_path.read_text(encoding="utf-8").strip()

                if not text_content:
                    errors.append(f"{chunk_entity}: text_file is empty: {text_file_raw}")
                    continue
            elif text_inline:
                text_content = text_inline
            else:
                errors.append(f"{chunk_entity}: neither text_file nor text is provided.")
                continue

            prepared_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "source_id": source_id,
                    "heading_path": _clean(chunk.get("heading_path")),
                    "chunk_index": chunk.get("chunk_index", chunk_index - 1),
                    "text": text_content,
                    "keywords": _clean(chunk.get("keywords")),
                    "topic": _clean(chunk.get("topic")) or "OT",
                    "obligation_type": _clean(chunk.get("obligation_type")),
                    "applies_to_json": chunk.get("applies_to_json"),
                    "required_documents_json": chunk.get("required_documents_json"),
                    "status": _clean(chunk.get("status")) or "PARSED",
                    "confidence_tag": _clean(chunk.get("confidence_tag")) or "REQUIRES_VERIFICATION",
                }
            )

        source["chunks"] = prepared_chunks
        prepared_sources.append(source)

    return prepared_sources, errors, warnings


def check_existing_records(sources: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []

    for source in sources:
        source_id = source.get("source_id")

        if source_id and source_exists(str(source_id)):
            errors.append(f"regulatory_sources: source_id={source_id} already exists.")

        for chunk in source.get("chunks", []):
            chunk_id = chunk.get("chunk_id")

            if chunk_id and chunk_exists(str(chunk_id)):
                errors.append(f"regulatory_chunks: chunk_id={chunk_id} already exists.")

    return errors


def commit_import(sources: list[dict[str, Any]]) -> None:
    for source in sources:
        create_source(source)

        for chunk in source.get("chunks", []):
            add_chunk(chunk)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import synthetic normative fragments into SQLite."
    )
    parser.add_argument(
        "--manifest",
        default="06_TESTS/synthetic_norms/synthetic_norms_manifest.json",
        help="Path to synthetic norms manifest.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Perform real database write. Without this flag, dry-run only.",
    )

    args = parser.parse_args()

    manifest_path = _resolve_relative_path(args.manifest)

    init_db()
    init_regulatory_schema()

    try:
        manifest = _read_manifest(manifest_path)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    sources, errors, warnings = validate_manifest(manifest)

    print("=== SYNTHETIC NORMS IMPORT DIAGNOSTICS ===")
    print(f"manifest: {manifest_path}")
    print(f"sources: {len(sources)}")
    print(f"chunks: {sum(len(source.get('chunks', [])) for source in sources)}")

    if warnings:
        print("\nWARNINGS:")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("\nWARNINGS: none")

    if errors:
        print("\nERRORS:")
        for error in errors:
            print(f"- {error}")
        print("\nImport aborted.")
        return 1

    if not args.commit:
        print("\nDRY-RUN completed successfully. No database write was performed.")
        print("Run with --commit to write data.")
        return 0

    existing_errors = check_existing_records(sources)

    if existing_errors:
        print("\nDATABASE ERRORS:")
        for error in existing_errors:
            print(f"- {error}")
        print("\nImport aborted. Duplicates were not created.")
        return 1

    commit_import(sources)

    print("\nIMPORT COMPLETED SUCCESSFULLY.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())