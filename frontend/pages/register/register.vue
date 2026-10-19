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
    <view class="header">
      <text class="page-title">创建你的手账本</text>
      <text class="sub">记录每一笔，也收藏每一天</text>
      <text class="deco">✧ ✦ ✧</text>
    </view>

    <view class="card form">
      <view class="washi" />
      <view class="form-item">
        <text class="label">用户名（3-20 位字母数字）</text>
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
.page { min-height: 100vh; padding: 50rpx 0 60rpx; }
.header { padding: 0 44rpx; margin-bottom: 10rpx; }
.header .page-title { margin: 6rpx 0; }
.sub { display: block; font-size: 27rpx; color: #8A90A8; letter-spacing: 1rpx; }
.deco { display: block; margin-top: 12rpx; font-size: 25rpx; color: #C7B7F7; letter-spacing: 10rpx; }
.form { position: relative; margin: 26rpx 40rpx 0; padding: 40rpx 36rpx; }
.form-item { margin-bottom: 26rpx; }
.label { display: block; font-size: 27rpx; color: #5A5F78; margin-bottom: 12rpx; letter-spacing: 1rpx; }
.ph { color: #C3C7DA; }
</style>
