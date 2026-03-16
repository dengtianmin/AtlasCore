#!/usr/bin/env python3

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def build_sample_graph(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    now = _now_iso()
    version_id = str(uuid4())

    nodes = [
        {
            "id": "atlascore",
            "name": "AtlasCore",
            "node_type": "system",
            "source_document": "sample_overview.md",
            "description": "AtlasCore backend service",
            "tags_json": json.dumps(["backend", "fastapi"]),
            "metadata_json": json.dumps({"layer": "platform", "status": "active"}),
        },
        {
            "id": "dify",
            "name": "Dify",
            "node_type": "integration",
            "source_document": "sample_overview.md",
            "description": "Knowledge QA orchestrator",
            "tags_json": json.dumps(["integration", "qa"]),
            "metadata_json": json.dumps({"role": "answer-generation"}),
        },
        {
            "id": "sqlite",
            "name": "SQLite",
            "node_type": "storage",
            "source_document": "sample_architecture.md",
            "description": "Primary local storage",
            "tags_json": json.dumps(["database", "local"]),
            "metadata_json": json.dumps({"mode": "single-instance"}),
        },
        {
            "id": "graph_runtime",
            "name": "Graph Runtime",
            "node_type": "module",
            "source_document": "sample_architecture.md",
            "description": "In-memory graph query runtime",
            "tags_json": json.dumps(["networkx", "graph"]),
            "metadata_json": json.dumps({"engine": "networkx.MultiDiGraph"}),
        },
        {
            "id": "admin_console",
            "name": "Admin Console",
            "node_type": "frontend",
            "source_document": "sample_ui.md",
            "description": "Administrator UI for graph operations",
            "tags_json": json.dumps(["frontend", "admin"]),
            "metadata_json": json.dumps({"path": "/admin"}),
        },
        {
            "id": "graph_page",
            "name": "Graph Page",
            "node_type": "frontend",
            "source_document": "sample_ui.md",
            "description": "Frontend graph visualization page",
            "tags_json": json.dumps(["frontend", "graph"]),
            "metadata_json": json.dumps({"path": "/graph"}),
        },
        {
            "id": "qa_logs",
            "name": "QA Logs",
            "node_type": "data",
            "source_document": "sample_logs.md",
            "description": "Question-answer record storage",
            "tags_json": json.dumps(["logs", "analytics"]),
            "metadata_json": json.dumps({"exportable": True}),
        },
        {
            "id": "csv_exports",
            "name": "CSV Exports",
            "node_type": "feature",
            "source_document": "sample_exports.md",
            "description": "CSV export capability",
            "tags_json": json.dumps(["export", "csv"]),
            "metadata_json": json.dumps({"admin_only": True}),
        },
    ]

    edges = [
        ("e1", "atlascore", "dify", "INTEGRATES_WITH", "integrates_with"),
        ("e2", "atlascore", "sqlite", "PERSISTS_TO", "persists_to"),
        ("e3", "atlascore", "graph_runtime", "USES", "uses"),
        ("e4", "graph_page", "atlascore", "CALLS_API", "calls_api"),
        ("e5", "admin_console", "atlascore", "MANAGES", "manages"),
        ("e6", "atlascore", "qa_logs", "WRITES", "writes"),
        ("e7", "csv_exports", "qa_logs", "EXPORTS", "exports"),
        ("e8", "admin_console", "csv_exports", "TRIGGERS", "triggers"),
        ("e9", "graph_page", "graph_runtime", "VISUALIZES", "visualizes"),
        ("e10", "graph_runtime", "sqlite", "LOADS_FROM", "loads_from"),
    ]

    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE graph_nodes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                node_type TEXT,
                source_document TEXT,
                description TEXT,
                tags_json TEXT,
                metadata_json TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE graph_edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                relation_label TEXT,
                source_document TEXT,
                weight REAL,
                metadata_json TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE graph_sync_records (
                id TEXT PRIMARY KEY,
                source_document_id TEXT,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                error_message TEXT,
                summary TEXT
            );

            CREATE TABLE graph_versions (
                id TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                build_time TEXT,
                source_batch TEXT,
                exported_at TEXT,
                imported_at TEXT,
                note TEXT,
                is_current INTEGER NOT NULL
            );
            """
        )

        conn.executemany(
            """
            INSERT INTO graph_nodes (
                id, name, node_type, source_document, description, tags_json, metadata_json, created_at, updated_at
            ) VALUES (
                :id, :name, :node_type, :source_document, :description, :tags_json, :metadata_json, :created_at, :updated_at
            )
            """,
            [{**node, "created_at": now, "updated_at": now} for node in nodes],
        )

        conn.executemany(
            """
            INSERT INTO graph_edges (
                id, source_id, target_id, relation_type, relation_label, source_document, weight, metadata_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    edge_id,
                    source_id,
                    target_id,
                    relation_type,
                    relation_label,
                    "sample_relations.md",
                    1.0,
                    json.dumps({"demo": True}),
                    now,
                    now,
                )
                for edge_id, source_id, target_id, relation_type, relation_label in edges
            ],
        )

        conn.execute(
            """
            INSERT INTO graph_sync_records (
                id, source_document_id, status, started_at, finished_at, error_message, summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                None,
                "seeded",
                now,
                now,
                None,
                "Sample graph generated for frontend validation",
            ),
        )
        conn.execute(
            """
            INSERT INTO graph_versions (
                id, version, build_time, source_batch, exported_at, imported_at, note, is_current
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id,
                "sample-v1",
                now,
                "sample-script",
                None,
                now,
                "Generated by scripts/generate_sample_graph_sqlite.py",
                1,
            ),
        )
        conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a sample graph SQLite file for AtlasCore.")
    parser.add_argument(
        "--output",
        default="data/sample_graph.db",
        help="Output SQLite path. Default: data/sample_graph.db",
    )
    args = parser.parse_args()

    output_path = Path(args.output).expanduser().resolve()
    build_sample_graph(output_path)
    print(f"Sample graph SQLite generated: {output_path}")
    print("Nodes: 8, Edges: 10, Version: sample-v1")


if __name__ == "__main__":
    main()
