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
