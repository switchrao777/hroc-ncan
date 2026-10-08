import zarr
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

z = zarr.open("data/processed/animal9.zarr", mode="r")

emg = z["emg"][:]

sample_rate = 5000
n_samples = emg.shape[1]
time_ms = np.arange(n_samples) / sample_rate * 1000

avg_emg = np.mean(emg, axis=0)

print("EMG shape:", emg.shape)
print("Average EMG shape:", avg_emg.shape)
print("Average EMG min:", avg_emg.min())
print("Average EMG max:", avg_emg.max())
print("Average EMG mean:", avg_emg.mean())

plt.figure(figsize=(10, 5))
plt.plot(time_ms, avg_emg)

plt.axvspan(2, 4, alpha=0.2, label="M-wave window (2–4 ms)")
plt.axvspan(8, 10, alpha=0.2, label="H-reflex window (8–10 ms)")

plt.title("Animal 9 Average EMG Across All Decoded Records")
plt.xlabel("Time after stimulus (ms)")
plt.ylabel("Amplitude (µV)")
plt.legend()
plt.tight_layout()

Path("outputs").mkdir(exist_ok=True)
plt.savefig("outputs/animal9_average_emg.png", dpi=200)
plt.show()

print("Saved plot to outputs/animal9_average_emg.png")
