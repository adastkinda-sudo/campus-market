<template>
  <template v-if="session.principal">
    <!-- 用户主页 -->
    <section v-if="session.isUser" class="mine-page animate-in">
      <div class="mine-header">
        <div class="mine-user">
          <img class="mine-avatar-lg" :src="session.principal.avatarUrl || '/assets/avatar-1.svg'" alt="" />
          <div class="mine-info">
            <h2>{{ session.principal.nickname }}</h2>
            <p class="muted">{{ session.principal.realName }} · {{ session.principal.userType }} · {{ session.principal.studentNo }}</p>
            <div class="mine-tags">
              <span :class="['pill', session.principal.authStatus === '已认证' ? 'green' : 'gold']">{{ session.principal.authStatus }}</span>
              <span class="pill">信用 {{ session.principal.creditScore }}</span>
              <span class="pill">{{ session.principal.status }}</span>
            </div>
          </div>
        </div>
        <button class="ghost-btn" type="button" @click="logoutAndGo">退出登录</button>
      </div>

      <div class="mine-grid">
        <RouterLink v-for="entry in userEntries" :key="entry.to" class="mine-card" :to="entry.to">
          <span class="mine-card-icon">{{ entry.icon }}</span>
          <strong>{{ entry.label }}</strong>
          <span v-if="entry.badge" class="mine-badge">{{ entry.badge }}</span>
        </RouterLink>
      </div>

      <div class="band">
        <div class="section-head"><h2>个人资料</h2></div>
        <form class="form-grid account-form" @submit.prevent="saveProfile">
          <label>昵称<input v-model="profile.nickname" required /></label>
          <label>性别
            <select v-model="profile.gender">
              <option>保密</option><option>男</option><option>女</option><option>其他</option>
            </select>
          </label>
          <label>入学年份<input v-model="profile.entryYear" placeholder="如 2024级" /></label>
          <label>手机号<input v-model="profile.phone" /></label>
          <label>微信号<input v-model="profile.wechat" /></label>
          <label style="grid-column: 1 / -1">个性签名<textarea v-model="profile.bio" maxlength="160" /></label>
          <FileUpload v-model="profile.avatarUrl" purpose="avatar" label="个人头像" hint="支持 png/jpg/webp/gif，最大 3MB" />
          <button class="btn" type="submit">保存资料</button>
        </form>
      </div>

      <div class="band">
        <div class="section-head"><h2>校园身份认证</h2></div>
        <form class="form-grid one" @submit.prevent="doSubmitAuth">
          <FileUpload v-model="authForm.campusCardImageUrl" purpose="campus-card" label="校园卡照片" hint="仅本人和管理员可查看" />
          <label>补充说明<textarea v-model="authForm.bio" placeholder="可补充院系、交易偏好或身份说明" /></label>
          <button class="btn" type="submit">提交校园认证</button>
          <p v-if="session.principal.campusCardImageUrl" class="muted">已上传校园卡照片。</p>
          <img v-if="session.principal.campusCardImageUrl" class="card-preview" :src="campusCardSrc(session.principal.campusCardImageUrl)" alt="校园卡照片" />
        </form>
      </div>
    </section>

    <!-- 管理员主页 -->
    <section v-else class="mine-page animate-in">
      <div class="mine-header">
        <div class="mine-user">
          <div class="mine-avatar-lg admin-avatar">A</div>
          <div class="mine-info">
            <h2>管理员</h2>
            <p class="muted">{{ session.principal.username }}</p>
          </div>
        </div>
        <button class="ghost-btn" type="button" @click="logoutAndGo">退出登录</button>
      </div>
      <div class="mine-grid">
        <RouterLink v-for="entry in adminEntries" :key="entry.to" class="mine-card" :to="entry.to">
          <span class="mine-card-icon">{{ entry.icon }}</span>
          <strong>{{ entry.label }}</strong>
        </RouterLink>
      </div>
    </section>
  </template>

  <!-- 未登录 -->
  <section v-else class="auth-stage">
    <div :class="['auth-card animate-in', registerMode ? 'register-mode' : '']">
      <aside class="auth-brand-panel">
        <div>
          <div class="auth-logo">CampusMarket</div>
          <div class="auth-line"></div>
        </div>
        <div class="auth-brand-copy">
          <h2>{{ registerMode ? "开启新旅程" : "让闲置重新流动" }}</h2>
          <p>{{ registerMode ? "创建账号后，完善资料并提交校园认证。" : "登录后即可收藏、发布、下单、私聊和反馈。" }}</p>
        </div>
      </aside>
      <div class="auth-form-panel">
        <form v-if="!registerMode" class="auth-form" @submit.prevent="doLogin">
          <div class="auth-heading"><h2>欢迎回来</h2><p>请登录您的账号以继续</p></div>
          <div class="auth-fields">
            <label class="auth-field"><input v-model="loginForm.account" placeholder="用户名 / 学号 / 手机号" required /></label>
            <label class="auth-field"><input v-model="loginForm.password" type="password" placeholder="密码" required /></label>
          </div>
          <button class="btn auth-submit" type="submit">立即登录</button>
          <p class="auth-switch">还没有账号？ <button class="auth-link" type="button" @click="registerMode = true">免费注册</button></p>
        </form>
        <form v-else class="auth-form auth-form-register" @submit.prevent="doRegister">
          <div class="auth-heading"><h2>创建账号</h2><p>注册后再提交校园卡认证</p></div>
          <div class="auth-fields">
            <label class="auth-field"><select v-model="registerForm.userType"><option>学生</option><option>教职工</option><option>校友</option></select></label>
            <label class="auth-field"><input v-model="registerForm.studentNo" placeholder="学号 / 工号" required /></label>
            <label class="auth-field"><input v-model="registerForm.realName" placeholder="真实姓名" required /></label>
            <label class="auth-field"><input v-model="registerForm.nickname" placeholder="昵称" required /></label>
            <label class="auth-field"><input v-model="registerForm.phone" placeholder="手机号（可选）" /></label>
            <label class="auth-field"><input v-model="registerForm.wechat" placeholder="微信号（可选）" /></label>
            <label class="auth-field"><input v-model="registerForm.password" type="password" placeholder="密码" required /></label>
            <label class="auth-field"><input v-model="registerForm.confirmPassword" type="password" placeholder="确认密码" required /></label>
          </div>
          <button class="btn auth-submit" type="submit">完成注册</button>
          <p class="auth-switch">已有账号？ <button class="auth-link" type="button" @click="registerMode = false">立即登录</button></p>
        </form>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import FileUpload from "../components/FileUpload.vue";
