<template>
  <div class="dashboard">
    <div class="toolbar">
      <h2>Data Dashboard</h2>
      <div class="toolbar-actions">
        <el-upload
          :action="uploadUrl"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :show-file-list="false"
          accept=".csv,.xlsx,.xls,.json"
        >
          <el-button type="primary" :icon="Upload">Upload Data</el-button>
        </el-upload>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card" v-for="stat in statistics" :key="stat.label">
        <div class="stat-icon" :style="{ background: stat.color + '18' }">
          <el-icon :size="24" :color="stat.color">{{ stat.icon }}</el-icon>
        </div>
        <div class="stat-body">
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-label">{{ stat.label }}</span>
        </div>
      </div>
    </div>

    <div class="main-grid">
      <div class="panel dataset-panel">
        <div class="panel-header">
          <h3>Datasets</h3>
          <el-input v-model="searchQuery" placeholder="Search..." size="small" clearable />
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
              <span class="dataset-meta">{{ formatSize(ds.size) }} · {{ ds.upload_time }}</span>
            </div>
            <el-icon v-if="selectedDataset?.id === ds.id" color="#409eff"><Check /></el-icon>
          </div>
          <el-empty v-if="filteredDatasets.length === 0" description="No datasets" />
        </div>
      </div>

      <div class="panel analysis-panel">
        <template v-if="selectedDataset">
          <div class="panel-header">
            <h3>Analysis</h3>
            <div class="analysis-tabs">
              <el-button :type="activeAnalysis === 'summary' ? 'primary' : 'default'"
                size="small" @click="runAnalysis('summary')">Summary</el-button>
              <el-button :type="activeAnalysis === 'correlation' ? 'primary' : 'default'"
                size="small" @click="runAnalysis('correlation')">Correlation</el-button>
              <el-button :type="activeAnalysis === 'clustering' ? 'primary' : 'default'"
                size="small" @click="runAnalysis('clustering')">Clustering</el-button>
            </div>
          </div>

          <div class="data-preview" v-if="datasetPreview.length">
            <h4>Preview (first 10 rows)</h4>
            <el-table :data="datasetPreview" border stripe size="small" max-height="300">
              <el-table-column v-for="col in previewColumns" :key="col" :prop="col" :label="col" min-width="120" />
            </el-table>
          </div>

          <div v-if="analysisResult" class="analysis-result">
            <AnalysisChart :data="analysisResult" :type="activeAnalysis" />
          </div>

          <div class="export-actions">
            <el-dropdown @command="handleExport">
              <el-button type="success">Export <el-icon><ArrowDown /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="excel">Excel</el-dropdown-item>
                  <el-dropdown-item command="csv">CSV</el-dropdown-item>
                  <el-dropdown-item command="json">JSON</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button @click="generateReport">Generate Report</el-button>
          </div>
        </template>

        <el-empty v-else description="Select a dataset to start analysis" />
      </div>
    </div>

    <el-dialog v-model="showReportDialog" :title="reportTitle" width="800px" top="2vh" destroy-on-close>
      <div v-loading="reportLoading" class="report-body-wrap">
        <div v-if="reportHtml" class="report-body" v-html="reportHtml"></div>
        <el-empty v-else :description="reportLoading ? 'Generating...' : 'Empty'" />
      </div>
      <template #footer>
        <el-button type="primary" @click="downloadReport" :disabled="!reportDownloadUrl">Download</el-button>
        <el-button @click="showReportDialog = false">Close</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios'
import { Upload, Check, ArrowDown } from '@element-plus/icons-vue'
import AnalysisChart from '@/components/AnalysisChart.vue'

const API = '/api'

