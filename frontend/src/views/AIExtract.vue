<template>
  <div class="ai-page">
    <h2>AI Smart Extract</h2>
    <p class="desc">Enter a URL and describe what data you want — AI generates CSS selectors automatically.</p>

    <el-card>
      <el-form :model="form" label-width="140px">
        <el-form-item label="Target URL">
          <el-input v-model="form.url" placeholder="https://example.com/products" />
        </el-form-item>
        <el-form-item label="Description">
          <el-input v-model="form.description" placeholder="e.g. Extract all product names, prices, and ratings" />
        </el-form-item>
        <el-form-item label="Provider">
          <el-select v-model="form.provider" style="width:200px">
            <el-option label="Ollama (local)" value="ollama" />
            <el-option label="OpenAI" value="openai" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleExtract">
            Start Extraction
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result" class="result-card">
      <template #header><span>Extraction Result</span></template>

      <div v-if="error" class="error-msg">{{ error }}</div>

      <template v-if="result.schema?.fields">
        <h4>Inferred Schema</h4>
        <el-table :data="schemaFields" border stripe size="small" style="margin-bottom:20px">
          <el-table-column prop="name" label="Field" width="160" />
          <el-table-column prop="selector" label="CSS Selector" />
        </el-table>
      </template>

      <template v-if="result.data?.length">
        <h4>Extracted Data ({{ result.data_count || result.data.length }} total)</h4>
        <el-table :data="result.data" border stripe size="small" max-height="400">
          <el-table-column v-for="col in dataColumns" :key="col" :prop="col" :label="col" min-width="120" show-overflow-tooltip />
        </el-table>
      </template>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AIExtractPage',

  data() {
    return {
      loading: false,
      form: { url: '', description: '', provider: 'ollama' },
      result: null,
      error: '',
    }
  },

  computed: {
    schemaFields() {
      if (!this.result?.schema?.fields) return []
      return Object.entries(this.result.schema.fields).map(([name, selector]) => ({ name, selector }))
    },
    dataColumns() {
      return this.result?.data?.length > 0 ? Object.keys(this.result.data[0]) : []
    },
  },

  methods: {
    async handleExtract() {
      if (!this.form.url || !this.form.description) {
        this.error = 'Please enter URL and description'
        return
      }
      this.loading = true
      this.error = ''
      this.result = null
      try {
        const { data } = await axios.post('/api/ai/extract', this.form)
        this.result = data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Extraction failed'
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style scoped>
.ai-page { padding: 24px; max-width: 900px; margin: 0 auto; }
.ai-page h2 { margin-bottom: 8px; font-size: 22px; color: #303133; }
.desc { color: #909399; font-size: 13px; margin-bottom: 20px; }
.result-card { margin-top: 20px; }
.result-card h4 { margin: 16px 0 8px; font-size: 15px; color: #303133; }
.error-msg { color: #f56c6c; padding: 12px; background: #fef0f0; border-radius: 8px; margin-bottom: 12px; }
</style>
