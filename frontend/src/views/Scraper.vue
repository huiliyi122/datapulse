<template>
  <div class="scraper-page">
    <h2>Scraper Tasks</h2>

    <el-card>
      <template #header><span>New Scrape Job</span></template>
      <el-form :model="form" label-width="120px">
        <el-form-item label="Target URLs">
          <el-input v-model="form.urls" type="textarea" :rows="4" placeholder="One URL per line" />
        </el-form-item>
        <el-form-item label="Max Pages">
          <el-input-number v-model="form.maxPages" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="Delay">
          <el-slider v-model="form.delay" :min="0.5" :max="5" :step="0.5" show-input />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="scraping" @click="startScraper">
            {{ scraping ? 'Scraping...' : 'Start Scraping' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="scraping || progress.percent === 100" class="progress-card">
      <template #header><span>Progress</span></template>
      <div class="progress-stats">
        <div class="progress-item"><span>Crawled</span><strong>{{ progress.crawled }}</strong></div>
        <div class="progress-item"><span>Success</span><strong style="color:#67c23a">{{ progress.success }}</strong></div>
        <div class="progress-item"><span>Failed</span><strong style="color:#f56c6c">{{ progress.failed }}</strong></div>
        <div class="progress-item"><span>Elapsed</span><strong>{{ progress.elapsed }}s</strong></div>
      </div>
      <el-progress :percentage="progress.percent" :status="progress.percent === 100 ? 'success' : undefined"
        :stroke-width="14" striped striped-flow />
    </el-card>

    <el-card v-if="scrapeResults.length > 0" class="result-card">
      <template #header><span>Results ({{ scrapeResults.length }} items)</span></template>
      <el-table :data="scrapeResults.slice(0, 20)" border stripe size="small" max-height="400">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column v-for="col in scrapeResultCols" :key="col" :prop="col" :label="col" min-width="120" show-overflow-tooltip />
      </el-table>
      <p v-if="scrapeResults.length > 20" class="table-tip">Showing 20 of {{ scrapeResults.length }}</p>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios'
import { ElMessage } from 'element-plus'

export default {
  name: 'ScraperPage',

  data() {
    return {
      form: { urls: '', maxPages: 10, delay: 1.0 },
      scraping: false,
      progress: { crawled: 0, success: 0, failed: 0, elapsed: 0, percent: 0 },
      scrapeResults: [],
      scrapeResultCols: [],
      _timer: null,
    }
  },

  beforeUnmount() {
    if (this._timer) clearInterval(this._timer)
  },

  methods: {
    async startScraper() {
      const urls = this.form.urls.split('\n').map(s => s.trim()).filter(Boolean)
      if (urls.length === 0) {
        ElMessage.warning('Enter at least one URL')
        return
      }

      this.scraping = true
      this.progress = { crawled: 0, success: 0, failed: 0, elapsed: 0, percent: 0 }
      this.scrapeResults = []
      this.scrapeResultCols = []

      const startTime = Date.now()
      this._timer = setInterval(() => {
        this.progress.elapsed = Math.floor((Date.now() - startTime) / 1000)
      }, 1000)

      try {
        const { data } = await axios.post('/api/scrape/start', {
          urls, max_pages: this.form.maxPages, delay: this.form.delay,
        })
        const taskId = data.task_id

        let completed = false
        while (!completed) {
          await new Promise(r => setTimeout(r, 1000))
          const statusRes = await axios.get(`/api/scrape/task/${taskId}`)
          const task = statusRes.data

          if (task.status === 'completed') {
            completed = true
            this.progress.crawled = task.total || 0
            this.progress.success = task.success || 0
            this.progress.failed = task.failed || 0
            this.progress.percent = 100

            try {
              const resRes = await axios.get(`/api/scrape/results/${taskId}`)
              const items = resRes.data.results || []
              this.scrapeResults = items
              this.scrapeResultCols = items.length > 0
                ? Object.keys(items[0]).filter(k => k !== 'crawled_at') : []
            } catch (e) { /* ignore */ }

            ElMessage.success(`Scraped ${task.success || 0} items`)
          } else if (task.status === 'failed') {
            completed = true
            ElMessage.error('Scrape failed: ' + (task.error || 'unknown'))
          } else {
            if (this.progress.percent < 90) this.progress.percent += 2
          }
        }
      } catch (err) {
        ElMessage.error('Failed to start: ' + (err.response?.data?.detail || err.message))
      } finally {
        clearInterval(this._timer)
        this.scraping = false
      }
    },
  },
}
</script>

<style scoped>
.scraper-page { padding: 24px; max-width: 900px; margin: 0 auto; }
.scraper-page h2 { margin-bottom: 20px; font-size: 22px; color: #303133; }
.progress-card, .result-card { margin-top: 20px; }

.progress-stats {
  display: flex; gap: 28px; margin-bottom: 20px;
}
.progress-item { display: flex; flex-direction: column; gap: 4px; }
.progress-item span { font-size: 12px; color: #909399; }
.progress-item strong { font-size: 22px; }
.table-tip { text-align: center; color: #909399; font-size: 12px; margin-top: 8px; }
</style>
