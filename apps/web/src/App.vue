<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'

const route = useRoute()
const title = computed(() => String(route.meta.title ?? '系统概览'))
const description = computed(() => String(route.meta.description ?? '小苏企业智能助手管理后台'))

const menuItems = [
  { path: '/dashboard', label: '系统概览', icon: 'grid' },
  { path: '/documents', label: '文档管理', icon: 'file' },
  { path: '/conversations', label: '对话日志', icon: 'history' },
  { path: '/chat', label: '调试聊天', icon: 'sparkle' },
  { path: '/settings', label: '系统设置', icon: 'setting' },
]
</script>

<template>
  <el-container class="app-shell">
    <el-aside width="252px" class="app-sidebar">
      <div class="brand">
        <span class="brand-mark">苏</span>
        <div class="brand-copy"><strong>小苏</strong><small>企业智能助手</small></div>
      </div>
      <div class="nav-caption">工作台</div>
      <el-menu :default-active="route.path" router class="app-menu">
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <span class="nav-icon" :class="`nav-icon-${item.icon}`" aria-hidden="true"></span>
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
        <div class="admin-chip">
          <span class="admin-avatar">管</span>
          <div><strong>管理员</strong><small>系统后台</small></div>
        </div>
      </el-header>
      <el-main class="app-main"><RouterView /></el-main>
    </el-container>
  </el-container>
</template>
