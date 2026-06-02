<template>
  <div class="app-layout">
    <SidebarNav v-if="!isGuestRoute" />
    <div class="main-content" :class="{ 'full-width': isGuestRoute }">
      <router-view />
    </div>
  </div>
</template>

<script>
import SidebarNav from '@/layout/Sidebar.vue'

export default {
  name: 'App',
  components: { SidebarNav },

  computed: {
    isGuestRoute() {
      return this.$route.meta?.guest === true
    },
  },
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, 'Microsoft YaHei', sans-serif; background: #f5f7fa; }

.app-layout {
  display: flex;
  min-height: 100vh;
}

.main-content {
  margin-left: 220px;
  flex: 1;
  min-width: 0;
}

.main-content.full-width {
  margin-left: 0;
}
</style>