import { register, submitAuth as apiSubmitAuth, updateProfile } from "../api/modules/auth.js";
import { campusCardSrc } from "../api/modules/uploads.js";
import { useSessionStore } from "../stores/session.js";

const router = useRouter();
const session = useSessionStore();

const registerMode = ref(false);
const loginForm = reactive({ account: "", password: "" });
const registerForm = reactive({ userType: "学生", studentNo: "", realName: "", nickname: "", phone: "", wechat: "", password: "", confirmPassword: "" });
const profile = reactive({ nickname: "", gender: "保密", entryYear: "", avatarUrl: "", bio: "", phone: "", wechat: "" });
const authForm = reactive({ campusCardImageUrl: "", bio: "" });

const userEntries = computed(() => [
  { to: "/favorites", label: "我的收藏", icon: "⭐" },
  { to: "/orders", label: "我的订单", icon: "📦" },
  { to: "/chats", label: "私信", icon: "💬", badge: session.unreadCount > 0 ? session.unreadCount : null },
  { to: "/notifications", label: "通知", icon: "🔔", badge: session.unreadCount > 0 ? session.unreadCount : null },
  { to: "/publish", label: "发布管理", icon: "📝" },
  { to: "/wanted", label: "求购市场", icon: "🛒" },
  { to: "/contact", label: "联系我们", icon: "📞" },
]);

const adminEntries = computed(() => [
  { to: "/admin", label: "后台管理", icon: "⚙️" },
  { to: "/contact", label: "用户反馈", icon: "📞" },
]);

function syncProfile() {
  if (!session.principal || !session.isUser) return;
  Object.assign(profile, {
    nickname: session.principal.nickname || "",
    gender: session.principal.gender || "保密",
    entryYear: session.principal.entryYear || "",
    avatarUrl: session.principal.avatarUrl || "",
    bio: session.principal.bio || "",
    phone: session.principal.phone || "",
    wechat: session.principal.wechat || "",
  });
  authForm.campusCardImageUrl = session.principal.campusCardImageUrl || "";
  authForm.bio = session.principal.bio || "";
}

