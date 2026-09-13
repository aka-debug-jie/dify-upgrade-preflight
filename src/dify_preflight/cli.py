import argparse
import json
import sys
from collections.abc import Sequence

from dify_preflight.demo import load_demo


class ContractArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(64, f"{self.prog}: error: {message}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = ContractArgumentParser(prog="dify-preflight", description="Synthetic-only Dify Upgrade Preflight demo")
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo", help="Run a synthetic-only contract demonstration")
    demo.add_argument("--case", choices=("blocked", "resolved", "unknown", "external"), default="blocked")
    demo.add_argument("--format", choices=("json", "text"), default="text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report, exit_code = load_demo(args.case)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"DEMO synthetic=true verdict={report['verdict']}")
        print("This is synthetic protocol evidence, not a Dify compatibility result.")
    return exit_code
