<script setup lang="ts">
import { ChatDotRound, Clock, Document, Grid, Setting, SwitchButton, User } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const title = computed(() => String(route.meta.title ?? '系统概览'))
const description = computed(() => String(route.meta.description ?? '小苏企业智能助手管理后台'))
const activeMenu = computed(() =>
  route.path.startsWith('/documents') ? '/documents' : route.path,
)

const menuItems = [
  { path: '/dashboard', label: '系统概览', icon: Grid },
  { path: '/documents', label: '文档管理', icon: Document },
  { path: '/conversations', label: '对话日志', icon: Clock },
  { path: '/chat', label: '调试聊天', icon: ChatDotRound },
  { path: '/settings', label: '系统设置', icon: Setting },
]

async function signOut(): Promise<void> {
  await auth.logout()
  await router.replace('/login')
}
</script>

<template>
  <RouterView v-if="route.meta.layout === 'auth'" />
  <el-container v-else class="app-shell">
    <el-aside width="252px" class="app-sidebar">
      <div class="brand">
        <span class="brand-mark"><img src="/xiaosu-mascot.png" alt="小苏" /></span>
        <div class="brand-copy"><strong>小苏</strong><small>企业智能助手</small></div>
      </div>
      <div class="nav-caption">工作台</div>
      <el-menu :default-active="activeMenu" router class="app-menu">
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <span class="nav-icon" aria-hidden="true"><el-icon><component :is="item.icon" /></el-icon></span>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <span class="status-dot"></span>
        <div><strong>服务运行中</strong><small>钉钉 Stream 已接入</small></div>
      </div>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div class="page-heading">
          <span class="page-kicker">XIAOSU CONSOLE</span>
          <h1>{{ title }}</h1>
          <p>{{ description }}</p>
        </div>
        <button class="admin-chip" type="button" title="退出登录" @click="signOut">
          <span class="admin-avatar"><el-icon><User /></el-icon></span>
          <div><strong>{{ auth.username || '管理员' }}</strong><small>点击退出登录</small></div>
          <el-icon class="logout-icon"><SwitchButton /></el-icon>
        </button>
      </el-header>
      <el-main class="app-main"><RouterView /></el-main>
    </el-container>
  </el-container>
</template>
