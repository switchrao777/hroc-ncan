

"""
convert_animal9_to_zarr.py

Purpose:
Convert real Animal 9 decoded signal data into the Zarr format expected by
Suchith's HROC autoencoder training pipeline.

This is the first practical converter version. It does NOT use the unfinished
SQLAlchemy ORM stub yet because `utils/sqlalchemy_loader.py` currently has the
blob-decoding function marked as not implemented.

Current workflow:
Animal 9 .MYD file
    -> decoder_2006.py
    -> NumPy signal array shaped (N, 2, 150)
    -> split into EMG and ECoG
    -> compute H-reflex peak amplitude from 8-10 ms
    -> create placeholder phase labels
    -> save everything into animal9.zarr

Output Zarr schema:
animal9.zarr/
    ecog     (N, 150) float32
    emg      (N, 150) float32
    hreflex  (N,)     float32
    phase    (N,)     int64
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
import zarr


# -----------------------------------------------------------------------------
# Project path setup
# -----------------------------------------------------------------------------
# This script lives here:
#   hroc-ncan/hroc-training/scripts/convert_animal9_to_zarr.py
#
# But the Animal 9 decoder lives here:
#   hroc-ncan/decoders/decoder_2006.py
#
# So we add the main hroc-ncan project root to Python's import path.
# That lets this script import decoder_2006.py even though this file is inside
# the hroc-training folder.
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from decoders.decoder_2006 import decode_frag1  # noqa: E402


# -----------------------------------------------------------------------------
# Constants for Animal 9
# -----------------------------------------------------------------------------
SAMPLE_RATE_HZ = 5000
WINDOW_SAMPLES = 150
H_REFLEX_START_MS = 8.0
H_REFLEX_END_MS = 10.0


# -----------------------------------------------------------------------------
# Helper function: convert milliseconds to sample index
# -----------------------------------------------------------------------------
def ms_to_sample(ms: float, sample_rate_hz: int = SAMPLE_RATE_HZ) -> int:
    """
    Convert a time in milliseconds into a sample index.

    Animal 9 was sampled at 5000 Hz, meaning 5000 samples per second.
    Since 1 second = 1000 ms, this is 5 samples per millisecond.

    Example:
    8 ms  -> sample 40
    10 ms -> sample 50
    """
    return int((ms / 1000.0) * sample_rate_hz)


# -----------------------------------------------------------------------------
# Main converter
# -----------------------------------------------------------------------------
def convert_animal9_to_zarr(myd_path: Path, out_path: Path) -> None:
    """
    Convert Animal 9 MYD data into a Zarr store.

    Parameters
    ----------
    myd_path:
        Path to Animal 9 data MYD file, usually:
        data/raw/ani-emg-eeg-9/emg-eeg-9-data.MYD

    out_path:
        Path where the Zarr output should be written, usually:
        hroc-training/data/processed/animal9.zarr
    """
    if not myd_path.exists():
        raise FileNotFoundError(f"Could not find MYD file: {myd_path}")

    print("=" * 72)
    print("Animal 9 -> Zarr converter")
    print("=" * 72)
    print(f"Input MYD:  {myd_path}")
    print(f"Output Zarr: {out_path}")
    print()

    # -------------------------------------------------------------------------
    # Step 1: Decode the raw Animal 9 MYD file
    # -------------------------------------------------------------------------
    # decode_frag1 reads the 2006-format Animal 9 binary file and returns:
    #   signals shape = (N, 2, 150)
    #
    # N = number of decoded records/trials
    # 2 = two channels
    # 150 = 150 samples per 30 ms trial window
    #
    # Important: fix_baseline=False because the baseline fix is not implemented
    # yet. Suchith said this is currently blocked on him.
    # -------------------------------------------------------------------------
    print("Decoding Animal 9 MYD with decoder_2006.py...")
    signals = decode_frag1(str(myd_path), fix_baseline=False)

    print(f"Decoded signals shape: {signals.shape}")

    if signals.ndim != 3:
        raise ValueError(f"Expected signals to be 3D, got shape {signals.shape}")

    if signals.shape[1] != 2:
        raise ValueError(f"Expected 2 channels, got shape {signals.shape}")

    if signals.shape[2] != WINDOW_SAMPLES:
        raise ValueError(
            f"Expected {WINDOW_SAMPLES} samples per trial, got shape {signals.shape}"
        )

    # -------------------------------------------------------------------------
    # Step 2: Split the two channels
    # -------------------------------------------------------------------------
    # Lab naming:
    #   Channel 1 = SOLR EMG muscle signal
    #   Channel 2 = ECoG cortical brain signal
    #
    # Python indexing:
    #   signals[:, 0, :] = Channel 1 = EMG
    #   signals[:, 1, :] = Channel 2 = ECoG
    # -------------------------------------------------------------------------
    emg = signals[:, 0, :].astype(np.float32)
    ecog = signals[:, 1, :].astype(np.float32)

    n_trials = emg.shape[0]

    print(f"EMG shape:  {emg.shape}")
    print(f"ECoG shape: {ecog.shape}")
    print(f"Number of decoded records/trials: {n_trials}")

    # -------------------------------------------------------------------------
    # Step 3: Compute H-reflex label
    # -------------------------------------------------------------------------
    # The H-reflex is expected in Channel 1 / EMG around 8-10 ms after stimulus.
    # At 5000 Hz:
    #   8 ms  = sample 40
    #   10 ms = sample 50
    #
    # For each trial, we take the largest absolute EMG value inside that window.
    # This creates one H-reflex amplitude label per trial.
    #
    # NOTE: This is a starter label. Suchith/Carp may later decide to use
    # peak-to-peak H amplitude, H/M ratio, or H normalized to Mmax instead.
    # -------------------------------------------------------------------------
    h_start_idx = ms_to_sample(H_REFLEX_START_MS)
    h_end_idx = ms_to_sample(H_REFLEX_END_MS)

    print(
        f"H-reflex window: {H_REFLEX_START_MS}-{H_REFLEX_END_MS} ms "
        f"-> samples {h_start_idx}:{h_end_idx}"
    )

    h_window = emg[:, h_start_idx:h_end_idx]
    hreflex = np.max(np.abs(h_window), axis=1).astype(np.float32)

    print(f"H-reflex label shape: {hreflex.shape}")
    print(f"H-reflex min:    {float(np.min(hreflex)):.3f} uV")
    print(f"H-reflex max:    {float(np.max(hreflex)):.3f} uV")
    print(f"H-reflex mean:   {float(np.mean(hreflex)):.3f} uV")
    print(f"H-reflex median: {float(np.median(hreflex)):.3f} uV")

    # -------------------------------------------------------------------------
    # Step 4: Create placeholder phase labels
    # -------------------------------------------------------------------------
    # The training pipeline expects one phase label per trial.
    # Valid real labels should eventually be:
    #   0 = Baseline
    #   1 = Down-cond 1
    #   2 = Up-cond 1
    #   3 = Freely Running
    #   4 = Down-cond 2
    #   5 = Up-cond 2
    #
    # Suchith said true phase-label recovery from logs is still blocked/open.
    # For now, we store all zeros so the schema is valid and the loader can run.
    # This means phase-analysis outputs are NOT scientifically meaningful yet.
    # -------------------------------------------------------------------------
    phase = np.zeros(n_trials, dtype=np.int64)

    print("Phase labels: placeholder zeros only")
    print("WARNING: UMAP-by-phase and centroid drift are not meaningful until real phase labels are recovered.")

    # -------------------------------------------------------------------------
    # Step 5: Save arrays to Zarr
    # -------------------------------------------------------------------------
    # The hroc-training README requires exactly these four arrays:
    #   ecog     (N, 150) float32
    #   emg      (N, 150) float32
    #   hreflex  (N,)     float32
    #   phase    (N,)     int64
    # -------------------------------------------------------------------------
    if out_path.exists():
        print(f"Removing existing Zarr store: {out_path}")
        shutil.rmtree(out_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("Writing Zarr store...")
    root = zarr.open_group(str(out_path), mode="w")

    root.create_array("ecog", data=ecog)
    root.create_array("emg", data=emg)
    root.create_array("hreflex", data=hreflex)
    root.create_array("phase", data=phase)

    print()
    print("Done. Created Zarr store with arrays:")
    print(f"  ecog:    {root['ecog'].shape} {root['ecog'].dtype}")
    print(f"  emg:     {root['emg'].shape} {root['emg'].dtype}")
    print(f"  hreflex: {root['hreflex'].shape} {root['hreflex'].dtype}")
    print(f"  phase:   {root['phase'].shape} {root['phase'].dtype}")
    print()
    print("Next step: update hroc-training/config.yaml")
    print("  data.use_synthetic: false")
    print(f"  data.zarr_path: {out_path}")


# -----------------------------------------------------------------------------
# Command-line interface
# -----------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Animal 9 MYD file into the Zarr format expected by hroc-training."
    )

    parser.add_argument(
        "--myd",
        type=Path,
        default=PROJECT_ROOT / "data/raw/ani-emg-eeg-9/emg-eeg-9-data.MYD",
        help="Path to Animal 9 data MYD file.",
    )

    parser.add_argument(
        "--out",
        type=Path,
        default=PROJECT_ROOT / "hroc-training/data/processed/animal9.zarr",
        help="Output Zarr path.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    convert_animal9_to_zarr(args.myd, args.out)