<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import {
  apiGoals, apiAddGoal, apiDepositGoal, apiDeleteGoal,
  apiChallenges, apiAddChallenge, apiDeleteChallenge, apiCategories,
} from '../../api/index.js'

// 储蓄目标
const goals = ref([])
const goalFormOpen = ref(false)
const goalName = ref('')
const goalTarget = ref('')
const depositOpenId = ref(null)
const depositAmount = ref('')

// 生活挑战
const challenges = ref([])
const categories = ref([])
const challengeFormOpen = ref(false)
const chName = ref('')
const chCategory = ref('')
const chPeriod = ref(7)
const chTarget = ref('')

const STATUS_META = {
  on_track: { label: '进行中', cls: 'st-ok' },
  over: { label: '已超上限', cls: 'st-over' },
  finished: { label: '已达成', cls: 'st-done' },
  failed: { label: '未达成', cls: 'st-fail' },
}

async function load() {
  try {
    const [g, c, cats] = await Promise.all([
      apiGoals(), apiChallenges(), apiCategories(),
    ])
    goals.value = g
    challenges.value = c
    categories.value = cats.items.filter(c => c.type === 'expense')
    if (!chCategory.value && categories.value.length) {
      chCategory.value = categories.value[0].name
    }
  } catch (e) { /* 统一提示 */ }
}

async function createGoal() {
  if (!goalName.value.trim() || !Number(goalTarget.value)) {
    uni.showToast({ title: '请填写名称和目标金额', icon: 'none' }); return
  }
  try {
    await apiAddGoal({ name: goalName.value.trim(), target_amount: Number(goalTarget.value).toFixed(2) })
    goalFormOpen.value = false
    goalName.value = ''
    goalTarget.value = ''
    uni.showToast({ title: '目标已创建', icon: 'success' })
    load()
  } catch (e) { /* 统一提示 */ }
}

function toggleDeposit(id) {
  depositOpenId.value = depositOpenId.value === id ? null : id
  depositAmount.value = ''
}

async function doDeposit(goal) {
  const amount = Number(depositAmount.value)
  if (!amount || amount <= 0) {
    uni.showToast({ title: '请输入存入金额', icon: 'none' }); return
  }
  try {
    await apiDepositGoal(goal.id, amount.toFixed(2))
    depositOpenId.value = null
    depositAmount.value = ''
    uni.showToast({ title: '已存入', icon: 'success' })
    load()
  } catch (e) { /* 统一提示 */ }
}

async function removeGoal(g) {
  uni.showModal({
    title: '删除目标',
    content: `确定删除「${g.name}」吗？`,
    success: async (res) => {
      if (res.confirm) { await apiDeleteGoal(g.id); load() }
    },
  })
}

async function createChallenge() {
  if (!chName.value.trim() || !Number(chTarget.value)) {
    uni.showToast({ title: '请填写挑战名称和支出上限', icon: 'none' }); return
  }
  if (!chCategory.value) {
    uni.showToast({ title: '请选择分类', icon: 'none' }); return
  }
  try {
    await apiAddChallenge({
      name: chName.value.trim(),
      category: chCategory.value,
      period_days: chPeriod.value,
      target_amount: Number(chTarget.value).toFixed(2),
    })
    challengeFormOpen.value = false
    chName.value = ''
    chTarget.value = ''
    uni.showToast({ title: '挑战已创建', icon: 'success' })
    load()
  } catch (e) { /* 统一提示 */ }
}

async function removeChallenge(c) {
  uni.showModal({
    title: '删除挑战',
    content: `确定删除「${c.name}」吗？`,
    success: async (res) => {
      if (res.confirm) { await apiDeleteChallenge(c.id); load() }
    },
  })
}

function pct(ratio) { return Math.min(Math.round(ratio * 100), 100) }
function periodText(c) { return c.period_days === 7 ? '本周' : '本月' }

onShow(load)
</script>

