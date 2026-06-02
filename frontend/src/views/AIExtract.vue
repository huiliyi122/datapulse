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
          <el-select v-model="form.provider" style="width:200px" @change="onProviderChange">
            <el-option label="Ollama (local)" value="ollama" />
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="Custom (OpenAI-compatible)" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="Model" v-if="modelOptions.length > 0">
          <el-select v-model="form.model" style="width:280px" filterable allow-create>
            <el-option v-for="m in modelOptions" :key="m.value" :label="m.label" :value="m.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleExtract">
            Start Extraction
          </el-button>
        </el-form-item>
      </el-form>

      <div class="provider-hint">
        <template v-if="form.provider === 'ollama'">
          Requires <a href="https://ollama.com" target="_blank">Ollama</a> running locally. Pull a model first: <code>ollama pull qwen2.5:7b</code>
        </template>
        <template v-else-if="form.provider === 'deepseek'">
          Set <code>ai.api_key</code> in <code>datapulse.yaml</code> with your DeepSeek API key.
        </template>
        <template v-else-if="form.provider === 'openai'">
          Set <code>ai.api_key</code> in <code>datapulse.yaml</code> with your OpenAI API key.
        </template>
      </div>
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

const MODEL_MAP = {
  ollama: [
    { label: 'Qwen 2.5 7B (recommended)', value: 'qwen2.5:7b' },
    { label: 'Qwen 2.5 14B', value: 'qwen2.5:14b' },
    { label: 'Llama 3 8B', value: 'llama3:8b' },
    { label: 'Llama 3 70B', value: 'llama3:70b' },
    { label: 'Mistral 7B', value: 'mistral:7b' },
  ],
  deepseek: [
    { label: 'DeepSeek V4 Pro', value: 'deepseek-v4-pro' },
    { label: 'DeepSeek V4 Flash', value: 'deepseek-v4-flash' },
  ],
  openai: [
    { label: 'GPT-4o Mini', value: 'gpt-4o-mini' },
    { label: 'GPT-4o', value: 'gpt-4o' },
    { label: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' },
  ],
  custom: [],
}

export default {
  name: 'AIExtractPage',

  data() {
    return {
      loading: false,
      form: { url: '', description: '', provider: 'ollama', model: 'qwen2.5:7b' },
      result: null,
      error: '',
    }
  },

  computed: {
    modelOptions() {
      return MODEL_MAP[this.form.provider] || []
    },
    schemaFields() {
      if (!this.result?.schema?.fields) return []
      return Object.entries(this.result.schema.fields).map(([name, selector]) => ({ name, selector }))
    },
    dataColumns() {
      return this.result?.data?.length > 0 ? Object.keys(this.result.data[0]) : []
    },
  },

  methods: {
    onProviderChange(provider) {
      const models = MODEL_MAP[provider] || []
      this.form.model = models.length > 0 ? models[0].value : 'default'
    },
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
.provider-hint {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
}
.provider-hint code {
  background: #e8eaed;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 11px;
}
.provider-hint a {
  color: #409eff;
  text-decoration: none;
}
</style>
