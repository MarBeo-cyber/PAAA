from paaa.baseline import BaselineEngine

history = [0.10, 0.11, 0.09, 0.10, 0.12, 0.11, 0.10]
current = 0.18

engine = BaselineEngine()
result = engine.compare(history, current)

print("Current:", result.value)
print("Baseline:", round(result.baseline_mean, 3))
print("Z-score:", round(result.z_score, 2))
print("Persistent deviation:", result.persistent)
