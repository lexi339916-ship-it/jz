<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { apiBudget, apiSetBudget, apiUpdateMe, apiProfileStats } from '../../api/index.js'
import store, { clearLogin } from '../../store/user.js'
import { BASE_URL } from '../../common/config.js'

const stats = ref({ total_bills: 0, total_days: 0, total_notes: 0, pending_todos: 0 })

// 服务器地址（真机调试时填写电脑局域网 IP）
const apiOpen = ref(false)
const apiBase = ref(uni.getStorageSync('api_base') || BASE_URL)
const apiBaseLabel = computed(() => String(apiBase.value).replace(/^https?:\/\//, ''))

function saveApiBase() {
  const value = String(apiBase.value || '').trim().replace(/\/+$/, '')
  if (!/^https?:\/\/.+/.test(value)) {
    uni.showToast({ title: '请输入 http:// 开头的地址', icon: 'none' })
    return
  }
  uni.setStorageSync('api_base', value)
  apiBase.value = value
  apiOpen.value = false
  uni.showToast({ title: '服务器地址已保存', icon: 'success' })
}

// 昵称编辑
const nickname = ref('')
const editingName = ref(false)

// 修改密码
const pwdOpen = ref(false)
const oldPwd = ref('')
const newPwd = ref('')
const confirmPwd = ref('')
const pwdSaving = ref(false)

// 月度预算
const budgetOpen = ref(false)
const budgetAmount = ref('')
const budgetInfo = ref(null)
const currentMonth = (() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
})()

// 关于
const aboutOpen = ref(false)

async function loadAll() {
  try {
    const [s, b] = await Promise.all([
      apiProfileStats(),
      apiBudget(currentMonth).catch(() => null),
    ])
    stats.value = s
    budgetInfo.value = b
    if (b && Number(b.amount) > 0) budgetAmount.value = String(Number(b.amount))
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

async function savePassword() {
  if (!oldPwd.value || !newPwd.value) {
    uni.showToast({ title: '请填写原密码和新密码', icon: 'none' }); return
  }
  if (newPwd.value.length < 6) {
    uni.showToast({ title: '新密码至少 6 位', icon: 'none' }); return
  }
  if (newPwd.value !== confirmPwd.value) {
    uni.showToast({ title: '两次输入的新密码不一致', icon: 'none' }); return
  }
  pwdSaving.value = true
  try {
    await apiUpdateMe({ old_password: oldPwd.value, new_password: newPwd.value })
    uni.showToast({ title: '密码修改成功', icon: 'success' })
    pwdOpen.value = false
    oldPwd.value = newPwd.value = confirmPwd.value = ''
  } catch (e) { /* 统一提示（原密码错误等 400 信息） */ } finally { pwdSaving.value = false }
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

function goBills() { uni.switchTab({ url: '/pages/bills/list' }) }
function goAi() { uni.switchTab({ url: '/pages/ai/assistant' }) }

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
  loadAll()
})
</script>

<template>
  <view class="page">
    <view class="title-row">
      <text class="page-title">我的</text>
      <image class="profile-sun" src="/static/doodles/sun.png" mode="widthFix" />
    </view>

    <!-- 用户卡 -->
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
        <view class="status-chip">
          <view class="status-dot" />
          <text>已记账 {{ stats.total_days }} 天 · 陪你记好每一笔</text>
        </view>
      </view>
    </view>

    <!-- 统计三卡 -->
    <view class="stats-row">
      <view class="stat-card">
        <text class="stat-num">{{ stats.total_bills }}</text>
        <text class="stat-label">记账条目</text>
      </view>
      <view class="stat-card">
        <text class="stat-num">{{ stats.total_days }}</text>
        <text class="stat-label">记账天数</text>
      </view>
      <view class="stat-card">
        <text class="stat-num">{{ stats.pending_todos }}</text>
        <text class="stat-label">待办事项</text>
      </view>
    </view>

    <!-- 账号与安全 -->
    <text class="group-title">账号与安全</text>
    <view class="group-card">
      <view class="menu-item" @click="pwdOpen = !pwdOpen">
        <view class="menu-icon" style="background: #EFF1FF"><image class="menu-img" src="/static/icons/act_lock.png" mode="widthFix" /></view>
        <view class="menu-main">
          <text class="menu-title">账号与安全</text>
          <text class="menu-sub">@{{ store.user?.username }} · 修改登录密码</text>
        </view>
        <text class="menu-arrow">{{ pwdOpen ? '⌄' : '›' }}</text>
      </view>
      <view v-if="pwdOpen" class="expand-form">
        <input class="input form-input" v-model="oldPwd" password placeholder="原密码" placeholder-class="ph" />
        <input class="input form-input" v-model="newPwd" password placeholder="新密码（至少 6 位）" placeholder-class="ph" />
        <input class="input form-input" v-model="confirmPwd" password placeholder="确认新密码" placeholder-class="ph" />
        <button class="btn btn-primary form-btn" :class="{ 'btn-disabled': pwdSaving }"
          :disabled="pwdSaving" @click="savePassword">
          {{ pwdSaving ? '保存中…' : '保存新密码' }}
        </button>
      </view>
    </view>

    <!-- 常用功能 -->
    <text class="group-title">常用功能</text>
    <view class="group-card">
      <view class="menu-item" @click="goBills">
        <view class="menu-icon" style="background: #E9F8F2"><image class="menu-img" src="/static/icons/act_chart.png" mode="widthFix" /></view>
        <view class="menu-main">
          <text class="menu-title">我的明细</text>
          <text class="menu-sub">查看和管理你的收支记录</text>
        </view>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="budgetOpen = !budgetOpen">
        <view class="menu-icon" style="background: #FFF6E7"><image class="menu-img" src="/static/icons/act_wallet.png" mode="widthFix" /></view>
        <view class="menu-main">
          <text class="menu-title">月度预算</text>
          <text class="menu-sub">
            <block v-if="budgetInfo && Number(budgetInfo.amount) > 0">
              {{ currentMonth }} 预算 ¥{{ Number(budgetInfo.amount).toFixed(0) }} · 已用 {{ Math.round(budgetInfo.usage_ratio * 100) }}%
            </block>
            <block v-else>设置每月支出预算，超支有提示</block>
          </text>
        </view>
        <text class="menu-arrow">{{ budgetOpen ? '⌄' : '›' }}</text>
      </view>
      <view v-if="budgetOpen" class="expand-form">
        <view class="budget-row">
          <input class="input budget-input" type="digit" v-model="budgetAmount"
            :placeholder="currentMonth + ' 月预算金额'" placeholder-class="ph" />
          <button class="btn btn-primary budget-save" @click="saveBudget">保存</button>
        </view>
        <view v-if="budgetInfo && Number(budgetInfo.amount) > 0" class="budget-status">
          已支出 ¥{{ Number(budgetInfo.spent).toFixed(2) }} · 剩余 ¥{{ Number(budgetInfo.remaining).toFixed(2) }}
        </view>
      </view>
      <view class="menu-item" @click="apiOpen = !apiOpen">
        <view class="menu-icon" style="background: #F6F4FB"><image class="menu-img" src="/static/icons/act_info.png" mode="widthFix" /></view>
        <view class="menu-main">
          <text class="menu-title">服务器地址</text>
          <text class="menu-sub">{{ apiBaseLabel }}（真机调试用）</text>
        </view>
        <text class="menu-arrow">{{ apiOpen ? '⌄' : '›' }}</text>
      </view>
      <view v-if="apiOpen" class="expand-form">
        <input class="input form-input" v-model="apiBase"
          placeholder="http://192.168.1.100:8000" placeholder-class="ph" />
        <button class="btn btn-primary form-btn" @click="saveApiBase">保存地址</button>
      </view>
      <view class="menu-item" @click="uni.navigateTo({ url: '/pages/goals/goals' })">
        <view class="menu-icon" style="background: #FFEDEE"><image class="menu-img" src="/static/icons/act_target.png" mode="widthFix" /></view>
        <view class="menu-main">
          <text class="menu-title">储蓄目标与挑战</text>
          <text class="menu-sub">攒钱目标 · 生活挑战 · 进度追踪</text>
        </view>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="goAi">
        <view class="menu-icon" style="background: #F4F0FF"><image class="menu-img" src="/static/icons/act_sparkle.png" mode="widthFix" /></view>
        <view class="menu-main">
          <text class="menu-title">AI 助手</text>
          <text class="menu-sub">一句话记账 · 任务提取 · 问账本</text>
        </view>
        <text class="menu-arrow">›</text>
      </view>
    </view>

    <!-- 关于 -->
    <text class="group-title">关于我们</text>
    <view class="group-card">
      <view class="menu-item" @click="aboutOpen = !aboutOpen">
        <view class="menu-icon" style="background: #F6F4FB"><image class="menu-img" src="/static/icons/act_info.png" mode="widthFix" /></view>
        <view class="menu-main">
          <text class="menu-title">关于系统</text>
          <text class="menu-sub">智能记账与生活便签一体化管理系统 v1.0</text>
        </view>
        <text class="menu-arrow">{{ aboutOpen ? '⌄' : '›' }}</text>
      </view>
      <view v-if="aboutOpen" class="expand-form">
        <text class="about-text">
          课程设计项目：前端 uni-app + Vue3，后端 FastAPI + SQLAlchemy + MySQL。
          AI 能力：自然语言记账、任务提取、问账本（工具调用）、月度总结与洞察。
          所有 AI 结果均需人工确认后才会保存，可随时手动录入。
        </text>
      </view>
    </view>

    <view class="logout-wrap">
      <button class="btn btn-danger" @click="logout">退出登录</button>
    </view>
  </view>
</template>

<style scoped>
.page { padding: 24rpx 24rpx 60rpx; }
.title-row { display: flex; justify-content: space-between; align-items: center; padding-right: 16rpx; }
.title-row .page-title { margin-bottom: 14rpx; }
.profile-sun { width: 88rpx; height: 88rpx; opacity: .9; transform: rotate(8deg); margin-top: -4rpx; }
.page-title { display: block; font-size: 48rpx; font-weight: 800; margin: 10rpx 8rpx 26rpx; }

/* 用户卡 */
.user-card { display: flex; align-items: center; background: #FFFDF8; border-radius: 32rpx;
  padding: 34rpx 30rpx; box-shadow: 0 6rpx 24rpx rgba(124, 139, 255, .10); }
.avatar { width: 118rpx; height: 118rpx; border-radius: 36rpx; flex-shrink: 0;
  background: linear-gradient(135deg, #6C7BF5, #A8B2FF); color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 52rpx; font-weight: 800; }
.user-info { margin-left: 26rpx; flex: 1; min-width: 0; }
.name-row { display: flex; align-items: center; gap: 16rpx; }
.name { font-size: 38rpx; font-weight: 700; }
.edit-hint { font-size: 25rpx; color: #6C7BF5; background: #EFF1FF; border-radius: 20rpx; padding: 4rpx 16rpx; }
.name-edit { display: flex; align-items: center; gap: 16rpx; }
.name-input { height: 64rpx; background: #F6F4FB; border-radius: 12rpx; padding: 0 20rpx;
  font-size: 32rpx; width: 300rpx; }
.save-btn { font-size: 28rpx; font-weight: 600; color: #6C7BF5; }
.username { display: block; font-size: 26rpx; color: #A6AAC2; margin-top: 8rpx; }
.status-chip { display: inline-flex; align-items: center; gap: 10rpx; margin-top: 16rpx;
  background: #E9F8F2; color: #33B98E; border-radius: 28rpx; padding: 8rpx 20rpx; font-size: 25rpx; }
.status-dot { width: 12rpx; height: 12rpx; border-radius: 6rpx; background: #45C39A; }

/* 统计三卡 */
.stats-row { display: flex; gap: 18rpx; margin-top: 20rpx; }
.stat-card { flex: 1; background: #FFFDF8; border-radius: 26rpx; padding: 26rpx 0;
  text-align: center; box-shadow: 0 6rpx 24rpx rgba(124, 139, 255, .10); }
.stat-num { display: block; font-size: 42rpx; font-weight: 800; color: #6C7BF5; }
.stat-label { display: block; font-size: 25rpx; color: #A6AAC2; margin-top: 8rpx; }

/* 分组菜单 */
.group-title { display: block; font-size: 28rpx; color: #8A90A8; font-weight: 600;
  margin: 34rpx 8rpx 14rpx; }
.group-card { background: #FFFDF8; border-radius: 28rpx; overflow: hidden;
  box-shadow: 0 6rpx 24rpx rgba(124, 139, 255, .10); }
.menu-item { display: flex; align-items: center; padding: 28rpx 26rpx;
  border-bottom: 1rpx solid #F4F2FA; }
.menu-item:last-child { border-bottom: none; }
.menu-item:active { background: #FBFAFE; }
.menu-icon { width: 76rpx; height: 76rpx; border-radius: 26rpx; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; margin-right: 22rpx; }
.menu-img { width: 56rpx; height: 56rpx; }
.menu-main { flex: 1; min-width: 0; }
.menu-title { display: block; font-size: 31rpx; font-weight: 600; }
.menu-sub { display: block; font-size: 25rpx; color: #A6AAC2; margin-top: 8rpx; }
.menu-arrow { font-size: 36rpx; color: #D3D7E7; padding-left: 12rpx; }

/* 展开表单 */
.expand-form { padding: 8rpx 26rpx 30rpx; background: #FBFAFE; border-bottom: 1rpx solid #F4F2FA; }
.form-input { margin-bottom: 18rpx; background: #FFFDF8; }
.ph { color: #C3C7DA; }
.form-btn { height: 80rpx; font-size: 30rpx; }
.budget-row { display: flex; gap: 18rpx; }
.budget-input { flex: 1; background: #FFFDF8; }
.budget-save { margin: 0; width: 170rpx; height: 88rpx; font-size: 30rpx; }
.budget-status { margin-top: 18rpx; font-size: 26rpx; color: #5A5F78; }
.about-text { display: block; font-size: 26rpx; color: #8A90A8; line-height: 1.9; }

.logout-wrap { margin-top: 40rpx; }
</style>
