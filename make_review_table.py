import csv

lengthes = [5, 50, 100, 500, "1day", "3day"]
results = []

for length in lengthes:
    with open(f"data/result/microsoft_vscode_JavaScript_pulls_{length}.csv", "r") as target:
        reader = csv.DictReader(target)
        patched = [x for x in reader if x["suggested_num"] != "0"]
        corrected = [x for x in patched if x["success"] == "True"]
        results.append({
            "length": length,
            "patched": len(patched),
            "fixed": len(corrected)
        })

with open(f"microsoft_vscode_JavaScript_pulls.csv", "w") as target:
    writer = csv.DictWriter(target, ["length", "patched", "fixed"])
    writer.writeheader()
    writer.writerows(results)