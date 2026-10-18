<script setup>
import { ref } from 'vue'
import { apiLogin } from '../../api/index.js'
import { setLogin, isLogged } from '../../store/user.js'

const username = ref('')
const password = ref('')
const loading = ref(false)

// 已登录直接进入首页
if (isLogged()) {
  uni.switchTab({ url: '/pages/index/index' })
}

async function onLogin() {
  if (!username.value || !password.value) {
    uni.showToast({ title: '请输入用户名和密码', icon: 'none' })
    return
  }
  loading.value = true
  try {
    const res = await apiLogin({ username: username.value, password: password.value })
    setLogin(res.access_token, res.user)
    uni.switchTab({ url: '/pages/index/index' })
  } catch (e) {
    // 错误提示已由 request.js 统一处理
  } finally {
    loading.value = false
  }
}

function goRegister() {
  uni.navigateTo({ url: '/pages/register/register' })
}
</script>

<template>
  <view class="page">
    <view class="hero">
      <text class="title">智能记账</text>
      <text class="sub">记好每一笔，也安排好每一天</text>
    </view>
    <view class="card form">
      <view class="form-item">
        <text class="label">用户名</text>
        <input class="input" v-model="username" placeholder="请输入用户名" placeholder-class="ph" />
      </view>
      <view class="form-item">
        <text class="label">密码</text>
        <input class="input" v-model="password" password placeholder="请输入密码" placeholder-class="ph" />
      </view>
      <button class="btn btn-primary" :class="{ 'btn-disabled': loading }" :disabled="loading" @click="onLogin">
        {{ loading ? '登录中…' : '登 录' }}
      </button>
      <view class="links">
        <text class="link" @click="goRegister">没有账号？去注册</text>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page { min-height: 100vh; padding: 120rpx 0 60rpx; }
.hero { text-align: center; margin-bottom: 60rpx; }
.title { display: block; font-size: 56rpx; font-weight: 800; color: #2f6fed; }
.sub { display: block; margin-top: 16rpx; font-size: 26rpx; color: #7c8595; }
.form { padding: 40rpx 32rpx; }
.form-item { margin-bottom: 28rpx; }
.label { display: block; font-size: 26rpx; color: #4a5568; margin-bottom: 12rpx; }
.ph { color: #b6bdcc; }
.links { margin-top: 28rpx; text-align: center; }
.link { color: #2f6fed; font-size: 26rpx; }
</style>
