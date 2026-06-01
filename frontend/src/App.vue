<template>
  <DataDashboard />
</template>

<script>
import DataDashboard from './views/DataDashboard.vue'

export default {
  name: 'App',
  components: { DataDashboard },
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, 'Microsoft YaHei', sans-serif; }
</style>
