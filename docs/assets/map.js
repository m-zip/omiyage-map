// 各ページの <div class="map" data-map="ID"> に、<script type="application/json" id="ID"> の地点を描く
(function () {
  if (typeof L === "undefined") return;
  document.querySelectorAll("[data-map]").forEach(function (el) {
    var src = document.getElementById(el.dataset.map);
    if (!src) return;
    var d = JSON.parse(src.textContent);
    var map = L.map(el, { scrollWheelZoom: false });
    window.__maps = window.__maps || {};
    window.__maps[el.dataset.map] = map;
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    var bounds = [];
    d.points.forEach(function (p) {
      var icon = L.divIcon({ className: "", html: '<div class="pin ' + p.city + '">' + p.n + "</div>", iconSize: [28, 28], iconAnchor: [14, 14] });
      var m = L.marker([p.lat, p.lng], { icon: icon, title: p.name }).addTo(map);
      var html = '<a href="' + p.url + '">' + p.name + "</a><br>" + p.count + "品";
      m.bindPopup(html);
      bounds.push([p.lat, p.lng]);
    });
    if (bounds.length === 1) map.setView(bounds[0], 16);
    else map.fitBounds(bounds, { padding: [36, 36], maxZoom: 15 });
  });
})();

// トップページの絞り込み
(function () {
  var box = document.getElementById("finder");
  var src = document.getElementById("items-data");
  if (!box || !src) return;
  var items = JSON.parse(src.textContent);
  var out = document.getElementById("finder-results");
  var count = document.getElementById("finder-count");
  var LABEL = { only: "この店・この駅だけ", area: "地域限定", meibutsu: "地元の名物" };
  var f = { city: document.getElementById("f-city"), type: document.getElementById("f-type"), budget: document.getElementById("f-budget"), keep: document.getElementById("f-keep"), wrapped: document.getElementById("f-wrapped") };
  try {
    var saved = JSON.parse(localStorage.getItem("finder") || "{}");
    Object.keys(saved).forEach(function (k) { if (!f[k]) return; if (f[k].type === "checkbox") f[k].checked = saved[k]; else f[k].value = saved[k]; });
  } catch (e) {}
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function run() {
    var budget = +f.budget.value, keep = +f.keep.value;
    var hit = items.filter(function (it) {
      if (f.city.value !== "all" && it.city !== f.city.value) return false;
      if (f.type.value !== "all" && it.type !== f.type.value) return false;
      if (budget && !(it.price_yen != null && it.price_yen <= budget)) return false;
      if (keep && !(it.keep_days != null && it.keep_days >= keep)) return false;
      if (f.wrapped.checked && it.wrapped !== true) return false;
      return true;
    });
    count.textContent = hit.length + "件";
    out.innerHTML = hit.length ? hit.map(function (it) {
      return '<a class="card c-' + it.city + '" href="' + it.url + '"><span class="name">' + esc(it.name) + '</span>' +
        '<span class="meta">' + esc(it.spot) + "（" + esc(it.cityName) + "）</span>" +
        '<span class="row"><span class="tag ' + it.type + '">' + LABEL[it.type] + "</span>" +
        (it.keep ? '<span class="tag plain">日持ち ' + esc(it.keep) + "</span>" : "") + "</span>" +
        '<span class="price">' + esc(it.price || "価格は店頭で") + "</span></a>";
    }).join("") : '<p class="result-count">条件に合うお土産がありません。条件をゆるめてください。日持ちや価格がわからない品は、その条件を選ぶと表示されません。</p>';
    try { localStorage.setItem("finder", JSON.stringify({ city: f.city.value, type: f.type.value, budget: f.budget.value, keep: f.keep.value, wrapped: f.wrapped.checked })); } catch (e) {}
  }
  box.addEventListener("change", run);
  run();
})();

// 現在地から近いお店
(function () {
  var btn = document.getElementById("near-btn");
  var src = document.getElementById("near-data");
  if (!btn || !src) return;
  var spots = JSON.parse(src.textContent);
  var msg = document.getElementById("near-msg");
  var list = document.getElementById("near-list");
  var CITY = { tokyo: "東京", osaka: "大阪" };
  var userMarker = null;
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function dist(a, b, c, d) {
    var R = 6371, r = Math.PI / 180;
    var x = Math.sin((c - a) * r / 2), y = Math.sin((d - b) * r / 2);
    return 2 * R * Math.asin(Math.sqrt(x * x + Math.cos(a * r) * Math.cos(c * r) * y * y));
  }
  function fmt(km) {
    if (km < 1) return "約" + Math.round(km * 1000 / 10) * 10 + "m（徒歩" + Math.max(1, Math.round(km * 1000 / 80)) + "分）";
    if (km < 3) return "約" + km.toFixed(1) + "km（徒歩" + Math.round(km * 1000 / 80) + "分）";
    return "約" + (km < 100 ? km.toFixed(1) : Math.round(km)) + "km";
  }
  function show(lat, lng) {
    var ranked = spots.map(function (s) { return Object.assign({ d: dist(lat, lng, s.lat, s.lng) }, s); })
      .sort(function (a, b) { return a.d - b.d; });
    ranked = ranked.slice(0, ranked[0].d > 30 ? 3 : 8);
    msg.textContent = ranked[0].d > 30
      ? "近くに掲載中のお店がありません。今は東京23区と大阪のお店だけを載せています。いちばん近いお店から順に出します。"
      : "近い順に" + ranked.length + "か所を出しています（直線距離）。";
    list.innerHTML = ranked.map(function (s) {
      var its = s.items.slice(0, 3).join("、") + (s.items.length > 3 ? " ほか" : "");
      return '<li><a class="card c-' + s.city + '" href="' + s.url + '"><span class="name">' + esc(s.name) + '</span>' +
        '<span class="meta">' + esc(CITY[s.city] || "") + "・" + esc(s.sub) + '</span><span class="dist">' + fmt(s.d) + "</span>" +
        '<span class="meta">' + esc(its) + "</span></a></li>";
    }).join("");
    var map = window.__maps && window.__maps["map-all"];
    if (map && typeof L !== "undefined") {
      if (userMarker) map.removeLayer(userMarker);
      userMarker = L.marker([lat, lng], { icon: L.divIcon({ className: "", html: '<div class="me-pin" aria-label="現在地"></div>', iconSize: [18, 18], iconAnchor: [9, 9] }), title: "現在地" }).addTo(map);
      var pts = [[lat, lng]].concat(ranked.slice(0, 3).map(function (s) { return [s.lat, s.lng]; }));
      if (ranked[0].d <= 30) map.fitBounds(pts, { padding: [40, 40], maxZoom: 16 });
    }
  }
  btn.addEventListener("click", function () {
    if (!navigator.geolocation) { msg.textContent = "このブラウザでは現在地を取得できません。上の地図や「条件で探す」からお店を探してください。"; return; }
    btn.disabled = true; msg.textContent = "現在地を取得しています…";
    navigator.geolocation.getCurrentPosition(function (pos) {
      btn.disabled = false; show(pos.coords.latitude, pos.coords.longitude);
    }, function (err) {
      btn.disabled = false;
      msg.textContent = err.code === 1
        ? "位置情報の利用が許可されていません。ブラウザやスマホの設定で、このサイトの位置情報を「許可」にしてから、もう一度押してください。"
        : "現在地を取得できませんでした。電波のよい場所で、もう一度押してください。";
    }, { enableHighAccuracy: false, timeout: 15000, maximumAge: 300000 });
  });
})();