export default {
  name: 'DashboardPage',
  components: { AnalysisChart, Check, ArrowDown },

  data() {
    return {
      Upload, Check, ArrowDown,
      statistics: [
        { label: 'Datasets', value: 0, icon: 'Folder', color: '#409eff' },
        { label: 'Total Rows', value: 0, icon: 'Document', color: '#67c23a' },
        { label: 'Tasks', value: 0, icon: 'Monitor', color: '#e6a23c' },
        { label: 'Storage', value: '0 MB', icon: 'Coin', color: '#f56c6c' },
      ],
      datasets: [],
      selectedDataset: null,
      datasetPreview: [],
      analysisResult: null,
      activeAnalysis: 'summary',
      searchQuery: '',
      showReportDialog: false,
      reportHtml: '',
      reportTitle: '',
      reportLoading: false,
      reportDownloadUrl: '',
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
      return this.datasetPreview.length > 0 ? Object.keys(this.datasetPreview[0]).slice(0, 12) : []
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
        this.statistics[1].value = datasets.reduce((s, d) => s + (d.rows || 0), 0).toLocaleString()
        this.statistics[3].value = this.formatSize(datasets.reduce((s, d) => s + d.size, 0))
      } catch (err) {
        console.error('Failed to load datasets:', err)
      }
    },

    async loadScraperStats() {
      try {
        const { data } = await axios.get(`${API}/scrape/tasks`)
        this.statistics[2].value = data.total || 0
      } catch (err) { /* ignore */ }
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
        this.$message.success('Analysis complete')
      } catch (err) {
        this.$message.error('Analysis failed: ' + (err.response?.data?.detail || err.message))
      }
    },

    async handleExport(format) {
      if (!this.selectedDataset) return
      try {
        const { data } = await axios.post(`${API}/export`, {
          dataset_id: this.selectedDataset.id, format,
        })
        window.open(data.download_url, '_blank')
        this.$message.success(`Exported ${data.rows} rows`)
      } catch (err) {
        this.$message.error('Export failed')
      }
    },

    async generateReport() {
      if (!this.selectedDataset) return
      this.reportLoading = true
      this.reportTitle = `${this.selectedDataset.filename} - Report`
      this.showReportDialog = true
      try {
        const { data } = await axios.post(`${API}/report/generate`, null, {
          params: { dataset_id: this.selectedDataset.id, title: this.reportTitle },
        })
        this.reportHtml = data.report
        this.reportDownloadUrl = data.download_url || ''
      } catch (err) {
        this.reportHtml = '<p style="color:red">Failed to generate report</p>'
        this.reportDownloadUrl = ''
      } finally {
        this.reportLoading = false
      }
    },

    downloadReport() {
      if (this.reportDownloadUrl) window.open(this.reportDownloadUrl, '_blank')
    },

    handleUploadSuccess(res) {
      if (res?.file_id) {
        this.$message.success(`Uploaded: ${res.filename} (${res.rows} rows)`)
        this.loadDatasets()
      }
    },

    handleUploadError() {
      this.$message.error('Upload failed')
    },

    formatSize(bytes) {
      const n = Number(bytes) || 0
      if (n >= 1024 * 1024) return (n / 1024 / 1024).toFixed(1) + ' MB'
      if (n >= 1024) return (n / 1024).toFixed(1) + ' KB'
      return n + ' B'
    },
  },
}
</script>

<style scoped>
.dashboard { padding: 24px; max-width: 1440px; margin: 0 auto; }

.toolbar {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;
}
.toolbar h2 { font-size: 22px; color: #303133; }
.toolbar-actions { display: flex; gap: 12px; }

.stats-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px;
}
.stat-card {
  background: #fff; border-radius: 12px; padding: 20px; display: flex; align-items: center;
  gap: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.stat-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.stat-body { display: flex; flex-direction: column; gap: 4px; }
.stat-value { font-size: 22px; font-weight: 600; color: #303133; }
.stat-label { font-size: 13px; color: #909399; }

.main-grid { display: grid; grid-template-columns: 300px 1fr; gap: 20px; }
.panel { background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.04); overflow: hidden; }
.panel-header { padding: 16px 20px; border-bottom: 1px solid #ebeef5; display: flex; justify-content: space-between; align-items: center; }
.panel-header h3 { font-size: 16px; font-weight: 600; }

.dataset-list { padding: 8px; max-height: 600px; overflow-y: auto; }
.dataset-item {
  padding: 12px 16px; border-radius: 8px; cursor: pointer;
  display: flex; justify-content: space-between; align-items: center; transition: all .2s;
}
.dataset-item:hover { background: #f5f7fa; }
.dataset-item.active { background: #ecf5ff; color: #409eff; }
.dataset-info { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.dataset-name { font-size: 14px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dataset-meta { font-size: 12px; color: #c0c4cc; }

.analysis-panel { padding: 0; }
.analysis-tabs { display: flex; gap: 8px; }
.data-preview, .analysis-result { padding: 16px 20px; border-bottom: 1px solid #ebeef5; }
.data-preview h4, .analysis-result h4 { margin: 0 0 12px; font-size: 14px; color: #606266; }
.export-actions { padding: 16px 20px; display: flex; gap: 12px; }
.report-body-wrap { max-height: 70vh; overflow-y: auto; padding: 8px; }
</style>
