<template>
  <template v-if="state.principal">
    <section v-if="isUser()" class="page-header animate-in profile-hero">
      <img class="avatar-lg" :src="profile.avatarUrl || '/assets/avatar-1.svg'" alt="" />
      <div>
        <h1>{{ state.principal.nickname }}</h1>
        <p class="muted">{{ state.principal.realName }} · {{ state.principal.userType }} · {{ state.principal.studentNo }}</p>
        <p v-if="state.principal.bio" class="muted">{{ state.principal.bio }}</p>
      </div>
      <span :class="['pill', state.principal.authStatus === '已认证' ? 'green' : 'gold']">{{ state.principal.authStatus }}</span>
    </section>
    <section v-else class="page-header animate-in">
      <div>
        <h1>管理员账号</h1>
        <p class="muted">{{ state.principal.username }}</p>
      </div>
    </section>

    <section v-if="isUser()" class="band animate-in delay-1 account-stats-band">
      <div class="stats">
        <div class="stat"><span class="muted">信用积分</span><strong>{{ state.principal.creditScore }}</strong></div>
        <div class="stat"><span class="muted">账号状态</span><strong>{{ state.principal.status }}</strong></div>
        <div class="stat"><span class="muted">性别</span><strong>{{ state.principal.gender || "保密" }}</strong></div>
        <div class="stat"><span class="muted">入学年份</span><strong>{{ state.principal.entryYear || "未填写" }}</strong></div>
      </div>
    </section>

    <section v-if="isUser()" class="split animate-in delay-2 account-panels">
      <div class="band account-panel">
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
      <div class="band account-panel">
        <div class="section-head"><h2>校园身份认证</h2></div>
        <form class="form-grid one" @submit.prevent="submitAuth">
          <FileUpload v-model="authForm.campusCardImageUrl" purpose="campus-card" label="校园卡照片" hint="仅本人和管理员可查看" />
          <label>补充说明<textarea v-model="authForm.bio" placeholder="可补充院系、交易偏好或身份说明" /></label>
          <button class="btn" type="submit">提交校园认证</button>
          <p v-if="state.principal.campusCardImageUrl" class="muted">已上传校园卡照片。</p>
          <img v-if="state.principal.campusCardImageUrl" class="card-preview" :src="campusCardSrc(state.principal.campusCardImageUrl)" alt="校园卡照片" />
        </form>
      </div>
    </section>

    <section class="band slim animate-in delay-3">
      <button class="danger-btn" type="button" @click="logoutAndGo">退出登录</button>
    </section>
  </template>

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
import { onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { api, campusCardSrc } from "../api/client.js";
import FileUpload from "../components/FileUpload.vue";
import { isUser, loadMe, login, logout, notify, state } from "../state/session.js";

const router = useRouter();
const registerMode = ref(false);
const loginForm = reactive({ account: "", password: "" });
const registerForm = reactive({ userType: "学生", studentNo: "", realName: "", nickname: "", phone: "", wechat: "", password: "", confirmPassword: "" });
const profile = reactive({ nickname: "", gender: "保密", entryYear: "", avatarUrl: "", bio: "", phone: "", wechat: "" });
const authForm = reactive({ campusCardImageUrl: "", bio: "" });

function syncProfile() {
  if (!state.principal || !isUser()) return;
  Object.assign(profile, {
    nickname: state.principal.nickname || "",
    gender: state.principal.gender || "保密",
    entryYear: state.principal.entryYear || "",
    avatarUrl: state.principal.avatarUrl || "",
    bio: state.principal.bio || "",
    phone: state.principal.phone || "",
    wechat: state.principal.wechat || "",
  });
  authForm.campusCardImageUrl = state.principal.campusCardImageUrl || "";
  authForm.bio = state.principal.bio || "";
}

async function doLogin() {
  try {
    await login(loginForm.account, loginForm.password);
    syncProfile();
    await router.push("/items");
  } catch (error) {
    notify(error.message, true);
  }
}

async function doRegister() {
  if (registerForm.password !== registerForm.confirmPassword) {
    notify("两次输入的密码不一致", true);
    return;
  }
  const body = { ...registerForm };
  delete body.confirmPassword;
  try {
    const data = await api("/api/auth/register", { method: "POST", body: JSON.stringify(body) });
    notify(data.message);
    registerMode.value = false;
  } catch (error) {
    notify(error.message, true);
  }
}

async function saveProfile() {
  try {
    const data = await api("/api/me", { method: "PUT", body: JSON.stringify(profile) });
    state.principal = data.principal;
    syncProfile();
    notify(data.message);
  } catch (error) {
    notify(error.message, true);
  }
}

async function submitAuth() {
  if (!authForm.campusCardImageUrl) {
    notify("请先上传校园卡照片", true);
    return;
  }
  try {
    const data = await api("/api/auth/submit-auth", {
      method: "POST",
      body: JSON.stringify({ ...profile, campusCardImageUrl: authForm.campusCardImageUrl, bio: authForm.bio || profile.bio }),
    });
    notify(data.message);
    await loadMe();
    syncProfile();
  } catch (error) {
    notify(error.message, true);
  }
}

async function logoutAndGo() {
  await logout();
  await router.push("/");
}

watch(() => state.principal, syncProfile);
onMounted(syncProfile);
</script>
