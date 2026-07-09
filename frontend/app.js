const state = {
  token: localStorage.getItem("campus-market-token") || "",
  principal: null,
  categories: [],
  locations: [],
  announcements: [],
  dashboard: null,
  unreadCount: 0,
  view: "home",
  authMode: "login",
  homeCategoryFilter: "",
};

const ECUST_CAMPUSES = ["徐汇校区", "奉贤校区"];

const viewEl = document.getElementById("view");
const navEl = document.getElementById("nav");
const noticeEl = document.getElementById("notice");
const userBadgeEl = document.getElementById("userBadge");
const modalEl = document.getElementById("modal");
const modalBodyEl = document.getElementById("modalBody");
const themeToggleEl = document.getElementById("themeToggle");

const themeKey = "campus-market-theme";

function applyTheme(theme) {
  const root = document.documentElement;
  if (theme === "dark") {
    root.setAttribute("data-theme", "dark");
  } else if (theme === "light") {
    root.setAttribute("data-theme", "light");
  } else {
    root.removeAttribute("data-theme");
  }
  const metaTheme = document.querySelector('meta[name="theme-color"]');
  if (metaTheme) {
    metaTheme.content = theme === "dark" ? "#0b1120" : "#0d9488";
  }
  if (themeToggleEl) {
    themeToggleEl.textContent = theme === "dark" ? "☀️" : "🌙";
    themeToggleEl.title = theme === "dark" ? "切换浅色模式" : "切换深色模式";
    themeToggleEl.setAttribute("aria-label", theme === "dark" ? "切换浅色模式" : "切换深色模式");
  }
}

function initTheme() {
  const stored = localStorage.getItem(themeKey);
  if (stored === "dark" || stored === "light") {
    applyTheme(stored);
  } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    applyTheme("dark");
  } else {
    applyTheme("light");
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const next = current === "dark" ? "light" : "dark";
  localStorage.setItem(themeKey, next);
  applyTheme(next);
}

if (themeToggleEl) {
  themeToggleEl.addEventListener("click", toggleTheme);
}
initTheme();

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || "操作失败");
  }
  return data;
}

