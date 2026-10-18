<script setup>
import { ref } from 'vue'
import { apiRegister } from '../../api/index.js'

const username = ref('')
const nickname = ref('')
const password = ref('')
const confirmPwd = ref('')
const loading = ref(false)

async function onRegister() {
  if (!username.value || !password.value) {
    uni.showToast({ title: '请填写用户名和密码', icon: 'none' }); return
  }
  if (password.value.length < 6) {
    uni.showToast({ title: '密码至少 6 位', icon: 'none' }); return
  }
  if (password.value !== confirmPwd.value) {
    uni.showToast({ title: '两次输入的密码不一致', icon: 'none' }); return
  }
  loading.value = true
  try {
    await apiRegister({
      username: username.value,
      password: password.value,
      nickname: nickname.value,
    })
    uni.showToast({ title: '注册成功，请登录', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 800)
  } catch (e) {
    // 错误提示已由 request.js 统一处理
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <view class="page">
    <view class="card form">
      <view class="form-item">
        <text class="label">用户名（3-20位字母数字）</text>
        <input class="input" v-model="username" placeholder="用于登录" placeholder-class="ph" />
      </view>
      <view class="form-item">
        <text class="label">昵称（可选）</text>
        <input class="input" v-model="nickname" placeholder="展示用昵称" placeholder-class="ph" />
      </view>
      <view class="form-item">
        <text class="label">密码（至少 6 位）</text>
        <input class="input" v-model="password" password placeholder="设置密码" placeholder-class="ph" />
      </view>
      <view class="form-item">
        <text class="label">确认密码</text>
        <input class="input" v-model="confirmPwd" password placeholder="再次输入密码" placeholder-class="ph" />
      </view>
      <button class="btn btn-primary" :class="{ 'btn-disabled': loading }" :disabled="loading" @click="onRegister">
        {{ loading ? '注册中…' : '注 册' }}
      </button>
    </view>
  </view>
</template>

<style scoped>
.page { min-height: 100vh; padding: 40rpx 0; }
.form { padding: 40rpx 32rpx; }
.form-item { margin-bottom: 28rpx; }
.label { display: block; font-size: 26rpx; color: #4a5568; margin-bottom: 12rpx; }
.ph { color: #b6bdcc; }
</style>
