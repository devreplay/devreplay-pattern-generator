# Generate Source Code Change Pattern from Review History

This rules can be used on [devreplay](https://www.npmjs.com/package/devreplay)
And you can use your rule by the [vscode extension](https://marketplace.visualstudio.com/items?itemName=Ikuyadeu.devreplay)

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

(If your target `Ruby` organization name is `mruby`)
```json
{
    "github_token": "Your github token",
    // Your Target Language (e.g. Python, Ruby, Java, JavaScript, CPP)
    "lang": "CPP",
    // Number of rules that you want (e.g. 100)
    "change_size": 1000,
    "projects": [
        {
            "owner": "mruby",
            "repo": "mruby"
        },
        {
            "owner": "matz",
            "repo": "streem"
        }
    ],
    // will you get all authors change? (true or false)
    "all_author": true,
    "authors": [
        // if all_author is true, choose target authors' name and github id
        {
            "git": "Yukihiro Matsumoto",
            "github": "matz"
        },
        {
            "git": "Yukihiro \"Matz\" Matsumoto"
        }
    ],
    "learn_from": "pulls",
    "validate_by": "master"
}
```

### 2. Collecting training data set

Run `collect_changes.py`.

```sh
python3 collect_changes.py
```

After run these script, some files output to `data` dirs.The details are as follows.

Output:
* Pull List (`data/pulls/{owner}_{repo}.csv`)
If `learn_from` or `validate_by` is `master`
* Master Change List (`data/changes/{owner}_{repo}_{lang}_master.json`)

If `learn_from` or `validate_by` is `pulls`
* Pull Change List (`data/changes/{owner}_{repo}_{lang}_pulls.json`)


### 3. Extracting reusable changes

If you want to get more information about these output, please do this section.
```sh
python3 test_rules.py
```
You can get frequency,accuracy,failed_number(pull_requests),successed_number(pull_requests) informations.


or
```sh
python3 test_rules_on_dir.py
```

Output:
If projects is only one project

* Pattern (`data/changes/{owner}_{repo}_{lang}_(pulls|master)_validated.json`)

If you choose more than one projects

* Pattern (`data/changes/devreplay.json`)

### Thanks

I would like to thank the Support Center for Advanced Telecommunications (SCAT) Technology Research, Foundation. This system was supported by JSPS KAKENHI Grant Numbers JP18H03222, JP17H00731, JP15H02683, and JP18KT0013.

Also, this repository use other repository
https://github.com/Ikuyadeu/CodeTokenizer

