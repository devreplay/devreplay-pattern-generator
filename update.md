## ルールのフォーマット

[Textmate snippet](https://www.google.com/search?q=textmate+snippets&oq=textmate+snippets&aqs=chrome..69i57j0l4.4459j0j4&sourceid=chrome&ie=UTF-8)を採用
* $1, $2...と続くものは変更前後で共通する変数

### メリット

* 複数行の変更へ対応可能になった
* vimおよびvscodeのコードスニペットとして転用可能

## 要素について

```json
#ソース元に関する情報
number: 該当プルリクエスト(PR)番号
author: 該当PRの作成者
participant: 該当PRの参加者（レビューア）
file_path: 変更されたファイル

#ルールに関する情報
condition: 変更前を抽象化した文
condition: 変更後を抽象化した文
identifiers: 変更前後での特徴的な識別子，または利用された関数

#評価項目
condition/consequent: 変更後の識別子を含むファイル数/変更前の識別子を含むファイル数
frequency: 該当PR後に類似した変更を行ったPRの数

repeated_pr_id: 同様の変更を適用できる可能性のあるファイル
```

利用ケースとして，２つの用途を考えています
1. repeated_pr_idに該当するファイルを修正する
2. レビュー時にidentifiers.conditionを含むファイルに対してルールを適用する

## 環境：
* 対象とする変更数を決めるためにconfigの` Target` に `changesize` を定義する必要がある．
学習データとして最新のPRのなかで学習に利用できるもの `changesize` 件を取得する
現状使われているソースコードを抽出する都合上100以上にしてもあまり有用なデータはとれにくい

## パフォーマンス

`sider/sideci`, Target.changesize = 200時
* 実行速度は `collect_pulls` を実行し終わっていれば30分からない程度

## 提供したルールファイルのフィルタリング

* condition != consequent != []
* condition/consequent > 1.0　または condition > consequent(e.g. create -> create)