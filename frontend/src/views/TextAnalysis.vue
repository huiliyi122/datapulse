<template>
  <div class="text-page">
    <h2>Text Analysis</h2>
    <p class="desc">Analyze word frequency, extract keywords, or evaluate sentiment.</p>

    <el-card>
      <el-form label-width="100px">
        <el-form-item label="Text Input">
          <el-input v-model="textInput" type="textarea" :rows="5" placeholder="Paste text here, one line per entry..." />
        </el-form-item>
        <el-form-item label="Analysis">
          <el-radio-group v-model="analysisType">
            <el-radio value="wordcloud">Word Frequency</el-radio>
            <el-radio value="keyword">Keywords</el-radio>
            <el-radio value="sentiment">Sentiment</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="runAnalysis">
            Analyze
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result" class="result-card">
      <template #header><span>Result</span></template>

      <template v-if="analysisType === 'sentiment' && result.length">
        <el-table :data="result" border stripe size="small" max-height="400">
          <el-table-column prop="text" label="Text" min-width="200" show-overflow-tooltip />
          <el-table-column prop="score" label="Score" width="120">
            <template #default="{ row }">
              <el-tag :type="row.score > 0.5 ? 'success' : row.score < 0.5 ? 'danger' : 'info'">
                {{ row.score }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </template>

      <template v-else-if="result.length">
        <div ref="wordChart" class="chart-box"></div>
        <el-table :data="result.slice(0, 20)" border stripe size="small" max-height="400">
          <el-table-column prop="word" label="Term" width="180">
            <template #default="{ row }">{{ row.word || row.keyword }}</template>
          </el-table-column>
          <el-table-column prop="count" label="Count" width="100">
            <template #default="{ row }">{{ row.count ?? row.weight?.toFixed(4) ?? '-' }}</template>
          </el-table-column>
        </el-table>
      </template>

      <el-empty v-else description="No results" />
    </el-card>
  </div>
</template>

<script>
import axios from 'axios'
import { nextTick } from 'vue'
import * as echarts from 'echarts'

export default {
  name: 'TextAnalysisPage',

  data() {
    return {
      loading: false,
      textInput: '',
      analysisType: 'wordcloud',
      result: null,
      chart: null,
    }
  },

  methods: {
    async runAnalysis() {
      const texts = this.textInput.split('\n').map(s => s.trim()).filter(Boolean)
      if (texts.length === 0) return

      if (this.chart) { this.chart.dispose(); this.chart = null }

      this.loading = true
      try {
        const { data } = await axios.post('/api/analyze/text', {
          texts, analysis: this.analysisType,
        })
        this.result = data.result
        if (this.analysisType !== 'sentiment' && this.result.length) {
          nextTick(() => this.renderChart())
        }
      } catch (err) {
        this.$message.error('Analysis failed: ' + (err.response?.data?.detail || err.message))
      } finally {
        this.loading = false
      }
    },

    renderChart() {
      const el = this.$refs.wordChart
      if (!el) return
      if (!this.chart) this.chart = echarts.init(el)

      const items = this.result.slice(0, 20)
      const isWordFreq = this.analysisType === 'wordcloud'

      this.chart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: items.map(r => r.word || r.keyword).reverse(),
          axisLabel: { fontSize: 11 } },
        yAxis: { type: 'value' },
        grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
        series: [{
          type: 'bar',
          data: items.map(r => isWordFreq ? (r.count || 0) : (r.weight || 0)).reverse(),
          itemStyle: { borderRadius: [4, 4, 0, 0], color: '#409eff' },
        }],
      })
    },
  },

  beforeUnmount() {
    if (this.chart) this.chart.dispose()
  },
}
</script>

<style scoped>
.text-page { padding: 24px; max-width: 900px; margin: 0 auto; }
.text-page h2 { margin-bottom: 8px; font-size: 22px; color: #303133; }
.desc { color: #909399; font-size: 13px; margin-bottom: 20px; }
.result-card { margin-top: 20px; }
.chart-box { width: 100%; height: 300px; margin-bottom: 16px; }
</style>
