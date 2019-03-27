# Generate Source Code Change Pattern from Review History

## How to Use

### 0 Cloning this repository

```sh
git clone https://github.com/Ikuyadeu/review_pattern_gen.git
cd review_pattern_gen
```

### 1 Preparing config file

```sh
touch config
```

and edit `config` file like berrow

(If your target `Python` repository name is `tensorflow/model`)
```properties
[GitHub]
id = YourGitHubId
password = YourGitHubPassword
[Target]
owner = Your Target GitHub Repository Owner (e.g. model)
repo = Your Target GitHub Repository (e.g. tensorflow)
lang = Your Target Language (e.g. Python)
```

### 2 Collecting training data set


```sh
python3 collect_pulls.py
puthon3 collect_changes.py
```

Output:
* Pull List (`pulls/{owner}_{repo}.csv`)
* Change List (`changes/{owner}_{repo}_python.json`)

### 3 Generating frequently appered patterns

```sh
python3 generate_rules.py
```

Output:
* Pattern (`rules/{owner}_{repo}_python.json`)

<!-- ### 4 (Option) Filter patterns

If you want the pattern that has
Frequency > 0.1%
Accuracy > 50%

```sh
python3 filter_patterns.py owner repo 0.1 50
```

Output
* Pattern (`patterns/{owner}_{repo}_python_filtered.json`) -->
