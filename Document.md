# フィックスポイント プログラミング試験 説明

## 実行方法

本ソースコードはDocker上のPythonで動く。

まず、以下のコマンドでコンテナの起動を行う。

```
% docker-compose up -d
```

次に、以下のコマンドでPythonのコンテナに入る。

```
% docker-compose exec answer bash
```

コンテナを終了させたい場合は、以下のコマンドを実行する。

```
% docker-compose down
```

コンテナ内でのプロンプトを'#'、コンテナ外でのプロンプトを'%'で表す。以降はコンテナ内で作業する。


## テスト方法

細かい処理は`pytest`を用いてテストしている。これは`tests/`にある。これは以下のコマンドでテストできる。

```
# pytest
```


プログラム全体の処理をテストするためのテストデータは`testcases/`ディレクトリ下にある。この使い方については設問ごとに後述する。


## 設問1

以下のコマンドで、設問1のプログラムを動かす。ただし、`src`は入力となるログファイルである。

```
# python answer/ans1.py src
```


### 使用したテストデータとその実行結果

以下は、`testcases/in1-1.txt`の内容である。

```txt
20201019133124,10.20.30.1/16,2
20201019133125,10.20.30.2/16,1
20201019133134,192.168.1.1/24,10
20201019133135,192.168.1.2/24,-
20201019133136,192.168.1.2/24,-
20201019133137,192.168.1.2/24,5
20201019133138,192.168.1.2/24,5
20201019133139,192.168.1.2/24,-
20201019133140,192.168.1.2/24,-
20201019133141,192.168.1.2/24,5
20201019133224,10.20.30.1/16,522
20201019133225,10.20.30.2/16,-
20201019133234,192.168.1.1/24,8
20201019133235,192.168.1.2/24,15
20201019133324,10.20.30.1/16,-
20201019133325,10.20.30.2/16,2
```

これをテストデータとした場合、以下のコマンドで実行できる。

```
# python answer/ans1.py testcases/in1-1.txt
```

実行すると、以下のように出力される。

```txt
10.20.30.1/16:
  2020-10-19 13:33:24 -
10.20.30.2/16:
  2020-10-19 13:32:25 - 2020-10-19 13:33:25
192.168.1.1/24:

192.168.1.2/24:
  2020-10-19 13:31:35 - 2020-10-19 13:31:37
  2020-10-19 13:31:39 - 2020-10-19 13:31:41
```

IPアドレスの下に、故障期間のリストが出力される。故障期間は`開始時刻 - 終了時刻`の形式で表される。ただし、故障から復帰しない場合は、`終了時刻`は表示されない。


## 設問2

以下のコマンドで、設問1のプログラムを動かす。ただし、`src`は入力となるログファイル、`N`は設問2の問題文で与えられたパラメーターである。

```
# python answer/ans2.py src N
```

### 使用したテストデータとその実行結果

以下は、`testcases/in2-1.txt`の内容である。

```txt
20201019133124,10.20.30.1/16,2
20201019133125,10.20.30.2/16,-
20201019133134,192.168.1.1/24,10
20201019133135,192.168.1.2/24,5
20201019133224,10.20.30.1/16,522
20201019133225,10.20.30.2/16,-
20201019133234,192.168.1.1/24,8
20201019133235,192.168.1.2/24,15
20201019133324,10.20.30.1/16,-
20201019133325,10.20.30.1/16,-
20201019133326,10.20.30.1/16,-
20201019133327,10.20.30.1/16,-
20201019133328,10.20.30.1/16,-
20201019133329,10.20.30.1/16,2
20201019133329,10.20.30.1/16,-
20201019133329,10.20.30.1/16,-
20201019133230,10.20.30.2/16,-
20201019133231,10.20.30.2/16,-
20201019133232,10.20.30.2/16,-
```

これをテストデータとした場合、以下のコマンドで実行できる。以下の場合、3回以上連続してタイムアウトとなった場合故障とみなす。

```
# python answer/ans2.py testcases/in2-1.txt 3
```

実行すると、以下のように出力される。

```txt
10.20.30.1/16:
  2020-10-19 13:33:24 - 2020-10-19 13:33:29
10.20.30.2/16:
  2020-10-19 13:31:25 -
192.168.1.1/24:

192.168.1.2/24:
  
```

入力のフォーマットは設問1と同様である。


## 設問3

以下のコマンドで、設問3のプログラムを動かす。ただし、`src`は入力となるログファイル、`N`は設問2の問題文で与えられたパラメータ、`m,t`は設問3の問題文で与えられたパラメータである。

```
# python answer/ans3.py src N m t
```

