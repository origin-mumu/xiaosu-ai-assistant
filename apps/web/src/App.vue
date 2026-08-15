<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'

const route = useRoute()
const title = computed(() => String(route.meta.title ?? '系统概览'))
const description = computed(() => String(route.meta.description ?? '小苏企业智能助手管理后台'))
</script>

<template>
  <el-container class="app-shell">
    <el-aside width="232px" class="app-sidebar">
      <div class="brand">
        <span class="brand-mark">苏</span>
        <div><strong>小苏</strong><small>企业智能助手</small></div>
      </div>
      <el-menu :default-active="route.path" router>
        <el-menu-item index="/dashboard">系统概览</el-menu-item>
        <el-menu-item index="/documents">文档管理</el-menu-item>
        <el-menu-item index="/conversations">对话日志</el-menu-item>
        <el-menu-item index="/chat">调试聊天</el-menu-item>
        <el-menu-item index="/settings">系统设置</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div><h1>{{ title }}</h1><p>{{ description }}</p></div>
        <el-tag type="primary" effect="light">管理员后台</el-tag>
      </el-header>
      <el-main class="app-main"><RouterView /></el-main>
    </el-container>
  </el-container>
</template>
