# Generate Source Code Change Pattern from Review History

This rules can be used on [devreplay](https://www.npmjs.com/package/devreplay)
And you can use your rule by the [vscode extension](https://marketplace.visualstudio.com/items?itemName=Ikuyadeu.devreplay)

### Requirements

* Python3
* Ruby (If you will collect ruby rulles)
* git
* GitHub account and [github token](https://github.com/settings/tokens)

## How to Use

### 0. Cloning this repository

```sh
git clone https://github.com/Ikuyadeu/review_pattern_gen.git
cd review_pattern_gen
pip3 install antlr4-python3-runtime unidiff gitpython
git clone https://github.com/Ikuyadeu/CodeTokenizer.git
```

### 1. Preparing config file

Making empty `config.json` file

```sh
touch config.json
```

and edit `config.json` file like berrow

* If you try first time, please check bottom example for the `Option` setting
* GitHub token can be generated from https://github.com/settings/tokens)

(If your target `CPP` organization name is `mruby`)
```json
{
    // Your github token from https://github.com/settings/tokens
    "github_token": "Your github token",
    // Your Target Language (Python, Ruby, Java, JavaScript, CPP, PHP)
    "lang": "CPP",
    "all_change": true,
    // (if all_change is false) Number of rules that you want (e.g. 100)
    "change_size": 1000,
    // (Option) Target time span
    "time_length": {
        // Default (if not defined) is 1 years ago from today
        "start": "2018-01-01 00:00:00",
        // Default is today
        "end": "2019-01-01 00:00:00"
    },
    // Target of learning and validating (pulls or master)
    "learn_from": "pulls",
    "validate_by": "master",
    // You will get all authors change or not (true or false)
    "all_author": false,
    // Projects that you want to learn
    "projects": [
        {
            "owner": "mruby",
            "repo": "mruby",
            "branch": "master"
        },
        {
            "owner": "matz",
            "repo": "streem"
        }
    ],
    // (Option) You can define projects by another file
    "projects_path": "data/projects/rails_Ruby.json",
    // (Option) Projects that you want to apply
    "applied_projects": [
        {
            "owner": "matz",
            "repo": "streem"
        }
    ],
    // (Option) if all_author is false, choose target authors' name and github id
    "authors": [
        {
            "git": "Yukihiro Matsumoto",
            "github": "matz"
        },
        {
            "git": "Yukihiro \"Matz\" Matsumoto"
        }
    ]
}
```

### 2. Collecting training data set

```sh
chmod +x make_rules.sh
sh make_rules.sh
```

`make_rules.sh` will runnning `collect_changes.py` and `test_rules.py`

#### collect_changes.py

After run this script, followed files will be output on `data` dir.

* Pull List (`data/pulls/{owner}_{repo}.csv`)
If `learn_from` or `validate_by` is `master`
* Master Change List (`data/changes/{owner}_{repo}_{lang}_master.json`)

If `learn_from` or `validate_by` is `pulls`
* Pull Change List (`data/changes/{owner}_{repo}_{lang}_pulls.json`)


#### test_rules.py

You can get popularity, frequency, accuracy,failed_number(pull_requests),successed_number(pull_requests) informations.

Example:

```json
[  
  {
    "repository": "owner/repo",
    "sha": "Change_Commit_Sha",
    "author": "Change Author",
    "created_at": "2019-04-09 11:56:38",
    "condition": [
      "${0:Identifier}.pullRequests.${1:Identifier}"
    ],
    "consequent": [
      "${0:Identifier}.pulls.${1:Identifier}"
    ],
    "popularity": 0.7272727272727273,
    "self_popularity": 0.3333333333333333,
    "applicable_files": [
      "app/lib/pro/get-status.js",
      "app/test/integration/pro-plan-test.js"
    ],
    "link": "https://github.com/wei/pull/commit/Change_Commit_SHA",
    "successed_number": [],
    "failed_number": [
      "wip/app:669407dcef96ae12227e4e5d0308d335eb6ca052"
    ],
    "frequency": 0,
    "accuracy": 0.0
  },
]
```
If projects is only one project

* Pattern (`data/changes/{owner}_{repo}_{lang}_(pulls|master)_devreplay.json`)

If you choose more than one projects

* Pattern (`data/changes/devreplay.json`)

### Thanks

I would like to thank the Support Center for Advanced Telecommunications (SCAT) Technology Research, Foundation. This system was supported by JSPS KAKENHI Grant Numbers JP18H03222, JP17H00731, JP15H02683, and JP18KT0013.

Also, this repository use other repository
https://github.com/Ikuyadeu/CodeTokenizer
