<template>
  <div class="data-dashboard">
    <!-- 顶部操作栏 -->
    <div class="toolbar">
      <h2>数据采集与分析平台</h2>
      <div class="toolbar-actions">
        <el-upload
          :action="uploadUrl"
          :on-success="handleUploadSuccess"
          :show-file-list="false"
          accept=".csv,.xlsx,.xls,.json"
        >
          <el-button type="primary" :icon="Upload">上传数据</el-button>
        </el-upload>
        <el-button @click="showScraperDialog = true" :icon="Monitor">
          新建爬虫任务
        </el-button>
      </div>
    </div>

    <!-- 数据集概览卡片 -->
    <div class="stats-grid">
      <div class="stat-card" v-for="stat in statistics" :key="stat.label">
        <div class="stat-icon" :style="{ background: stat.color + '18' }">
          <el-icon :size="24" :color="stat.color">{{ stat.icon }}</el-icon>
        </div>
        <div class="stat-body">
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-label">{{ stat.label }}</span>
        </div>
        <div class="stat-change" :class="stat.trend >= 0 ? 'up' : 'down'">
          {{ stat.trend >= 0 ? '+' : '' }}{{ stat.trend }}%
        </div>
      </div>
    </div>

    <!-- 主区域：数据集列表 + 分析面板 -->
    <div class="main-grid">
      <!-- 左侧：数据集列表 -->
      <div class="panel dataset-panel">
        <div class="panel-header">
          <h3>数据集</h3>
          <el-input
            v-model="searchQuery"
            placeholder="搜索数据集..."
            prefix-icon="Search"
            size="small"
            clearable
          />
        </div>
        <div class="dataset-list">
          <div
            v-for="ds in filteredDatasets"
            :key="ds.id"
            class="dataset-item"
            :class="{ active: selectedDataset?.id === ds.id }"
            @click="selectDataset(ds)"
          >
            <div class="dataset-info">
              <span class="dataset-name">{{ ds.filename }}</span>
              <span class="dataset-meta">
                {{ formatSize(ds.size) }} · {{ ds.upload_time }}
              </span>
            </div>
            <el-icon v-if="selectedDataset?.id === ds.id" color="#409eff">
              <Check />
            </el-icon>
          </div>
          <el-empty v-if="filteredDatasets.length === 0" description="暂无数据集" />
        </div>
      </div>

      <!-- 右侧：分析面板 -->
      <div class="panel analysis-panel">
        <template v-if="selectedDataset">
          <div class="panel-header">
            <h3>数据分析</h3>
            <div class="analysis-tabs">
              <el-button
                :type="activeAnalysis === 'summary' ? 'primary' : 'default'"
                size="small" @click="runAnalysis('summary')"
              >数据概览</el-button>
              <el-button
                :type="activeAnalysis === 'correlation' ? 'primary' : 'default'"
                size="small" @click="runAnalysis('correlation')"
              >相关性</el-button>
              <el-button
                :type="activeAnalysis === 'clustering' ? 'primary' : 'default'"
                size="small" @click="runAnalysis('clustering')"
              >聚类分析</el-button>
            </div>
          </div>

          <!-- 数据预览 -->
          <div class="data-preview" v-if="datasetPreview.length">
            <h4>数据预览（前10行）</h4>
            <el-table :data="datasetPreview" border stripe size="small" max-height="300">
              <el-table-column
                v-for="col in previewColumns"
                :key="col"
                :prop="col"
                :label="col"
                min-width="120"
              />
            </el-table>
          </div>

          <!-- 分析结果图表 -->
          <div v-if="analysisResult" class="analysis-result">
            <AnalysisChart :data="analysisResult" :type="activeAnalysis" />
          </div>

          <!-- 导出按钮 -->
          <div class="export-actions">
            <el-dropdown @command="handleExport">
              <el-button type="success">
                导出结果 <el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="excel">Excel</el-dropdown-item>
                  <el-dropdown-item command="csv">CSV</el-dropdown-item>
                  <el-dropdown-item command="json">JSON</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button @click="generateReport">生成分析报告</el-button>
          </div>
        </template>

        <el-empty v-else description="请选择一个数据集">
          <template #image>
            <el-icon :size="64" color="#c0c4cc"><DataAnalysis /></el-icon>
          </template>
        </el-empty>
      </div>
    </div>

    <!-- 爬虫任务对话框 -->
    <el-dialog v-model="showScraperDialog" title="新建爬虫任务" width="600px">
      <el-form :model="scraperForm" label-width="100px">
        <el-form-item label="目标URL">
          <el-input
            v-model="scraperForm.urls"
            type="textarea"
            :rows="4"
            placeholder="每行输入一个URL"
          />
        </el-form-item>
        <el-form-item label="最大页数">
          <el-input-number v-model="scraperForm.maxPages" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="请求延迟">
          <el-slider
            v-model="scraperForm.delay"
            :min="0.5"
            :max="5"
            :step="0.5"
            show-input
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showScraperDialog = false">取消</el-button>
        <el-button type="primary" @click="startScraper" :loading="scraping">
          {{ scraping ? '爬取中...' : '开始爬取' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios'
import {
  Upload, Monitor, Search, Check,
  ArrowDown, DataAnalysis,
} from '@element-plus/icons-vue'
import AnalysisChart from '@/components/AnalysisChart.vue'

const API = 'http://localhost:8000/api'

export default {
  name: 'DataDashboard',

  components: { DataAnalysis, AnalysisChart },

  data() {
    return {
      Upload, Monitor, Search, Check, ArrowDown,

      // 状态
      statistics: [
        { label: '数据集总量', value: 0, icon: 'Folder', color: '#409eff', trend: 12 },
        { label: '数据总条数', value: 0, icon: 'Document', color: '#67c23a', trend: 8 },
        { label: '爬虫任务', value: 0, icon: 'Monitor', color: '#e6a23c', trend: -3 },
        { label: '存储用量', value: '0 MB', icon: 'Coin', color: '#f56c6c', trend: 15 },
      ],

      datasets: [],
      selectedDataset: null,
      datasetPreview: [],
      analysisResult: null,
      activeAnalysis: 'summary',
      searchQuery: '',

      // 爬虫
      showScraperDialog: false,
      scraperForm: { urls: '', maxPages: 10, delay: 1.0 },
      scraping: false,
    }
  },

  computed: {
    uploadUrl: () => `${API}/data/upload`,

    filteredDatasets() {
      if (!this.searchQuery) return this.datasets
      const q = this.searchQuery.toLowerCase()
      return this.datasets.filter(d => d.filename.toLowerCase().includes(q))
    },

    previewColumns() {
      return this.datasetPreview.length > 0
        ? Object.keys(this.datasetPreview[0]).slice(0, 12)
        : []
    },
  },

  async mounted() {
    await this.loadDatasets()
    await this.loadScraperStats()
  },

  methods: {
    async loadDatasets() {
      try {
        const { data: { datasets } } = await axios.get(`${API}/data/datasets`)
        this.datasets = datasets
        this.statistics[0].value = datasets.length

        const totalRows = datasets.reduce((sum, d) => sum + (d.rows || 0), 0)
        this.statistics[1].value = totalRows.toLocaleString()
        this.statistics[3].value = this.formatSize(
          datasets.reduce((s, d) => s + d.size, 0)
        )
      } catch (err) {
        console.error('加载数据集失败:', err)
      }
    },

    async loadScraperStats() {
      try {
        const { data } = await axios.get(`${API}/scrape/tasks`)
        this.statistics[2].value = data.total || 0
      } catch (err) {
        console.error('加载爬虫统计失败:', err)
      }
    },

    async selectDataset(ds) {
      this.selectedDataset = ds
      this.analysisResult = null
      this.datasetPreview = ds.preview || []
    },

    async runAnalysis(type) {
      if (!this.selectedDataset) return
      this.activeAnalysis = type
      try {
        const { data } = await axios.post(`${API}/analyze`, {
          dataset_id: this.selectedDataset.id,
          analysis_type: type,
        })
        this.analysisResult = data.result
        this.$message.success('分析完成')
      } catch (err) {
        this.$message.error('分析失败: ' + (err.response?.data?.detail || err.message))
      }
    },

    async handleExport(format) {
      if (!this.selectedDataset) return
      try {
        const { data } = await axios.post(`${API}/export`, {
          dataset_id: this.selectedDataset.id,
          format,
        })
        window.open(`http://localhost:8000${data.download_url}`, '_blank')
        this.$message.success(`导出成功，共 ${data.rows} 条`)
      } catch (err) {
        this.$message.error('导出失败')
      }
    },

    async generateReport() {
      if (!this.selectedDataset) return
      try {
        const { data } = await axios.post(`${API}/report/generate`, null, {
          params: {
            dataset_id: this.selectedDataset.id,
            title: `${this.selectedDataset.filename} - 分析报告`,
          },
        })
        this.$alert(data.report.slice(0, 500) + '...', '报告预览')
      } catch (err) {
        this.$message.error('生成报告失败')
      }
    },

    async startScraper() {
      const urls = this.scraperForm.urls
        .split('\n')
        .map(s => s.trim())
        .filter(Boolean)

      if (urls.length === 0) {
        this.$message.warning('请至少输入一个URL')
        return
      }

      this.scraping = true
      try {
        const { data } = await axios.post(`${API}/scrape/start`, {
          urls,
          max_pages: this.scraperForm.maxPages,
          delay: this.scraperForm.delay,
        })
        this.$message.success(`爬虫任务已创建: ${data.task_id}`)
        this.showScraperDialog = false
      } catch (err) {
        this.$message.error('创建任务失败')
      } finally {
        this.scraping = false
      }
    },

    handleUploadSuccess(res) {
      if (res?.file_id) {
        this.$message.success(`上传成功: ${res.filename} (${res.rows}行)`)
        this.loadDatasets()
      }
    },

    formatSize(bytes) {
      if (bytes >= 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB'
      if (bytes >= 1024) return (bytes / 1024).toFixed(1) + ' KB'
      return bytes + ' B'
    },
  },
}
</script>

<style scoped lang="scss">
.data-dashboard {
  padding: 24px;
  max-width: 1440px;
  margin: 0 auto;
  min-height: 100vh;
  background: #f5f7fa;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;

  h2 {
    margin: 0;
    font-size: 22px;
    color: #303133;
  }

  .toolbar-actions {
    display: flex;
    gap: 12px;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  position: relative;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
}

.stat-label {
  font-size: 13px;
  color: #909399;
}

.stat-change {
  position: absolute;
  top: 16px;
  right: 20px;
  font-size: 13px;
  font-weight: 500;
  &.up { color: #67c23a; }
  &.down { color: #f56c6c; }
}

.main-grid {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 20px;
}

.panel {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;

  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
  }
}

.dataset-list {
  padding: 8px;
  max-height: 600px;
  overflow-y: auto;
}

.dataset-item {
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s;

  &:hover { background: #f5f7fa; }
  &.active { background: #ecf5ff; color: #409eff; }
}

.dataset-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.dataset-name {
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dataset-meta {
  font-size: 12px;
  color: #c0c4cc;
}

.analysis-panel {
  padding: 0;

  .panel-header {
    flex-wrap: wrap;
    gap: 12px;
  }
}

.analysis-tabs {
  display: flex;
  gap: 8px;
}

.data-preview, .analysis-result {
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;

  h4 {
    margin: 0 0 12px;
    font-size: 14px;
    color: #606266;
  }
}

.result-json {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  font-size: 13px;
  line-height: 1.6;
  max-height: 400px;
  overflow: auto;
}

.export-actions {
  padding: 16px 20px;
  display: flex;
  gap: 12px;
}
</style>
