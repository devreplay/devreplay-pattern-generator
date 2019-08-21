# Generate Source Code Change Pattern from Review History

This rules can be used on [devreplay](https://www.npmjs.com/package/devreplay)

## How to Use

### 0. Cloning this repository

```sh
git clone https://github.com/Ikuyadeu/review_pattern_gen.git
cd review_pattern_gen
pip3 install antlr4-python3-runtime prefixspan PyGithub unidiff numpy
git clone https://github.com/Ikuyadeu/CodeTokenizer.git
```

### 1. Preparing config file

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
lang = Your Target Language (e.g. Python, Ruby, Java, JavaScript, CPP)
[Option]
rule_size = Number of rules that you want (e.g. 100)
learn_from_pulls = If no, this tool will learn from master branch (e.g. yes or no)
abstract_master_change = If yes, this tool will abstract master changes' identifier, string, number like `${1:NAME}` (e.g. yes or no)
validate_by_pulls = Check collected changes by pull changes or master changes. If `learn_from_pulls` is `no`, you can not choose yes (e.g. yes or no)

combined_owner = (**option if you want to use other projects' rules) Your Combination GitHub Repository Owner (e.g. tensorflow)
combined_repo = repo = (**option if you want to use other projects' rules) Your Combination GitHub Repository (e.g. models)
```
**GitHub token can be generated from https://github.com/settings/tokens)

### 2. Collecting training data set

```sh
python3 collect_pulls.py
python3 collect_pulls_changes.py
```

Output:
* Pull List (`data/pulls/{owner}_{repo}.csv`)
* Master Change List (`data/changes/{owner}_{repo}_{lang}_master.json`)

If `Option/learn_from_pulls` is `yes`
* Pull Change List (`data/changes/{owner}_{repo}_{lang}_pulls.json`)


### 3. Extracting reusable changes

```sh
python3 test_rules.py
```

Output:
* Pattern (`data/changes/{owner}_{repo}_{lang}_(pulls|master)_validated.json`)

### Sample

This repository put a part of `tensorflow/model`s' review data on `data/changes` directory.
Also, these data is shorter than correct data set.

### Use Case, and How should you set config `Option`?

#### Case 1: If you want to get rules from small repository that does not have any pull request.

```properties
[Option]
rule_size = 100
learn_from_pulls = no
abstract_master_change = yes
validate_by_pulls = no
```

#### Case 2: If you want to get rules from large repository that has more than 100 pull request.

```properties
[Option]
rule_size = 100
learn_from_pulls = yes
abstract_master_change = no
validate_by_pulls = yes or no
```

#### Case 3: If you want to use rules from other repositories' for your repository.

1. Get Rules by

```properties
[Target]
owner = Other Project Repository Owner (e.g. tensorflow)
repo = Other Project Repository (e.g. models)
lang = Your Target Language
[Option]
rule_size = 100
learn_from_pulls = no
abstract_master_change = yes
validate_by_pulls = no
```

2. Check Rules by 

```properties
[Target]
owner = Your Project Repository Owner
repo = Your Project Repository
lang = Your Target Language
[Option]
rule_size = 100
learn_from_pulls = yes
abstract_master_change = no
validate_by_pulls = yes or no
```

### Thanks

I would like to thank the Support Center for Advanced Telecommunications (SCAT) Technology Research, Foundation. This system was supported by JSPS KAKENHI Grant Numbers JP18H03222, JP17H00731, JP15H02683, and JP18KT0013.

Also, this repository use other repository
https://github.com/Ikuyadeu/CodeTokenizer

