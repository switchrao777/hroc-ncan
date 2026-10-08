import zarr

import numpy as np

z = zarr.open("data/processed/animal9.zarr", mode="r")

for name in ["ecog", "emg", "hreflex", "phase"]:

    arr = z[name][:]

    print(f"{name}: shape={arr.shape}, dtype={arr.dtype}")

    print(f"  NaNs: {np.isnan(arr).sum() if arr.dtype.kind == 'f' else 0}")

    print(f"  min={arr.min()}, max={arr.max()}, mean={arr.mean()}")

phase = z["phase"][:]

unique, counts = np.unique(phase, return_counts=True)

print("\nTrials per phase:")

for p, c in zip(unique, counts):

    print(f"  phase {p}: {c}")
    