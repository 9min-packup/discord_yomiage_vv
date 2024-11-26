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
制御
$c  ボイスチャットに参加
$d  ボイスチャットから切断
$next 再生中の音声をスキップ

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

会話
名前を呼んでも反応します。
$talk

会話（辞書）
$talk_d
$talk_add kusa 草
$talk_list
$talk_check kusa
$talk_rm kusa

会話（マルコフ連鎖）
$talk_m

チャンネルの履歴から学習する
$learn_history {整数(メッセージの数)}

学習結果を忘れる
$learn_forget

マルコフ連鎖による文章生成はある程度学習が進むとうまくいくようになります。失敗した時は辞書による生成を行います。

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

python のバージョンは 3.12 です。 \

### MeCab 導入

MeCab のインストール

```
$ sudo apt install mecab
$ sudo apt install libmecab-dev
$ sudo apt install mecab-ipadic-utf8
```

\
mecab-ipadic-neologd（辞書）のインストール
https://github.com/neologd/mecab-ipadic-neologd/blob/master/README.ja.md

```
$ git clone https://github.com/neologd/mecab-ipadic-neologd.git
$ cd mecab-ipadic-neologd
$ sudo bin/install-mecab-ipadic-neologd
```

mecab-ipadic-neologd の移動

```
$ sudo mv /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd /var/lib/mecab/dic
```

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

Python に導入

```
$ pip install mecab-python3
$ pip install markovify
```

mecabrc へのシンボリックリンクを作成

```
$ sudo ln -s /etc/mecabrc /usr/local/etc/mecabrc
```

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

### 導入

1. requirements を pip インストール
2. VOICEVOX の vv-engine を起動（サービスに登録したほうがいい）
3. config_exapmle.json を config.json にリネーム
4. config.json 内に discord bot のトークンを記載
5. yomiage.py を実行　（これもサービスに登録したほうがいいです）

### 参考

https://qiita.com/kado_u/items/e736600f8d295afb8bd9 \
https://qiita.com/kakakaya/items/38042e807f3410b88b2d \
https://atmarkit.itmedia.co.jp/ait/articles/2102/19/news026.html
