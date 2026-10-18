<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { apiBills } from '../../api/index.js'
import { categoryMeta } from '../../common/category-icons.js'

const month = ref('')
const typeFilter = ref('')          // '' 全部 / expense / income
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)

function currentMonth() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function shiftMonth(m, delta) {
  const [y, mo] = m.split('-').map(Number)
  const d = new Date(y, mo - 1 + delta, 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

async function load(reset = true) {
  if (reset) { page.value = 1 }
  loading.value = true
  try {
    const res = await apiBills({
      month: month.value,
      type: typeFilter.value,
      page: page.value,
      page_size: pageSize,
    })
    items.value = reset ? res.items : items.value.concat(res.items)
    total.value = res.total
  } catch (e) { /* 统一提示 */ } finally { loading.value = false }
}

function setType(t) { typeFilter.value = t; load(true) }
function prevMonth() { month.value = shiftMonth(month.value, -1); load(true) }
function nextMonth() { month.value = shiftMonth(month.value, 1); load(true) }
function loadMore() {
  if (items.value.length < total.value && !loading.value) {
    page.value += 1
    load(false)
  }
}
function goEdit(id) {
  uni.navigateTo({ url: '/pages/bills/edit' + (id ? '?id=' + id : '') })
}

onShow(() => {
  if (!month.value) month.value = currentMonth()
  load(true)
})
</script>

<template>
  <view class="page">
    <!-- 月份与类型筛选 -->
    <view class="filter-bar">
      <view class="month-nav">
        <text class="arrow" @click="prevMonth">‹</text>
        <text class="month">{{ month }}</text>
        <text class="arrow" @click="nextMonth">›</text>
      </view>
      <view class="type-tabs">
        <text :class="['tab', typeFilter === '' && 'tab-active']" @click="setType('')">全部</text>
        <text :class="['tab', typeFilter === 'expense' && 'tab-active']" @click="setType('expense')">支出</text>
        <text :class="['tab', typeFilter === 'income' && 'tab-active']" @click="setType('income')">收入</text>
      </view>
    </view>

    <view class="list" v-if="items.length">
      <view class="bill-card" v-for="b in items" :key="b.id" @click="goEdit(b.id)">
        <view class="cat-icon" :style="{ background: categoryMeta(b.category).color + '22' }">
          {{ categoryMeta(b.category).icon }}
        </view>
        <view class="mid">
          <view class="mid-top">
            <text class="cat-name">{{ b.category }}</text>
            <text class="amount" :class="b.type === 'income' ? 'amount-in' : 'amount-out'">
              {{ b.type === 'income' ? '+' : '-' }}{{ Number(b.amount).toFixed(2) }}
            </text>
          </view>
          <view class="mid-bottom">
            <text class="remark">{{ b.remark || (b.type === 'income' ? '收入' : '支出') }}</text>
            <text class="date">{{ b.bill_date.slice(5) }}<text v-if="b.source === 'ai'" class="ai-tag">AI</text></text>
          </view>
        </view>
      </view>
      <view class="load-more" v-if="items.length < total" @click="loadMore">
        {{ loading ? '加载中…' : '加载更多' }}
      </view>
    </view>
    <view v-else class="empty">该条件下暂无账单</view>

    <!-- 悬浮新增按钮 -->
    <view class="fab" @click="goEdit()">＋</view>
  </view>
</template>

<style scoped>
.page { padding-bottom: 140rpx; }
.filter-bar { background: #fff; padding: 20rpx 24rpx 6rpx; }
.month-nav { display: flex; align-items: center; justify-content: center; gap: 24rpx; }
.arrow { font-size: 40rpx; color: #7c8595; padding: 0 20rpx; }
.month { font-size: 30rpx; font-weight: 700; }
.type-tabs { display: flex; gap: 20rpx; justify-content: center; margin: 18rpx 0 14rpx; }
.tab { font-size: 26rpx; color: #7c8595; padding: 8rpx 30rpx; border-radius: 26rpx; background: #f5f7fb; }
.tab-active { color: #fff; background: #2f6fed; font-weight: 600; }

.list { margin-top: 16rpx; }
.bill-card { display: flex; align-items: center; background: #fff; margin: 14rpx 24rpx;
  border-radius: 18rpx; padding: 24rpx 24rpx; box-shadow: 0 6rpx 24rpx rgba(40, 70, 120, .06); }
.bill-card:active { opacity: .85; }
.cat-icon { width: 84rpx; height: 84rpx; border-radius: 24rpx; font-size: 40rpx;
  display: flex; align-items: center; justify-content: center; margin-right: 22rpx; flex-shrink: 0; }
.mid { flex: 1; min-width: 0; }
.mid-top { display: flex; justify-content: space-between; align-items: center; }
.mid-bottom { display: flex; justify-content: space-between; align-items: center; margin-top: 10rpx; }
.cat-name { font-size: 28rpx; font-weight: 600; }
.remark { font-size: 22rpx; color: #9aa3b5; max-width: 380rpx; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap; }
.date { font-size: 22rpx; color: #9aa3b5; }
.ai-tag { margin-left: 10rpx; background: #eef3ff; color: #2f6fed; border-radius: 8rpx;
  padding: 2rpx 10rpx; font-size: 20rpx; font-weight: 600; }
.amount { font-size: 32rpx; font-weight: 700; }
.amount-in { color: #16b07a; } .amount-out { color: #263246; }

.load-more { text-align: center; color: #7c8595; font-size: 24rpx; padding: 24rpx; }

.fab { position: fixed; right: 40rpx; bottom: 200rpx; width: 108rpx; height: 108rpx;
  border-radius: 54rpx; background: #2f6fed; color: #fff; font-size: 56rpx;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 10rpx 30rpx rgba(47, 111, 237, .4); }
.fab:active { opacity: .85; }
</style>