async function doLogin() {
  try {
    await session.login(loginForm.account, loginForm.password);
    syncProfile();
    await router.push("/");
  } catch (error) {
    session.notify(error.message, true);
  }
}

async function doRegister() {
  if (registerForm.password !== registerForm.confirmPassword) {
    session.notify("两次输入的密码不一致", true);
    return;
  }
  const body = { ...registerForm };
  delete body.confirmPassword;
  try {
    const data = await register(body);
    session.notify(data.message);
    registerMode.value = false;
  } catch (error) {
    session.notify(error.message, true);
  }
}

async function saveProfile() {
  try {
    const data = await updateProfile(profile);
    session.principal = data.principal;
    syncProfile();
    session.notify(data.message);
  } catch (error) {
    session.notify(error.message, true);
  }
}

async function doSubmitAuth() {
  if (!authForm.campusCardImageUrl) {
    session.notify("请先上传校园卡照片", true);
    return;
  }
  try {
    const data = await apiSubmitAuth({ ...profile, campusCardImageUrl: authForm.campusCardImageUrl, bio: authForm.bio || profile.bio });
    session.notify(data.message);
    await session.loadMe();
    syncProfile();
  } catch (error) {
    session.notify(error.message, true);
  }
}

async function logoutAndGo() {
  await session.logout();
  await router.push("/");
}

watch(() => session.principal, syncProfile);
onMounted(syncProfile);
</script>

<style scoped>
/* ===== Auth Stage (Login/Register) ===== */
.auth-stage {
  position: fixed;
  inset: 0;
  z-index: 10;
  display: grid;
  place-items: center;
  overflow: auto;
  padding: 90px 18px 28px;
  background: var(--bg);
}
.auth-stage::before {
  content: "";
  position: absolute;
  z-index: -1;
  top: -20%;
  right: -10%;
  width: 520px;
  height: 520px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(20, 184, 166, 0.12), transparent 66%);
  filter: blur(20px);
  pointer-events: none;
}
.auth-card {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(260px, 0.78fr) minmax(380px, 1fr);
  width: min(900px, calc(100vw - 44px));
  max-height: min(560px, calc(100vh - 120px));
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: var(--shadow-xl), var(--shadow-glow);
  backdrop-filter: blur(26px);
}

/* Brand Panel */
.auth-brand-panel {
  display: grid;
  align-content: center;
  gap: 24px;
  padding: clamp(20px, 2.5vw, 32px);
  color: #fff;
  background: linear-gradient(135deg, rgba(13, 148, 136, 0.9), rgba(20, 184, 166, 0.82));
  box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.25);
}
.auth-logo {
  color: #fff;
  font-size: clamp(26px, 3vw, 36px);
  font-style: italic;
  font-weight: 850;
  line-height: 1;
  letter-spacing: -0.02em;
  text-shadow: 0 10px 22px rgba(4, 35, 83, 0.14);
}
.auth-line {
  width: min(160px, 100%);
  height: 3px;
  margin-top: 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.42);
}
.auth-brand-copy { display: grid; gap: 16px; }
.auth-brand-copy h2, .auth-brand-copy p, .auth-footnote { margin: 0; }
.auth-brand-copy h2 { font-size: clamp(22px, 2.4vw, 28px); line-height: 1.2; font-weight: 850; }
.auth-brand-copy p { max-width: 340px; color: rgba(255, 255, 255, 0.9); font-size: 14px; font-weight: 750; line-height: 1.8; }
.auth-footnote { align-self: end; display: grid; gap: 8px; color: rgba(255, 255, 255, 0.76); font-size: 13px; font-weight: 750; }

/* Form Panel */
.auth-form-panel {
  display: grid;
  align-items: center;
  justify-items: center;
  overflow: auto;
  padding: clamp(16px, 2.5vw, 28px) clamp(18px, 2.5vw, 30px);
  background: rgba(248, 250, 252, 0.62);
  min-width: 0;
}
.auth-form { display: grid; gap: 12px; width: 100%; max-width: 430px; }
.auth-form-register { width: 100%; max-width: 520px; gap: 10px; }
.auth-heading { display: grid; gap: 4px; margin-bottom: 2px; }
.auth-heading h2, .auth-heading p, .auth-switch { margin: 0; }
.auth-heading h2 { color: var(--ink); font-size: clamp(20px, 2.2vw, 26px); line-height: 1.15; font-weight: 850; letter-spacing: -0.02em; }
.auth-heading p { color: var(--muted); font-size: 14px; font-weight: 700; }

