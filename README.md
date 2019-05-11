# Generate Source Code Change Pattern from Review History

## How to Use

### 0 Cloning this repository

```sh
git clone https://github.com/Ikuyadeu/review_pattern_gen.git
cd review_pattern_gen
pip3 install antlr4-python3-runtime prefixspan PyGithub unidiff numpy
git clone https://github.com/Ikuyadeu/CodeTokenizer.git
```

### 1 Preparing config file

Making empty `config` file

```sh
touch config
```

and edit `config` file like berrow

(If your target `Python` repository name is `tensorflow/models`)
```properties
[GitHub]
id = YourGitHubId
password = YourGitHubPassword
token = (**option if you will collect from private repo)YourGitHubToken
[Target]
owner = Your Target GitHub Repository Owner (e.g. tensorflow)
repo = Your Target GitHub Repository (e.g. models)
lang = Your Target Language (e.g. Python)
[Rule]
threshold = Rule threshold (e.g. 2, it means all repeated changes are rule)
```
**GitHub token can be generated from https://github.com/settings/tokens)

### 2 Collecting training data set


```sh
python3 collect_pulls.py
python3 collect_changes.py
```

Output:
* Pull List (`data/pulls/{owner}_{repo}.csv`)
* Change List (`data/changes/{owner}_{repo}_python.json`)

### 3 Generating frequently appered patterns

This process needs long time

```sh
python3 generate_rules.py
```

Output:
* Pattern (`data/rules/{owner}_{repo}_python.json`)

### 4 Evaluating detected patterns

```sh
python3 evaluated_rules.py
```

Output:
* Pattern (`data/rules/{owner}_{repo}_python_evaluated.json`)

### Sample

This repository put a part of `tensorflow/model`s' review data on each directory.
Also, these data is shorter than correct data set.

### Thanks

I would like to thank the Support Center for Advanced Telecommunications (SCAT) Technology Research, Foundation. This system was supported by JSPS KAKENHI Grant Numbers JP18H03222, JP17H00731, JP15H02683, and JP18KT0013.

Also, this repository use other repository
https://github.com/Ikuyadeu/CodeTokenizer

