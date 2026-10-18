<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { apiBudget, apiSetBudget, apiUpdateMe } from '../../api/index.js'
import store, { clearLogin } from '../../store/user.js'

const budgetAmount = ref('')
const budgetInfo = ref(null)
const nickname = ref('')
const editingName = ref(false)
const currentMonth = (() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
})()

async function loadBudget() {
  try {
    budgetInfo.value = await apiBudget(currentMonth)
    if (budgetInfo.value && Number(budgetInfo.value.amount) > 0) {
      budgetAmount.value = String(Number(budgetInfo.value.amount))
    }
  } catch (e) { /* 统一提示 */ }
}

async function saveBudget() {
  const amount = Number(budgetAmount.value)
  if (!amount || amount <= 0) {
    uni.showToast({ title: '请输入正确的预算金额', icon: 'none' }); return
  }
  try {
    budgetInfo.value = await apiSetBudget({ month: currentMonth, amount: amount.toFixed(2) })
    uni.showToast({ title: '预算已保存', icon: 'success' })
  } catch (e) { /* 统一提示 */ }
}

async function saveNickname() {
  if (!nickname.value.trim()) { editingName.value = false; return }
  try {
    const user = await apiUpdateMe({ nickname: nickname.value.trim() })
    store.user = user
    uni.setStorageSync('user', user)
    uni.showToast({ title: '昵称已更新', icon: 'success' })
  } catch (e) { /* 统一提示 */ } finally { editingName.value = false }
}

function logout() {
  uni.showModal({
    title: '退出登录',
    content: '确定退出当前账号吗？',
    success: (res) => {
      if (res.confirm) {
        clearLogin()
        uni.reLaunch({ url: '/pages/login/login' })
      }
    },
  })
}

onShow(() => {
  nickname.value = store.user?.nickname || store.user?.username || ''
  loadBudget()
})
</script>

<template>
  <view class="page">
    <!-- 用户信息 -->
    <view class="user-card">
      <view class="avatar">{{ (nickname || 'U').slice(0, 1) }}</view>
      <view class="user-info">
        <view v-if="!editingName" class="name-row" @click="editingName = true">
          <text class="name">{{ nickname }}</text>
          <text class="edit-hint">修改</text>
        </view>
        <view v-else class="name-edit">
          <input class="name-input" v-model="nickname" maxlength="30" />
          <text class="save-btn" @click="saveNickname">保存</text>
        </view>
        <text class="username">@{{ store.user?.username }}</text>
      </view>
    </view>

    <!-- 月度预算 -->
    <view class="card">
      <text class="block-title">{{ currentMonth }} 月预算</text>
      <view class="budget-row">
        <input class="input budget-input" type="digit" v-model="budgetAmount"
          placeholder="设置本月支出预算" placeholder-class="ph" />
        <button class="btn btn-primary save-budget" @click="saveBudget">保存</button>
      </view>
      <view v-if="budgetInfo && Number(budgetInfo.amount) > 0" class="budget-status">
        <text>已支出 ¥{{ Number(budgetInfo.spent).toFixed(2) }}，
          剩余 ¥{{ Number(budgetInfo.remaining).toFixed(2) }}
          （{{ Math.round(budgetInfo.usage_ratio * 100) }}%）
        </text>
      </view>
    </view>

    <!-- 功能说明 -->
    <view class="card">
      <text class="block-title">关于系统</text>
      <text class="about">
        智能记账与生活便签一体化管理系统（课程设计）
        前端：uni-app + Vue3　后端：FastAPI + SQLAlchemy + MySQL
        AI 能力：自然语言记账草稿、便签整理、月度消费总结
        所有 AI 结果均需人工确认后才会保存，可随时手动记账
      </text>
    </view>

    <view class="card">
      <button class="btn btn-danger" @click="logout">退出登录</button>
    </view>
  </view>
</template>

<style scoped>
.page { padding-bottom: 60rpx; }
.user-card { display: flex; align-items: center; margin: 24rpx; padding: 40rpx 30rpx;
  border-radius: 28rpx; background: linear-gradient(135deg, #2f6fed, #63a7ff); color: #fff; }
.avatar { width: 110rpx; height: 110rpx; border-radius: 55rpx; background: rgba(255, 255, 255, .25);
  display: flex; align-items: center; justify-content: center; font-size: 48rpx; font-weight: 800; }
.user-info { margin-left: 28rpx; flex: 1; }
.name-row { display: flex; align-items: center; gap: 16rpx; }
.name { font-size: 36rpx; font-weight: 700; }
.edit-hint { font-size: 22rpx; opacity: .85; background: rgba(255, 255, 255, .2); border-radius: 16rpx; padding: 4rpx 16rpx; }
.name-edit { display: flex; align-items: center; gap: 16rpx; }
.name-input { height: 64rpx; background: rgba(255, 255, 255, .25); border-radius: 12rpx;
  padding: 0 20rpx; font-size: 30rpx; color: #fff; width: 300rpx; }
.save-btn { font-size: 26rpx; font-weight: 600; }
.username { display: block; font-size: 24rpx; opacity: .85; margin-top: 10rpx; }

.block-title { display: block; font-size: 28rpx; font-weight: 700; margin-bottom: 20rpx; }
.budget-row { display: flex; gap: 20rpx; }
.budget-input { flex: 1; background: #f5f7fb; }
.ph { color: #b6bdcc; }
.save-budget { margin: 0; width: 180rpx; height: 88rpx; font-size: 28rpx; }
.budget-status { margin-top: 20rpx; font-size: 24rpx; color: #4a5568;
  background: #f5f7fb; border-radius: 12rpx; padding: 16rpx 20rpx; }

.about { display: block; font-size: 24rpx; color: #7c8595; line-height: 1.9; }
</style>
