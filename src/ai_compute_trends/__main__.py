"""Command line entry point: python -m ai_compute_trends."""

import argparse
import sys
from pathlib import Path

from .analysis import main as run
from .load import DEFAULT_CSV, ROOT


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_CSV, help="Epoch notable models CSV")
    parser.add_argument("--out", type=Path, default=ROOT / "outputs", help="findings and Tableau CSV directory")
    parser.add_argument("--docs", type=Path, default=ROOT / "docs", help="findings page and chart directory")
    args = parser.parse_args(argv)
    try:
        findings = run(args.data, args.out, args.docs)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, f"ai-compute-trends: {error}\n")
    totals = findings["totals"]
    print(f"{totals['models']} models, {totals['with_compute']} with compute | {args.out} | {args.docs / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
