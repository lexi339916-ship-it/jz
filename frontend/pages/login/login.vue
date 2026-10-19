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
    <!-- 手账插画页眉 -->
    <view class="auth-hero">
      <view class="blob blob-a" />
      <view class="blob blob-b" />
      <image class="doodle doodle-coffee" src="/static/doodles/coffee.png" mode="widthFix" />
      <image class="doodle doodle-stars" src="/static/doodles/stars.png" mode="widthFix" />
      <text class="brand">智能记账</text>
      <image class="brand-underline" src="/static/doodles/underline.png" mode="widthFix" />
      <text class="slogan">记好每一笔 · 也安排好每一天</text>
      <text class="deco-dots">✧ ✦ ✧</text>
    </view>

    <!-- 登录卡片 -->
    <view class="card-sketch form">
      <image class="form-tape" src="/static/doodles/tape_mint.png" mode="widthFix" />
      <text class="form-title">欢迎回来</text>
      <text class="form-sub">登录后继续记录你的生活</text>
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

    <image class="login-cat" src="/static/doodles/cat.png" mode="widthFix" />
    <image class="login-flower" src="/static/doodles/flower.png" mode="widthFix" />
  </view>
</template>

<style scoped>
.page { min-height: 100vh; padding: 100rpx 0 60rpx; }

/* 手账插画页眉 */
.auth-hero { position: relative; text-align: center; margin-bottom: 26rpx; padding: 0 40rpx; }
.blob { position: absolute; border-radius: 50%; filter: blur(2rpx); }
.blob-a { width: 240rpx; height: 240rpx; left: 50%; top: -80rpx; transform: translateX(-50%);
  background: radial-gradient(circle at 30% 30%, #DDE3FF, #EFE9FF 70%); }
.blob-b { width: 120rpx; height: 120rpx; right: 26rpx; top: 10rpx;
  background: radial-gradient(circle at 40% 40%, #FFF3D9, #FFEAC2 70%); opacity: .8; }
.doodle-coffee { left: 26rpx; top: 6rpx; width: 86rpx; transform: rotate(-6deg); }
.doodle-stars { right: 20rpx; top: -2rpx; width: 104rpx; transform: rotate(5deg); }
.brand { position: relative; display: block; font-size: 62rpx; font-weight: 800; color: #5A54B8;
  letter-spacing: 4rpx; text-shadow: 0 4rpx 0 rgba(255, 255, 255, .8); }
.brand-underline { display: block; width: 244rpx; height: 28rpx; margin: -2rpx auto 0; opacity: .75; }
.slogan { position: relative; display: block; margin-top: 10rpx; font-size: 28rpx; color: #8A90A8;
  letter-spacing: 2rpx; }
.deco-dots { display: block; margin-top: 14rpx; font-size: 25rpx; color: #C7B7F7; letter-spacing: 10rpx; }

/* 卡片 */
.form { position: relative; margin: 30rpx 40rpx 0; padding: 46rpx 36rpx 36rpx; }
.form-tape { position: absolute; top: -24rpx; left: 50%; width: 148rpx;
  transform: translateX(-50%) rotate(-3deg); }
.form-title { display: block; font-size: 38rpx; font-weight: 800; color: #3A3F58; letter-spacing: 1rpx; }
.form-sub { display: block; font-size: 26rpx; color: #A6AAC2; margin: 10rpx 0 34rpx; }
.form-item { margin-bottom: 28rpx; }
.label { display: block; font-size: 27rpx; color: #5A5F78; margin-bottom: 12rpx; letter-spacing: 1rpx; }
/* 手绘输入框：虚线描边 + 不规则圆角 */
.input { border: 2rpx dashed #C9BFF0; background: #FFFDF8;
  border-radius: 255rpx 20rpx 235rpx 18rpx / 18rpx 235rpx 20rpx 255rpx; }
.ph { color: #C3C7DA; }
.links { margin-top: 26rpx; text-align: center; }
.link { color: #6C7BF5; font-size: 27rpx; letter-spacing: 1rpx; }
.login-cat { position: fixed; right: 14rpx; bottom: 10rpx; width: 122rpx; opacity: .92; }
.login-flower { position: fixed; left: 8rpx; bottom: 6rpx; width: 92rpx; opacity: .9; }
</style>
