# 限定みやげ地図

東京23区・大阪の「その店・その駅でしか買えないお土産」を地図で探せる静的サイトです。
`data/spots.json` を編集して `python3 build.py` を実行すると、`docs/` にサイト一式が生成されます。

## フォルダ構成

```
omiyage-site/
├── build.py          サイト生成スクリプト（Python 3.8以上、追加インストール不要）
├── config.json       サイト名・URL・運営者・アフィリエイト設定
├── data/spots.json   店とお土産のデータ（ここを編集する）
├── assets/           CSS と地図・絞り込みの JavaScript
└── docs/             生成されたサイト（これを公開する）
```

生成されるページ（現在44ページ）:

- トップ（全地点の地図＋エリア・種類・予算・日持ち・個包装での絞り込み）
- エリアページ `/tokyo/` `/osaka/`
- 店ページ `/spot/<id>/`（例：グランスタ東京）
- 商品ページ `/item/<id>/`（価格・日持ち・個包装・最終確認日・出典）
- このサイトについて（広告の方針）、プライバシーポリシー、404
- `sitemap.xml`、`robots.txt`

## GitHub Pages で公開する手順

1. GitHub で新しいリポジトリを作る（例：`omiyage-map`）。
2. `config.json` を書き換える。
   - `site_url`: `https://<あなたのGitHubユーザー名>.github.io`
   - `base_path`: `/<リポジトリ名>`（例：`/omiyage-map`）
   - `owner`、`contact`: 運営者名と問い合わせ先
3. `python3 build.py` を実行する。
4. このフォルダ全体をリポジトリに push する。
5. リポジトリの Settings → Pages → Build and deployment で、
   Source を「Deploy from a branch」、Branch を `main` / `/docs` にして保存する。
6. 数分後に `https://<ユーザー名>.github.io/<リポジトリ名>/` で公開されます。
7. Google Search Console にサイトを登録し、`sitemap.xml` を送信する。

独自ドメインを使う場合は、`site_url` をそのドメイン、`base_path` を `""`（空）にして再生成し、Pages の Custom domain に設定します。

## お土産を追加する

`data/spots.json` の `items` に1件追加して再生成します。

```json
{"id": "英数字とハイフンのID", "spot": "店のid", "name": "商品名", "shop": "ブランド名",
 "price": "表示用の価格（例：1,296円 / 9枚）", "price_yen": 1296,
 "keep": "表示用の日持ち", "keep_days": 30, "wrapped": true,
 "type": "only | area | meibutsu",
 "desc": "説明文", "where": "売り場（任意）", "src": "出典キー", "checked": "2026-10-29"}
```

- `price_yen`・`keep_days` は絞り込みに使う数値です。わからなければ `null` にします（その条件で絞り込んだときは表示されません）。
- `wrapped` は個包装なら `true`、なしなら `false`、未確認なら `null`。
- 新しい店は `spots` に追加します。`lat`・`lng` は Google マップで店を右クリックすると出る座標をそのまま使えます。
- `checked` は実際に確認した日付に更新してください。

**現在の店の座標は目安です。** 公開前に Google マップで確認して直してください（特になんば周辺）。

## アフィリエイトを有効にする

1. `config.json` の `affiliate_enabled` を `true` にする。
2. 通販で買える商品には、その商品に `online` を追加する。
   ```json
   "online": [{"label": "楽天市場で見る", "url": "https://（アフィリエイトリンク）"}]
   ```
3. ホテルなどの宿泊リンクは `config.json` の `stay_links` に追加する。
   ```json
   "stay_links": {"tokyo": [{"label": "東京駅周辺のホテル（楽天トラベル）", "url": "https://..."}]}
   ```
4. 再生成すると、リンクに「PR」表示が付き、全ページのフッターに広告利用の告知が出ます。

広告リンクには `rel="sponsored"` が自動で付きます。ステルスマーケティング規制（景品表示法）への対応として、PR表示は消さないでください。

## 公開前のチェックリスト

- [ ] `config.json` の URL・運営者・問い合わせ先を設定した
- [ ] 店の座標を Google マップで確認した
- [ ] 亀十のどら焼きの価格（記事によって360円と430円で違う）を確認した
- [ ] プライバシーポリシーを、使うサービス（解析・広告）に合わせて直した
- [ ] 写真を載せる場合は自分で撮ったものを使う

## 地図について

地図は Leaflet と OpenStreetMap のタイルで表示しています。OpenStreetMap の公式タイルは大量アクセス向けではないため、アクセスが増えてきたら MapTiler などのタイル配信サービスに切り替えてください（`assets/map.js` の `tileLayer` の URL を変えるだけです）。
