// 各ページの <div class="map" data-map="ID"> に、<script type="application/json" id="ID"> の地点を描く
(function () {
  if (typeof L === "undefined") return;
  document.querySelectorAll("[data-map]").forEach(function (el) {
    var src = document.getElementById(el.dataset.map);
    if (!src) return;
    var d = JSON.parse(src.textContent);
    var map = L.map(el, { scrollWheelZoom: false });
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
