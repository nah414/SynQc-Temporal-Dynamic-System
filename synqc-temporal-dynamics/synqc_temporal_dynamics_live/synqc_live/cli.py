"""
Command-line interface for the SynQc Temporal Dynamic System live core.

This CLI is intentionally thin and delegates all heavy lifting to
synqc_live.runtime so that:
- notebooks can reuse the same helpers
- services can import the same functions
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from .runtime import (
    PipelineResult,
    build_quickstart_config,
    run_pipeline,
    run_pipeline_from_yaml,
)


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the SynQc Temporal Dynamics live pipeline."
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Optional YAML config file. If omitted, a built-in quickstart "
             "configuration is used.",
    )
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=5,
        help="Number of adaptive loop iterations to run (default: 5).",
    )
    parser.add_argument(
        "--no-adapt",
        action="store_true",
        help="Skip the adaptive loop and run only a single iteration.",
    )
    parser.add_argument(
        "--dump-iteration-csv",
        type=Path,
        help="Optional path to write the single-iteration DataFrame as CSV.",
    )
    parser.add_argument(
        "--dump-adaptive-csv",
        type=Path,
        help="Optional path to write the adaptive-loop DataFrame as CSV.",
    )
    return parser.parse_args(argv)


def _print_summary(result: PipelineResult) -> None:
    iter_df = result.iteration
    print("=== SynQc iteration ===")
    print(f"Samples: {len(iter_df)}")
    print(f"Columns: {list(iter_df.columns)}")
    print(iter_df.head())

    if result.adaptive is not None:
        loop_df = result.adaptive
        print("\n=== Adaptive loop ===")
        print(f"Iterations: {len(loop_df)}")
        print(f"Columns: {list(loop_df.columns)}")
        print(loop_df)


def main(argv: Optional[List[str]] = None) -> None:
    args = _parse_args(argv)

    if args.config is not None:
        result = run_pipeline_from_yaml(
            args.config,
            num_iterations=args.iterations,
            run_adaptive=not args.no_adapt,
        )
    else:
        cfg = build_quickstart_config()
        result = run_pipeline(
            cfg,
            num_iterations=args.iterations,
            run_adaptive=not args.no_adapt,
        )

    _print_summary(result)

    if args.dump_iteration_csv is not None:
        result.iteration.to_csv(args.dump_iteration_csv, index=False)
        print(f"\n[written] iteration CSV → {args.dump_iteration_csv}")

    if args.dump_adaptive_csv is not None and result.adaptive is not None:
        result.adaptive.to_csv(args.dump_adaptive_csv, index=False)
        print(f"[written] adaptive CSV → {args.dump_adaptive_csv}")


if __name__ == "__main__":
    main()
