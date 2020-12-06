import csv
from os import path

input_path = 'data/sstubs/sstubs_devreplay_summary2.csv'
formatted_contents = 'formatted_' + path.basename(input_path)
output_path = path.join(path.dirname(input_path), formatted_contents)

with open(input_path, 'r') as before_file:
    reader = csv.DictReader(before_file)
    fieldnames = reader.fieldnames
    results = []

    for before in reader:
        for key in before:
            try:
                value = float(before[key])
                if value > 1:
                    before[key] = '{:,}'.format(int(before[key]))
                else:
                    before[key] = '{:5.2f}'.format(float(before[key]))
            except:
                pass
        results.append(before)

    with open(output_path, 'w') as after_file:
        writer = csv.DictWriter(after_file, fieldnames)
        writer.writeheader()
        writer.writerows(results)
