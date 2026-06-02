<template>
  <div class="register-page">
    <div class="register-card">
      <h1>Create Account</h1>
      <p class="subtitle">Join DataPulse</p>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="Username" prop="username">
          <el-input v-model="form.username" placeholder="3-50 characters" />
        </el-form-item>
        <el-form-item label="Email" prop="email">
          <el-input v-model="form.email" placeholder="your@email.com" />
        </el-form-item>
        <el-form-item label="Password" prop="password">
          <el-input v-model="form.password" type="password" placeholder="6+ characters" show-password />
        </el-form-item>
        <el-button type="primary" :loading="loading" class="reg-btn" @click="handleRegister">
          Register
        </el-button>
      </el-form>

      <p class="login-link">
        Have an account?
        <router-link to="/login">Log in →</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { setAuth } from '@/router'

export default {
  name: 'RegisterPage',

  data() {
    return {
      loading: false,
      form: { username: '', email: '', password: '' },
      rules: {
        username: [
          { required: true, message: 'Username required', trigger: 'blur' },
          { min: 3, max: 50, message: '3-50 characters', trigger: 'blur' },
        ],
        email: [
          { required: true, message: 'Email required', trigger: 'blur' },
          { type: 'email', message: 'Invalid email', trigger: 'blur' },
        ],
        password: [
          { required: true, message: 'Password required', trigger: 'blur' },
          { min: 6, message: 'At least 6 characters', trigger: 'blur' },
        ],
      },
    }
  },

  methods: {
    async handleRegister() {
      const valid = await this.$refs.formRef.validate().catch(() => false)
      if (!valid) return

      this.loading = true
      try {
        const { data } = await axios.post('/api/auth/register', this.form)
        setAuth(data.access_token, data.user.username)
        ElMessage.success('Registration successful!')
        this.$router.push('/')
      } catch (err) {
        ElMessage.error(err.response?.data?.detail || 'Registration failed')
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style scoped>
.register-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.register-card {
  background: #fff;
  border-radius: 16px;
  padding: 48px 40px;
  width: 420px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.register-card h1 {
  text-align: center;
  font-size: 24px;
  color: #303133;
  margin-bottom: 4px;
}

.subtitle {
  text-align: center;
  color: #909399;
  font-size: 13px;
  margin-bottom: 28px;
}

.reg-btn {
  width: 100%;
  margin-top: 8px;
  height: 42px;
  font-size: 16px;
}

.login-link {
  text-align: center;
  margin-top: 20px;
  font-size: 13px;
  color: #909399;
}

.login-link a {
  color: #409eff;
  text-decoration: none;
}
</style>
