<template>
  <div class="login-page">
    <div class="login-card">
      <h1>DataPulse</h1>
      <p class="subtitle">Data Collection &amp; Analysis Platform</p>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="handleLogin">
        <el-form-item label="Username" prop="username">
          <el-input v-model="form.username" placeholder="Enter username" :prefix-icon="User" />
        </el-form-item>
        <el-form-item label="Password" prop="password">
          <el-input v-model="form.password" type="password" placeholder="Enter password" :prefix-icon="Lock"
            show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-button type="primary" :loading="loading" class="login-btn" @click="handleLogin">
          Log In
        </el-button>
      </el-form>

      <p class="register-link">
        No account?
        <router-link to="/register">Register →</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { setAuth } from '@/router'

export default {
  name: 'LoginPage',

  data() {
    return {
      User, Lock,
      loading: false,
      form: { username: '', password: '' },
      rules: {
        username: [{ required: true, message: 'Username required', trigger: 'blur' }],
        password: [{ required: true, message: 'Password required', trigger: 'blur' }],
      },
    }
  },

  methods: {
    async handleLogin() {
      const valid = await this.$refs.formRef.validate().catch(() => false)
      if (!valid) return

      this.loading = true
      try {
        const { data } = await axios.post('/api/auth/login', this.form)
        setAuth(data.access_token, data.user.username)
        ElMessage.success(`Welcome, ${data.user.username}`)
        this.$router.push('/')
      } catch (err) {
        ElMessage.error(err.response?.data?.detail || 'Login failed')
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.login-card {
  background: #fff;
  border-radius: 16px;
  padding: 48px 40px;
  width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-card h1 {
  text-align: center;
  font-size: 28px;
  color: #303133;
  margin-bottom: 4px;
}

.subtitle {
  text-align: center;
  color: #909399;
  font-size: 13px;
  margin-bottom: 32px;
}

.login-btn {
  width: 100%;
  margin-top: 8px;
  height: 42px;
  font-size: 16px;
}

.register-link {
  text-align: center;
  margin-top: 20px;
  font-size: 13px;
  color: #909399;
}

.register-link a {
  color: #409eff;
  text-decoration: none;
}
</style>
