from pathlib import Path
import matplotlib.pyplot as plt

gt_dir = Path("dataset/final_set/final")
lengths = []
for f in gt_dir.glob("*.gt.txt"):
    text = f.read_text(encoding="utf-8").strip()
    lengths.append(len(text))

plt.figure()
plt.hist(lengths, bins=30, color="steelblue", edgecolor="black")
plt.xlabel("Line length (characters)")
plt.ylabel("Frequency")
plt.title("Distribution of Ground Truth Line Lengths")
plt.savefig("line_length_distribution.png", dpi=150, bbox_inches="tight")
plt.close()
