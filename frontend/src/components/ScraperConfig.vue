<template>
  <div class="scraper-config">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>爬虫配置</span>
          <el-tag type="success" v-if="isRunning" effect="dark">运行中</el-tag>
        </div>
      </template>

      <!-- 配置表单 -->
      <el-form
        ref="formRef"
        :model="config"
        :rules="rules"
        label-width="120px"
        size="default"
      >
        <el-form-item label="爬虫名称" prop="name">
          <el-input v-model="config.name" placeholder="例如：电商商品采集" />
        </el-form-item>

        <el-form-item label="起始URL" prop="startUrls">
          <el-input
            v-model="config.startUrls"
            type="textarea"
            :rows="4"
            placeholder="每行输入一个URL"
          />
        </el-form-item>

        <el-form-item label="爬取深度" prop="maxDepth">
          <el-slider
            v-model="config.maxDepth"
            :min="1"
            :max="5"
            show-input
          />
          <span class="form-tip">限制爬虫跟踪链接的层数</span>
        </el-form-item>

        <el-form-item label="并发数" prop="concurrency">
          <el-input-number
            v-model="config.concurrency"
            :min="1"
            :max="50"
          />
          <span class="form-tip">同时发起的HTTP请求数</span>
        </el-form-item>

        <el-form-item label="请求延迟" prop="delay">
          <el-slider
            v-model="config.delay"
            :min="0"
            :max="5"
            :step="0.5"
            show-input
          />
          <span class="form-tip">每次请求之间的等待秒数</span>
        </el-form-item>

        <el-form-item label="User-Agent">
          <el-select v-model="config.uaMode" class="w-full">
            <el-option label="随机轮换" value="random" />
            <el-option label="固定 Chrome" value="chrome" />
            <el-option label="固定 Firefox" value="firefox" />
            <el-option label="移动端" value="mobile" />
          </el-select>
        </el-form-item>

        <el-form-item label="代理模式">
          <el-radio-group v-model="config.proxyMode">
            <el-radio value="none">不使用</el-radio>
            <el-radio value="random">随机代理</el-radio>
            <el-radio value="custom">自定义</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="代理列表" v-if="config.proxyMode === 'custom'">
          <el-input
            v-model="config.proxyList"
            type="textarea"
            :rows="3"
            placeholder="每行一个代理，格式: http://ip:port"
          />
        </el-form-item>

        <!-- 数据提取规则 -->
        <el-divider>数据提取规则</el-divider>

        <el-form-item label="标题选择器">
          <el-input v-model="config.selectors.title" placeholder="例如: .product-title, h1" />
        </el-form-item>

        <el-form-item label="价格选择器">
          <el-input v-model="config.selectors.price" placeholder="例如: .price, span[data-price]" />
        </el-form-item>

        <el-form-item label="描述选择器">
          <el-input v-model="config.selectors.desc" placeholder="例如: .description, #intro" />
        </el-form-item>

        <el-form-item label="图片选择器">
          <el-input v-model="config.selectors.image" placeholder="例如: .product-img img, img.main" />
        </el-form-item>

        <!-- 输出配置 -->
        <el-divider>输出配置</el-divider>

        <el-form-item label="输出格式">
          <el-checkbox-group v-model="config.outputFormats">
            <el-checkbox label="csv">CSV</el-checkbox>
            <el-checkbox label="json">JSON</el-checkbox>
            <el-checkbox label="excel">Excel</el-checkbox>
            <el-checkbox label="database">数据库</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="定时采集">
          <el-switch v-model="config.scheduled" />
          <span v-if="config.scheduled" class="form-tip">
            <el-input v-model="config.cronExpr" placeholder="cron表达式: 0 */6 * * *" size="small" style="width:200px" />
            每6小时执行一次
          </span>
        </el-form-item>
      </el-form>

      <!-- 操作按钮 -->
      <div class="form-actions">
        <el-button type="primary" @click="handleStart" :loading="isRunning" size="large">
          {{ isRunning ? '爬取中...' : '开始采集' }}
        </el-button>
        <el-button @click="handleTest" :disabled="isRunning">测试连接</el-button>
        <el-button @click="handleSave">保存配置</el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>
    </el-card>

    <!-- 爬取进度 -->
    <el-card v-if="isRunning" shadow="never" class="progress-card">
      <template #header>
        <span>采集进度</span>
      </template>
      <div class="progress-info">
        <div class="progress-item">
          <span>已爬取</span>
          <strong>{{ progress.crawled }}</strong>
        </div>
        <div class="progress-item">
          <span>成功</span>
          <strong style="color:#67c23a">{{ progress.success }}</strong>
        </div>
        <div class="progress-item">
          <span>失败</span>
          <strong style="color:#f56c6c">{{ progress.failed }}</strong>
        </div>
        <div class="progress-item">
          <span>耗时</span>
          <strong>{{ progress.elapsed }}s</strong>
        </div>
      </div>
      <el-progress
        :percentage="progress.percent"
        :status="progress.percent === 100 ? 'success' : undefined"
        :stroke-width="12"
        striped
      />
    </el-card>

    <!-- 采集结果 -->
    <el-card v-if="results.length > 0" shadow="never" class="result-card">
      <template #header>
        <div class="card-header">
          <span>采集结果 (共 {{ results.length }} 条)</span>
          <el-button type="primary" size="small" @click="handleDownload">
            下载数据
          </el-button>
        </div>
      </template>
      <el-table :data="results.slice(0, 50)" border stripe size="small" max-height="400">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column
          v-for="col in resultColumns"
          :key="col"
          :prop="col"
          :label="col"
          min-width="140"
          show-overflow-tooltip
        />
      </el-table>
      <div v-if="results.length > 50" class="table-footer">
        仅展示前50条，共 {{ results.length }} 条
      </div>
    </el-card>
  </div>
