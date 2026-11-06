#!/usr/bin/env python3
"""限定みやげ地図の静的サイトを生成する。

使い方:  python3 build.py
出力先:  docs/  （GitHub Pages の「/docs フォルダから公開」設定でそのまま公開できる）

データは data/spots.json、サイト設定は config.json を編集する。
外部ライブラリは不要（Python 3.8 以上の標準ライブラリだけで動く）。
"""
import json, shutil, html, datetime
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
DATA = json.loads((ROOT / "data" / "spots.json").read_text(encoding="utf-8"))
CHAINS = json.loads((ROOT / "data" / "chains.json").read_text(encoding="utf-8"))
FORM = CFG.get("form_url") or ""

BASE = CFG["base_path"].rstrip("/")
SITE = CFG["site_url"].rstrip("/") + BASE
NAME = CFG["site_name"]
LABEL = {"only": "この店・この駅だけ", "area": "地域限定", "meibutsu": "地元の名物"}
TYPE_HELP = {
    "only": "特定の店舗・駅・百貨店でしか買えない品",
    "area": "その地域（大阪府内・関西など）の店でしか買えない品",
    "meibutsu": "通販や他地域でも手に入ることがあるが、その土地らしい定番の品",
}
LEAFLET_CSS = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"
LEAFLET_JS = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"

e = lambda s: html.escape(str(s or ""), quote=True)
url = lambda p="": f"{BASE}/{p}"            # サイト内リンク
abs_url = lambda p="": f"{SITE}/{p}"        # canonical / sitemap 用

cities = {c["id"]: c for c in DATA["cities"]}
spots = {s["id"]: s for s in DATA["spots"]}
items = DATA["items"]
for it in items:
    it["_spot"] = spots[it["spot"]]
    it["_city"] = cities[it["_spot"]["city"]]
spot_items = {sid: [i for i in items if i["spot"] == sid] for sid in spots}
city_spots = {cid: [s for s in DATA["spots"] if s["city"] == cid] for cid in cities}
pages = []  # sitemap 用


def gmaps(q):
    from urllib.parse import quote
    return "https://www.google.com/maps/search/?api=1&query=" + quote(q)


