from json import load, dump
from csv import DictWriter

out_name = f"data/changes/sstubs_devreplay.json"
with open(out_name, "r", encoding='utf-8') as f:
    data_set = load(f)
    total_count = sum(x['count'] for x in data_set)
    
    for i, pattern in enumerate(data_set):
        data_set[i]['Shift'] = any([pattern['change'][0] == y['change'][1] or y['change'][0] == pattern['change'][1] for y in data_set])
        data_set[i]['Contradiction'] = any([pattern['change'][0] == y['change'][1] and y['change'][0] == pattern['change'][1] for y in data_set])
        data_set[i]['Multi opinion'] = any([pattern['change'][0] == y['change'][0] and i!=j for j, y in enumerate(data_set)])
        data_set[i]['Filter'] = not (data_set[i]['Shift'] or data_set[i]['Contradiction'] or data_set[i]['Multi opinion'])
        data_set[i]['Bug common'] = len(pattern['bugType']) > 1
        data_set[i]['Project common'] = len(pattern['author']) > 1
    
    output = []
    for key in ['All' ,'Shift', 'Contradiction', 'Multi opinion', 'Filter']:
        if key == 'All':
            patterns = data_set.copy()
        else:
            patterns = [x for x in data_set if x[key] == True]

        project_common = [x for x in patterns if len(x['author']) > 1]
        bug_common = [x for x in patterns if len(x['bugType']) > 1]

        value = {
            key: str(len(patterns)) + ' / ' + str(sum(x['count'] for x in patterns))  for key, patterns 
            in {"All":  patterns, "Bug common":bug_common, "Project common": project_common}.items()}
        value["Category"] = key

        output.append(value)

    out_name = f"data/changes/sstubs_devreplay_summary2.csv"
    with open(out_name, "w",  encoding='utf-8') as f:
        writer = DictWriter(f, ["Category", "All", "Bug common", "Project common"])
        writer.writeheader()
        writer.writerows(output)
        print("\nSuccess to collect the pull changes Output is " + out_name)

    out_name = f"data/changes/sstubs_devreplay_common_summary.json"
    with open(out_name, "w", encoding='utf-8') as f:
        data_set = sorted(data_set, key=lambda k: k['count'], reverse=True) 
        dump(data_set, f, indent=1)
    