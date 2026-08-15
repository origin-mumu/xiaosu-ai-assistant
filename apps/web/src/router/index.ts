import { createRouter, createWebHistory } from 'vue-router'

import DashboardView from '@/views/DashboardView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { title: '系统概览', description: '服务状态与关键数据' },
    },
    {
      path: '/documents/:id?',
      name: 'documents',
      component: () => import('@/views/DocumentsView.vue'),
      meta: { title: '文档管理', description: '上传、索引、替换和定位知识库原文' },
    },
    {
      path: '/conversations',
      name: 'conversations',
      component: () => import('@/views/ConversationsView.vue'),
      meta: { title: '对话日志', description: '查看用户、工具、Token、耗时和失败原因' },
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('@/views/ChatView.vue'),
      meta: { title: '调试聊天', description: '模拟员工对话，验证流式输出和引用' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
      meta: { title: '系统设置', description: '检查模型、检索与钉钉接入状态' },
    },
  ],
})

export default router
