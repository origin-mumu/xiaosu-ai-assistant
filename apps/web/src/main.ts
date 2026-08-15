import 'element-plus/dist/index.css'
import './styles/main.css'

import ElementPlus from 'element-plus'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia).use(router).use(ElementPlus)

router.beforeEach(async (to) => {
  const auth = useAuthStore(pinia)
  if (!auth.checked) await auth.checkSession()
  if (to.meta.public) return auth.authenticated ? '/dashboard' : true
  if (!auth.authenticated) return { path: '/login', query: { redirect: to.fullPath } }
  return true
})

window.addEventListener('xiaosu:unauthorized', () => {
  const auth = useAuthStore(pinia)
  auth.clearSession()
  void router.replace({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
})

app.mount('#app')