.auth-fields { display: grid; gap: 8px; }
.auth-fields.register { grid-template-columns: 1fr; gap: 10px; }
.auth-fields.register .wide { grid-column: auto; }
.auth-field { display: block; min-width: 0; }
.auth-field input, .auth-field select { min-height: 38px; border-radius: var(--radius-md); padding: 0 14px; min-width: 0; font-size: 14px; }
.auth-field input[aria-invalid="true"] { border-color: var(--red); box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.12); }

.auth-error {
  margin: -6px 0 0;
  padding: 10px 12px;
  border: 1px solid rgba(239, 68, 68, 0.26);
  border-radius: var(--radius-sm);
  background: rgba(239, 68, 68, 0.08);
  color: #b91c1c;
  font-size: 14px;
  font-weight: 800;
  line-height: 1.45;
}
.auth-submit {
  width: 100%;
  min-height: 46px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  border-color: transparent;
  box-shadow: 0 12px 26px rgba(13, 148, 136, 0.24);
  font-size: 16px;
}
.auth-submit:hover { background: linear-gradient(135deg, #2dd4bf, var(--primary-light)); box-shadow: 0 14px 30px rgba(13, 148, 136, 0.3); }
.auth-switch { text-align: center; color: var(--muted); font-size: 15px; font-weight: 750; }
.auth-link { min-height: auto; padding: 4px; border: 0; color: var(--primary); text-decoration: none; background: transparent; box-shadow: none; font-weight: 850; }
.auth-link:hover { transform: none; color: var(--primary-dark); }

/* ===== Wizard Steps ===== */
.wizard-steps { display: flex; align-items: center; justify-content: center; gap: 0; margin-bottom: 4px; }
.wizard-step { display: flex; flex-direction: column; align-items: center; gap: 6px; cursor: default; }
.wizard-dot {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--line);
  color: var(--muted);
  font-size: 14px;
  font-weight: 800;
  transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}
.wizard-step.active .wizard-dot { background: linear-gradient(135deg, var(--primary-light), var(--primary)); color: #fff; box-shadow: 0 6px 18px rgba(13, 148, 136, 0.3); }
.wizard-label { color: var(--muted); font-size: 12px; font-weight: 700; transition: color 0.2s ease; }
.wizard-step.active .wizard-label { color: var(--primary-dark); }
.wizard-line { width: 48px; height: 2px; margin: 0 8px; margin-bottom: 20px; border-radius: 999px; background: var(--line); transition: background 0.2s ease; }
.wizard-line.done { background: var(--primary); }
.wizard-panels { position: relative; overflow: hidden; }
.wizard-panel { display: none; }
.wizard-panel.active { display: block; animation: fadeUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
.wizard-actions { display: flex; gap: 10px; }
.wizard-actions .btn, .wizard-actions .ghost-btn { flex: 1; }

/* ===== Mine Page ===== */
.mine-page { display: flex; flex-direction: column; gap: 20px; }
.mine-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 24px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--primary-dark), var(--primary));
  color: #fff;
}
.mine-user { display: flex; align-items: center; gap: 16px; }
.mine-avatar-lg {
  width: 72px;
  height: 72px;
  border-radius: 999px;
  object-fit: cover;
  border: 3px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}
.mine-avatar-lg.admin-avatar {
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, var(--accent-purple), var(--accent-orange));
  color: #fff;
  font-size: 28px;
  font-weight: 800;
}
.mine-info h2 { color: #fff; font-size: 22px; font-weight: 800; margin-bottom: 4px; }
.mine-info .muted { color: rgba(255, 255, 255, 0.75); font-size: 14px; }
.mine-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.mine-tags .pill { background: rgba(255, 255, 255, 0.2); color: #fff; border: none; font-size: 12px; }
.mine-header .ghost-btn { border-color: rgba(255, 255, 255, 0.3); color: #fff; background: rgba(255, 255, 255, 0.1); }
.mine-header .ghost-btn:hover { background: rgba(255, 255, 255, 0.2); border-color: rgba(255, 255, 255, 0.5); }
.mine-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 14px; }
.mine-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px 12px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--surface);
  color: var(--ink);
  text-decoration: none;
  font-size: 14px;
  font-weight: 700;
  transition: all 0.16s ease;
  position: relative;
}
.mine-card:hover { transform: translateY(-2px); border-color: var(--primary-light); box-shadow: var(--shadow-md); }
.mine-card-icon { font-size: 28px; line-height: 1; }
.mine-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: var(--red);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  display: grid;
  place-items: center;
}

