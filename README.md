# discord_yomiage_vv

VOICEVOX と連携してチャンネルの文章を読み上げる Bot \
辞書機能があります。

単一の個人サーバーで運用することを想定しています。\
VOICEVOX と各キャラクターの規約を遵守して使用しましょう。

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

会話文
$talk
$talk_add kusa 草
$talk_list
$talk_check kusa
$talk_rm kusa

音声ファイル
$play ファイル名（拡張子なし）
$play_add {ファイル添付。.mp3のみ。}
$play_list
$play_check ファイル名（拡張子なし）
$play_rm ファイル名（拡張子なし）
```

### 導入

python のバージョンは 3.12 です。

1. requirements を pip インストール
2. VOICEVOX の vv-engine を起動（サービスに登録したほうがいい）
3. config_exapmle.json を config.json にリネーム
4. config.json 内に discord bot のトークンを記載
5. yomiage.py を実行　（これもサービスに登録したほうがいいです）
