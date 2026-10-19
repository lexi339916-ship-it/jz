<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { apiBills, apiMonthlyStats } from '../../api/index.js'
import { categoryMeta, channelMeta } from '../../common/category-icons.js'

// 本地日期（避免 toISOString 的 UTC 偏移）
const todayStr = new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
  .toISOString().slice(0, 10)

const viewMode = ref('list')        // list 列表 / calendar 日历
const month = ref('')
const typeFilter = ref('')          // '' 全部 / expense / income
const pageSize = 20

// 列表视图状态
const items = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)

// 日历视图状态
const monthDays = ref([])           // [{date, expense, income}]（当月每天）
const selectedDate = ref('')
const dayBills = ref([])
const dayLoading = ref(false)

function currentMonth() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function shiftMonth(m, delta) {
  const [y, mo] = m.split('-').map(Number)
  const d = new Date(y, mo - 1 + delta, 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

// 金额缩写：1 万以上显示 x.x万；整数不带小数，否则保留一位
function fmtAmount(v) {
  const n = Number(v)
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return Number.isInteger(n) ? String(n) : n.toFixed(1)
}

// ---------- 日历网格 ----------
const expenseMax = computed(() =>
  Math.max(0, ...monthDays.value.map(d => Number(d.expense))))

const calCells = computed(() => {
  if (!monthDays.value.length) return []
  const [y, m] = month.value.split('-').map(Number)
  const lead = (new Date(y, m - 1, 1).getDay() + 6) % 7  // 周一开头
  const cells = []
  for (let i = 0; i < lead; i += 1) cells.push({ key: `b${i}`, blank: true })
  for (const d of monthDays.value) {
    const expense = Number(d.expense)
    const income = Number(d.income)
    cells.push({
      key: d.date,
      date: d.date,
      day: Number(d.date.slice(8)),
      expense,
      income,
      showExpense: expense > 0 && typeFilter.value !== 'income',
      showIncome: income > 0 && typeFilter.value !== 'expense',
      isToday: d.date === todayStr,
      selected: d.date === selectedDate.value,
      heat: expense > 0 && expenseMax.value > 0
        ? Math.min(0.3, 0.06 + 0.24 * (expense / expenseMax.value))
        : 0,
    })
  }
  while (cells.length % 7 !== 0) cells.push({ key: `e${cells.length}`, blank: true })
  return cells
})

const monthSummary = computed(() => {
  let income = 0
  let expense = 0
  for (const d of monthDays.value) {
    income += Number(d.income)
    expense += Number(d.expense)
  }
  return { income, expense }
})

const selectedDayStat = computed(() =>
  monthDays.value.find(d => d.date === selectedDate.value) || { expense: 0, income: 0 })

const selectedDateLabel = computed(() => {
  if (!selectedDate.value) return ''
  const [y, m, d] = selectedDate.value.split('-').map(Number)
  const week = ['日', '一', '二', '三', '四', '五', '六'][new Date(y, m - 1, d).getDay()]
  return `${m}月${d}日 周${week}`
})

function defaultSelectedDate() {
  if (month.value === todayStr.slice(0, 7)) return todayStr
  const firstWithData = monthDays.value.find(d => Number(d.expense) > 0 || Number(d.income) > 0)
  return firstWithData ? firstWithData.date : `${month.value}-01`
}

// ---------- 数据加载 ----------
async function loadDayBills() {
  if (!selectedDate.value) return
  dayLoading.value = true
  try {
    const res = await apiBills({
      start_date: selectedDate.value,
      end_date: selectedDate.value,
      type: typeFilter.value,
      page: 1,
      page_size: 50,
    })
    dayBills.value = res.items
  } catch (e) { /* 统一提示 */ } finally { dayLoading.value = false }
}

async function load(reset = true) {
  if (reset) page.value = 1
  loading.value = true
  try {
    const stats = await apiMonthlyStats(month.value)
    monthDays.value = stats.days
    if (viewMode.value === 'list') {
      const res = await apiBills({
        month: month.value,
        type: typeFilter.value,
        page: page.value,
        page_size: pageSize,
      })
      items.value = reset ? res.items : items.value.concat(res.items)
      total.value = res.total
    } else {
      if (!selectedDate.value || !selectedDate.value.startsWith(month.value)) {
        selectedDate.value = defaultSelectedDate()
      }
      await loadDayBills()
    }
  } catch (e) { /* 统一提示 */ } finally { loading.value = false }
}

function toggleView() {
  viewMode.value = viewMode.value === 'list' ? 'calendar' : 'list'
  load(true)
}

function setType(t) {
  typeFilter.value = t
  if (viewMode.value === 'list') load(true)
  else loadDayBills()
}

function prevMonth() { month.value = shiftMonth(month.value, -1); load(true) }
function nextMonth() { month.value = shiftMonth(month.value, 1); load(true) }

function loadMore() {
  if (items.value.length < total.value && !loading.value) {
    page.value += 1
    load(false)
  }
}

function goEdit(id, date) {
  let url = '/pages/bills/edit'
  if (id) url += '?id=' + id
  else if (date) url += '?date=' + date
  uni.navigateTo({ url })
}

function selectDay(cell) {
  if (cell.blank || !cell.date) return
  selectedDate.value = cell.date
  loadDayBills()
}

onShow(() => {
  if (!month.value) month.value = currentMonth()
  load(true)
})
</script>

<template>
  <view class="page">
    <!-- 月份 / 视图切换 / 类型筛选 -->
    <view class="filter-bar">
      <view class="month-row">
        <view class="month-nav">
          <text class="arrow" @click="prevMonth">‹</text>
          <text class="month">{{ month }}</text>
          <text class="arrow" @click="nextMonth">›</text>
        </view>
        <text class="view-toggle" @click="toggleView">
          {{ viewMode === 'list' ? '▦ 日历' : '☰ 列表' }}
        </text>
      </view>
      <view class="type-tabs">
        <text :class="['tab', typeFilter === '' && 'tab-active']" @click="setType('')">全部</text>
        <text :class="['tab', typeFilter === 'expense' && 'tab-active']" @click="setType('expense')">支出</text>
        <text :class="['tab', typeFilter === 'income' && 'tab-active']" @click="setType('income')">收入</text>
      </view>
    </view>

    <!-- ===== 列表视图 ===== -->
    <view class="list" v-if="viewMode === 'list' && items.length">
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
            <view class="row-right">
              <text v-if="b.pay_channel" class="channel-tag"
                :style="{ color: channelMeta(b.pay_channel).color, background: channelMeta(b.pay_channel).color + '18' }">
                {{ b.pay_channel }}
              </text>
              <text class="date">{{ b.bill_date.slice(5) }}<text v-if="b.source === 'ai'" class="ai-tag">AI</text><text v-if="b.source === 'receipt'" class="ai-tag">截图</text></text>
            </view>
          </view>
        </view>
      </view>
      <view class="load-more" v-if="items.length < total" @click="loadMore">
        {{ loading ? '加载中…' : '加载更多' }}
      </view>
    </view>
    <view v-else-if="viewMode === 'list'" class="empty">该条件下暂无账单</view>

    <!-- ===== 日历视图 ===== -->
    <block v-else>
      <view class="card cal-card">
        <view class="cal-summary">
          <text class="cal-sum-item">本月支出 <text class="out">¥{{ monthSummary.expense.toFixed(2) }}</text></text>
          <text class="cal-sum-item">收入 <text class="in">¥{{ monthSummary.income.toFixed(2) }}</text></text>
        </view>
        <view class="cal-week">
          <text v-for="w in ['一', '二', '三', '四', '五', '六', '日']" :key="w">{{ w }}</text>
        </view>
        <view class="cal-grid">
          <view v-for="c in calCells" :key="c.key"
            class="cal-cell" :class="{ 'cal-selected': c.selected }"
            :style="c.heat && !c.blank ? { background: `rgba(255, 107, 129, ${c.heat})` } : {}"
            @click="selectDay(c)">
            <block v-if="!c.blank">
              <view class="cal-day" :class="{ 'cal-today': c.isToday }">{{ c.day }}</view>
              <text v-if="c.showExpense" class="cal-amount out">-{{ fmtAmount(c.expense) }}</text>
              <text v-if="c.showIncome" class="cal-amount in">+{{ fmtAmount(c.income) }}</text>
            </block>
          </view>
        </view>
      </view>

      <!-- 选中日期的明细 -->
      <view class="card day-panel" v-if="selectedDate">
        <view class="day-head">
          <text class="day-title">{{ selectedDateLabel }}</text>
          <text class="day-sum">
            支 ¥{{ Number(selectedDayStat.expense).toFixed(2) }}
            <text v-if="Number(selectedDayStat.income) > 0" class="in">
              · 收 ¥{{ Number(selectedDayStat.income).toFixed(2) }}
            </text>
          </text>
        </view>
        <view v-if="dayBills.length">
          <view class="bill-card day-bill" v-for="b in dayBills" :key="b.id" @click="goEdit(b.id)">
            <view class="cat-icon sm" :style="{ background: categoryMeta(b.category).color + '22' }">
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
                <view class="row-right">
                  <text v-if="b.pay_channel" class="channel-tag"
                    :style="{ color: channelMeta(b.pay_channel).color, background: channelMeta(b.pay_channel).color + '18' }">
                    {{ b.pay_channel }}
                  </text>
                  <text class="date" v-if="b.source === 'ai' || b.source === 'receipt'">
                    <text class="ai-tag">{{ b.source === 'receipt' ? '截图' : 'AI' }}</text>
                  </text>
                </view>
              </view>
            </view>
          </view>
        </view>
        <view v-else-if="!dayLoading" class="day-empty">
          <text class="day-empty-text">这一天还没有账单</text>
          <button class="btn btn-ghost day-add" @click="goEdit(null, selectedDate)">＋ 为这天记一笔</button>
        </view>
      </view>
    </block>

    <!-- 悬浮新增按钮 -->
    <view class="fab" @click="viewMode === 'list' ? goEdit() : goEdit(null, selectedDate)">＋</view>
  </view>
</template>

<style scoped>
.page { padding-bottom: 140rpx; }
.filter-bar { background: #fff; padding: 20rpx 24rpx 6rpx; }
.month-row { position: relative; }
.month-nav { display: flex; align-items: center; justify-content: center; gap: 24rpx; }
.arrow { font-size: 40rpx; color: #7c8595; padding: 0 20rpx; }
.month { font-size: 30rpx; font-weight: 700; }
.view-toggle { position: absolute; right: 0; top: 50%; transform: translateY(-50%);
  font-size: 24rpx; color: #2f6fed; background: #eef3ff; border-radius: 24rpx; padding: 8rpx 22rpx; }
.type-tabs { display: flex; gap: 20rpx; justify-content: center; margin: 18rpx 0 14rpx; }
.tab { font-size: 26rpx; color: #7c8595; padding: 8rpx 30rpx; border-radius: 26rpx; background: #f5f7fb; }
.tab-active { color: #fff; background: #2f6fed; font-weight: 600; }

/* ===== 列表 ===== */
.list { margin-top: 16rpx; }
.bill-card { display: flex; align-items: center; background: #fff; margin: 14rpx 24rpx;
  border-radius: 18rpx; padding: 24rpx 24rpx; box-shadow: 0 6rpx 24rpx rgba(40, 70, 120, .06); }
.bill-card:active { opacity: .85; }
.cat-icon { width: 84rpx; height: 84rpx; border-radius: 24rpx; font-size: 40rpx;
  display: flex; align-items: center; justify-content: center; margin-right: 22rpx; flex-shrink: 0; }
.cat-icon.sm { width: 68rpx; height: 68rpx; font-size: 32rpx; border-radius: 18rpx; }
.mid { flex: 1; min-width: 0; }
.mid-top { display: flex; justify-content: space-between; align-items: center; }
.mid-bottom { display: flex; justify-content: space-between; align-items: center; margin-top: 10rpx; }
.cat-name { font-size: 28rpx; font-weight: 600; }
.remark { font-size: 22rpx; color: #9aa3b5; max-width: 380rpx; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap; }
.date { font-size: 22rpx; color: #9aa3b5; }
.row-right { display: flex; align-items: center; gap: 10rpx; }
.channel-tag { font-size: 20rpx; padding: 2rpx 12rpx; border-radius: 8rpx; font-weight: 600; }
.ai-tag { margin-left: 10rpx; background: #eef3ff; color: #2f6fed; border-radius: 8rpx;
  padding: 2rpx 10rpx; font-size: 20rpx; font-weight: 600; }
.amount { font-size: 32rpx; font-weight: 700; }
.amount-in { color: #16b07a; } .amount-out { color: #263246; }
.load-more { text-align: center; color: #7c8595; font-size: 24rpx; padding: 24rpx; }

/* ===== 日历 ===== */
.cal-card { padding: 24rpx 18rpx 18rpx; }
.cal-summary { display: flex; justify-content: space-between; padding: 0 10rpx 18rpx;
  border-bottom: 1rpx solid #f0f3f9; }
.cal-sum-item { font-size: 24rpx; color: #7c8595; }
.out { color: #e5484d; } .in { color: #16b07a; }
.cal-week { display: grid; grid-template-columns: repeat(7, 1fr); margin: 16rpx 0 8rpx; }
.cal-week text { text-align: center; font-size: 22rpx; color: #9aa3b5; }
.cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8rpx; }
.cal-cell { min-height: 112rpx; border-radius: 14rpx; padding: 8rpx 2rpx 6rpx;
  display: flex; flex-direction: column; align-items: center; box-sizing: border-box;
  border: 2rpx solid transparent; }
.cal-selected { border-color: #2f6fed; background-color: #eef3ff; }
.cal-day { font-size: 24rpx; font-weight: 600; color: #33415c; line-height: 40rpx;
  min-width: 40rpx; text-align: center; border-radius: 20rpx; }
.cal-today { background: #2f6fed; color: #fff; }
.cal-amount { font-size: 18rpx; line-height: 26rpx; max-width: 100%;
  overflow: hidden; white-space: nowrap; }
.cal-amount.out { color: #d64550; }
.cal-amount.in { color: #0f9d6e; }

/* ===== 当日明细 ===== */
.day-panel { padding: 24rpx; }
.day-head { display: flex; justify-content: space-between; align-items: center;
  padding-bottom: 16rpx; border-bottom: 1rpx solid #f0f3f9; }
.day-title { font-size: 30rpx; font-weight: 700; }
.day-sum { font-size: 22rpx; color: #7c8595; }
.day-bill { margin: 16rpx 0 0; box-shadow: none; border: 1rpx solid #f0f3f9; padding: 20rpx; }
.day-empty { text-align: center; padding: 36rpx 0 20rpx; }
.day-empty-text { display: block; font-size: 24rpx; color: #9aa3b5; margin-bottom: 22rpx; }
.day-add { width: 340rpx; height: 72rpx; font-size: 26rpx; margin: 0 auto; }

.fab { position: fixed; right: 40rpx; bottom: 200rpx; width: 108rpx; height: 108rpx;
  border-radius: 54rpx; background: #2f6fed; color: #fff; font-size: 56rpx;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 10rpx 30rpx rgba(47, 111, 237, .4); }
.fab:active { opacity: .85; }
</style>