def crumbs(trail):
    lis = "".join(
        f'<li><a href="{e(u)}">{e(t)}</a></li>' if u else f'<li aria-current="page">{e(t)}</li>'
        for t, u in trail)
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": t, **({"item": SITE + u[len(BASE):]} if u else {})}
        for i, (t, u) in enumerate(trail)]}
    return (f'<nav class="crumbs" aria-label="パンくずリスト"><ol>{lis}</ol></nav>'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')


def page(path, title, desc, body, *, cls="", leaflet=False, full_title=False):
    """path は 'tokyo/' のような docs/ からの相対パス（ディレクトリは index.html にする）"""
    t = title if full_title else f"{title}｜{NAME}"
    canon = abs_url(path)
    head_extra = f'<link rel="stylesheet" href="{LEAFLET_CSS}">' if leaflet else ""
    foot_js = (f'<script src="{LEAFLET_JS}"></script>' if leaflet else "") + f'<script src="{url("assets/map.js")}" defer></script>'
    any_aff = CFG.get("affiliate_enabled")
    pr_line = (f'<p>当サイトはアフィリエイト広告を利用しています。「PR」と表示したリンクから購入・予約があると、運営者に報酬が支払われることがあります。詳しくは<a href="{url("about/")}#pr">広告の方針</a>をご覧ください。</p>'
               if any_aff else "")
    doc = f"""<!doctype html>
<html lang="{CFG['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(t)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(canon)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(NAME)}">
<meta property="og:title" content="{e(t)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(canon)}">
<meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Dela+Gothic+One&family=Zen+Kaku+Gothic+New:wght@400;500;700&family=IBM+Plex+Mono:wght@500&display=swap">
{head_extra}
<link rel="stylesheet" href="{url('assets/style.css')}">
</head>
<body class="{cls}">
<div class="wrap">
<header class="site-head">
  <a class="logo" href="{url()}">限定<span>みやげ</span><span>地図</span></a>
  <nav class="site-nav" aria-label="サイト内">
    {''.join(f'<a href="{url(c["id"] + "/")}">{e(c["name"])}</a>' for c in DATA["cities"])}
    <a href="{url('chains/')}">地域限定チェーン</a>
    <a href="{url()}#finder">条件で探す</a>
    <a href="{url('about/')}">このサイトについて</a>
  </nav>
</header>
<main>
{body}
</main>
<footer class="site-foot">
  {pr_line}
  {form_box()}
  <p>価格・販売状況は各ページの「最終確認日」時点の情報です。限定品は販売終了や価格改定が多いので、出かける前に各店の公式情報を確認してください。</p>
  <nav aria-label="フッター">
    <a href="{url('about/')}">このサイトについて</a>
    <a href="{url('privacy/')}">プライバシーポリシー</a>
  </nav>
  <p>© {datetime.date.today().year} {e(NAME)}</p>
</footer>
</div>
{foot_js}
</body>
</html>
"""
    out = OUT / path / "index.html" if path.endswith("/") or path == "" else OUT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    if not path.endswith(".html") or path == "":
        pages.append(path)


def form_box(label="情報を送る"):
    if not FORM:
        return ""
    return (f'<div class="formbox"><p>ここに載っていない限定みやげや、販売終了・価格の変更を知っていたら教えてください。確認してから掲載します。</p>'
            f'<a class="btn" href="{e(FORM)}" target="_blank" rel="noopener">{e(label)} ↗</a></div>')


def map_block(map_id, spot_list, numbered=True, small=False):
    pts = []
    for n, s in enumerate(spot_list, 1):
        pts.append({"n": n if numbered else "", "name": s["name"], "lat": s["lat"], "lng": s["lng"],
                    "city": s["city"], "url": url(f"spot/{s['id']}/"), "count": len(spot_items[s["id"]])})
    cls = "map small" if small else "map"
    return (f'<div class="{cls}" data-map="{map_id}" role="region" aria-label="地図"></div>'
            f'<script type="application/json" id="{map_id}">{json.dumps({"points": pts}, ensure_ascii=False)}</script>')


def tag(t):
    return f'<span class="tag {t}">{LABEL[t]}</span>'


def item_li(it):
    sub = " ・ ".join(x for x in [it["shop"], f'日持ち {it["keep"]}' if it.get("keep") else ""] if x)
    return (f'<li><a href="{url("item/" + it["id"] + "/")}">{e(it["name"])}</a>'
            f'<span class="price">{e(it["price"] or "価格は店頭で")}</span>'
            f'<span class="sub">{tag(it["type"])} {e(sub)}</span></li>')


def spot_block(s, n):
    its = spot_items[s["id"]]
    return f"""<article class="spot c-{s['city']}" id="{s['id']}">
  <div class="spot-head"><span class="num">{n}</span><div>
    <h3><a href="{url('spot/' + s['id'] + '/')}" style="color:inherit">{e(s['name'])}</a></h3>
    <p class="where">{e(s['sub'])} ・ {e(s['area'])} ・ <a href="{gmaps(s['q'])}" target="_blank" rel="noopener">Googleマップ ↗</a></p>
  </div></div>
  <ul class="items">{''.join(item_li(i) for i in its)}</ul>
</article>"""


# ---------- トップ ----------
def build_index():
    all_spots = DATA["spots"]
    city_cards = "".join(
        f'<a class="city-card c-{c["id"]}" href="{url(c["id"] + "/")}"><h2>{e(c["name"])}の限定みやげ</h2>'
        f'<span class="count">{len(city_spots[c["id"]])}か所 ・ {sum(len(spot_items[s["id"]]) for s in city_spots[c["id"]])}品</span>'
        f'<span>{e(c["intro"])}</span></a>' for c in DATA["cities"])
    finder_items = [{
        "name": it["name"], "url": url(f"item/{it['id']}/"), "city": it["_city"]["id"], "cityName": it["_city"]["short"],
        "spot": it["_spot"]["name"], "type": it["type"], "price": it["price"], "price_yen": it["price_yen"],
        "keep": it["keep"], "keep_days": it["keep_days"], "wrapped": it["wrapped"]} for it in items]
    city_opts = "".join(f'<option value="{c["id"]}">{e(c["name"])}</option>' for c in DATA["cities"])
    body = f"""
<section class="section">
  <p class="eyebrow">東京23区・大阪</p>
  <h1>その店でしか買えない<br>お土産を、地図で探す</h1>
  <p class="lead">駅の改札内、百貨店の1店舗、老舗の本店。「ここでしか買えない」お土産を、買える場所ごとにまとめています。日持ちや予算でも絞り込めます。</p>
</section>
<section class="section">{map_block("map-all", all_spots, numbered=False)}</section>
<section class="section"><div class="cities">{city_cards}</div></section>
<section class="section" id="finder-section">
  <h2>条件で探す</h2>
  <form class="finder" id="finder" onsubmit="return false">
    <div class="finder-row">
      <label class="field">エリア<select id="f-city"><option value="all">すべて</option>{city_opts}</select></label>
      <label class="field">限定の種類<select id="f-type"><option value="all">すべて</option>{''.join(f'<option value="{k}">{v}</option>' for k, v in LABEL.items())}</select></label>
      <label class="field">予算（1箱・1個あたり）<select id="f-budget"><option value="0">指定なし</option><option value="1000">1,000円以下</option><option value="2000">2,000円以下</option><option value="3000">3,000円以下</option></select></label>
      <label class="field">日持ち<select id="f-keep"><option value="0">指定なし</option><option value="3">3日以上</option><option value="7">7日以上</option><option value="30">30日以上</option></select></label>
      <label class="check"><input type="checkbox" id="f-wrapped"> 個包装のみ</label>
    </div>
    <p class="result-count" aria-live="polite">該当 <span id="finder-count"></span></p>
  </form>
  <div class="cards" id="finder-results"></div>
  <script type="application/json" id="items-data">{json.dumps(finder_items, ensure_ascii=False)}</script>
</section>
<section class="section prose">
  <h2>「限定」の種類について</h2>
  <p>{"".join(f'{tag(k)} {e(v)}。<br>' for k, v in TYPE_HELP.items())}</p>
</section>"""
    page("", f"{NAME}｜東京・大阪の駅限定・店舗限定お土産マップ",
         "東京駅・浅草・梅田・なんば・新大阪で、その店や駅でしか買えないお土産を地図で探せます。日持ち・予算・個包装で絞り込み可能。",
         body, leaflet=True, full_title=True)


# ---------- エリア ----------
def build_city(c):
    ss = city_spots[c["id"]]
    n_items = sum(len(spot_items[s["id"]]) for s in ss)
    stay = CFG.get("stay_links", {}).get(c["id"]) or []
    stay_html = ""
    if CFG.get("affiliate_enabled") and stay:
        stay_html = (f'<aside class="aff"><h2>{e(c["short"])}に泊まるなら <span class="tag pr">PR</span></h2><ul>'
                     + "".join(f'<li><a href="{e(l["url"])}" rel="sponsored noopener" target="_blank">{e(l["label"])}</a></li>' for l in stay)
                     + "</ul></aside>")
    body = f"""{crumbs([("トップ", url()), (c["name"], None)])}
<section class="section">
  <p class="eyebrow">{len(ss)}か所 ・ {n_items}品</p>
  <h1><span class="acc">{e(c["name"])}</span>でしか買えないお土産</h1>
  <p class="lead">{e(c["intro"])}</p>
</section>
<div class="split">
  <section class="section">{map_block("map-" + c["id"], ss)}</section>
  <section class="spots">{''.join(spot_block(s, i) for i, s in enumerate(ss, 1))}</section>
</div>
{stay_html}"""
    page(f'{c["id"]}/', f'{c["name"]}の限定お土産マップ',
         f'{c["name"]}で、その店や駅でしか買えないお土産{n_items}品を買える場所ごとに地図で紹介。価格・日持ち付き。',
         body, cls=f'c-{c["id"]}', leaflet=True)


# ---------- 店 ----------
def build_spot(s):
    c = cities[s["city"]]
    its = spot_items[s["id"]]
    names = "、".join(i["name"] for i in its[:3])
    note = f'<p class="note">{e(s["note"])}</p>' if s.get("note") else ""
    others = [x for x in city_spots[s["city"]] if x["id"] != s["id"]]
    body = f"""{crumbs([("トップ", url()), (c["name"], url(c["id"] + "/")), (s["name"], None)])}
<section class="section">
  <p class="eyebrow">{e(c["short"])} ・ {e(s["sub"])}</p>
  <h1>{e(s["name"])}で買える限定みやげ</h1>
  <p class="lead">{e(s["area"])}</p>
  {note}
  <p><a class="btn" href="{gmaps(s['q'])}" target="_blank" rel="noopener">Googleマップで開く ↗</a></p>
</section>
<div class="split">
  <section class="section"><h2>{len(its)}品</h2><div class="spot"><ul class="items">{''.join(item_li(i) for i in its)}</ul></div></section>
  <section class="section">{map_block("map-spot", [s], numbered=False, small=True)}
    <h2>{e(c["short"])}のほかの場所</h2>
    <ul class="items spot">{''.join(f'<li><a href="{url("spot/" + o["id"] + "/")}">{e(o["name"])}</a><span class="price">{len(spot_items[o["id"]])}品</span></li>' for o in others)}</ul>
  </section>
</div>"""
    page(f'spot/{s["id"]}/', f'{s["name"]}の限定お土産{len(its)}選',
         f'{s["name"]}（{s["area"]}）でしか買えない・買うべきお土産。{names}など。価格と日持ち付き。',
         body, cls=f'c-{s["city"]}', leaflet=True)


# ---------- 商品 ----------
def build_item(it):
    s, c = it["_spot"], it["_city"]
    srcs = [DATA["sources"][k] for k in it["src"].split(",") if k in DATA["sources"]]
    rows = [("販売店", f'<a href="{url("spot/" + s["id"] + "/")}">{e(s["name"])}</a>' + (f'（{e(it["where"])}）' if it.get("where") else "")),
            ("ブランド", e(it["shop"])),
            ("価格", f'<span class="price">{e(it["price"] or "店頭で確認")}</span>'),
            ("日持ち", e(it["keep"] or "店頭で確認")),
            ("個包装", {True: "あり", False: "なし"}.get(it["wrapped"], "未確認")),
            ("限定の種類", f'{tag(it["type"])} {e(TYPE_HELP[it["type"]])}'),
            ("最終確認日", e(it["checked"]))]
    facts = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    online = it.get("online") or []
    aff = ""
    if CFG.get("affiliate_enabled") and online:
        aff = ('<aside class="aff"><h2>通販で買えるもの <span class="tag pr">PR</span></h2><ul>'
               + "".join(f'<li><a href="{e(l["url"])}" rel="sponsored noopener" target="_blank">{e(l["label"])}</a></li>' for l in online)
               + "</ul></aside>")
    same = [x for x in spot_items[s["id"]] if x["id"] != it["id"]]
    same_html = (f'<section class="section"><h2>{e(s["name"])}のほかの限定みやげ</h2><div class="spot"><ul class="items">{"".join(item_li(x) for x in same)}</ul></div></section>'
                 if same else "")
    src_html = "".join(f'<li><a href="{e(x["url"])}" target="_blank" rel="noopener">{e(x["title"])}</a></li>' for x in srcs)
    body = f"""{crumbs([("トップ", url()), (c["name"], url(c["id"] + "/")), (s["name"], url("spot/" + s["id"] + "/")), (it["name"], None)])}
<section class="section">
  <p class="eyebrow">{e(s["name"])}</p>
  <h1>{e(it["name"])}</h1>
  <p class="lead">{e(it["desc"])}</p>
</section>
<div class="split">
  <section class="section"><dl class="facts">{facts}</dl>{aff}</section>
  <section class="section">{map_block("map-item", [s], numbered=False, small=True)}
    <p><a class="btn" href="{gmaps(s['q'])}" target="_blank" rel="noopener">{e(s["name"])}をGoogleマップで開く ↗</a></p></section>
</div>
{same_html}
<section class="section prose"><h2>情報の出典</h2><ul>{src_html}</ul>
<p class="note">ここに載せた情報は公開されている紹介記事をもとにしています。販売状況は変わることがあるので、購入前に店舗の公式情報を確認してください。</p>
{form_box("間違い・販売終了を報告する")}</section>"""
    price_part = f'価格は{it["price"]}、' if it["price"] else ""
    page(f'item/{it["id"]}/', f'{it["name"]}（{s["name"]}）',
         f'{it["name"]}は{s["name"]}で買える{LABEL[it["type"]]}のお土産。{price_part}日持ちは{it["keep"] or "店頭で確認"}。{it["desc"][:60]}',
         body, cls=f'c-{c["id"]}', leaflet=True)


# ---------- 地域限定チェーン ----------
def build_chains():
    def card(ch):
        srcs = [CHAINS["sources"][k] for k in ch["src"].split(",") if k in CHAINS["sources"]]
        link = ""
        if ch.get("spot") and ch["spot"] in spots:
            link = f' ・ <a href="{url("spot/" + ch["spot"] + "/")}">{e(spots[ch["spot"]]["name"])}のページ</a>'
        return f"""<article class="chain" id="{ch['id']}">
  <div class="chain-head"><h3>{e(ch['name'])}</h3><span class="tag plain">{e(ch['genre'])}</span><span class="tag area">{e(ch['takeout'])}</span></div>
  <p>{e(ch['desc'])}</p>
  <dl class="facts compact"><dt>名物</dt><dd>{e(ch['signature'])}</dd><dt>店があるところ</dt><dd>{e(ch['area'])}</dd></dl>
  <p class="where"><a href="{gmaps(ch['name'])}" target="_blank" rel="noopener">近くの店をGoogleマップで探す ↗</a>{link}</p>
  <p class="src">出典：{"、".join(f'<a href="{e(x["url"])}" target="_blank" rel="noopener">{e(x["title"])}</a>' for x in srcs)}（最終確認 {e(ch['checked'])}）</p>
</article>"""
    secs = ""
    for r in CHAINS["regions"]:
        cs = [c for c in CHAINS["chains"] if c["region"] == r["id"]]
        secs += f"""<section class="section c-{'osaka' if r['id']=='kansai' else 'tokyo'}" id="{r['id']}">
  <h2><span class="acc">{e(r['name'])}</span>（{len(cs)}）</h2>
  <p class="lead">{e(r['lead'])}</p>
  <div class="chains">{''.join(card(c) for c in cs)}</div>
</section>"""
    jump = " ・ ".join(f'<a href="#{r["id"]}">{e(r["name"])}</a>' for r in CHAINS["regions"])
    body = f"""{crumbs([("トップ", url()), ("地域限定チェーン", None)])}
<section class="section">
  <p class="eyebrow">関西・関東</p>
  <h1>その地方にしかないチェーン店</h1>
  <p class="lead">店がたくさんあるので地図には載せず、一覧にまとめています。店の場所は、各チェーンの「Googleマップで探す」から確認してください。</p>
  <p>{jump}</p>
</section>
{secs}
{form_box("チェーンの情報を送る")}"""
    page("chains/", "関西にしかないチェーン・関東にしかないチェーン",
         "関西にしかないチェーン（551蓬莱・北極星など）と、関東にしかないチェーン（崎陽軒・日高屋など）を、名物と店のあるエリアつきで紹介。",
         body)


# ---------- 固定ページ ----------
def build_static():
    about = f"""{crumbs([("トップ", url()), ("このサイトについて", None)])}
<section class="section prose">
  <h1>このサイトについて</h1>
  <p>{e(NAME)}は、その店・その駅・その地域でしか買えないお土産を、買える場所ごとに地図でまとめたサイトです。現在は東京23区と大阪を掲載しています。</p>
  <h2>掲載情報の確認方法</h2>
  <p>商品の価格・日持ち・販売場所は、公開されている紹介記事や公式情報をもとにまとめ、各商品ページに出典と最終確認日を載せています。限定品は販売終了や価格改定が多いため、お出かけ前に店舗の公式情報をご確認ください。誤りに気づいたら、下記までお知らせください。</p>
  <h2 id="pr">広告の方針</h2>
  <p>当サイトはアフィリエイトプログラム（成果報酬型広告）を利用することがあります。広告リンクには「PR」と表示し、リンク先で購入・予約があった場合に運営者が報酬を受け取ることがあります。掲載する商品や順番は、報酬の有無ではなく「その場所でしか買えないか」を基準に決めています。</p>
  <h2>運営者</h2>
  <p>運営：{e(CFG["owner"])}<br>お問い合わせ：{e(CFG["contact"])}</p>
</section>"""
    page("about/", "このサイトについて", f"{NAME}の運営方針・掲載情報の確認方法・広告の方針について。", about)
    privacy = f"""{crumbs([("トップ", url()), ("プライバシーポリシー", None)])}
<section class="section prose">
  <h1>プライバシーポリシー</h1>
  <p>（公開前に、利用するサービスに合わせて内容を確認・修正してください。）</p>
  <h2>アクセス解析について</h2>
  <p>当サイトでは、サイトの改善のためにアクセス解析ツールを利用することがあります。解析ツールはCookieを使って匿名の利用データを収集しますが、個人を特定する情報は含みません。</p>
  <h2>広告について</h2>
  <p>当サイトは第三者のアフィリエイトプログラムを利用することがあります。広告配信事業者は、利用者の興味に応じた広告を表示するためにCookieを使用することがあります。</p>
  <h2>地図について</h2>
  <p>地図の表示にはOpenStreetMapのタイルを利用しています。地図を表示する際、利用者のブラウザからOpenStreetMapのサーバーへ接続が行われます。</p>
  <h2>免責事項</h2>
  <p>掲載情報の正確性には注意していますが、内容を保証するものではありません。当サイトの情報を利用したことで生じた損害について、運営者は責任を負いかねます。</p>
  <h2>お問い合わせ</h2>
  <p>{e(CFG["contact"])}</p>
</section>"""
    page("privacy/", "プライバシーポリシー", f"{NAME}のプライバシーポリシーと免責事項。", privacy)
    nf = f"""<section class="section"><h1>ページが見つかりません</h1>
<p class="lead">お探しのページは移動したか、販売終了にともない削除された可能性があります。</p>
<p><a class="btn" href="{url()}">トップへ戻る</a></p></section>"""
    page("404.html", "ページが見つかりません", "ページが見つかりません。", nf)


def build_meta():
    today = datetime.date.today().isoformat()
    urls = "".join(f"<url><loc>{e(abs_url(p))}</loc><lastmod>{today}</lastmod></url>" for p in pages if p != "404.html")
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {abs_url('sitemap.xml')}\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets")
    build_index()
    for c in DATA["cities"]:
        build_city(c)
    for s in DATA["spots"]:
        build_spot(s)
    for it in items:
        build_item(it)
    build_chains()
    build_static()
    build_meta()
    print(f"生成完了: {len(pages)}ページ → {OUT}")


if __name__ == "__main__":
    main()