<template>
  <view class="page">
    <!-- 储蓄目标 -->
    <view class="section-head">
      <view class="section-title"><image class="sec-icon" src="/static/icons/act_target.png" mode="widthFix" /><text>储蓄目标</text></view>
      <text class="add-btn" @click="goalFormOpen = !goalFormOpen">＋ 新建目标</text>
    </view>
    <view v-if="goalFormOpen" class="card form-card">
      <input class="input form-input" v-model="goalName" maxlength="50" placeholder="目标名称，如：旅行基金" placeholder-class="ph" />
      <input class="input form-input" type="digit" v-model="goalTarget" placeholder="目标金额（元）" placeholder-class="ph" />
      <button class="btn btn-primary" @click="createGoal">创建目标</button>
    </view>

    <view v-if="!goals.length && !goalFormOpen" class="empty">还没有储蓄目标，建一个开始攒钱吧</view>
    <view class="card goal-card" v-for="g in goals" :key="g.id">
      <view class="row-between">
        <text class="goal-name">{{ g.name }}</text>
        <text class="del" @click="removeGoal(g)">×</text>
      </view>
      <view class="goal-nums">
        <text class="goal-saved">¥{{ Number(g.saved_amount).toFixed(2) }}</text>
        <text class="goal-target">/ ¥{{ Number(g.target_amount).toFixed(2) }}</text>
        <text class="goal-percent">{{ pct(g.progress_ratio) }}%</text>
      </view>
      <view class="bar-track">
        <view class="bar-fill" :style="{ width: pct(g.progress_ratio) + '%' }" />
      </view>
      <view class="goal-meta">
        <text>还差 ¥{{ Number(g.remaining).toFixed(2) }}</text>
        <text v-if="g.estimated_finish">预计完成：{{ g.estimated_finish }}</text>
        <text v-else class="warn">月均结余为负，先控制支出才能估算完成时间</text>
      </view>
      <view class="deposit-row">
        <button class="mini-btn" @click="toggleDeposit(g.id)">存入一笔</button>
      </view>
      <view v-if="depositOpenId === g.id" class="deposit-form">
        <input class="input deposit-input" type="digit" v-model="depositAmount"
          placeholder="存入金额" placeholder-class="ph" />
        <button class="btn btn-primary deposit-btn" @click="doDeposit(g)">确认存入</button>
      </view>
    </view>

    <!-- 生活挑战 -->
    <view class="section-head">
      <view class="section-title"><image class="sec-icon" src="/static/icons/act_sparkle.png" mode="widthFix" /><text>生活挑战</text></view>
      <text class="add-btn" @click="challengeFormOpen = !challengeFormOpen">＋ 新建挑战</text>
    </view>
    <view v-if="challengeFormOpen" class="card form-card">
      <input class="input form-input" v-model="chName" maxlength="60"
        placeholder="挑战名称，如：本周减少外卖支出" placeholder-class="ph" />
      <view class="ch-row">
        <picker mode="selector" :range="categories" range-key="name"
          @change="chCategory = categories[$event.detail.value]?.name || chCategory">
          <view class="picker-value">分类：{{ chCategory || '选择' }} ▾</view>
        </picker>
        <view class="period-tabs">
          <text :class="['p-tab', chPeriod === 7 && 'p-active']" @click="chPeriod = 7">本周</text>
          <text :class="['p-tab', chPeriod === 30 && 'p-active']" @click="chPeriod = 30">本月</text>
        </view>
      </view>
      <input class="input form-input" type="digit" v-model="chTarget"
        placeholder="该分类支出上限（元）" placeholder-class="ph" />
      <button class="btn btn-primary" @click="createChallenge">创建挑战</button>
    </view>

    <view v-if="!challenges.length && !challengeFormOpen" class="empty">还没有挑战，设一个试试</view>
    <view class="card challenge-card" v-for="c in challenges" :key="c.id">
      <view class="row-between">
        <view class="ch-title-row">
          <text class="ch-name">{{ c.name }}</text>
          <text class="st-tag" :class="STATUS_META[c.status].cls">{{ STATUS_META[c.status].label }}</text>
        </view>
        <text class="del" @click="removeChallenge(c)">×</text>
      </view>
      <text class="ch-sub">{{ periodText(c) }} · {{ c.category }} · 上限 ¥{{ Number(c.target_amount).toFixed(2) }} · 剩 {{ c.days_left }} 天</text>
      <view class="goal-nums small">
        <text class="goal-saved">¥{{ Number(c.current_spend).toFixed(2) }}</text>
        <text class="goal-target">已花 / ¥{{ Number(c.target_amount).toFixed(2) }}</text>
        <text class="goal-percent" :class="{ 'over-text': c.status === 'over' }">{{ pct(c.progress_ratio) }}%</text>
      </view>
      <view class="bar-track">
        <view class="bar-fill" :class="{ 'bar-over': c.status === 'over' }"
          :style="{ width: pct(c.progress_ratio) + '%' }" />
      </view>
      <view class="goal-meta" v-if="c.previous_spend !== null">
        <text>上期支出 ¥{{ Number(c.previous_spend).toFixed(2) }}
          <text v-if="c.change_pct !== null" :class="c.change_pct > 0 ? 'up-text' : 'down-text'">
            （{{ c.change_pct > 0 ? '+' : '' }}{{ c.change_pct }}%）
          </text>
        </text>
      </view>
      <view class="goal-meta" v-else>
        <text class="muted">上期无该分类支出记录，暂无法对比</text>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page { padding: 24rpx 24rpx 60rpx; }
