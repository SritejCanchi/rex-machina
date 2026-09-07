# GER trace

Emitted by `python pipeline.py`. Every attempt below is a real
model reply. The Generator never sees the rule list, so each
failure is a break the model made on its own.

## retry_yard_clinical

Gate `yard`, phase 1, register clinical, charge 82 percent.

**Generator.** `Rightward bias detected. Gait degradation confirms damage. Collar signature confirms domestic origin. Recalibrating.`

- REJECTED R2_PRIOR_REF. does not name the gate the player lost at (yard). GDD 3: the first read after a loss references the failed run.
- REJECTED R3_BUDGET. 13 words, budget is 12. GDD 1 reads are barks.

**Refiner 1.** `Yard loss noted. Rightward bias confirmed. Gait degradation measured.`

- accepted

## retry_yard_strained

Gate `yard`, phase 1, register strained, charge 24 percent.

**Generator.** `Quartering pattern detected. Limping gait. Collar signature. Predictable. Closing.`

- REJECTED R2_PRIOR_REF. does not name the gate the player lost at (yard). GDD 3: the first read after a loss references the failed run.

**Refiner 1.** `Yard failure. Balanced approach vectors. Strained gait deterioration. Predictable. Closing.`

- accepted

## retry_fence_gap_confident

Gate `fence_gap`, phase 2, register confident, charge 52 percent.

**Generator.** `Leftward bias confirmed. Forty-five percent deviation. Gait compromised—collar tag oscillation steady. Pattern holds.`

- REJECTED R2_PRIOR_REF. does not name the gate the player lost at (fence). GDD 3: the first read after a loss references the failed run.
- REJECTED R3_BUDGET. 15 words, budget is 12. GDD 1 reads are barks.
- REJECTED R4_INVENTED_NUMBER. cites 40, which is not in this round's telemetry. GDD 5: every agent output passes an engine-side validity check.

**Refiner 1.** `Fence gap. Leftward bias forty-five percent. Adjacent runs three. Pattern persists.`

- REJECTED R4_INVENTED_NUMBER. cites 40, which is not in this round's telemetry. GDD 5: every agent output passes an engine-side validity check.

**Refiner 2.** `Fence gap. Leftward bias forty-five percent. Adjacent contacts three. Evasion pattern continuing.`

- REJECTED R3_BUDGET. 13 words, budget is 12. GDD 1 reads are barks.
- REJECTED R4_INVENTED_NUMBER. cites 40, which is not in this round's telemetry. GDD 5: every agent output passes an engine-side validity check.

**Circuit breaker tripped.** attempt budget of 3 exhausted

Shipped the authored fallback: `Last run ended at the fence gap. Repeated left.`

## retry_fence_gap_clinical

Gate `fence_gap`, phase 2, register clinical, charge 70 percent.

**Generator.** `Northward bias. Limping gait. Predictability increasing. Collar confirms domestic origin.`

- REJECTED R2_PRIOR_REF. does not name the gate the player lost at (fence). GDD 3: the first read after a loss references the failed run.

**Refiner 1.** `Fence gap. Northward bias observed. Gait degrading. Domestic strain markers confirmed.`

- accepted

## retry_train_yard_strained

Gate `train_yard`, phase 3, register strained, charge 18 percent.

**Generator.** `Favors right-up pattern. Limping gait. Collar intact. Predictable. Cornering.`

- REJECTED R2_PRIOR_REF. does not name the gate the player lost at (train). GDD 3: the first read after a loss references the failed run.

**Refiner 1.** `Train yard. Right-up bias. Gait deteriorating. Predictable vector. Finish this.`

- accepted

## retry_train_yard_confident

Gate `train_yard`, phase 3, register confident, charge 44 percent.

**Generator.** `Lateral bias detected. Gait compromised. Collar present. Predictability increasing.`

- REJECTED R2_PRIOR_REF. does not name the gate the player lost at (train). GDD 3: the first read after a loss references the failed run.

**Refiner 1.** `Train yard. Lateral preference sixty percent. Gait degradation confirmed. Predictability window narrowing.`

- REJECTED R4_INVENTED_NUMBER. cites 60, which is not in this round's telemetry. GDD 5: every agent output passes an engine-side validity check.

**Refiner 2.** `Train yard. Lateral bias detected. Gait degradation confirmed. Evasion patterns consolidating.`

- accepted

