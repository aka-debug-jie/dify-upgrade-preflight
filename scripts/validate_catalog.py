#!/usr/bin/env python3
"""Validate catalog structure without treating a planning matrix as supported."""

import argparse
import json
from pathlib import Path

from dify_preflight.catalog.load import CatalogPolicy, CatalogValidationError, load_catalog


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    args = parser.parse_args()
    try:
        catalog = load_catalog(args.catalog, CatalogPolicy(root=args.catalog.parent))
    except CatalogValidationError as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 1
    print(json.dumps({"ok": True, "edge_count": len(catalog.edges), "rule_count": len(catalog.rules), "catalog_digest": catalog.digest, "catalog_trust": catalog.trust, "supported_edges_claimed": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
