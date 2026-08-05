# Animal roster — direction and conditioning strength (from logs)

Scanned every available `emg-eeg-N-log.MYD` (2026-08-05). Direction comes from the
type-15 "Start HRdown / Started HRup" marker. **Conditioning strength** is read from
how the reward criterion `RW` evolved: the experimenters RAISE the bar as the animal
succeeds and LOWER it when the animal struggles. For up-conditioning, a rising RW
means the reflex is genuinely getting bigger (Carp's 20% success bar).

## UP-conditioned
| animal | RW start → peak | change | read |
|---|---|---|---|
| **4** | 150 → 220 | **+47%** | **STRONG — best up animal** |
| **3** | 90 → 190 | **+111%** | **STRONG** |
| 1 | 110 → 55 | −50% | failed (criterion lowered) |
| 6 | 150 → 100 | −33% | failed (criterion lowered) |
| 12 | (processed) | — | weak responder; also poor EMG signal (~2x background) |

## DOWN-conditioned
| animal | status |
|---|---|
| 9 | processed — clear down-conditioning (H −77% M-matched) |
| 10 | processed — 40-day recording gap complicates it |
| 11 | processed — effect vanishes after background subtraction |
| 7, 8, 13, 14, 15 | logs scanned, direction confirmed, data not downloaded |

## Other
- **2** — only 1 type-15 entry; log looks incomplete/unusable.
- `Ni` variants (7i, 8i, …) — intermittent, no conditioning. Phase-1 pretraining only.

## Download priority (big `-data.{MYD,MYI,frm}` files)
1. **Animal 4** — strongest up-conditioner. The single highest-value dataset we
   don't have; it's what the up-vs-down contrast needs.
2. **Animal 3** — second strong up-conditioner. Two up animals >> one.
3. **Animal 13 or 14** — additional down animals (long logs, 163/129 entries).

Do NOT prioritise animals 1, 6 (failed up-conditioning) or 2 (bad log).
