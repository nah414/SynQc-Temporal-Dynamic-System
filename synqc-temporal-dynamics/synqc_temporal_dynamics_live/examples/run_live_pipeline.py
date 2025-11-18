"""Run the live SynQc pipeline and optionally package the directory.

This script mirrors the quick-start example for the `synqc_live` package
while ensuring the local sources are importable without installation. It
can also recreate a zip archive of the live package directory for
transfer or archival testing.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import zipfile

# Ensure the live package directory is importable even if the legacy
# `synqc` package shadows it on the Python path.
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from synqc_live.config import PulseConfig, SynQcConfig
from synqc_live.engine import SynQcEngine


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=2,
        help="Number of adaptive loop iterations to run (default: 2)",
    )
    parser.add_argument(
        "--skip-zip",
        action="store_true",
        help="Skip rebuilding the synqc_temporal_dynamics_live.zip archive",
    )
    parser.add_argument(
        "--zip-path",
        type=Path,
        default=BASE_DIR.parent / "synqc_temporal_dynamics_live.zip",
        help="Optional path for the rebuilt zip archive",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    iterations = max(1, args.iterations)

    config = SynQcConfig(
        sample_rate_hz=1e9,
        lo_frequency_hz=50e6,
        cycle_duration_ns=1000.0,
        num_cycles=4,
        target_amplitude=1.0,
        pulses=[
            PulseConfig(
                label="drive",
                amplitude=1.0,
                phase_deg=0.0,
                frequency_hz=50e6,
                duration_ns=400.0,
            ),
        ],
        probe_every_n_cycles=2,
    )

    engine = SynQcEngine.build_default(config)
    df_iter = engine.run_iteration()
    df_loop = engine.run_adaptive(num_iterations=iterations)

    if not args.skip_zip:
        zip_path = args.zip_path
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in BASE_DIR.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(BASE_DIR.parent))
        print("Zip written to", zip_path)

    print("Iteration samples: ", df_iter.head())
    print("Adaptive loop summary:\n", df_loop)


if __name__ == "__main__":
    main()
