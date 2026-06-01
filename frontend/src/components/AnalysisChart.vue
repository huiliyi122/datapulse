<template>
  <div class="analysis-chart">
    <div v-if="!chartData" class="empty-chart">
      <el-icon :size="48" color="#c0c4cc"><DataAnalysis /></el-icon>
      <p>点击「数据概览」查看图表</p>
    </div>

    <!-- 数据概览 -->
    <div v-else-if="type === 'summary'" class="charts-grid">
      <div class="chart-card" v-if="numericColumns.length > 0">
        <h4>数值列统计分布</h4>
        <div ref="barChartRef" class="chart-box"></div>
      </div>

      <div class="chart-card" v-if="bestCategory">
        <h4>分类 Top 分布（{{ bestCategory.name }}）</h4>
        <div ref="pieChartRef" class="chart-box"></div>
      </div>

      <div class="chart-card summary-card">
        <h4>数据摘要</h4>
        <div class="summary-grid">
          <div class="summary-item" v-for="item in summaryItems" :key="item.label">
            <span class="summary-label">{{ item.label }}</span>
            <span class="summary-value" :style="{ color: item.color }">{{ item.value }}</span>
          </div>
        </div>
      </div>

      <div class="chart-card" v-if="columnDetails.length > 0">
        <h4>字段统计详情</h4>
        <el-table :data="columnDetails" stripe size="small" max-height="360">
          <el-table-column prop="column" label="字段" width="140" />
          <el-table-column prop="type" label="类型" width="80">
            <template #default="{ row }"><el-tag size="small">{{ row.type }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="unique" label="唯一值" width="80" />
          <el-table-column prop="missing" label="缺失值" width="80" />
          <el-table-column prop="detail" label="详情" min-width="180" show-overflow-tooltip />
        </el-table>
      </div>
    </div>

    <!-- 相关性分析 -->
    <div v-else-if="type === 'correlation'" class="charts-grid">
      <div class="chart-card" v-if="corrColumns.length > 0">
        <h4>相关系数热力图</h4>
        <div ref="heatmapRef" class="chart-box" style="height:340px"></div>
      </div>
      <div class="chart-card" v-if="corrColumns.length > 0">
        <h4>相关系数矩阵</h4>
        <el-table :data="corrTableData" border stripe size="small" max-height="340">
          <el-table-column prop="col" label="" width="100" fixed />
          <el-table-column v-for="c in corrColumns" :key="c" :prop="c" :label="c" width="110" />
        </el-table>
      </div>
      <div v-if="!corrColumns.length" class="chart-card" style="grid-column:1/-1;text-align:center;padding:40px;color:#909399">
        数据集中数值列不足 2 列，无法计算相关性
      </div>
    </div>

    <!-- 聚类分析 -->
    <div v-else-if="type === 'clustering'" class="charts-grid">
      <div class="chart-card" v-if="clusterCounts.length > 0">
        <h4>聚类分布</h4>
        <div ref="clusterBarRef" class="chart-box"></div>
      </div>
      <div class="chart-card summary-card" v-if="clusterCounts.length > 0">
        <h4>聚类详情</h4>
        <div class="summary-grid">
          <div class="summary-item" v-for="c in clusterCounts" :key="c.label">
            <span class="summary-label">{{ c.label }}</span>
            <span class="summary-value" :style="{ color: c.color }">{{ c.value }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-else style="text-align:center;padding:40px;color:#909399">
      暂不支持此分析类型
    </div>
  </div>
</template>

<script>
import { DataAnalysis } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { nextTick, watch } from 'vue'

export default {
  name: 'AnalysisChart',

  components: { DataAnalysis },

  props: {
    data: { type: Object, default: null },
    type: { type: String, default: 'summary' },
  },

  data() {
    return {
      barChart: null,
      pieChart: null,
      heatmapChart: null,
      clusterChart: null,
    }
  },

  computed: {
    chartData() {
      return this.data
    },

    // === summary ===
    numericColumns() {
      if (!this.chartData?.columns_detail) return []
      const result = []
      for (const [col, desc] of Object.entries(this.chartData.columns_detail)) {
        if (desc.mean !== undefined && desc.mean !== null) {
          result.push({ name: col, ...desc })
        }
      }
      return result.slice(0, 8)
    },

    bestCategory() {
      if (!this.chartData?.columns_detail) return null
      let best = null, bestLen = 0
      for (const [col, desc] of Object.entries(this.chartData.columns_detail)) {
        if (desc.top_values && desc.top_values.length > 1 && desc.top_values.length > bestLen) {
          best = { name: col, values: desc.top_values }
          bestLen = desc.top_values.length
        }
      }
      return best
    },

    summaryItems() {
      if (!this.chartData) return []
      const d = this.chartData
      return [
        { label: '总行数', value: d.rows, color: '#409eff' },
        { label: '总列数', value: d.columns, color: '#67c23a' },
        { label: '缺失值', value: d.null_count, color: d.null_count > 0 ? '#f56c6c' : '#67c23a' },
        { label: '重复值', value: d.duplicate_count || 0, color: (d.duplicate_count || 0) > 0 ? '#e6a23c' : '#67c23a' },
        { label: '内存占用', value: (d.memory_mb || 0) + ' MB', color: '#909399' },
      ]
    },

    columnDetails() {
      if (!this.chartData?.columns_detail) return []
      return Object.entries(this.chartData.columns_detail).map(([col, desc]) => ({
        column: col,
        type: desc.mean !== undefined ? '数值' : '文本',
        unique: desc.unique || '-',
        missing: desc.missing || 0,
        detail: desc.mean !== undefined
          ? `均值 ${desc.mean?.toFixed(1) ?? '-'}  |  范围 ${desc.min ?? '-'} ~ ${desc.max ?? '-'}`
          : `Top: ${desc.top || '-'}  (${desc.top_freq || 0}次)`,
      }))
    },

    // === correlation ===
    corrColumns() {
      return this.chartData?.columns || []
    },

    corrTableData() {
      const cols = this.corrColumns
      if (!cols.length || !this.chartData?.data) return []
      return cols.map((c, i) => ({
        col: c,
        ...Object.fromEntries(cols.map((c2, j) => [c2, this.chartData.data[i]?.[j]?.toFixed(3) ?? '-']))
      }))
    },

    // === clustering ===
    clusterCounts() {
      const clusters = this.chartData?.clusters
      if (!clusters || !clusters.length) return []
      const counts = {}
      clusters.forEach(c => { counts[c] = (counts[c] || 0) + 1 })
      const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']
      return Object.entries(counts).map(([k, v]) => ({
        label: `聚类 ${Number(k) + 1}`,
        value: v,
        color: colors[Number(k) % colors.length],
      }))
    },
  },

  methods: {
    // === summary charts ===
    renderBarChart() {
      if (!this.numericColumns.length || !this.$refs.barChartRef) {
        if (this.$refs.barChartRef && this.barChart) this.barChart.resize()
        return
      }
      if (!this.barChart) this.barChart = echarts.init(this.$refs.barChartRef)

      const names = this.numericColumns.map(c => c.name)
      this.barChart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['均值', '最大值', '最小值'], top: 0 },
        grid: { left: '3%', right: '4%', bottom: '12%', containLabel: true },
        xAxis: { type: 'category', data: names, axisLabel: { rotate: names.length > 5 ? 30 : 0, fontSize: 11 } },
        yAxis: { type: 'value' },
        series: [
          { name: '均值', type: 'bar', data: this.numericColumns.map(c => c.mean || 0), itemStyle: { borderRadius: [4, 4, 0, 0], color: '#409eff' } },
          { name: '最大值', type: 'bar', data: this.numericColumns.map(c => c.max || 0), itemStyle: { borderRadius: [4, 4, 0, 0], color: '#f56c6c' } },
          { name: '最小值', type: 'bar', data: this.numericColumns.map(c => c.min || 0), itemStyle: { borderRadius: [4, 4, 0, 0], color: '#67c23a' } },
        ],
      })
    },

    renderPieChart() {
      const cat = this.bestCategory
      if (!cat || !this.$refs.pieChartRef) {
        if (this.$refs.pieChartRef && this.pieChart) this.pieChart.resize()
        return
      }
      if (!this.pieChart) this.pieChart = echarts.init(this.$refs.pieChartRef)

      this.pieChart.setOption({
        tooltip: { trigger: 'item' },
        legend: { orient: 'vertical', right: 10, top: 20 },
        series: [{
          type: 'pie', radius: ['40%', '70%'], center: ['40%', '55%'],
          data: cat.values.slice(0, 8).map(v => ({ name: String(v.value), value: v.count })),
          emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } },
          label: { formatter: '{b}\n{d}%' },
        }],
      })
    },

    // === correlation chart ===
    renderHeatmap() {
      if (!this.corrColumns.length || !this.$refs.heatmapRef) return
      if (!this.heatmapChart) this.heatmapChart = echarts.init(this.$refs.heatmapRef)

      const cols = this.corrColumns
      const data = []
      cols.forEach((c1, i) => {
        cols.forEach((c2, j) => {
          data.push([j, i, this.chartData.data[i]?.[j] ?? 0])
        })
      })

      this.heatmapChart.setOption({
        tooltip: {},
        grid: { left: '15%', right: '5%', top: '5%', bottom: '10%' },
        xAxis: { type: 'category', data: cols, axisLabel: { rotate: 30, fontSize: 11 } },
        yAxis: { type: 'category', data: cols },
        visualMap: { min: -1, max: 1, orient: 'horizontal', left: 'center', bottom: 0,
          inRange: { color: ['#f56c6c', '#fff', '#409eff'] } },
        series: [{
          type: 'heatmap', data, label: { show: true, formatter: p => p.data[2].toFixed(2), fontSize: 11 },
          emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' } },
        }],
      })
    },

    // === clustering chart ===
    renderClusterBar() {
      if (!this.clusterCounts.length || !this.$refs.clusterBarRef) return
      if (!this.clusterChart) this.clusterChart = echarts.init(this.$refs.clusterBarRef)

      this.clusterChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: this.clusterCounts.map(c => c.label) },
        yAxis: { type: 'value', name: '样本数' },
        series: [{
          type: 'bar', data: this.clusterCounts.map(c => c.value),
          itemStyle: { color: p => this.clusterCounts[p.dataIndex]?.color || '#409eff', borderRadius: [6, 6, 0, 0] },
        }],
      })
    },

    // === resize ===
    resizeAll() {
      this.barChart?.resize()
      this.pieChart?.resize()
      this.heatmapChart?.resize()
      this.clusterChart?.resize()
    },
  },

  watch: {
    type() {
      nextTick(() => {
        if (this.type === 'summary') { this.renderBarChart(); this.renderPieChart() }
        else if (this.type === 'correlation') this.renderHeatmap()
        else if (this.type === 'clustering') this.renderClusterBar()
      })
    },

    chartData() {
      nextTick(() => {
        if (this.type === 'summary') { this.renderBarChart(); this.renderPieChart() }
        else if (this.type === 'correlation') this.renderHeatmap()
        else if (this.type === 'clustering') this.renderClusterBar()
      })
    },

    numericColumns() { nextTick(() => this.renderBarChart()) },
    bestCategory() { nextTick(() => this.renderPieChart()) },
    corrColumns() { nextTick(() => this.renderHeatmap()) },
    clusterCounts() { nextTick(() => this.renderClusterBar()) },
  },

  mounted() {
    window.addEventListener('resize', this.resizeAll)
    nextTick(() => {
      if (this.type === 'summary') { this.renderBarChart(); this.renderPieChart() }
      else if (this.type === 'correlation') this.renderHeatmap()
      else if (this.type === 'clustering') this.renderClusterBar()
    })
  },

  beforeUnmount() {
    this.barChart?.dispose()
    this.pieChart?.dispose()
    this.heatmapChart?.dispose()
    this.clusterChart?.dispose()
    window.removeEventListener('resize', this.resizeAll)
  },
}
</script>

<style scoped lang="scss">
.analysis-chart { width: 100%; }

.empty-chart {
  text-align: center; padding: 60px 20px; color: #909399;
  p { margin-top: 12px; font-size: 14px; }
}

.charts-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
  .summary-card { grid-column: 1 / -1; }
}

.chart-card {
  background: #fff; border-radius: 10px; padding: 16px 20px; border: 1px solid #ebeef5;
  h4 { margin: 0 0 12px; font-size: 14px; font-weight: 600; color: #303133; }
}

.chart-box { width: 100%; height: 280px; }

.summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }

.summary-item {
  display: flex; flex-direction: column; gap: 6px; padding: 12px 16px; background: #f5f7fa; border-radius: 8px;
}

.summary-label { font-size: 13px; color: #909399; }

.summary-value { font-size: 22px; font-weight: 600; }
</style>
