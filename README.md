# 最強かわいい読み上げちゃん Bot

![screenshot](assets/screenshot.png)

VOICEVOX と連携して Discord チャンネルの文章を読み上げる Bot。以下の機能があります。

-   テキストチャットの文章読み上げ
-   単語辞書
-   会話文辞書によるおしゃべり
-   マルコフ連鎖によるおしゃべり
-   mp3 ファイルの登録と再生

単一の個人サーバーで運用することを想定しています。\
VOICEVOX と各キャラクターの規約を遵守して使用しましょう。

### コマンド一覧

```
ボイスチャットに参加
$c
ボイスチャットから切断
$d
再生中の音声をスキップ
$next
再生速度を変更
$set_speed {小数}
文字数が多い時にどれだけ速くするかを変更
$set_speed_margin {小数}
声のピッチを変更
$set_pitch {小数}

キャラクター変更
$tumugi
$zundamon
$himari
$sayo
$tt

辞書
$dict_add 肉 にく
$dict_list
$dict_check 肉
$dict_rm 肉

会話（マルコフ連鎖）
名前を呼ぶかメンションをしても反応します。
$talk
または
$talk_m

マルコフ連鎖による文章生成はある程度学習が進むとうまくいくようになります。失敗した時は辞書を参照します。

会話（辞書）
$talk_d
$talk_add kusa 草
$talk_list
$talk_check kusa
$talk_rm kusa

チャンネルの履歴から学習する（admin権限が必要です）
$learn_history {整数。読み込むメッセージの数}

サーバー内のすべてのテキストチャンネルの履歴から学習する（admin権限が必要です）
指定する数値は各チャンネルに適応されます。
$learn_channels_history {整数。読み込むメッセージの数}

学習結果を忘れる（admin権限が必要です）
$learn_forget

会話文中の特殊文字
{dict} ... 辞書に登録された言葉
{dict_yomi} ... 辞書に登録された言葉の読み
{emoji} ... サーバーに登録された絵文字

音声ファイル
$play ファイル名（拡張子なし）
$play_add {ファイル添付。.mp3のみ。}
$play_list
$play_check ファイル名（拡張子なし）
$play_rm ファイル名（拡張子なし）
```

<br>

Ubunto 22.04LTS で動作確認。 \
python のバージョンは 3.12 です。

<br>

### MeCab 導入

MeCab のインストール

```
$ sudo apt install mecab
$ sudo apt install libmecab-dev
$ sudo apt install mecab-ipadic-utf8
```

<br>

mecab-ipadic-neologd（辞書）のインストール

https://github.com/neologd/mecab-ipadic-neologd/blob/master/README.ja.md

```
$ git clone https://github.com/neologd/mecab-ipadic-neologd.git
$ cd mecab-ipadic-neologd
$ sudo bin/install-mecab-ipadic-neologd
```

<br>

mecab-ipadic-neologd の移動

```
$ sudo mv /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd /var/lib/mecab/dic
```

<br>

MeCab の辞書の設定がまだ ipadic になっているので変更する

```
$ sudo vim /etc/mecabrc

;
; Configuration file of MeCab
;
; $Id: mecabrc.in,v 1.3 2006/05/29 15:36:08 taku-ku Exp $;
;
; dicdir = /var/lib/mecab/dic/debian ⇐ 最初にセミコロン追加
dicdir = /var/lib/mecab/dic/mecab-ipadic-neologd ⇐ 一行追加
; userdic = /home/foo/bar/user.dic
; output-format-type = wakati
; input-buffer-size = 8192
; node-format = %m\n
; bos-format = %S\n
; eos-format = EOS\n
```

<br>

Python に導入

```
$ pip install mecab-python3
$ pip install markovify
```

<br>

mecabrc へのシンボリックリンクを作成

```
$ sudo ln -s /etc/mecabrc /usr/local/etc/mecabrc
```

<br>

必要であればユーザー辞書を作成する
https://taku910.github.io/mecab/dic.html

補足: nkf コマンド（文字コード変換）のインストール

```
$ sudo apt-get install nkf
```

補足: mecab-dict-index の path

```
$ /usr/lib/mecab/mecab-dict-index
```

<br>

### 導入

1. requirements を pip インストール
2. VOICEVOX の vv-engine を起動（サービスに登録したほうがいい）
3. config_exapmle.json を config.json にリネーム
4. config.json 内に discord bot のトークンを記載
5. `yomiage.py`を実行　（これもサービスに登録したほうがいいです）

<br>

補足: VOICEVOX の導入

以下の URL からダウンロードして解凍する。

```
wget https://github.com/VOICEVOX/voicevox/releases/download/0.21.1/voicevox-linux-cpu-0.21.1.tar.gz
tar xvzf voicevox-linux-cpu-0.21.1.tar.gz
```

手動でダウンロードしてインストールしてもいい。バージョンが更新されていることがあるので公式サイトを確認すること。 \
https://voicevox.hiroshiba.jp/

<br>

解凍したフォルダ内の `vv-engine/run` を実行する

```
cd VOICEVOX
./vv-engine/run
```

<br>

補足: サービスの登録

以下の記事が参考になります。
https://pyopyopyo.hatenablog.com/entry/2021/04/30/233755 \
https://yuukou-exp.plus/ubuntu-register-my-service-to-system/

<br>

### 参考

https://qiita.com/kado_u/items/e736600f8d295afb8bd9 \
https://qiita.com/kakakaya/items/38042e807f3410b88b2d \
https://atmarkit.itmedia.co.jp/ait/articles/2102/19/news026.html