/* ===== Profile ===== */
.profile-hero { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; padding: 22px 26px; }
.card-preview { width: min(100%, 420px); max-height: 240px; border-radius: var(--radius-md); border: 1px solid var(--line); background: var(--surface-soft); object-fit: cover; }

.account-stats-band { padding: 16px; }
.account-stats-band .stats { gap: 12px; }
.account-stats-band .stat { padding: 14px 16px; border-radius: var(--radius-md); }
.account-stats-band .stat strong { margin-top: 6px; font-size: 22px; }
.account-panels { gap: 28px; align-items: start; }
.account-panel { padding: 22px; }
.account-panel .section-head { margin-bottom: 16px; }
.account-form { gap: 12px; }
.account-panel textarea { min-height: 84px; }
.account-panel .upload-box { min-height: 82px; }

/* ===== Dark Mode ===== */
:global([data-theme="dark"]) .auth-stage::before { background: radial-gradient(circle, rgba(20, 184, 166, 0.14), transparent 66%); }
:global([data-theme="dark"]) .auth-card { background: rgba(15, 23, 42, 0.82); border-color: rgba(30, 41, 59, 0.85); }
:global([data-theme="dark"]) .auth-form-panel { background: rgba(15, 23, 42, 0.58); }
:global([data-theme="dark"]) .auth-brand-panel { color: #e2e8f0; background: linear-gradient(135deg, rgba(13, 148, 136, 0.45), rgba(15, 23, 42, 0.85)); box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.08); }
:global([data-theme="dark"]) .auth-logo { color: #f1f5f9; text-shadow: 0 10px 22px rgba(0, 0, 0, 0.25); }
:global([data-theme="dark"]) .auth-line { background: rgba(255, 255, 255, 0.35); box-shadow: none; }
:global([data-theme="dark"]) .auth-brand-copy p { color: rgba(226, 232, 240, 0.72); }
:global([data-theme="dark"]) .auth-footnote { color: rgba(148, 163, 184, 0.65); }
:global([data-theme="dark"]) .auth-heading h2 { color: var(--ink); }
:global([data-theme="dark"]) .auth-error { border-color: rgba(248, 113, 113, 0.32); background: rgba(239, 68, 68, 0.12); color: #fca5a5; }
:global([data-theme="dark"]) .wizard-dot { background: var(--surface-soft); color: var(--muted); }
:global([data-theme="dark"]) .wizard-step.active .wizard-dot { background: linear-gradient(135deg, var(--primary-light), var(--primary)); color: #fff; }
:global([data-theme="dark"]) .wizard-label { color: var(--muted); }
:global([data-theme="dark"]) .wizard-step.active .wizard-label { color: var(--primary-light); }
:global([data-theme="dark"]) .wizard-line { background: var(--line-strong); }
:global([data-theme="dark"]) .wizard-line.done { background: var(--primary); }
:global([data-theme="dark"]) .mine-card { background: var(--surface); border-color: var(--line-strong); }

/* ===== Responsive ===== */
@media (max-width: 980px) {
  .auth-card { grid-template-columns: 1fr; min-height: auto; }
  .auth-stage { padding: 36px 18px; }
  .auth-card { width: min(720px, calc(100vw - 36px)); }
  .auth-brand-panel { min-height: 220px; gap: 24px; }
  .auth-form-panel { padding: 28px 24px; }
}
@media (max-width: 620px) {
  .auth-stage { padding: 22px 10px 34px; }
  .auth-card { width: min(100% - 12px, 720px); max-height: calc(100vh - 44px); }
  .auth-brand-panel { min-height: 260px; padding: 28px; }
  .auth-form-panel { padding: 30px 18px; }
  .auth-fields.register { grid-template-columns: 1fr; }
  .auth-logo { font-size: 38px; }
  .auth-brand-copy p { font-size: 15px; }
  .mine-grid { grid-template-columns: repeat(3, 1fr); }
}
</style>