.section-head { display: flex; justify-content: space-between; align-items: center; margin: 26rpx 8rpx 14rpx; }
.section-title { font-size: 30rpx; font-weight: 700; display: flex; align-items: center; gap: 10rpx; }
.sec-icon { width: 40rpx; height: 40rpx; }
.add-btn { font-size: 24rpx; color: #6C7BF5; background: #EFF1FF; border-radius: 26rpx; padding: 8rpx 20rpx; }
.form-card { margin: 0 0 16rpx; }
.form-input { margin-bottom: 18rpx; }
.ph { color: #C3C7DA; }
.btn-primary { height: 80rpx; font-size: 28rpx; }

.goal-card { margin: 0 0 16rpx; }
.row-between { display: flex; justify-content: space-between; align-items: center; }
.goal-name { font-size: 29rpx; font-weight: 700; }
.del { color: #D3D7E7; font-size: 40rpx; padding: 0 6rpx; }
.goal-nums { display: flex; align-items: baseline; gap: 8rpx; margin: 18rpx 0 14rpx; }
.goal-saved { font-size: 36rpx; font-weight: 800; color: #6C7BF5; }
.goal-target { font-size: 24rpx; color: #A6AAC2; }
.goal-percent { margin-left: auto; font-size: 24rpx; color: #6C7BF5; font-weight: 600; }
.goal-nums.small .goal-saved { font-size: 30rpx; }
.bar-track { height: 14rpx; background: #EFEDF7; border-radius: 7rpx; overflow: hidden; }
.bar-fill { height: 100%; background: linear-gradient(90deg, #6C7BF5, #9DA9FF); border-radius: 7rpx; transition: width .3s; }
.bar-over { background: #F27E7E; }
.goal-meta { display: flex; flex-direction: column; gap: 6rpx; margin-top: 14rpx; font-size: 22rpx; color: #8A90A8; }
.warn { color: #D98A32; }
.muted { color: #A6AAC2; }
.over-text { color: #F27E7E; }
.up-text { color: #F27E7E; }
.down-text { color: #45C39A; }
.deposit-row { display: flex; justify-content: flex-end; margin-top: 12rpx; }
.mini-btn { margin: 0; font-size: 23rpx; color: #6C7BF5; background: #FFFDF8;
  border: 2rpx solid #6C7BF5; border-radius: 34rpx; padding: 0 26rpx; height: 60rpx; line-height: 60rpx; }
.deposit-form { display: flex; gap: 16rpx; margin-top: 14rpx; }
.deposit-input { flex: 1; }
.deposit-btn { margin: 0; width: 180rpx; height: 88rpx; font-size: 26rpx; }

.ch-title-row { display: flex; align-items: center; gap: 14rpx; }
.ch-name { font-size: 29rpx; font-weight: 700; }
.st-tag { font-size: 20rpx; border-radius: 10rpx; padding: 4rpx 14rpx; font-weight: 600; }
.st-ok { background: #E9F8F2; color: #33B98E; }
.st-over { background: #FFEDEE; color: #F27E7E; }
.st-done { background: #EFF1FF; color: #6C7BF5; }
.st-fail { background: #F4F2FA; color: #8b93a5; }
.ch-sub { display: block; font-size: 22rpx; color: #A6AAC2; margin-top: 10rpx; }
.ch-row { display: flex; gap: 16rpx; align-items: center; margin-bottom: 18rpx; }
.picker-value { height: 88rpx; background: #F6F4FB; border-radius: 20rpx;
  display: flex; align-items: center; padding: 0 24rpx; font-size: 26rpx; }
.period-tabs { display: flex; background: #F6F4FB; border-radius: 20rpx; padding: 6rpx; }
.p-tab { font-size: 24rpx; color: #8A90A8; padding: 12rpx 26rpx; border-radius: 12rpx; }
.p-active { background: #6C7BF5; color: #fff; font-weight: 600; }
</style>
