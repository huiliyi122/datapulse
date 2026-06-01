<template>
  <div class="analysis-chart">
    <div v-if="!chartData" class="empty-chart">
      <el-icon :size="48" color="#c0c4cc"><DataAnalysis /></el-icon>
      <p>点击「数据概览」查看图表</p>
    </div>

    <div v-else class="charts-grid">
      <!-- 统计柱状图 -->
      <div class="chart-card" v-if="numericColumns.length > 0">
        <h4>数值列统计分布</h4>
        <div ref="barChartRef" class="chart-box"></div>
      </div>

      <!-- Top值饼图 -->
      <div class="chart-card" v-if="topCategories.length > 0">
        <h4>分类 Top 分布</h4>
        <div ref="pieChartRef" class="chart-box"></div>
      </div>

      <!-- 数据摘要表格 -->
      <div class="chart-card summary-card">
        <h4>数据摘要</h4>
        <div class="summary-grid">
          <div class="summary-item" v-for="item in summaryItems" :key="item.label">
            <span class="summary-label">{{ item.label }}</span>
            <span class="summary-value" :style="{ color: item.color }">{{ item.value }}</span>
          </div>
        </div>
      </div>

      <!-- 字段详情 -->
      <div class="chart-card" v-if="columnDetails.length > 0">
        <h4>字段统计详情</h4>
        <el-table :data="columnDetails" stripe size="small" max-height="300">
          <el-table-column prop="column" label="字段" width="120" />
          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }"><el-tag size="small">{{ row.type }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="unique" label="唯一值" width="80" />
          <el-table-column prop="missing" label="缺失值" width="80" />
          <el-table-column prop="top_value" label="典型值" min-width="150" show-overflow-tooltip />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { nextTick, onMounted, onBeforeUnmount, watch } from 'vue'

export default {
  name: 'AnalysisChart',

  props: {
    data: { type: Object, default: null },
    type: { type: String, default: 'summary' },
  },

  data() {
    return {
      barChart: null,
      pieChart: null,
    }
  },

  computed: {
    chartData() {
      return this.data
    },

    numericColumns() {
      if (!this.chartData?.columns_detail) return []
      const result = []
      for (const [col, desc] of Object.entries(this.chartData.columns_detail)) {
        if (desc.mean !== undefined) {
          result.push({ name: col, ...desc })
        }
      }
      return result.slice(0, 8)
    },

    topCategories() {
      if (!this.chartData?.columns_detail) return []
      for (const [col, desc] of Object.entries(this.chartData.columns_detail)) {
        if (desc.top_values && desc.top_values.length > 0) {
          return desc.top_values.map(v => ({ name: String(v.value), value: v.count }))
        }
      }
      return []
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
        top_value: desc.top || desc.mean?.toFixed(2) || '-',
      }))
    },
  },

  methods: {
    renderBarChart() {
      if (!this.numericColumns.length || !this.$refs.barChartRef) return

      if (!this.barChart) {
        this.barChart = echarts.init(this.$refs.barChartRef)
      }

      const names = this.numericColumns.map(c => c.name)
      const means = this.numericColumns.map(c => c.mean || 0)
      const maxs = this.numericColumns.map(c => c.max || 0)
      const mins = this.numericColumns.map(c => c.min || 0)

      this.barChart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['均值', '最大值', '最小值'], top: 0 },
        grid: { left: '3%', right: '4%', bottom: '12%', containLabel: true },
        xAxis: {
          type: 'category',
          data: names,
          axisLabel: { rotate: names.length > 5 ? 30 : 0, fontSize: 11 },
        },
        yAxis: { type: 'value' },
        series: [
          { name: '均值', type: 'bar', data: means, itemStyle: { borderRadius: [4, 4, 0, 0], color: '#409eff' } },
          { name: '最大值', type: 'bar', data: maxs, itemStyle: { borderRadius: [4, 4, 0, 0], color: '#f56c6c' } },
          { name: '最小值', type: 'bar', data: mins, itemStyle: { borderRadius: [4, 4, 0, 0], color: '#67c23a' } },
        ],
      })
    },

    renderPieChart() {
      if (!this.topCategories.length || !this.$refs.pieChartRef) return

      if (!this.pieChart) {
        this.pieChart = echarts.init(this.$refs.pieChartRef)
      }

      this.pieChart.setOption({
        tooltip: { trigger: 'item' },
        legend: { orient: 'vertical', right: 10, top: 20 },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['40%', '55%'],
          data: this.topCategories.slice(0, 8),
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' },
          },
          label: {
            formatter: '{b}\n{d}%',
          },
        }],
      })
    },
  },

  watch: {
    chartData() {
      nextTick(() => {
        this.renderBarChart()
        this.renderPieChart()
      })
    },

    numericColumns() {
      nextTick(() => this.renderBarChart())
    },

    topCategories() {
      nextTick(() => this.renderPieChart())
    },
  },

  mounted() {
    window.addEventListener('resize', () => {
      this.barChart?.resize()
      this.pieChart?.resize()
    })
  },

  beforeUnmount() {
    this.barChart?.dispose()
    this.pieChart?.dispose()
    window.removeEventListener('resize', this.handleResize)
  },
}
</script>

<style scoped lang="scss">
.analysis-chart {
  width: 100%;
}

.empty-chart {
  text-align: center;
  padding: 60px 20px;
  color: #909399;
  p { margin-top: 12px; font-size: 14px; }
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;

  .summary-card {
    grid-column: 1 / -1;
  }
}

.chart-card {
  background: #fff;
  border-radius: 10px;
  padding: 16px 20px;
  border: 1px solid #ebeef5;

  h4 {
    margin: 0 0 12px;
    font-size: 14px;
    font-weight: 600;
    color: #303133;
  }
}

.chart-box {
  width: 100%;
  height: 280px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.summary-label {
  font-size: 13px;
  color: #909399;
}

.summary-value {
  font-size: 22px;
  font-weight: 600;
}
</style>
