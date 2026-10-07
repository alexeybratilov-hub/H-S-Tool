from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = BASE_DIR / "06_TESTS" / "synthetic_norms"

SOURCE_001_TEXT = """SYNTHETIC NORMATIVE FRAGMENT.

This is a technical test object for the OT Local Agent data pipeline.

It is not a real legal requirement.
It is not an official normative act.
It must not be used in an approved occupational health and safety document.

Synthetic subject: warehouse operations, work at height, moving loads, PPE, training, briefing.

This fragment is provided only to test source registration, chunk storage, keyword search, and human verification workflow.
"""

SOURCE_002_TEXT = """SYNTHETIC NORMATIVE FRAGMENT.

This is a technical test object for medical examination metadata workflow.

It is not a real legal requirement.
It does not establish examination intervals.
It does not establish contingents.
It does not contain medical diagnoses.

Synthetic subject: periodic medical examination metadata, deadline control, document drafting placeholder.

This fragment is provided only to test metadata minimization and verification status handling.
"""

SOURCE_003_TEXT = """SYNTHETIC NORMATIVE FRAGMENT.

This is a technical test object for operational control workflow.

It is not a real legal requirement.
It does not define inspection powers.
It does not define corrective action deadlines.

Synthetic subject: inspection, finding, corrective action, closure, work permit placeholder.

This fragment is provided only to test event-based operational documents later.
"""

MANIFEST = {
    "description": "Synthetic normative fragments for pipeline testing only. Not legal sources.",
    "sources": [
        {
            "source_id": "SYN_NORM_001",
            "title": "Synthetic Occupational Safety Requirement Alpha",
            "doctype": "TEST_RULE",
            "issuer": "TEST_AUTHORITY",
            "approval_date": "2026-01-01",
            "effective_date": "2026-01-01",
            "status": "ACTIVE",
            "topic": "OT",
            "industry": "TEST",
            "file_path": "06_TESTS/synthetic_norms/SYN_NORM_001.txt",
            "source_reference": "SYNTHETIC_TEST_DATA",
            "retrieval_date": "2026-10-08",
            "review_date": None,
            "verified_by": None,
            "verification_status": "REQUIRES_VERIFICATION",
            "comment": "Synthetic source. Requires manual verification before any use.",
            "chunks": [
                {
                    "chunk_id": "SYN_CHUNK_001_01",
                    "heading_path": "Section 1. Synthetic warehouse and height requirements",
                    "chunk_index": 0,
                    "text_file": "06_TESTS/synthetic_norms/SYN_NORM_001.txt",
                    "keywords": "warehouse height ppe training briefing moving_loads",
                    "obligation_type": "TEST_OBLIGATION",
                    "topic": "OT",
                    "status": "PARSED",
                    "confidence_tag": "REQUIRES_VERIFICATION",
                }
            ],
        },
        {
            "source_id": "SYN_NORM_002",
            "title": "Synthetic Medical Examination Metadata Placeholder",
            "doctype": "TEST_RULE",
            "issuer": "TEST_AUTHORITY",
            "approval_date": "2026-01-01",
            "effective_date": "2026-01-01",
            "status": "ACTIVE",
            "topic": "OT",
            "industry": "TEST",
            "file_path": "06_TESTS/synthetic_norms/SYN_NORM_002.txt",
            "source_reference": "SYNTHETIC_TEST_DATA",
            "retrieval_date": "2026-10-08",
            "review_date": None,
            "verified_by": None,
            "verification_status": "REQUIRES_VERIFICATION",
            "comment": "Synthetic source. Does not establish medical intervals or contingents.",
            "chunks": [
                {
                    "chunk_id": "SYN_CHUNK_002_01",
                    "heading_path": "Section 1. Synthetic medical metadata workflow",
                    "chunk_index": 0,
                    "text_file": "06_TESTS/synthetic_norms/SYN_NORM_002.txt",
                    "keywords": "medical examination metadata deadline contingent placeholder",
                    "obligation_type": "TEST_METADATA",
                    "topic": "OT",
                    "status": "PARSED",
                    "confidence_tag": "REQUIRES_VERIFICATION",
                }
            ],
        },
        {
            "source_id": "SYN_NORM_003",
            "title": "Synthetic Operational Control Placeholder",
            "doctype": "TEST_RULE",
            "issuer": "TEST_AUTHORITY",
            "approval_date": "2026-01-01",
            "effective_date": "2026-01-01",
            "status": "ACTIVE",
            "topic": "OT",
            "industry": "TEST",
            "file_path": "06_TESTS/synthetic_norms/SYN_NORM_003.txt",
            "source_reference": "SYNTHETIC_TEST_DATA",
            "retrieval_date": "2026-10-08",
            "review_date": None,
            "verified_by": None,
            "verification_status": "REQUIRES_VERIFICATION",
            "comment": "Synthetic source for future event-based operational documents.",
            "chunks": [
                {
                    "chunk_id": "SYN_CHUNK_003_01",
                    "heading_path": "Section 1. Synthetic inspection and corrective action workflow",
                    "chunk_index": 0,
                    "text_file": "06_TESTS/synthetic_norms/SYN_NORM_003.txt",
                    "keywords": "inspection finding corrective_action closure work_permit operational",
                    "obligation_type": "TEST_OPERATIONAL",
                    "topic": "OT",
                    "status": "PARSED",
                    "confidence_tag": "REQUIRES_VERIFICATION",
                }
            ],
        },
    ],
}


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Created: {path.relative_to(BASE_DIR).as_posix()}")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    write_text_file(OUT_DIR / "SYN_NORM_001.txt", SOURCE_001_TEXT)
    write_text_file(OUT_DIR / "SYN_NORM_002.txt", SOURCE_002_TEXT)
    write_text_file(OUT_DIR / "SYN_NORM_003.txt", SOURCE_003_TEXT)

    manifest_path = OUT_DIR / "synthetic_norms_manifest.json"

    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(MANIFEST, file, ensure_ascii=False, indent=2)

    print(f"Created: {manifest_path.relative_to(BASE_DIR).as_posix()}")
    print("Synthetic normative files created.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())