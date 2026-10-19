<script setup>
import { ref, computed } from 'vue'
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app'
import { apiMonthlyStats, apiBudget, apiBills, apiNotes, apiInsight } from '../../api/index.js'
import { categoryMeta } from '../../common/category-icons.js'
import store from '../../store/user.js'

const month = ref('')
const stats = ref({ income: '0', expense: '0', net: '0', count: 0, days: [] })
const budget = ref(null)
const recentBills = ref([])
const todos = ref([])
const pendingCount = ref(0)
const todayDueCount = ref(0)   // 今天到期 + 已逾期数量

// AI 洞察卡状态
const insightText = ref('')
const insightLoading = ref(false)
const insightNotice = ref('')

const netColor = computed(() =>
  (Number(stats.value.net) >= 0 ? '#b8ffdf' : '#ffd9d9'))

function currentMonth() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function shiftMonth(m, delta) {
  const [y, mo] = m.split('-').map(Number)
  const d = new Date(y, mo - 1 + delta, 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

// 近 7 日支出迷你趋势（取自月度按日明细）
const weekBars = computed(() => {
  if (!stats.value.days || !stats.value.days.length) return []
  const days = stats.value.days
  const isCurrent = month.value === currentMonth()
  const cutoff = isCurrent ? new Date().getDate() : days.length
  const slice = days.slice(Math.max(0, cutoff - 7), cutoff)
  const max = Math.max(...slice.map(d => Number(d.expense)), 1)
  return slice.map(d => {
    const amount = Number(d.expense)
    return {
      label: String(d.date).slice(8, 10),
      pct: amount > 0 ? Math.max(14, Math.round(amount / max * 100)) : 6,
      has: amount > 0,
    }
  })
})

async function loadInsight(refresh = false) {
  insightLoading.value = true
  try {
    const res = await apiInsight(refresh)
    insightText.value = res.text
    insightNotice.value = res.notice || ''
  } catch (e) {
    insightText.value = ''
  } finally {
    insightLoading.value = false
  }
}

async function loadAll() {
  if (!store.token) return
  try {
    const [s, b, bills, notes, todayNotes] = await Promise.all([
      apiMonthlyStats(month.value),
      apiBudget(month.value).catch(() => null),
      apiBills({ month: month.value, page: 1, page_size: 5 }),
      apiNotes({ note_type: 'todo', status: 'open', page: 1, page_size: 3 }),
      apiNotes({ view: 'today', page: 1, page_size: 1 }),
    ])
    stats.value = s
    budget.value = b
    recentBills.value = bills.items
    todos.value = notes.items
    pendingCount.value = notes.total
    todayDueCount.value = todayNotes.total
  } catch (e) { /* 统一提示已处理 */ }
}

function prevMonth() { month.value = shiftMonth(month.value, -1); loadAll() }
function nextMonth() { month.value = shiftMonth(month.value, 1); loadAll() }

onShow(() => {
  if (!store.token) {
    uni.reLaunch({ url: '/pages/login/login' })
    return
  }
  if (!month.value) month.value = currentMonth()
  loadAll()
  loadInsight(false)
})

onPullDownRefresh(() => {
  Promise.all([loadAll(), loadInsight(false)])
    .finally(() => uni.stopPullDownRefresh())
})
</script>

<template>
  <view class="page">
    <!-- 月度收支总览 -->
    <view class="hero">
      <view class="month-nav">
        <text class="arrow" @click="prevMonth">‹</text>
        <text class="month">{{ month.slice(0, 4) }}年{{ Number(month.slice(5)) }}月</text>
        <text class="arrow" @click="nextMonth">›</text>
      </view>
      <text class="net-label">本月结余</text>
      <text class="net-num" :style="{ color: netColor }">
        {{ Number(stats.net) >= 0 ? '' : '-' }}¥{{ Math.abs(Number(stats.net)).toFixed(2) }}
      </text>
      <view class="io-row">
        <text class="io-item">收入 ¥{{ Number(stats.income).toFixed(2) }}</text>
        <text class="io-divider">|</text>
        <text class="io-item">支出 ¥{{ Number(stats.expense).toFixed(2) }}</text>
      </view>
      <!-- 近 7 日支出趋势 -->
      <view class="trend" v-if="weekBars.length">
        <view class="trend-col" v-for="(b, i) in weekBars" :key="i">
          <view class="trend-bar" :class="{ 'trend-has': b.has }" :style="{ height: b.pct + '%' }" />
          <text class="trend-label">{{ b.label }}</text>
        </view>
      </view>
    </view>

    <!-- AI 洞察卡 -->
    <view class="card insight-card">
      <view class="insight-head">
        <view class="insight-badge">✨ AI 洞察</view>
        <text class="insight-refresh" @click="loadInsight(true)">刷新</text>
      </view>
      <view v-if="insightLoading" class="insight-loading">
        <text class="dot" /><text class="dot" /><text class="dot" />
      </view>
      <text v-else class="insight-text">{{ insightText || '继续记账，AI 会给出越来越多有用的提示' }}</text>
      <text v-if="insightNotice" class="insight-notice">{{ insightNotice }}</text>
    </view>

    <!-- 预算使用 -->
    <view class="card" v-if="budget && Number(budget.amount) > 0">
      <view class="row-between">
        <text class="budget-title">月度预算</text>
        <text class="budget-nums">
          ¥{{ Number(budget.spent).toFixed(2) }} / ¥{{ Number(budget.amount).toFixed(2) }}
        </text>
      </view>
      <view class="bar-track">
        <view class="bar-fill"
          :style="{ width: Math.min(budget.usage_ratio * 100, 100) + '%',
                    background: budget.usage_ratio > 0.9 ? '#e5484d' : '#2f6fed' }" />
      </view>
      <text class="budget-hint">
        {{ budget.usage_ratio >= 1 ? '预算已超支，注意控制支出' : `已使用 ${Math.round(budget.usage_ratio * 100)}%` }}
      </text>
    </view>

    <!-- 快捷入口 -->
    <view class="quick">
      <view class="quick-item" @click="uni.navigateTo({ url: '/pages/bills/edit' })">
        <text class="quick-icon q-blue">✏️</text><text>记一笔</text>
      </view>
      <view class="quick-item" @click="uni.switchTab({ url: '/pages/ai/assistant' })">
        <text class="quick-icon q-green">✨</text><text>智能记账</text>
      </view>
      <view class="quick-item" @click="uni.navigateTo({ url: '/pages/notes/edit' })">
        <text class="quick-icon q-orange">📝</text><text>写便签</text>
      </view>
      <view class="quick-item" @click="uni.navigateTo({ url: '/pages/statistics/statistics' })">
        <text class="quick-icon q-purple">📊</text><text>看统计</text>
      </view>
    </view>

    <!-- 最近账单 -->
    <view class="card">
      <view class="section-title">
        最近账单
        <text class="section-more" @click="uni.switchTab({ url: '/pages/bills/list' })">全部 ›</text>
      </view>
      <view v-if="recentBills.length === 0" class="empty">本月还没有账单，记一笔吧</view>
      <view class="bill-row" v-for="b in recentBills" :key="b.id"
        @click="uni.navigateTo({ url: '/pages/bills/edit?id=' + b.id })">
        <view class="cat-icon" :style="{ background: categoryMeta(b.category).color + '22' }">
          {{ categoryMeta(b.category).icon }}
        </view>
        <view class="bill-left">
          <text class="bill-cat">{{ b.category }}</text>
          <text class="bill-remark">{{ b.remark || (b.type === 'income' ? '收入' : '支出') }}</text>
        </view>
        <text class="bill-amount" :class="b.type === 'income' ? 'amount-in' : 'amount-out'">
          {{ b.type === 'income' ? '+' : '-' }}{{ Number(b.amount).toFixed(2) }}
        </text>
      </view>
    </view>

    <!-- 待办摘要 -->
    <view class="card">
      <view class="section-title">
        待办事项（{{ pendingCount }}）
        <text class="section-more" @click="uni.switchTab({ url: '/pages/notes/list' })">全部 ›</text>
      </view>
      <view v-if="todayDueCount > 0" class="overdue-tip" @click="uni.switchTab({ url: '/pages/notes/list' })">
        ⏰ 今天/已逾期 <text class="overdue-num">{{ todayDueCount }}</text> 项，记得处理
      </view>
      <view v-if="todos.length === 0" class="empty">暂无待办，安排得井井有条</view>
      <view class="todo-row" v-for="n in todos" :key="n.id">
        <view class="todo-dot" />
        <text class="todo-title">{{ n.title }}</text>
        <text class="todo-due" v-if="n.due_at">截止 {{ String(n.due_at).slice(5, 10) }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page { padding-bottom: 40rpx; }

/* 渐变总览卡 */
.hero { margin: 20rpx 24rpx; padding: 34rpx 30rpx 26rpx; border-radius: 30rpx;
  background: linear-gradient(150deg, #2b5fd9 0%, #4a86f7 55%, #6fb0ff 100%);
  color: #fff; box-shadow: 0 14rpx 36rpx rgba(47, 111, 237, .35); }
.month-nav { display: flex; align-items: center; justify-content: center; gap: 30rpx; }
.arrow { font-size: 44rpx; opacity: .9; padding: 0 20rpx; }
.month { font-size: 28rpx; font-weight: 600; opacity: .95; }
.net-label { display: block; text-align: center; font-size: 24rpx; opacity: .8; margin-top: 26rpx; }
.net-num { display: block; text-align: center; font-size: 72rpx; font-weight: 800;
  letter-spacing: 1rpx; margin: 8rpx 0 4rpx; }
.io-row { display: flex; justify-content: center; align-items: center; gap: 20rpx; }
.io-item { font-size: 24rpx; opacity: .92; }
.io-divider { opacity: .4; }

/* 近 7 日趋势 */
.trend { display: flex; align-items: flex-end; gap: 10rpx; height: 110rpx;
  margin-top: 28rpx; padding-top: 6rpx; border-top: 1rpx solid rgba(255,255,255,.22); }
.trend-col { flex: 1; height: 100%; display: flex; flex-direction: column;
  align-items: center; justify-content: flex-end; }
.trend-bar { width: 66%; border-radius: 6rpx 6rpx 2rpx 2rpx;
  background: rgba(255,255,255,.28); }
.trend-has { background: rgba(255,255,255,.85); }
.trend-label { font-size: 18rpx; opacity: .75; margin-top: 8rpx; }

/* AI 洞察 */
.insight-card { border: 2rpx solid #e3ebfd; background: linear-gradient(180deg, #f6f9ff, #ffffff); }
.insight-head { display: flex; justify-content: space-between; align-items: center; }
.insight-badge { font-size: 24rpx; font-weight: 700; color: #2f6fed; }
.insight-refresh { font-size: 22rpx; color: #7c8595; padding: 4rpx 12rpx; }
.insight-text { display: block; font-size: 26rpx; line-height: 1.7; color: #33415c; margin-top: 14rpx; }
.insight-notice { display: block; font-size: 20rpx; color: #9aa3b5; margin-top: 8rpx; }
.insight-loading { display: flex; gap: 10rpx; padding: 18rpx 0 6rpx; }
.dot { width: 14rpx; height: 14rpx; border-radius: 7rpx; background: #a9c4f7;
  animation: blink 1.2s infinite ease-in-out; }
.dot:nth-child(2) { animation-delay: .2s; }
.dot:nth-child(3) { animation-delay: .4s; }
@keyframes blink { 0%, 80%, 100% { opacity: .25; } 40% { opacity: 1; } }

/* 预算 */
.row-between { display: flex; justify-content: space-between; align-items: center; }
.budget-title { font-size: 28rpx; font-weight: 700; }
.budget-nums { font-size: 24rpx; color: #4a5568; }
.bar-track { height: 16rpx; background: #edf0f5; border-radius: 8rpx; margin: 20rpx 0 12rpx; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 8rpx; transition: width .3s; }
.budget-hint { font-size: 22rpx; color: #7c8595; }

/* 快捷入口 */
.quick { display: flex; gap: 14rpx; margin: 6rpx 24rpx 0; }
.quick-item { flex: 1; background: #fff; border-radius: 20rpx; padding: 24rpx 0;
  display: flex; flex-direction: column; align-items: center; gap: 10rpx;
  font-size: 23rpx; color: #4a5568; box-shadow: 0 6rpx 24rpx rgba(40, 70, 120, .06); }
.quick-item:active { opacity: .8; }
.quick-icon { width: 76rpx; height: 76rpx; border-radius: 38rpx;
  display: flex; align-items: center; justify-content: center; font-size: 36rpx; }
.q-blue { background: #eef3ff; } .q-green { background: #e8f8f2; }
.q-orange { background: #fdf6ec; } .q-purple { background: #f3f0ff; }

/* 账单行 */
.bill-row { display: flex; align-items: center; padding: 20rpx 0; border-bottom: 1rpx solid #f0f2f6; }
.bill-row:last-child { border-bottom: none; }
.cat-icon { width: 76rpx; height: 76rpx; border-radius: 22rpx; font-size: 36rpx;
  display: flex; align-items: center; justify-content: center; margin-right: 22rpx; }
.bill-left { flex: 1; display: flex; flex-direction: column; gap: 6rpx; }
.bill-cat { font-size: 28rpx; font-weight: 600; }
.bill-remark { font-size: 22rpx; color: #9aa3b5; max-width: 380rpx; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap; }
.bill-amount { font-size: 30rpx; font-weight: 700; }
.amount-in { color: #16b07a; } .amount-out { color: #263246; }

/* 待办 */
.overdue-tip { margin: 4rpx 0 14rpx; background: #fdf2f2; color: #c53030; border-radius: 14rpx;
  padding: 16rpx 22rpx; font-size: 24rpx; }
.overdue-num { font-weight: 800; }
.todo-row { display: flex; align-items: center; gap: 16rpx; padding: 20rpx 4rpx; border-bottom: 1rpx solid #f0f2f6; }
.todo-row:last-child { border-bottom: none; }
.todo-dot { width: 16rpx; height: 16rpx; border-radius: 8rpx; background: #f59f0b; flex-shrink: 0; }
.todo-title { flex: 1; font-size: 26rpx; }
.todo-due { font-size: 22rpx; color: #9aa3b5; }
</style>
