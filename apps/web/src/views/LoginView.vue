<script setup lang="ts">
import { Lock, Right, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const username = ref('admin')
const password = ref('')
const loading = ref(false)

async function submit(): Promise<void> {
  if (!username.value.trim() || !password.value) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(username.value.trim(), password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard'
    await router.replace(redirect)
  } catch (error: unknown) {
    ElMessage.error(error instanceof Error ? error.message : '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <!-- Left Showcase Card -->
    <section class="login-showcase">
      <div class="login-brand">
        <img src="/xiaosu-mascot.png" alt="小苏" />
        <span>小苏企业智能助手</span>
      </div>

      <div class="login-showcase-content">
        <div class="login-hero-text">
          <span class="login-kicker">XIAOSU AI CONSOLE</span>
          <h1>让企业知识，<br />随问随答。</h1>
          <p>统一管理知识库、员工问答、钉钉接入与模型运行状态。</p>
          <div class="login-feature-row">
            <span>知识库问答</span>
            <span>工具调用</span>
            <span>钉钉 Stream</span>
          </div>
        </div>
        <div class="mascot-stage">
          <img src="/xiaosu-mascot.png" alt="小苏助手形象" />
        </div>
      </div>

      <div class="login-showcase-footer">
        <span class="version-tag">v2.0 Enterprise</span>
      </div>
    </section>

    <!-- Right Login Card -->
    <section class="login-panel-wrap">
      <div class="login-panel">
        <div class="login-panel-icon"><Lock /></div>
        <span class="login-panel-kicker">ADMIN ACCESS</span>
        <h2>欢迎回来</h2>
        <p class="login-panel-subtitle">登录后进入小苏管理控制台</p>

        <el-form class="login-form" @submit.prevent="submit">
          <div class="login-field">
            <label>管理员账号</label>
            <el-input v-model="username" size="large" autocomplete="username" placeholder="请输入账号">
              <template #prefix><el-icon><User /></el-icon></template>
            </el-input>
          </div>
          <div class="login-field">
            <label>登录密码</label>
            <el-input
              v-model="password"
              size="large"
              type="password"
              show-password
              autocomplete="current-password"
              placeholder="请输入密码"
              @keydown.enter="submit"
            >
              <template #prefix><el-icon><Lock /></el-icon></template>
            </el-input>
          </div>
          <el-button class="login-submit" type="primary" size="large" :loading="loading" @click="submit">
            进入管理后台<el-icon class="el-icon--right"><Right /></el-icon>
          </el-button>
        </el-form>

        <div class="login-security">
          <span class="security-dot"></span>
          会话凭证仅保存在 HttpOnly Cookie 中
        </div>
      </div>
      <p class="login-copyright">© 2026 小苏企业智能助手</p>
    </section>
  </main>
</template>
