from collections import Counter
from pathlib import Path
import re
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# point to a Devanagari font
# adjust path if needed
font_path = "/usr/share/fonts/noto/NotoSansDevanagari-Regular.ttf"
prop = fm.FontProperties(fname=font_path)

gt_dir = Path("dataset/final_set/final")
all_text = ""
for f in gt_dir.glob("*.gt.txt"):
    all_text += f.read_text(encoding="utf-8")

# keep only Devanagari characters
devanagari = re.findall(r'[\u0900-\u097F]', all_text)
counter = Counter(devanagari)
top = counter.most_common(20)

chars, counts = zip(*top)
plt.figure(figsize=(12, 4))
bars = plt.bar(range(len(chars)), counts, color="steelblue")
plt.xticks(range(len(chars)), chars, fontproperties=prop, fontsize=12)
plt.xlabel("Character")
plt.ylabel("Frequency")
plt.title("Top 20 Most Frequent Devanagari Characters")
plt.savefig("char_frequency.png", dpi=150, bbox_inches="tight")
plt.close()
