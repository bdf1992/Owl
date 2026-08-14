#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from owl_engine.mcp import OwlMcpService, StdioMcpServer  # noqa: E402
from owl_engine.state import FileStateStore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OWL_ENGINE as a local-first stdio MCP server.")
    parser.add_argument(
        "--state-dir",
        type=Path,
        required=True,
        help="authorized directory for target-local JSON state",
    )
    args = parser.parse_args()
    server = StdioMcpServer(OwlMcpService(FileStateStore(args.state_dir)))

    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            response = server.handle(request)
        except Exception as error:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": str(error)},
            }
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