タイムアウトと過負荷状態の関係については、以下のように仕様を定義する: 直近`m`回の中でタイムアウトが1度でも起こると、サーバーは過負荷状態と判定される。特に、タイムアウトが`N`回以上連続すると故障と判定される。

### 使用したテストデータとその実行結果

以下は、`testcases/in3-1.txt`の内容である。

```txt
20201019133124,10.20.30.1/16,1
20201019133125,10.20.30.1/16,2
20201019133126,10.20.30.1/16,3
20201019133127,10.20.30.1/16,4
20201019133128,10.20.30.1/16,1
20201019133129,10.20.30.1/16,1
20201019133130,10.20.30.1/16,1
20201019133131,192.168.1.1/16,1
20201019133132,192.168.1.1/16,100
20201019133133,192.168.1.1/16,100
20201019133134,192.168.1.1/16,100
20201019133135,10.20.30.1/16,-
20201019133136,10.20.30.1/16,-
20201019133137,10.20.30.1/16,-
20201019133138,10.20.30.1/16,1
20201019133139,10.20.30.1/16,1
20201019133140,10.20.30.1/16,1
20201019133141,10.20.30.1/16,1
20201019133141,10.20.30.1/16,1
20201019133142,10.20.30.1/16,-
20201019133143,10.20.30.1/16,-
20201019133144,10.20.30.1/16,-
20201019133145,10.20.30.1/16,1
```

これをテストデータとした場合、以下のコマンドで実行できる。
以下の場合、3回以上連続してタイムアウトとなった場合故障とみなす。また、過去4回の中での平均応答時間が2.5ミリ秒を超え場合に、過負荷状態とみなす。

```
# python answer/ans3.py testcases/in3-1.txt 3 4 2.5
```

実行すると、以下のように出力される。

```txt
10.20.30.1/16:
  OVERLOAD(2020-10-19 13:31:27 - 2020-10-19 13:31:29)
  FAILURE (2020-10-19 13:31:35 - 2020-10-19 13:31:38)
  OVERLOAD(2020-10-19 13:31:38 - 2020-10-19 13:31:41)
  FAILURE (2020-10-19 13:31:42 - 2020-10-19 13:31:45)
  OVERLOAD(2020-10-19 13:31:45 -)
192.168.1.1/16:
  OVERLOAD(2020-10-19 13:31:32 -)
```

`OVERLOAD`は過負荷状態、`FAILURE`は故障を表す。括弧でくくられている日付は、過負荷または故障の期間を表す。

## 設問4

以下のコマンドで、設問4のプログラムを動かす。これは設問3と同様である。

```
# python answer/ans4.py src N m t
```

### 使用したテストデータとその実行結果

以下は、`testcases/in3-1.txt`の内容である。

```txt
20201019133101,192.168.1.1/24,-
20201019133102,192.168.1.1/24,-
20201019133103,192.168.1.2/24,-
20201019133104,192.168.1.1/24,-
20201019133105,192.168.1.2/24,-
20201019133106,192.168.1.2/24,-
20201019133107,192.168.1.2/24,-
20201019133108,192.168.1.3/24,-
20201019133109,192.168.1.3/24,-
20201019133110,192.168.1.3/24,-
20201019133111,192.168.2.1/24,1
20201019133112,192.168.2.2/24,2
20201019133113,192.168.2.3/24,3
20201019133114,192.168.2.1/24,1
20201019133115,192.168.1.1/24,1
```

これをテストデータとした場合、以下のコマンドで実行できる。
以下の場合、3回以上連続してタイムアウトとなった場合故障とみなす。また、過去100回の中での平均応答時間が100ミリ秒を超え場合に、過負荷状態とみなす。

```
# python answer/ans4.py testcases/in4-1.txt 3 100 100
```

実行すると、以下のように出力される。

```txt
[Interface]
192.168.1.1/24:
  FAILURE (2020-10-19 13:31:01 - 2020-10-19 13:31:15)
  OVERLOAD(2020-10-19 13:31:15 -)
192.168.1.2/24:
  FAILURE (2020-10-19 13:31:03 -)
192.168.1.3/24:
  FAILURE (2020-10-19 13:31:08 -)
192.168.2.1/24:

192.168.2.2/24:

192.168.2.3/24:


[Network]
192.168.1.0/24:
  FAILURE (2020-10-19 13:31:10 - 2020-10-19 13:31:15)
192.168.2.0/24:
```

`[Interface]`のセクションは、ネットワークインターフェースごとの過負荷・故障期間を表す。
`[Network]`セクションは、サブネットごとの故障期間を表す。サブネット上インターフェースがすべて故障している期間を、サブネットの故障期間としている。