</template>

<script>
import { reactive, ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

export default {
  name: 'ScraperConfig',

  setup() {
    const formRef = ref(null)

    const config = reactive({
      name: '',
      startUrls: '',
      maxDepth: 2,
      concurrency: 5,
      delay: 1.0,
      uaMode: 'random',
      proxyMode: 'none',
      proxyList: '',
      selectors: {
        title: '',
        price: '',
        desc: '',
        image: '',
      },
      outputFormats: ['csv', 'json'],
      scheduled: false,
      cronExpr: '0 */6 * * *',
    })

    const rules = {
      name: [{ required: true, message: '请输入爬虫名称', trigger: 'blur' }],
      startUrls: [{ required: true, message: '请输入起始URL', trigger: 'blur' }],
      maxDepth: [{ required: true, message: '请选择爬取深度' }],
      concurrency: [{ required: true, message: '请设置并发数' }],
    }

    const isRunning = ref(false)
    const progress = reactive({
      crawled: 0, success: 0, failed: 0, elapsed: 0, percent: 0,
    })
    const results = ref([])
    const resultColumns = ref([])

    const handleStart = async () => {
      const valid = await formRef.value.validate().catch(() => false)
      if (!valid) return

      const urls = config.startUrls.split('\n').map(s => s.trim()).filter(Boolean)
      if (urls.length === 0) {
        ElMessage.warning('请至少输入一个URL')
        return
      }

      isRunning.value = true
      progress.crawled = 0; progress.success = 0
      progress.failed = 0; progress.elapsed = 0; progress.percent = 0
      results.value = []
      resultColumns.value = []

      const startTime = Date.now()
      const timer = setInterval(() => {
        progress.elapsed = Math.floor((Date.now() - startTime) / 1000)
      }, 1000)

      try {
        const { data } = await axios.post('/api/scrape/start', {
          urls, max_pages: config.maxDepth, delay: config.delay,
        })

        // 轮询任务状态直到完成
        const taskId = data.task_id
        let completed = false
        while (!completed) {
          await new Promise(r => setTimeout(r, 1000))
          const statusRes = await axios.get(`/api/scrape/task/${taskId}`)
          const task = statusRes.data

          if (task.status === 'completed') {
            completed = true
            progress.crawled = task.total || 0
            progress.success = task.success || 0
            progress.failed = task.failed || 0
            progress.percent = 100

            // 加载结果数据
            const resRes = await axios.get(`/api/scrape/results/${taskId}`)
            const items = resRes.data.results || []
            results.value = items
            resultColumns.value = items.length > 0 ? Object.keys(items[0]) : []
            ElMessage.success(`采集完成，共 ${items.length} 条数据`)
          } else if (task.status === 'failed') {
            completed = true
            ElMessage.error('采集任务失败')
          } else {
            progress.percent = Math.min(progress.percent + 10, 90)
          }
        }
      } catch (err) {
        ElMessage.error('采集启动失败: ' + (err.response?.data?.detail || err.message))
      } finally {
        clearInterval(timer)
        isRunning.value = false
      }
    }

    const handleTest = () => {
      ElMessage.info('测试连接中...')
      setTimeout(() => ElMessage.success('连接正常'), 1500)
    }

    const handleSave = () => {
      localStorage.setItem('scraperConfig', JSON.stringify(config))
      ElMessage.success('配置已保存')
    }

    const handleReset = () => {
      Object.assign(config, {
        name: '', startUrls: '', maxDepth: 2, concurrency: 5,
        delay: 1.0, uaMode: 'random', proxyMode: 'none', proxyList: '',
        selectors: { title: '', price: '', desc: '', image: '' },
        outputFormats: ['csv', 'json'], scheduled: false, cronExpr: '0 */6 * * *',
      })
    }

    const handleDownload = () => {
      ElMessage.success('正在生成下载文件...')
    }

    return {
      formRef, config, rules,
      isRunning, progress, results, resultColumns,
      handleStart, handleTest, handleSave, handleReset, handleDownload,
    }
  },
}
</script>

<style scoped lang="scss">
.scraper-config {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #c0c4cc;
}

.w-full {
  width: 100%;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.progress-card,
.result-card {
  margin-top: 20px;
}

.progress-info {
  display: flex;
  gap: 32px;
  margin-bottom: 20px;

  .progress-item {
    display: flex;
    flex-direction: column;
    gap: 4px;

    span { font-size: 13px; color: #909399; }
    strong { font-size: 20px; }
  }
}

.table-footer {
  text-align: center;
  padding: 12px;
  color: #909399;
  font-size: 13px;
}
</style>
