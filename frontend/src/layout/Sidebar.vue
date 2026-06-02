<template>
  <div class="sidebar">
    <div class="sidebar-brand">
      <span class="brand-icon">📊</span>
      <span class="brand-text">DataPulse</span>
    </div>

    <div class="sidebar-menu">
      <router-link v-for="item in menuItems" :key="item.path" :to="item.path"
        class="menu-item" :class="{ active: isActive(item.path) }">
        <span class="menu-icon">{{ item.icon }}</span>
        <span class="menu-label">{{ item.label }}</span>
      </router-link>
    </div>

    <div class="sidebar-footer">
      <template v-if="username">
        <div class="user-info">
          <span class="user-avatar">👤</span>
          <span class="user-name">{{ username }}</span>
        </div>
        <div class="user-action" @click="handleLogout">Logout</div>
      </template>
      <template v-else>
        <router-link to="/login" class="menu-item">
          <span class="menu-icon">🔑</span>
          <span class="menu-label">Login</span>
        </router-link>
      </template>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { getUsername, clearAuth } from '@/router'

export default {
  name: 'SidebarNav',

  data() {
    return {
      menuItems: [
        { path: '/', icon: '📊', label: 'Dashboard' },
        { path: '/scraper', icon: '🕷️', label: 'Scraper' },
        { path: '/ai', icon: '🤖', label: 'AI Extract' },
        { path: '/text', icon: '📝', label: 'Text Analysis' },
      ],
    }
  },

  computed: {
    username() {
      return getUsername()
    },
  },

  methods: {
    isActive(path) {
      return this.$route.path === path
    },
    handleLogout() {
      const token = localStorage.getItem('datapulse_token')
      if (token) {
        axios.post('/api/auth/logout', {}, {
          headers: { Authorization: `Bearer ${token}` },
        }).catch(() => {})
      }
      clearAuth()
      window.location.href = '/#/login'
    },
  },
}
</script>

<style scoped>
.sidebar {
  width: 220px;
  height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  color: #e0e0e0;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
}

.sidebar-brand {
  padding: 24px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-icon { font-size: 24px; }

.brand-text {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
}

.sidebar-menu {
  flex: 1;
  padding: 12px 0;
  overflow-y: auto;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  color: #a0a8c0;
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s;
  border-left: 3px solid transparent;
  cursor: pointer;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}

.menu-item.active {
  background: rgba(64, 158, 255, 0.15);
  color: #409eff;
  border-left-color: #409eff;
}

.menu-icon { font-size: 18px; width: 24px; text-align: center; }

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.user-avatar { font-size: 20px; }

.user-name {
  font-size: 13px;
  color: #c0c8e0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-action {
  font-size: 12px;
  color: #f56c6c;
  cursor: pointer;
  padding: 4px 0;
}

.user-action:hover { color: #ff7875; }
</style>