function showNotice(message, isError = false) {
  noticeEl.textContent = message;
  noticeEl.classList.toggle("error", isError);
  noticeEl.hidden = false;
  clearTimeout(showNotice.timer);
  showNotice.timer = setTimeout(() => {
    noticeEl.hidden = true;
  }, 3600);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formObject(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function money(value) {
  return `¥${Number(value || 0).toFixed(2).replace(/\.00$/, "")}`;
}

function shortTime(value) {
  if (!value) return "";
  return String(value).replace("T", " ").slice(0, 16);
}

function truncateText(value, maxLength = 72) {
  const text = String(value ?? "").trim();
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength)}...`;
}

function discountPercent(item) {
  const original = Number(item.originalPrice || 0);
  const sell = Number(item.sellPrice || 0);
  if (!original || sell >= original) return 0;
  return Math.max(1, Math.round((1 - sell / original) * 100));
}

function originalPriceHtml(item) {
  return discountPercent(item) ? `<span class="original-price">${money(item.originalPrice)}</span>` : "";
}

function discountBadgeHtml(item) {
  const discount = discountPercent(item);
  return discount ? `<span class="discount-badge">省 ${discount}%</span>` : "";
}

function uniqueItems(...groups) {
  const seen = new Set();
  const result = [];
  for (const group of groups) {
    for (const item of group || []) {
      if (!item || seen.has(item.itemNo)) continue;
      seen.add(item.itemNo);
      result.push(item);
    }
  }
  return result;
}

function categoryLabel(category) {
  return category.parentCategoryName
    ? `${category.parentCategoryName} / ${category.categoryName}`
    : category.categoryName;
}

function categoryOptions(selected = "", includeAll = false) {
  const options = [];
  if (includeAll) options.push(`<option value="">全部分类</option>`);
  for (const category of state.categories) {
    const label = categoryLabel(category);
    const prefix = category.parentCategoryNo ? "　" : "";
    options.push(
      `<option value="${category.categoryNo}" ${String(selected) === String(category.categoryNo) ? "selected" : ""}>${prefix}${escapeHtml(label)}</option>`,
    );
  }
  return options.join("");
}

function locationOptions(selected = "") {
  return state.locations
    .map(
      (location) =>
        `<option value="${location.locationNo}" ${String(selected) === String(location.locationNo) ? "selected" : ""}>${escapeHtml(locationLabel(location))}</option>`,
    )
    .join("");
}

function locationLabel(location) {
  return location.campusName;
}

function campusOptions(selected = "奉贤校区") {
  return ECUST_CAMPUSES.map(
    (campus) => `<option value="${campus}" ${campus === selected ? "selected" : ""}>${campus}</option>`,
  ).join("");
}

function campusFilterOptions(selected = "") {
  return [
    `<option value="" ${selected === "" ? "selected" : ""}>全部校区</option>`,
    ...ECUST_CAMPUSES.map(
      (campus) => `<option value="${campus}" ${campus === selected ? "selected" : ""}>${campus}</option>`,
    ),
  ].join("");
}

function isUser() {
  return state.principal?.kind === "user";
}

function isAdmin() {
  return state.principal?.kind === "admin";
}

function canTrade() {
  return isUser() && state.principal.authStatus === "已认证" && state.principal.status === "正常" && state.principal.creditScore >= 60;
}

function userTypeOptions(selected = "学生") {
  return ["学生", "教职工", "校友"]
    .map((type) => `<option value="${type}" ${type === selected ? "selected" : ""}>${type}</option>`)
    .join("");
}

function renderNav() {
  const items = [
    ["home", "项目介绍", true],
    ["items", "浏览物品", true],
    ["wanted", "求购广场", true],
    ["favorites", "我的收藏", isUser()],
    ["notifications", state.unreadCount ? `通知(${state.unreadCount})` : "通知", isUser()],
    ["publish", "发布管理", isUser()],
    ["orders", "我的订单", isUser()],
    ["admin", "后台管理", isAdmin()],
    ["account", state.principal ? "账号" : "登录", true],
  ];
  navEl.innerHTML = items
    .filter((item) => item[2])
    .map(
      ([id, label]) =>
        `<button class="nav-btn ${state.view === id ? "active" : ""}" type="button" onclick="switchView('${id}')">${label}</button>`,
    )
    .join("");

  if (!state.principal) {
    userBadgeEl.textContent = "游客浏览";
  } else if (isAdmin()) {
    userBadgeEl.textContent = `管理员 ${state.principal.username}`;
  } else {
    userBadgeEl.textContent = `${state.principal.nickname} · ${state.principal.userType || "学生"} · ${state.principal.authStatus} · 信用 ${state.principal.creditScore}`;
  }
}

async function loadCommon() {
  const [categories, locations, announcements, dashboard] = await Promise.all([
    api("/api/categories"),
    api("/api/locations"),
    api("/api/announcements"),
    api("/api/dashboard"),
  ]);
  state.categories = categories.categories;
  state.locations = locations.locations;
  state.announcements = announcements.announcements;
  state.dashboard = dashboard;
  if (isUser()) {
    try {
      const notifications = await api("/api/notifications");
      state.unreadCount = notifications.unreadCount || 0;
    } catch {
      state.unreadCount = 0;
    }
  } else {
    state.unreadCount = 0;
  }
}

async function loadMe() {
  if (!state.token) {
    state.principal = null;
    return;
  }
  try {
    const data = await api("/api/me");
    state.principal = data.principal;
    if (!state.principal) {
      localStorage.removeItem("campus-market-token");
      state.token = "";
    }
  } catch {
    localStorage.removeItem("campus-market-token");
    state.token = "";
    state.principal = null;
  }
}

async function switchView(view) {
  state.view = view;
  renderNav();
  if (view === "home") return renderHome();
  if (view === "items") return renderItems();
  if (view === "wanted") return renderWanted();
  if (view === "favorites") return renderFavorites();
  if (view === "notifications") return renderNotifications();
  if (view === "publish") return renderPublish();
  if (view === "orders") return renderOrders();
  if (view === "admin") return renderAdmin();
  if (view === "account") return renderAccount();
}

async function renderHome() {
  const [latestData, hotData] = await Promise.all([
    api("/api/items?sort=new").catch(() => ({ items: [] })),
    api("/api/items?sort=hot").catch(() => ({ items: [] })),
  ]);
  const allLatest = latestData.items || [];
  const latest = allLatest.slice(0, 8);
  const hotItems = uniqueItems(hotData.items || [], allLatest).slice(0, 4);
  const dealItems = [...allLatest]
    .sort((a, b) => discountPercent(b) - discountPercent(a) || Number(a.sellPrice || 0) - Number(b.sellPrice || 0))
    .slice(0, 4);
  const featuredItems = uniqueItems(latest, hotItems).slice(0, 2);
  const featuredItemNos = new Set(featuredItems.map((item) => item.itemNo));
  const showcaseHotItems = uniqueItems(hotItems, allLatest).filter((item) => !featuredItemNos.has(item.itemNo)).slice(0, 2);
  const showcaseDealItems = uniqueItems(dealItems, allLatest).filter((item) => !featuredItemNos.has(item.itemNo)).slice(0, 2);
  const previewItems = uniqueItems(hotItems, latest).slice(0, 3);
  const categoriesHtml = state.categories.length
    ? `<section class="category-chips animate-in delay-2">
        ${state.categories
          .filter((category) => !category.parentCategoryNo)
          .slice(0, 8)
          .map(
            (category) =>
              `<button class="chip" type="button" onclick="browseCategory(${category.categoryNo})">
                ${escapeHtml(category.categoryName)}
                <span class="count">${category.itemCount || 0}</span>
              </button>`,
          )
          .join("")}
      </section>`
    : "";

  const latestHtml = latest.length
    ? `<section class="band animate-in delay-4">
        <div class="section-head">
          <div>
            <h2>更多在售好物</h2>
            <p class="muted">把商品直接铺出来，优先让用户看到价格、成色、卖家信用和操作入口。</p>
          </div>
          <button class="ghost-btn" type="button" onclick="switchView('items')">查看全部</button>
        </div>
        <div class="item-grid">${latest.map((item) => itemCardHtml(item)).join("")}</div>
      </section>`
    : "";

  const cta = isAdmin()
    ? `<button class="btn" type="button" onclick="switchView('admin')">进入后台管理</button>
       <button class="ghost-btn glass-button" type="button" onclick="switchView('items')">查看市场</button>`
    : isUser()
    ? `<button class="btn" type="button" onclick="switchView('items')">进入交易市场</button>
       <button class="ghost-btn glass-button" type="button" onclick="switchView('orders')">查看我的订单</button>`
    : `<button class="btn" type="button" onclick="switchView('account')">登录 / 注册</button>
       <button class="ghost-btn glass-button" type="button" onclick="switchView('items')">游客浏览物品</button>`;

  viewEl.innerHTML = `
    <section class="intro-hero animate-in">
      <div class="intro-copy">
        <span class="eyebrow animate-in delay-1">ECUST C2C Marketplace</span>
        <h1 class="animate-in delay-2">让华理闲置<br />重新流动起来</h1>
        <p class="animate-in delay-3">面向华东理工大学徐汇校区、奉贤校区学生、教职工与校友的校内交易平台。发布、浏览、求购、下单锁定、线下面交、评价与风控，全流程一站式完成。</p>
        <div class="intro-actions animate-in delay-4">
          ${cta}
        </div>
      </div>

      <div class="intro-stage animate-in delay-3" aria-label="系统功能预览">
        <div class="preview-stage">
          <div class="preview-orbit"></div>
          <div class="preview-window">
            <div class="preview-window-top">
              <span></span><span></span><span></span>
            </div>
            <div class="preview-window-content">
              ${previewItems.length ? previewItems.map(productPreviewRowHtml).join("") : `<div class="preview-empty">暂无在售商品</div>`}
            </div>
          </div>
          <div class="preview-card">
            <div class="preview-card-icon">🚲</div>
            <div><strong>代步工具</strong><span>快速转让自行车、滑板</span></div>
          </div>
          <div class="preview-card">
            <div class="preview-card-icon">🔒</div>
            <div><strong>订单锁定</strong><span>避免多人同时下单</span></div>
          </div>
          <div class="preview-dot"></div>
          <div class="preview-dot"></div>
          <div class="preview-dot"></div>
        </div>
      </div>
    </section>

    ${announcementsBannerHtml()}

    ${categoriesHtml}

    ${productShowcaseHtml(featuredItems, showcaseHotItems, showcaseDealItems)}

    ${latestHtml}

    <section class="intro-stats">
      <div class="glass-stat animate-in delay-2"><span>平台物品</span><strong>${state.dashboard?.itemCount ?? 0}</strong></div>
      <div class="glass-stat animate-in delay-3"><span>正在出售</span><strong>${state.dashboard?.onSaleCount ?? 0}</strong></div>
      <div class="glass-stat animate-in delay-4"><span>注册用户</span><strong>${state.dashboard?.userCount ?? 0}</strong></div>
      <div class="glass-stat animate-in delay-5"><span>成功订单</span><strong>${state.dashboard?.successOrderCount ?? 0}</strong></div>
    </section>

    <section class="intro-grid">
      <article class="intro-feature animate-in delay-2">
        <div class="feature-icon">🎓</div>
        <span>01</span>
        <h2>校内身份认证</h2>
        <p>注册用户可选择学生、教职工或校友身份，管理员审核后才能发布物品、提交订单和发布求购。</p>
      </article>
      <article class="intro-feature animate-in delay-3">
        <div class="feature-icon">🤝</div>
        <span>02</span>
        <h2>线上锁定，线下面交</h2>
        <p>买家提交订单后物品自动进入交易中，卖家确认后双方按校区和私聊约定完成校园面交。</p>
      </article>
      <article class="intro-feature animate-in delay-4">
        <div class="feature-icon">🛡️</div>
        <span>03</span>
        <h2>评价、通知与风控</h2>
        <p>交易成功后互评会影响信用积分；留言、订单和举报处理都会进入通知中心。</p>
      </article>
    </section>

    ${productGalleryHtml(latest)}
  `;
}

function productPreviewRowHtml(item) {
  return `
    <button class="preview-row" type="button" onclick="openItemDetail(${item.itemNo})">
      <div class="preview-thumb">
        <img src="${escapeHtml(item.imageUrl || "/assets/kettle.svg")}" alt="" />
      </div>
      <div class="preview-row-body">
        <div class="preview-row-title">${escapeHtml(item.title)}</div>
        <div class="preview-row-meta">${escapeHtml(item.campusName || "校区未标注")} · ${escapeHtml(item.condition)} · ${escapeHtml(item.categoryName)} · 信用 ${item.creditScore}</div>
      </div>
      <span class="preview-price">${money(item.sellPrice)}</span>
    </button>
  `;
}

function productShowcaseHtml(featuredItems, hotItems, dealItems) {
  if (!featuredItems.length) return "";
  return `
    <section class="product-showcase animate-in delay-3">
      <div class="section-head">
        <div>
          <h2>商品精选展示</h2>
          <p class="muted">保留重点商品，同时用少量热门和低价商品补足浏览入口。</p>
        </div>
        <button class="ghost-btn" type="button" onclick="switchView('items')">进入市场</button>
      </div>
      <div class="product-showcase-layout">
        <div class="featured-product-stack">
          ${featuredItems.map((item, index) => featuredProductHtml(item, index ? "精选好物" : "重点推荐")).join("")}
        </div>
        <div class="product-side-panels">
          <article class="showcase-panel">
            <div class="panel-heading">
              <span>热门关注</span>
              <strong>${hotItems.length}</strong>
            </div>
            <div class="mini-product-list">${productMiniListHtml(hotItems, "暂无热门商品")}</div>
          </article>
          <article class="showcase-panel">
            <div class="panel-heading">
              <span>实惠专区</span>
              <strong>${dealItems.length}</strong>
            </div>
            <div class="mini-product-list">${productMiniListHtml(dealItems, "暂无折扣商品")}</div>
          </article>
        </div>
      </div>
    </section>
  `;
}

function featuredProductHtml(item, badgeText = "重点推荐") {
  return `
    <article class="featured-product">
      <div class="featured-product-media">
        <img src="${escapeHtml(item.imageUrl || "/assets/kettle.svg")}" alt="${escapeHtml(item.title)}" />
        <span class="featured-badge">${escapeHtml(badgeText)}</span>
      </div>
      <div class="featured-product-body">
        <span class="eyebrow">Featured Item</span>
        <h2>${escapeHtml(item.title)}</h2>
        <p>${escapeHtml(truncateText(item.description, 92))}</p>
        <div class="featured-price-row">
          <span class="price">${money(item.sellPrice)}</span>
          ${originalPriceHtml(item)}
          ${discountBadgeHtml(item)}
        </div>
        <div class="meta">
          <span class="pill green">${escapeHtml(item.status)}</span>
          <span class="pill gold">${escapeHtml(item.campusName || "校区未标注")}</span>
          <span class="pill">${escapeHtml(item.condition)}</span>
          <span class="pill">${escapeHtml(item.categoryName)}</span>
          <span class="pill gold">信用 ${item.creditScore}</span>
        </div>
        <div class="product-metrics">
          <span>浏览 ${item.viewCount || 0}</span>
          <span>收藏 ${item.favoriteCount || 0}</span>
          <span>${escapeHtml(item.sellerName)}</span>
        </div>
        <div class="actions">
          <button class="btn" type="button" onclick="openItemDetail(${item.itemNo})">查看详情</button>
          <button class="ghost-btn" type="button" onclick="browseCategory(${item.categoryNo})">看同类商品</button>
        </div>
      </div>
    </article>
  `;
}

function productMiniListHtml(items, emptyText) {
  if (!items.length) return `<div class="empty mini-empty">${escapeHtml(emptyText)}</div>`;
  return items
    .map(
      (item) => `
        <button class="mini-product" type="button" onclick="openItemDetail(${item.itemNo})">
          <img src="${escapeHtml(item.imageUrl || "/assets/kettle.svg")}" alt="" />
          <span class="mini-product-main">
            <strong>${escapeHtml(item.title)}</strong>
            <span>${escapeHtml(item.campusName || "校区未标注")} · ${escapeHtml(item.condition)} · ${escapeHtml(item.categoryName)}</span>
          </span>
          <span class="mini-product-price">${money(item.sellPrice)}</span>
        </button>
      `,
    )
    .join("");
}

function productGalleryHtml(items) {
  const galleryItems = items.slice(0, 4);
  if (!galleryItems.length) return "";
  return `
    <section class="intro-gallery animate-in delay-3">
      <div class="section-head">
        <div>
          <h2>商品橱窗</h2>
          <p class="muted">用图片和价格直接展示当前市场里最容易被点开的商品。</p>
        </div>
        <button class="ghost-btn" type="button" onclick="switchView('items')">查看全部</button>
      </div>
      <div class="gallery-strip">
        ${galleryItems
          .map(
            (item, index) => `
              <button class="gallery-item animate-in delay-${Math.min(index + 2, 5)}" type="button" onclick="openItemDetail(${item.itemNo})">
                <img src="${escapeHtml(item.imageUrl || "/assets/kettle.svg")}" alt="${escapeHtml(item.title)}" />
                <span class="gallery-caption">
                  <strong>${escapeHtml(item.title)}</strong>
                  <span>${money(item.sellPrice)} · ${escapeHtml(item.condition)}</span>
                </span>
              </button>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

async function browseCategory(categoryNo) {
  state.homeCategoryFilter = categoryNo;
  await switchView("items");
  const form = document.getElementById("searchForm");
  if (form) {
    form.categoryNo.value = categoryNo;
    await loadItems();
  }
}

function announcementsBannerHtml() {
  if (!state.announcements.length) return "";
  const latest = state.announcements[0];
  return `
    <section class="band slim announcement-banner animate-in delay-2" onclick="switchView('items')" role="button" tabindex="0">
      <div class="announcement-banner-inner">
        <span class="announcement-tag">公告</span>
        <strong>${escapeHtml(latest.title)}</strong>
        <span class="muted">${escapeHtml(latest.content)}</span>
        <span class="muted time">${shortTime(latest.publishTime)}</span>
      </div>
    </section>
  `;
}

function announcementsHtml() {
  if (!state.announcements.length) return "";
  return `
    <div class="band slim">
      <div class="section-head">
        <h2>平台公告</h2>
      </div>
      <div class="table-list">
        ${state.announcements
          .slice(0, 2)
          .map(
            (item) => `
              <article class="announcement row-card">
                <div class="row-main">
                  <strong>${escapeHtml(item.title)}</strong>
                  <span class="muted">${shortTime(item.publishTime)}</span>
                </div>
                <div>${escapeHtml(item.content)}</div>
              </article>
            `,
          )
          .join("")}
      </div>
    </div>
  `;
}

async function renderItems() {
  const initialCategory = state.homeCategoryFilter || "";
  state.homeCategoryFilter = "";
  viewEl.innerHTML = `
    <section class="page-header animate-in">
      <div>
        <h1>在售物品</h1>
        <p class="muted">支持游客浏览，登录认证后可下单、留言和举报。</p>
      </div>
    </section>

    <section class="stats animate-in delay-1">
      <div class="stat"><span class="muted">平台物品</span><strong>${state.dashboard?.itemCount ?? 0}</strong></div>
      <div class="stat"><span class="muted">正在出售</span><strong>${state.dashboard?.onSaleCount ?? 0}</strong></div>
      <div class="stat"><span class="muted">成功订单</span><strong>${state.dashboard?.successOrderCount ?? 0}</strong></div>
      <div class="stat"><span class="muted">注册用户</span><strong>${state.dashboard?.userCount ?? 0}</strong></div>
    </section>

    ${announcementsHtml()}

    <section class="band animate-in delay-2">
      <form id="searchForm" class="toolbar">
        <label>关键词
          <input name="keyword" placeholder="书名、型号、卖家昵称、校区" />
        </label>
        <label>分类
          <select name="categoryNo">${categoryOptions(initialCategory, true)}</select>
        </label>
        <label>校区
          <select name="campusName">${campusFilterOptions()}</select>
        </label>
        <label>排序
          <select name="sort">
            <option value="new">最新发布</option>
            <option value="price_asc">价格从低到高</option>
            <option value="price_desc">价格从高到低</option>
            <option value="hot">浏览最多</option>
          </select>
        </label>
        <button class="btn" type="submit">搜索</button>
      </form>
    </section>
    <section id="itemsGrid" class="item-grid"></section>
  `;
  document.getElementById("searchForm").addEventListener("submit", (event) => {
    event.preventDefault();
    loadItems();
  });
  await loadItems();
}

async function loadItems() {
  const form = document.getElementById("searchForm");
  const params = new URLSearchParams(form ? formObject(form) : {});
  const data = await api(`/api/items?${params.toString()}`);
  const grid = document.getElementById("itemsGrid");
  if (!data.items.length) {
    grid.className = "empty";
    grid.innerHTML = "暂无符合条件的物品";
    return;
  }
  grid.className = "item-grid";
  grid.innerHTML = data.items.map((item) => itemCardHtml(item)).join("");
}

function itemCardHtml(item, mine = false) {
  const own = isUser() && item.sellerNo === state.principal.userNo;
  const buyButton =
    canTrade() && !own && item.status === "在售"
      ? `<button class="btn" type="button" onclick="openItemDetail(${item.itemNo})">下单</button>`
      : "";
  const favoriteButton =
    isUser() && !own
      ? `<button class="ghost-btn" type="button" onclick="toggleFavorite(${item.itemNo}, ${item.isFavorite ? "true" : "false"})">${item.isFavorite ? "取消收藏" : "收藏"}</button>`
      : "";
  const manageButtons = mine
    ? `
      <button class="ghost-btn" type="button" onclick="openEditItem(${item.itemNo})">编辑</button>
      ${
        item.status === "已下架"
          ? `<button class="ghost-btn" type="button" onclick="setItemStatus(${item.itemNo}, '在售')">上架</button>`
          : `<button class="ghost-btn" type="button" onclick="setItemStatus(${item.itemNo}, '已下架')">下架</button>`
      }
      <button class="danger-btn" type="button" onclick="deleteItem(${item.itemNo})">删除</button>
    `
    : "";
  return `
    <article class="item-card">
      <div class="item-media">
        <img src="${escapeHtml(item.imageUrl || "/assets/kettle.svg")}" alt="${escapeHtml(item.title)}" />
        <span class="item-badge">${escapeHtml(item.categoryName)}</span>
      </div>
      <div class="item-body">
        <div class="item-title">
          <h3>${escapeHtml(item.title)}</h3>
        </div>
        <p class="item-desc">${escapeHtml(truncateText(item.description, 58))}</p>
        <div class="price-line">
          <span class="price">${money(item.sellPrice)}</span>
          ${originalPriceHtml(item)}
          ${discountBadgeHtml(item)}
        </div>
        <div class="meta">
          <span class="pill green">${escapeHtml(item.status)}</span>
          <span class="pill gold">${escapeHtml(item.campusName || "校区未标注")}</span>
          <span class="pill">${escapeHtml(item.condition)}</span>
          <span class="pill">浏览 ${item.viewCount || 0}</span>
          <span class="pill gold">信用 ${item.creditScore}</span>
        </div>
        <div class="muted item-seller">${escapeHtml(item.sellerName)} · 收藏 ${item.favoriteCount || 0}</div>
        <div class="actions">
          <button class="ghost-btn" type="button" onclick="openItemDetail(${item.itemNo})">详情</button>
          ${favoriteButton}
          ${buyButton}
          ${manageButtons}
        </div>
      </div>
    </article>
  `;
}

async function openItemDetail(itemNo) {
  try {
    const data = await api(`/api/items/${itemNo}`);
    const item = data.item;
    const own = isUser() && item.sellerNo === state.principal.userNo;
    const canBuy = canTrade() && !own && item.status === "在售";
    modalBodyEl.innerHTML = `
      <div class="detail-layout">
        <div class="detail-media">
          <img src="${escapeHtml(item.imageUrl || "/assets/kettle.svg")}" alt="${escapeHtml(item.title)}" />
        </div>
        <div class="detail-body">
          <div class="section-head">
            <div>
              <h2>${escapeHtml(item.title)}</h2>
              <div class="meta">
                <span class="pill green">${escapeHtml(item.status)}</span>
                <span class="pill gold">${escapeHtml(item.campusName || "校区未标注")}</span>
                <span class="pill">${escapeHtml(item.categoryName)}</span>
                <span class="pill">${escapeHtml(item.condition)}</span>
              </div>
            </div>
            <span class="price">${money(item.sellPrice)}</span>
          </div>
          <p>${escapeHtml(item.description)}</p>
          <p class="muted">校区：${escapeHtml(item.campusName || "校区未标注")} · 原价 ${money(item.originalPrice)} · 卖家 ${escapeHtml(item.sellerName)} · 信用 ${item.creditScore} · 浏览 ${item.viewCount} · 收藏 ${item.favoriteCount || 0}</p>
          <div class="actions">
            ${
              isUser() && !own
                ? `<button class="ghost-btn" type="button" onclick="toggleFavorite(${item.itemNo}, ${item.isFavorite ? "true" : "false"}, true)">${item.isFavorite ? "取消收藏" : "收藏物品"}</button>`
                : ""
            }
            ${
              canBuy
                ? `<button class="btn" type="button" onclick="focusOrderForm()">提交订单</button>`
                : ""
            }
            ${
              isUser()
                ? `<button class="ghost-btn" type="button" onclick="reportTarget('物品', ${item.itemNo})">举报物品</button>
                   <button class="ghost-btn" type="button" onclick="reportTarget('用户', ${item.sellerNo})">举报卖家</button>`
                : ""
            }
          </div>
        </div>
      </div>

      ${
        canBuy
          ? `
          <section class="band slim footer-actions" id="orderArea">
            <h3>生成订单</h3>
            <form id="orderForm" class="form-grid three">
              <label>交易校区
                <select name="locationNo" required>${locationOptions()}</select>
              </label>
              <label>交易时间
                <input name="meetTime" type="datetime-local" required />
              </label>
              <label>&nbsp;
                <button class="btn" type="submit">提交并锁定物品</button>
              </label>
            </form>
          </section>`
          : ""
      }

      <section class="band slim footer-actions">
        <div class="section-head">
          <h3>留言</h3>
        </div>
        <div class="table-list">
          ${
            data.messages.length
              ? data.messages.map(messageHtml).join("")
              : `<div class="empty">暂无留言</div>`
          }
        </div>
        ${
          isUser()
            ? `
              <form id="messageForm" class="form-grid one footer-actions">
                <input type="hidden" name="parentMessageNo" id="parentMessageNo" />
                <label id="replyLabel">留言内容
                  <textarea name="content" required placeholder="询问细节、价格或面交安排"></textarea>
                </label>
                <div class="actions">
                  <button class="btn" type="submit">发布留言</button>
                  <button class="ghost-btn" type="button" onclick="clearReply()">取消回复</button>
                </div>
              </form>
            `
            : `<div class="empty footer-actions">登录后可留言</div>`
        }
      </section>
    `;
    showModal("detail");

    const orderForm = document.getElementById("orderForm");
    if (orderForm) {
      orderForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await submitOrder(item.itemNo, orderForm);
      });
    }
    const messageForm = document.getElementById("messageForm");
    if (messageForm) {
      messageForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await submitMessage(item.itemNo, messageForm);
      });
    }
  } catch (error) {
    showNotice(error.message, true);
  }
}

function messageHtml(message) {
  return `
    <article class="message ${message.parentMessageNo ? "reply" : ""}">
      <div class="row-main">
        <strong>${escapeHtml(message.userName)}</strong>
        <span class="muted">${shortTime(message.msgTime)}</span>
      </div>
      <p>${escapeHtml(message.content)}</p>
      ${
        isUser()
          ? `<button class="ghost-btn" type="button" onclick="setReply(${message.messageNo}, '${escapeHtml(message.userName)}')">回复</button>`
          : ""
      }
    </article>
  `;
}

function setReply(messageNo, userName) {
  document.getElementById("parentMessageNo").value = messageNo;
  document.getElementById("replyLabel").firstChild.textContent = `回复 ${userName}`;
}

function clearReply() {
  const parent = document.getElementById("parentMessageNo");
  if (parent) parent.value = "";
  const label = document.getElementById("replyLabel");
  if (label) label.firstChild.textContent = "留言内容";
}

function focusOrderForm() {
  document.getElementById("orderArea")?.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function submitOrder(itemNo, form) {
  try {
    const data = await api(`/api/items/${itemNo}/orders`, {
      method: "POST",
      body: JSON.stringify(formObject(form)),
    });
    showNotice(data.message);
    closeModal();
    await loadCommon();
    await switchView("orders");
  } catch (error) {
    showNotice(error.message, true);
  }
}

async function submitMessage(itemNo, form) {
  try {
    const data = await api(`/api/items/${itemNo}/messages`, {
      method: "POST",
      body: JSON.stringify(formObject(form)),
    });
    showNotice(data.message);
    await openItemDetail(itemNo);
  } catch (error) {
    showNotice(error.message, true);
  }
}

async function reportTarget(targetType, targetNo) {
  const reason = prompt("请输入举报原因");
  if (!reason) return;
  try {
    const data = await api("/api/reports", {
      method: "POST",
      body: JSON.stringify({ targetType, targetNo, reason }),
    });
    showNotice(data.message);
  } catch (error) {
    showNotice(error.message, true);
  }
}

async function toggleFavorite(itemNo, isFavorite, keepDetailOpen = false) {
  try {
    const data = await api(`/api/items/${itemNo}/favorite`, {
      method: isFavorite ? "DELETE" : "POST",
      body: "{}",
    });
    showNotice(data.message);
    if (keepDetailOpen) {
      await openItemDetail(itemNo);
      return;
    }
    await loadCommon();
    renderNav();
    await switchView(state.view);
  } catch (error) {
    showNotice(error.message, true);
  }
}

function closeModal() {
  modalEl.hidden = true;
  modalEl.classList.remove("detail-modal");
  modalBodyEl.innerHTML = "";
}

function showModal(mode = "") {
  modalEl.classList.toggle("detail-modal", mode === "detail");
  modalEl.hidden = false;
}

function switchAuthMode(mode) {
  state.authMode = mode === "register" ? "register" : "login";
  renderAccount();
}

async function renderAccount() {
  if (state.principal) {
    const userPanel = isUser()
      ? `
        <section class="page-header animate-in">
          <div>
            <h1>${escapeHtml(state.principal.nickname)}</h1>
            <p class="muted">${escapeHtml(state.principal.realName)} · ${escapeHtml(state.principal.userType || "学生")} · ${escapeHtml(state.principal.studentNo)}</p>
          </div>
          <span class="pill ${state.principal.authStatus === "已认证" ? "green" : "gold"}">${escapeHtml(state.principal.authStatus)}</span>
        </section>
        <section class="band animate-in delay-1">
          <div class="stats">
            <div class="stat"><span class="muted">信用积分</span><strong>${state.principal.creditScore}</strong></div>
            <div class="stat"><span class="muted">账号状态</span><strong>${escapeHtml(state.principal.status)}</strong></div>
          </div>
          ${
            state.principal.authStatus !== "已认证"
              ? `<button class="btn footer-actions" type="button" onclick="submitAuth()">提交校园认证</button>`
              : ""
          }
        </section>`
      : `
        <section class="page-header animate-in">
          <div>
            <h1>管理员账号</h1>
            <p class="muted">${escapeHtml(state.principal.username)}</p>
          </div>
        </section>`;
    viewEl.innerHTML = `
      ${userPanel}
      <section class="band slim animate-in delay-2">
        <button class="danger-btn" type="button" onclick="logout()">退出登录</button>
      </section>
    `;
    return;
  }

  const isRegister = state.authMode === "register";

  viewEl.innerHTML = `
    <section class="auth-stage">
      <div class="auth-card animate-in">
        <aside class="auth-brand-panel">
          <div>
            <div class="auth-logo">CampusMarket</div>
            <div class="auth-line"></div>
          </div>
          <div class="auth-brand-copy">
            <h2>${isRegister ? "开启新旅程" : "让闲置重新流动"}</h2>
            <p>${isRegister ? "创建账号后，你可以发布闲置、收藏物品、管理订单，并完成校园认证。" : "不管是教材资料、数码配件还是宿舍好物，都能在校园里安心完成交易。"}</p>
          </div>
          <div class="auth-footnote">
            <span>Database Principle Lab</span>
            <span>ECUST C2C Marketplace</span>
          </div>
        </aside>
        <div class="auth-form-panel">
          ${
            isRegister
              ? `
                <form id="registerForm" class="auth-form auth-form-register">
                  <div class="auth-heading">
                    <h2>创建账号</h2>
                    <p>两步完成注册，加入校园交易社区</p>
                  </div>
                  <div class="wizard-steps">
                    <div class="wizard-step active" data-step="1">
                      <span class="wizard-dot">1</span>
                      <span class="wizard-label">身份验证</span>
                    </div>
                    <div class="wizard-line"></div>
                    <div class="wizard-step" data-step="2">
                      <span class="wizard-dot">2</span>
                      <span class="wizard-label">完善信息</span>
                    </div>
                  </div>
                  <div class="wizard-panels">
                    <div class="wizard-panel active" data-panel="1">
                      <div class="auth-fields">
                        <label class="auth-field">
                          <span class="sr-only">用户类型</span>
                          <select name="userType" aria-label="用户类型">${userTypeOptions()}</select>
                        </label>
                        <label class="auth-field">
                          <span class="sr-only">学号/工号</span>
                          <input name="studentNo" placeholder="学号 / 工号" autocomplete="username" required />
                        </label>
                        <label class="auth-field">
                          <span class="sr-only">真实姓名</span>
                          <input name="realName" placeholder="真实姓名" autocomplete="name" required />
                        </label>
                      </div>
                    </div>
                    <div class="wizard-panel" data-panel="2">
                      <div class="auth-fields">
                        <label class="auth-field">
                          <span class="sr-only">手机号</span>
                          <input name="phone" placeholder="手机号（可选）" autocomplete="tel" />
                        </label>
                        <label class="auth-field">
                          <span class="sr-only">微信号</span>
                          <input name="wechat" placeholder="微信号（可选）" />
                        </label>
                        <label class="auth-field">
                          <span class="sr-only">昵称</span>
                          <input name="nickname" placeholder="昵称" required />
                        </label>
                        <label class="auth-field">
                          <span class="sr-only">密码</span>
                          <input name="password" type="password" placeholder="密码" autocomplete="new-password" required />
                        </label>
                        <label class="auth-field">
                          <span class="sr-only">确认密码</span>
                          <input name="confirmPassword" type="password" placeholder="确认密码" autocomplete="new-password" required />
                        </label>
                      </div>
                    </div>
                  </div>
                  <div class="wizard-actions">
                    <button class="ghost-btn wizard-back" type="button" style="display:none" onclick="wizardPrev()">上一步</button>
                    <button class="btn auth-submit wizard-next" type="button" onclick="wizardNext()">下一步</button>
                    <button class="btn auth-submit wizard-submit" type="submit" style="display:none">完成注册</button>
                  </div>
                  <p class="auth-switch">已有账号？ <button class="auth-link" type="button" onclick="switchAuthMode('login')">立即登录</button></p>
                </form>
              `
              : `
                <form id="loginForm" class="auth-form">
                  <div class="auth-heading">
                    <h2>欢迎回来</h2>
                    <p>请登录您的账号以继续</p>
                  </div>
                  <div class="auth-fields">
                    <label class="auth-field">
                      <span class="sr-only">账号</span>
                      <input name="account" placeholder="用户名 / 学号 / 手机号" autocomplete="username" required />
                    </label>
                    <label class="auth-field">
                      <span class="sr-only">密码</span>
                      <input name="password" type="password" placeholder="密码" autocomplete="current-password" required />
                    </label>
                  </div>
                  <p id="loginError" class="auth-error" role="alert" aria-live="polite" hidden></p>
                  <button class="btn auth-submit" type="submit">立即登录</button>
                  <p class="auth-switch">还没有账号？ <button class="auth-link" type="button" onclick="switchAuthMode('register')">免费注册</button></p>
                </form>
              `
          }
        </div>
      </div>
    </section>
  `;

  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    const loginErrorEl = document.getElementById("loginError");
    const loginInputs = loginForm.querySelectorAll("input");
    function setLoginError(message = "") {
      loginErrorEl.textContent = message;
      loginErrorEl.hidden = !message;
      loginInputs.forEach((input) => {
        input.setAttribute("aria-invalid", message ? "true" : "false");
      });
    }

    loginForm.addEventListener("input", () => setLoginError());

    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      setLoginError();
      try {
        const data = await api("/api/auth/login", {
          method: "POST",
          body: JSON.stringify(formObject(form)),
        });
        state.token = data.token;
        state.principal = data.principal;
        localStorage.setItem("campus-market-token", state.token);
        showNotice("登录成功");
        await loadCommon();
        await switchView(isAdmin() ? "admin" : "items");
      } catch (error) {
        const message = error.message || "账号或密码错误";
        setLoginError(message);
        showNotice(message, true);
      }
    });
  }

  const registerForm = document.getElementById("registerForm");
  if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      try {
        const body = formObject(form);
        if (body.password !== body.confirmPassword) {
          showNotice("两次输入的密码不一致", true);
          return;
        }
        delete body.confirmPassword;
        const data = await api("/api/auth/register", {
          method: "POST",
          body: JSON.stringify(body),
        });
        form.reset();
        state.authMode = "login";
        await renderAccount();
        showNotice(data.message);
      } catch (error) {
        showNotice(error.message, true);
      }
    });

    const userTypeSelect = document.querySelector('[name="userType"]');
    const studentNoInput = document.querySelector('[name="studentNo"]');
    if (userTypeSelect && studentNoInput) {
      function updateStudentNoPlaceholder() {
        studentNoInput.placeholder = userTypeSelect.value === "教职工" ? "工号" : "学号";
      }
      userTypeSelect.addEventListener("change", updateStudentNoPlaceholder);
      updateStudentNoPlaceholder();
    }
  }
}

function wizardGo(step) {
  const panels = document.querySelectorAll(".wizard-panel");
  const steps = document.querySelectorAll(".wizard-step");
  const backBtn = document.querySelector(".wizard-back");
  const nextBtn = document.querySelector(".wizard-next");
  const submitBtn = document.querySelector(".wizard-submit");

  panels.forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.panel === String(step));
  });
  steps.forEach((s) => {
    s.classList.toggle("active", s.dataset.step === String(step));
  });

  const line = document.querySelector(".wizard-line");
  if (line) line.classList.toggle("done", step === 2);

  if (backBtn) backBtn.style.display = step === 1 ? "none" : "";
  if (nextBtn) nextBtn.style.display = step === 2 ? "none" : "";
  if (submitBtn) submitBtn.style.display = step === 2 ? "" : "none";
}

function wizardNext() {
  const panel = document.querySelector('.wizard-panel.active');
  const fields = panel ? panel.querySelectorAll('input[required], select[required]') : [];
  let valid = true;
  fields.forEach((field) => {
    if (!field.reportValidity()) valid = false;
  });
  if (!valid) return;
  wizardGo(2);
}

function wizardPrev() {
  wizardGo(1);
}

async function submitAuth() {
  try {
    const data = await api("/api/auth/submit-auth", { method: "POST", body: "{}" });
    showNotice(data.message);
    await loadMe();
    renderNav();
    await renderAccount();
  } catch (error) {
    showNotice(error.message, true);
  }
}

async function logout() {
  await api("/api/auth/logout", { method: "POST", body: "{}" }).catch(() => {});
  state.token = "";
  state.principal = null;
  localStorage.removeItem("campus-market-token");
  showNotice("已退出登录");
  await switchView("home");
}

async function renderFavorites() {
  if (!isUser()) {
    viewEl.innerHTML = `
      <section class="empty-state animate-in">
        <span class="icon">🔒</span>
        <strong>需要先登录</strong>
        <p>登录用户账号后才能查看收藏的物品。</p>
        <button class="btn" type="button" onclick="switchView('account')">去登录</button>
      </section>`;
    return;
  }
  viewEl.innerHTML = `
    <section class="page-header animate-in">
      <div>
        <h1>我的收藏</h1>
        <p class="muted">把感兴趣的物品先收藏起来，后续可以快速回到详情或下单。</p>
      </div>
    </section>
    <section class="band animate-in delay-1">
      <div id="favoritesGrid" class="item-grid"></div>
    </section>
  `;
  const data = await api("/api/favorites");
  const grid = document.getElementById("favoritesGrid");
  if (!data.items.length) {
    grid.innerHTML = `
      <div class="empty-state">
        <span class="icon">⭐</span>
        <strong>暂无收藏</strong>
        <p>在浏览物品时点击收藏，即可在这里查看。</p>
      </div>`;
    return;
  }
  grid.className = "item-grid";
  grid.innerHTML = data.items.map((item) => itemCardHtml(item)).join("");
}

async function renderNotifications() {
  if (!isUser()) {
    viewEl.innerHTML = `
      <section class="empty-state animate-in">
        <span class="icon">🔒</span>
        <strong>需要先登录</strong>
        <p>登录用户账号后才能查看通知中心。</p>
        <button class="btn" type="button" onclick="switchView('account')">去登录</button>
      </section>`;
    return;
  }
  viewEl.innerHTML = `
    <section class="page-header animate-in">
      <div>
        <h1>通知中心</h1>
        <p class="muted">订单、留言、评价、认证审核和举报处理结果都会在这里汇总。</p>
      </div>
      <button class="ghost-btn" type="button" onclick="markAllNotificationsRead()">全部已读</button>
    </section>
    <section class="band animate-in delay-1">
      <div id="notificationsList" class="table-list"></div>
    </section>
  `;
  await loadNotifications();
}

async function loadNotifications() {
  const data = await api("/api/notifications");
  state.unreadCount = data.unreadCount || 0;
  renderNav();
  const list = document.getElementById("notificationsList");
  if (!data.notifications.length) {
    list.innerHTML = `
      <div class="empty-state">
        <span class="icon">📭</span>
        <strong>暂无通知</strong>
        <p>有新的订单、留言或审核结果时会自动出现在这里。</p>
      </div>`;
    return;
  }
  list.innerHTML = data.notifications
    .map(
      (item) => `
        <article class="row-card ${item.isRead ? "" : "unread"}">
          <div class="row-main">
            <div>
              <strong>${escapeHtml(item.title)}</strong>
              <p>${escapeHtml(item.content)}</p>
              <p class="muted">${shortTime(item.createTime)}</p>
            </div>
            <span class="pill ${item.isRead ? "" : "gold"}">${item.isRead ? "已读" : "未读"}</span>
          </div>
          <div class="actions">
            ${notificationLinkButton(item)}
            ${
              item.isRead
                ? ""
                : `<button class="ghost-btn" type="button" onclick="markNotificationRead(${item.notificationNo})">标记已读</button>`
            }
          </div>
        </article>
      `,
    )
    .join("");
}

function notificationLinkButton(item) {
  if (item.linkType === "item" && item.linkNo) {
    return `<button class="ghost-btn" type="button" onclick="openItemDetail(${item.linkNo})">查看物品</button>`;
  }
  if (item.linkType === "order") {
    return `<button class="ghost-btn" type="button" onclick="switchView('orders')">查看订单</button>`;
  }
  if (item.linkType === "account") {
    return `<button class="ghost-btn" type="button" onclick="switchView('account')">查看账号</button>`;
  }
  return "";
}

async function markNotificationRead(notificationNo) {
  try {
    const data = await api(`/api/notifications/${notificationNo}/read`, {
      method: "POST",
      body: "{}",
    });
    showNotice(data.message);
    await loadNotifications();
  } catch (error) {
    showNotice(error.message, true);
  }
}

async function markAllNotificationsRead() {
  try {
    const data = await api("/api/notifications/read-all", {
      method: "POST",
      body: "{}",
    });
    showNotice(data.message);
    await loadNotifications();
  } catch (error) {
    showNotice(error.message, true);
  }
}

async function renderPublish() {
  if (!isUser()) {
    viewEl.innerHTML = `
      <section class="empty-state animate-in">
        <span class="icon">🔒</span>
        <strong>需要先登录</strong>
        <p>登录用户账号后才能发布闲置物品。</p>
        <button class="btn" type="button" onclick="switchView('account')">去登录</button>
      </section>`;
    return;
  }

  viewEl.innerHTML = `
    <section class="page-header animate-in">
      <div>
        <h1>发布管理</h1>
        <p class="muted">认证用户且信用积分不低于 60 才能发布闲置。</p>
      </div>
      <span class="pill ${canTrade() ? "green" : "gold"}">${canTrade() ? "可发布" : "受限"}</span>
    </section>

    <section class="split">
      <div class="band animate-in delay-1">
        <div class="section-head">
          <h2>发布闲置物品</h2>
        </div>
        ${
          canTrade()
            ? `
              <form id="publishForm" class="form-grid">
                <label>物品标题
                  <input name="title" required />
                </label>
                <label>分类
                  <select name="categoryNo" required>${categoryOptions()}</select>
                </label>
                <label>校区
                  <select name="campusName" required>${campusOptions()}</select>
                </label>
                <label>原价
                  <input name="originalPrice" type="number" min="0" step="0.01" required />
                </label>
                <label>二手价
                  <input name="sellPrice" type="number" min="0" step="0.01" required />
                </label>
                <label>新旧程度
                  <select name="condition">
                    <option>全新</option>
                    <option>九成新</option>
                    <option selected>八成新</option>
                    <option>七成新</option>
                    <option>使用痕迹明显</option>
                  </select>
                </label>
                <label>图片地址
                  <input name="imageUrl" placeholder="可留空使用分类默认图" />
                </label>
                <label style="grid-column: 1 / -1">详细描述
                  <textarea name="description" required></textarea>
                </label>
                <button class="btn" type="submit">发布物品</button>
              </form>
            `
            : `<div class="empty-state">
                <span class="icon">🛡️</span>
                <strong>发布受限</strong>
                <p>请先完成校园认证，或等待信用积分恢复到 60 以上。</p>
              </div>`
        }
      </div>
      <div class="band animate-in delay-2">
        <div class="section-head"><h2>我的发布</h2></div>
        <div id="myItems" class="table-list"></div>
      </div>
    </section>
  `;
  const publishForm = document.getElementById("publishForm");
  if (publishForm) {
    publishForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      try {
        const data = await api("/api/items", {
          method: "POST",
          body: JSON.stringify(formObject(form)),
        });
        form.reset();
        showNotice(data.message);
        await loadCommon();
        await loadMyItems();
      } catch (error) {
        showNotice(error.message, true);
      }
    });
  }
  await loadMyItems();
}

async function loadMyItems() {
  const box = document.getElementById("myItems");
  if (!box) return;
  const data = await api("/api/items?status=全部&sort=new");
  const mine = data.items.filter((item) => item.sellerNo === state.principal.userNo);
  box.innerHTML = mine.length ? mine.map((item) => itemCardHtml(item, true)).join("") : `<div class="empty">暂无发布</div>`;
  box.className = mine.length ? "item-grid" : "table-list";
}

async function openEditItem(itemNo) {
  const data = await api(`/api/items/${itemNo}`);
  const item = data.item;
  modalBodyEl.innerHTML = `
    <section class="band slim">
      <div class="section-head"><h2>编辑物品</h2></div>
      <form id="editItemForm" class="form-grid">
        <label>物品标题
          <input name="title" value="${escapeHtml(item.title)}" required />
        </label>
        <label>分类
          <select name="categoryNo">${categoryOptions(item.categoryNo)}</select>
        </label>
        <label>校区
          <select name="campusName" required>${campusOptions(item.campusName || "奉贤校区")}</select>
        </label>
        <label>原价
          <input name="originalPrice" type="number" min="0" step="0.01" value="${item.originalPrice}" required />
        </label>
        <label>二手价
          <input name="sellPrice" type="number" min="0" step="0.01" value="${item.sellPrice}" required />
        </label>
        <label>新旧程度
          <select name="condition">
            ${["全新", "九成新", "八成新", "七成新", "使用痕迹明显"]
              .map((condition) => `<option ${condition === item.condition ? "selected" : ""}>${condition}</option>`)
              .join("")}
          </select>
        </label>
        <label>图片地址
          <input name="imageUrl" value="${escapeHtml(item.imageUrl || "")}" />
        </label>
        <label style="grid-column: 1 / -1">详细描述
          <textarea name="description" required>${escapeHtml(item.description)}</textarea>
        </label>
        <button class="btn" type="submit">保存修改</button>
      </form>
    </section>
  `;
  showModal();
  document.getElementById("editItemForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const result = await api(`/api/items/${itemNo}`, {
        method: "PUT",
        body: JSON.stringify(formObject(event.currentTarget)),
      });
      showNotice(result.message);
      closeModal();
      await loadMyItems();
    } catch (error) {
      showNotice(error.message, true);
    }
  });
}

async function setItemStatus(itemNo, status) {
  try {
    const data = await api(`/api/items/${itemNo}/status`, {
      method: "POST",
      body: JSON.stringify({ status }),
    });
    showNotice(data.message);
    await loadMyItems();
  } catch (error) {
    showNotice(error.message, true);
  }
}

async function deleteItem(itemNo) {
  if (!confirm("确定逻辑删除该物品吗？")) return;
  try {
    const data = await api(`/api/items/${itemNo}`, {
      method: "DELETE",
      body: "{}",
    });
    showNotice(data.message);
    await loadMyItems();
  } catch (error) {
    showNotice(error.message, true);
  }
}

async function renderOrders() {
  if (!isUser()) {
    viewEl.innerHTML = `
      <section class="empty-state animate-in">
        <span class="icon">🔒</span>
        <strong>需要先登录</strong>
        <p>登录用户账号后才能查看订单。</p>
        <button class="btn" type="button" onclick="switchView('account')">去登录</button>
      </section>`;
    return;
  }
  viewEl.innerHTML = `
    <section class="page-header animate-in">
      <div>
        <h1>我的订单</h1>
        <p class="muted">买家提交订单后物品进入“交易中”，取消恢复“在售”，确认收货后变为“已售出”。</p>
      </div>
    </section>
    <section class="band animate-in delay-1">
      <div id="ordersList" class="table-list"></div>
    </section>
  `;
  await loadOrders();
}

async function loadOrders() {
  const data = await api("/api/orders/mine");
  const list = document.getElementById("ordersList");
  if (!data.orders.length) {
    list.innerHTML = `<div class="empty">暂无订单</div>`;
    return;
  }
  list.innerHTML = data.orders.map(orderHtml).join("");
}

function orderHtml(order) {
  const role = order.buyerNo === state.principal.userNo ? "我买入" : "我售出";
  return `
    <article class="row-card order-row">
      <img class="order-thumb" src="${escapeHtml(order.imageUrl || "/assets/kettle.svg")}" alt="${escapeHtml(order.itemTitle)}" />
      <div>
        <div class="row-main">
          <div>
            <h3>${escapeHtml(order.itemTitle)}</h3>
            <p class="muted">${role} · ${escapeHtml(locationLabel(order))} · ${shortTime(order.meetTime)}</p>
          </div>
          <span class="pill ${order.orderStatus === "交易成功" ? "green" : order.orderStatus === "已取消" ? "red" : "gold"}">${escapeHtml(order.orderStatus)}</span>
        </div>
        <div class="meta">
          <span class="pill">${money(order.orderAmount)}</span>
          <span class="pill">买家 ${escapeHtml(order.buyerName)}</span>
          <span class="pill">卖家 ${escapeHtml(order.sellerName)}</span>
        </div>
        <div class="actions footer-actions">
          ${orderActionButtons(order)}
        </div>
      </div>
    </article>
  `;
}

function orderActionButtons(order) {
  const isBuyer = order.buyerNo === state.principal.userNo;
  const isSeller = order.sellerNo === state.principal.userNo;
  const buttons = [];
  if (isSeller && order.orderStatus === "待卖家确认") {
    buttons.push(`<button class="btn" type="button" onclick="orderAction(${order.orderNo}, 'confirm')">确认接单</button>`);
    buttons.push(`<button class="danger-btn" type="button" onclick="orderAction(${order.orderNo}, 'reject')">拒绝接单</button>`);
  }
  if (isBuyer && order.orderStatus === "待面交") {
    buttons.push(`<button class="btn" type="button" onclick="orderAction(${order.orderNo}, 'complete')">确认收货</button>`);
  }
  if ((isBuyer || isSeller) && ["待卖家确认", "待面交"].includes(order.orderStatus)) {
    buttons.push(`<button class="ghost-btn" type="button" onclick="orderAction(${order.orderNo}, 'cancel')">取消订单</button>`);
  }
  if ((isBuyer || isSeller) && order.orderStatus === "交易成功" && !order.reviewedByMe) {
    buttons.push(`<button class="ghost-btn" type="button" onclick="openReview(${order.orderNo})">评价对方</button>`);
  }
  return buttons.join("") || `<span class="muted">暂无可执行操作</span>`;
}

async function orderAction(orderNo, action) {
  try {
    const data = await api(`/api/orders/${orderNo}/action`, {
      method: "POST",
      body: JSON.stringify({ action }),
    });
    showNotice(data.message);
    await loadCommon();
    await loadOrders();
  } catch (error) {
    showNotice(error.message, true);
  }
}

function openReview(orderNo) {
  modalBodyEl.innerHTML = `
    <section class="band slim">
      <div class="section-head"><h2>交易评价</h2></div>
      <form id="reviewForm" class="form-grid one">
        <label>星级评分
          <select name="rating">
            <option value="5">5 星</option>
            <option value="4">4 星</option>
            <option value="3">3 星</option>
            <option value="2">2 星</option>
            <option value="1">1 星</option>
          </select>
        </label>
        <label>评价内容
          <textarea name="content" required></textarea>
        </label>
        <button class="btn" type="submit">提交评价</button>
      </form>
    </section>
  `;
  showModal();
  document.getElementById("reviewForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const data = await api(`/api/orders/${orderNo}/reviews`, {
        method: "POST",
        body: JSON.stringify(formObject(event.currentTarget)),
      });
      showNotice(data.message);
      closeModal();
      await loadMe();
      renderNav();
      await loadOrders();
    } catch (error) {
      showNotice(error.message, true);
    }
  });
}

async function renderWanted() {
  viewEl.innerHTML = `
    <section class="page-header animate-in">
      <div>
        <h1>求购广场</h1>
        <p class="muted">买家可发布求购需求，卖家可据此联系或发布对应物品。</p>
      </div>
    </section>

    <section class="split">
      <div class="band animate-in delay-1">
        <div class="section-head"><h2>求购广场</h2></div>
        <div id="wantedList" class="table-list"></div>
      </div>
      <div class="band animate-in delay-2">
        <div class="section-head"><h2>发布求购</h2></div>
        ${
          canTrade()
            ? `
              <form id="wantedForm" class="form-grid one">
                <label>求购标题
                  <input name="title" required />
                </label>
                <label>分类
                  <select name="categoryNo">${categoryOptions("", true)}</select>
                </label>
                <label>期望价格
                  <input name="expectedPrice" type="number" min="0" step="0.01" />
                </label>
                <label>求购描述
                  <textarea name="description" required></textarea>
                </label>
                <button class="btn" type="submit">发布求购</button>
              </form>
            `
            : `<div class="empty-state">
                <span class="icon">🛡️</span>
                <strong>发布受限</strong>
                <p>认证用户可发布求购信息。</p>
              </div>`
        }
      </div>
    </section>
  `;
  const wantedForm = document.getElementById("wantedForm");
  if (wantedForm) {
    wantedForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      try {
        const data = await api("/api/wanted", {
          method: "POST",
          body: JSON.stringify(formObject(form)),
        });
        form.reset();
        showNotice(data.message);
        await loadWanted();
      } catch (error) {
        showNotice(error.message, true);
      }
    });
  }
  await loadWanted();
}

async function loadWanted() {
  const data = await api("/api/wanted");
  const list = document.getElementById("wantedList");
  if (!data.wanted.length) {
    list.innerHTML = `<div class="empty">暂无求购信息</div>`;
    return;
  }
  list.innerHTML = data.wanted
    .map(
      (item) => `
        <article class="wanted-card row-card">
          <div class="row-main">
            <div>
              <h3>${escapeHtml(item.title)}</h3>
              <p>${escapeHtml(item.description)}</p>
              <div class="meta">
                <span class="pill">${escapeHtml(item.categoryName || "未分类")}</span>
                <span class="pill gold">${item.expectedPrice ? money(item.expectedPrice) : "价格面议"}</span>
                <span class="pill">${escapeHtml(item.buyerName)}</span>
              </div>
            </div>
            ${
              isUser() && item.buyerNo === state.principal.userNo
                ? `<button class="ghost-btn" type="button" onclick="closeWantedItem(${item.wantedNo})">关闭</button>`
                : ""
            }
          </div>
        </article>
      `,
    )
    .join("");
}

async function closeWantedItem(wantedNo) {
  try {
    const data = await api(`/api/wanted/${wantedNo}`, {
      method: "PUT",
      body: JSON.stringify({ status: "已关闭" }),
    });
    showNotice(data.message);
    await loadWanted();
  } catch (error) {
    showNotice(error.message, true);
  }
}

async function renderAdmin() {
  if (!isAdmin()) {
    viewEl.innerHTML = `
      <section class="empty-state animate-in">
        <span class="icon">🔒</span>
        <strong>需要管理员权限</strong>
        <p>请使用管理员账号登录后访问后台管理。</p>
        <button class="btn" type="button" onclick="switchView('account')">去登录</button>
      </section>`;
    return;
  }
  viewEl.innerHTML = `
    <section class="page-header animate-in">
      <div>
        <h1>后台管理</h1>
        <p class="muted">运营概览、身份审核、用户管理、分类校区维护、举报处理与公告发布。</p>
      </div>
    </section>

    <section class="admin-grid">
      <div class="band animate-in delay-1">
        <div class="section-head"><h2>运营概览</h2></div>
        <div id="adminStats" class="stats"></div>
        <div id="adminStatusSummary" class="mini-list"></div>
      </div>

      <div class="band animate-in delay-2">
        <div class="section-head"><h2>身份认证审核</h2></div>
        <div id="authRequests" class="table-list"></div>
      </div>

      <div class="band animate-in delay-3">
        <div class="section-head"><h2>用户管理</h2></div>
        <div id="usersList" class="table-list"></div>
      </div>

      <div class="split">
        <div class="band animate-in delay-2">
          <div class="section-head"><h2>商品分类</h2></div>
          <form id="categoryForm" class="form-grid three">
            <label>分类名称
              <input name="categoryName" required />
            </label>
            <label>父分类
              <select name="parentCategoryNo">${categoryOptions("", true)}</select>
            </label>
            <label>&nbsp;
              <button class="btn" type="submit">添加分类</button>
            </label>
          </form>
          <div id="categoryList" class="mini-list"></div>
        </div>
        <div class="band animate-in delay-3">
          <div class="section-head"><h2>交易校区</h2></div>
          <form id="locationForm" class="form-grid one">
            <label>校区
              <select name="campusName" required>${campusOptions()}</select>
            </label>
            <input name="locationName" type="hidden" value="具体地点私聊确定" />
            <button class="btn" type="submit">添加校区</button>
          </form>
          <div id="locationList" class="mini-list"></div>
        </div>
      </div>

      <div class="band animate-in delay-4">
        <div class="section-head"><h2>举报与投诉</h2></div>
        <div id="reportsList" class="table-list"></div>
      </div>

      <div class="band animate-in delay-5">
        <div class="section-head"><h2>信誉异常用户</h2></div>
        <div id="riskyUsers" class="table-list"></div>
      </div>

      <div class="band animate-in delay-4">
        <div class="section-head"><h2>公告维护</h2></div>
        <form id="announcementForm" class="form-grid one">
          <label>标题
            <input name="title" required />
          </label>
          <label>内容
            <textarea name="content" required></textarea>
          </label>
          <button class="btn" type="submit">发布公告</button>
        </form>
        <div id="announcementList" class="mini-list"></div>
      </div>
    </section>
  `;
  document.getElementById("categoryForm").addEventListener("submit", submitCategory);
  document.getElementById("locationForm").addEventListener("submit", submitLocation);
  document.getElementById("announcementForm").addEventListener("submit", submitAnnouncement);
  await refreshAdmin();
}

async function refreshAdmin() {
  await loadCommon();
  const [requests, users, reports, risky, stats] = await Promise.all([
    api("/api/admin/auth-requests"),
    api("/api/admin/users"),
    api("/api/admin/reports"),
    api("/api/admin/risky-users"),
    api("/api/admin/stats"),
  ]);
  renderAdminStats(stats);
  renderAuthRequests(requests.requests);
  renderUsers(users.users);
  renderCategoryList();
  renderLocationList();
  renderReports(reports.reports);
  renderRiskyUsers(risky.users);
  renderAnnouncementList();
  renderNav();
}

function renderAdminStats(stats) {
  const statBox = document.getElementById("adminStats");
  statBox.innerHTML = `
    <div class="stat"><span class="muted">收藏总数</span><strong>${stats.totalFavorites || 0}</strong></div>
    <div class="stat"><span class="muted">未处理举报</span><strong>${stats.unreadReports || 0}</strong></div>
    <div class="stat"><span class="muted">订单状态数</span><strong>${stats.orders?.length || 0}</strong></div>
    <div class="stat"><span class="muted">物品状态数</span><strong>${stats.items?.length || 0}</strong></div>
  `;
  const summary = document.getElementById("adminStatusSummary");
  const orderText = (stats.orders || [])
    .map((item) => `${escapeHtml(item.orderStatus)} ${item.statusCount}`)
    .join(" · ") || "暂无订单";
  const itemText = (stats.items || [])
    .map((item) => `${escapeHtml(item.status)} ${item.statusCount}`)
    .join(" · ") || "暂无物品";
  const categoryText = (stats.topCategories || [])
    .filter((item) => item.itemCount > 0)
    .slice(0, 5)
    .map((item) => `${escapeHtml(item.categoryName)} ${item.itemCount}`)
    .join(" · ") || "暂无分类数据";
  const userTypeText = (stats.userTypes || [])
    .map((item) => `${escapeHtml(item.userType || "学生")} ${item.userCount}`)
    .join(" · ") || "暂无用户类型数据";
  summary.innerHTML = `
    <div class="mini-row"><strong>订单分布</strong><span>${orderText}</span></div>
    <div class="mini-row"><strong>物品分布</strong><span>${itemText}</span></div>
    <div class="mini-row"><strong>用户类型</strong><span>${userTypeText}</span></div>
    <div class="mini-row"><strong>热门分类</strong><span>${categoryText}</span></div>
  `;
}

function renderAuthRequests(requests) {
  const box = document.getElementById("authRequests");
  if (!requests.length) {
    box.innerHTML = `<div class="empty">暂无待审核用户</div>`;
    return;
  }
  box.innerHTML = requests
    .map(
      (user) => `
        <article class="row-card">
          <div class="row-main">
            <div>
              <strong>${escapeHtml(user.realName)}</strong>
              <p class="muted">${escapeHtml(user.userType || "学生")} · ${escapeHtml(user.studentNo)} · ${escapeHtml(user.nickname)} · ${escapeHtml(user.phone || "")}</p>
            </div>
            <div class="actions">
              <button class="btn" type="button" onclick="auditUser(${user.userNo}, '已认证')">通过</button>
              <button class="danger-btn" type="button" onclick="auditUser(${user.userNo}, '认证驳回')">驳回</button>
            </div>
          </div>
        </article>
      `,
    )
    .join("");
}

async function auditUser(userNo, authStatus) {
  try {
    const data = await api(`/api/admin/users/${userNo}/auth`, {
      method: "POST",
      body: JSON.stringify({ authStatus }),
    });
    showNotice(data.message);
    await refreshAdmin();
  } catch (error) {
    showNotice(error.message, true);
  }
}

function renderUsers(users) {
  const box = document.getElementById("usersList");
  box.innerHTML = users
    .map(
      (user) => `
        <article class="row-card">
          <div class="row-main">
            <div>
              <strong>${escapeHtml(user.realName)} · ${escapeHtml(user.nickname)}</strong>
              <p class="muted">${escapeHtml(user.userType || "学生")} · ${escapeHtml(user.studentNo)} · ${escapeHtml(user.authStatus)} · 信用 ${user.creditScore}</p>
            </div>
            <div class="actions">
              <span class="pill ${user.status === "正常" ? "green" : "red"}">${escapeHtml(user.status)}</span>
              ${
                user.status === "正常"
                  ? `<button class="danger-btn" type="button" onclick="setUserStatus(${user.userNo}, '封禁')">封禁</button>`
                  : `<button class="ghost-btn" type="button" onclick="setUserStatus(${user.userNo}, '正常')">解封</button>`
              }
            </div>
          </div>
        </article>
      `,
    )
    .join("");
}

async function setUserStatus(userNo, status) {
  try {
    const data = await api(`/api/admin/users/${userNo}/status`, {
      method: "POST",
      body: JSON.stringify({ status }),
    });
    showNotice(data.message);
    await refreshAdmin();
  } catch (error) {
    showNotice(error.message, true);
  }
}

async function submitCategory(event) {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const data = await api("/api/categories", {
      method: "POST",
      body: JSON.stringify(formObject(form)),
    });
    form.reset();
    showNotice(data.message);
    await refreshAdmin();
  } catch (error) {
    showNotice(error.message, true);
  }
}

function renderCategoryList() {
  const box = document.getElementById("categoryList");
  box.innerHTML = state.categories
    .map(
      (category) => `
        <div class="mini-row">
          <span>${escapeHtml(categoryLabel(category))} <span class="muted">(${category.itemCount})</span></span>
          <div class="actions">
            <button class="ghost-btn" type="button" onclick="editCategory(${category.categoryNo})">编辑</button>
            <button class="danger-btn" type="button" onclick="deleteCategory(${category.categoryNo})">删除</button>
          </div>
        </div>
      `,
    )
    .join("");
}

async function editCategory(categoryNo) {
  const category = state.categories.find((item) => item.categoryNo === categoryNo);
  const categoryName = prompt("分类名称", category.categoryName);
  if (!categoryName) return;
  const parentInput = prompt("父分类编号，可留空", category.parentCategoryNo || "");
  try {
    const data = await api(`/api/categories/${categoryNo}`, {
      method: "PUT",
      body: JSON.stringify({ categoryName, parentCategoryNo: parentInput }),
    });
    showNotice(data.message);
    await refreshAdmin();
  } catch (error) {
    showNotice(error.message, true);
  }
}

async function deleteCategory(categoryNo) {
  if (!confirm("确定删除该分类吗？")) return;
  try {
    const data = await api(`/api/categories/${categoryNo}`, {
      method: "DELETE",
      body: "{}",
    });
    showNotice(data.message);
    await refreshAdmin();
  } catch (error) {
    showNotice(error.message, true);
  }
}

async function submitLocation(event) {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const data = await api("/api/locations", {
      method: "POST",
      body: JSON.stringify(formObject(form)),
    });
    form.reset();
    showNotice(data.message);
    await refreshAdmin();
  } catch (error) {
    showNotice(error.message, true);
  }
}

function renderLocationList() {
  const box = document.getElementById("locationList");
  box.innerHTML = state.locations
    .map(
      (location) => `
        <div class="mini-row">
          <span>${escapeHtml(locationLabel(location))}</span>
          <div class="actions">
            <button class="ghost-btn" type="button" onclick="editLocation(${location.locationNo})">编辑</button>
            <button class="danger-btn" type="button" onclick="deleteLocation(${location.locationNo})">删除</button>
          </div>
        </div>
      `,
    )
    .join("");
}

async function editLocation(locationNo) {
  const location = state.locations.find((item) => item.locationNo === locationNo);
  const campusName = prompt("校区（徐汇校区 / 奉贤校区）", location.campusName);
  if (!campusName) return;
  try {
    const data = await api(`/api/locations/${locationNo}`, {
      method: "PUT",
      body: JSON.stringify({ locationName: "具体地点私聊确定", campusName }),
    });
    showNotice(data.message);
    await refreshAdmin();
  } catch (error) {
    showNotice(error.message, true);
  }
}

async function deleteLocation(locationNo) {
  if (!confirm("确定删除该交易校区吗？")) return;
  try {
    const data = await api(`/api/locations/${locationNo}`, {
      method: "DELETE",
      body: "{}",
    });
    showNotice(data.message);
    await refreshAdmin();
  } catch (error) {
    showNotice(error.message, true);
  }
}

function renderReports(reports) {
  const box = document.getElementById("reportsList");
  if (!reports.length) {
    box.innerHTML = `<div class="empty">暂无举报</div>`;
    return;
  }
  box.innerHTML = reports
    .map(
      (report) => `
        <article class="row-card">
          <div class="row-main">
            <div>
              <strong>${escapeHtml(report.targetType)}：${escapeHtml(report.targetName || report.targetNo)}</strong>
              <p>${escapeHtml(report.reason)}</p>
              <p class="muted">举报人 ${escapeHtml(report.reporterName)} · ${shortTime(report.createTime)}</p>
              ${report.handleResult ? `<p class="muted">处理：${escapeHtml(report.handleResult)}</p>` : ""}
            </div>
            <span class="pill ${report.reportStatus === "未处理" ? "gold" : "green"}">${escapeHtml(report.reportStatus)}</span>
          </div>
          ${
            report.reportStatus === "未处理"
              ? `
                <div class="actions">
                  ${
                    report.targetType === "物品"
                      ? `<button class="danger-btn" type="button" onclick="handleReport(${report.reportNo}, '强制下架')">强制下架</button>`
                      : `<button class="danger-btn" type="button" onclick="handleReport(${report.reportNo}, '封禁用户')">封禁用户</button>`
                  }
                  <button class="ghost-btn" type="button" onclick="handleReport(${report.reportNo}, '扣信用分')">扣信用分</button>
                  <button class="ghost-btn" type="button" onclick="handleReport(${report.reportNo}, '仅记录')">仅记录</button>
                </div>
              `
              : ""
          }
        </article>
      `,
    )
    .join("");
}

async function handleReport(reportNo, action) {
  const handleResult = prompt("填写处理说明", "已核实并处理");
  if (!handleResult) return;
  try {
    const data = await api(`/api/admin/reports/${reportNo}/handle`, {
      method: "POST",
      body: JSON.stringify({ action, handleResult }),
    });
    showNotice(data.message);
    await refreshAdmin();
  } catch (error) {
    showNotice(error.message, true);
  }
}

function renderRiskyUsers(users) {
  const box = document.getElementById("riskyUsers");
  if (!users.length) {
    box.innerHTML = `<div class="empty">暂无信誉异常用户</div>`;
    return;
  }
  box.innerHTML = users
    .map(
      (user) => `
        <article class="row-card">
          <div class="row-main">
            <div>
              <strong>${escapeHtml(user.realName)} · ${escapeHtml(user.nickname)}</strong>
              <p class="muted">${escapeHtml(user.userType || "学生")} · ${escapeHtml(user.studentNo)} · 信用 ${user.creditScore} · 举报 ${user.reportCount} 次</p>
            </div>
            <span class="pill ${user.status === "正常" ? "gold" : "red"}">${escapeHtml(user.status)}</span>
          </div>
        </article>
      `,
    )
    .join("");
}

async function submitAnnouncement(event) {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const data = await api("/api/announcements", {
      method: "POST",
      body: JSON.stringify(formObject(form)),
    });
    form.reset();
    showNotice(data.message);
    await refreshAdmin();
  } catch (error) {
    showNotice(error.message, true);
  }
}

function renderAnnouncementList() {
  const box = document.getElementById("announcementList");
  box.innerHTML = state.announcements
    .map(
      (announcement) => `
        <div class="mini-row">
          <span>${escapeHtml(announcement.title)}</span>
          <button class="danger-btn" type="button" onclick="deleteAnnouncement(${announcement.announcementNo})">删除</button>
        </div>
      `,
    )
    .join("");
}

async function deleteAnnouncement(announcementNo) {
  if (!confirm("确定删除该公告吗？")) return;
  try {
    const data = await api(`/api/announcements/${announcementNo}`, {
      method: "DELETE",
      body: "{}",
    });
    showNotice(data.message);
    await refreshAdmin();
  } catch (error) {
    showNotice(error.message, true);
  }
}

modalEl.addEventListener("click", (event) => {
  if (event.target === modalEl) closeModal();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !modalEl.hidden) closeModal();
});

(async function init() {
  try {
    await loadMe();
    await loadCommon();
    renderNav();
    await switchView("home");
  } catch (error) {
    viewEl.innerHTML = `<div class="empty">初始化失败：${escapeHtml(error.message)}</div>`;
  }
})();
