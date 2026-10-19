<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { apiNotes, apiUpdateNote } from '../../api/index.js'

const TZ = new Date().getTimezoneOffset() * 60000
function nowLocal() { return new Date(Date.now() - TZ) }
function fmtDate(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
function addDays(dateStr, delta) {
  const d = new Date(dateStr + 'T00:00:00')
  d.setDate(d.getDate() + delta)
  return fmtDate(d)
}

const todayStr = fmtDate(nowLocal())
const tomorrowStr = addDays(todayStr, 1)

const tab = ref('todo')            // todo / note
const viewMode = ref('schedule')   // schedule 日程 / list 清单 / board 看板
const keyword = ref('')
const loading = ref(false)

const openTodos = ref([])
const doneTodos = ref([])
const noteItems = ref([])

// ---------- 数据 ----------
async function load() {
  loading.value = true
  try {
    if (tab.value === 'todo') {
      const [openRes, doneRes] = await Promise.all([
        apiNotes({ note_type: 'todo', status: 'open', q: keyword.value, page: 1, page_size: 100 }),
        apiNotes({ note_type: 'todo', status: 'done', q: keyword.value, page: 1, page_size: 50 }),
      ])
      openTodos.value = openRes.items
      doneTodos.value = doneRes.items
    } else {
      const res = await apiNotes({ note_type: 'note', q: keyword.value, page: 1, page_size: 100 })
      noteItems.value = res.items
    }
  } catch (e) { /* 统一提示 */ } finally { loading.value = false }
}

function setTab(t) { tab.value = t; load() }
function setView(v) { viewMode.value = v }

async function toggleDone(n) {
  if (n.note_type !== 'todo') return
  const next = n.status === 'open' ? 'done' : 'open'
  try {
    await apiUpdateNote(n.id, {
      title: n.title, content: n.content, note_type: n.note_type,
      status: next, due_at: n.due_at, priority: n.priority, pinned: n.pinned,
    })
    if (next === 'done') uni.showToast({ title: '已完成 ✓', icon: 'none' })
    load()
  } catch (e) { /* 统一提示 */ }
}

async function togglePin(n) {
  try {
    await apiUpdateNote(n.id, {
      title: n.title, content: n.content, note_type: n.note_type,
      status: n.status, due_at: n.due_at, priority: n.priority, pinned: !n.pinned,
    })
    uni.showToast({ title: n.pinned ? '已取消置顶' : '已置顶', icon: 'none' })
    load()
  } catch (e) { /* 统一提示 */ }
}

// ---------- 截止时间 ----------
function dueInfo(n) {
  if (!n.due_at || n.note_type !== 'todo') return null
  const s = String(n.due_at)
  const d = s.slice(0, 10)
  const hm = s.slice(11, 16) || '18:00'
  if (n.status === 'open' && d < todayStr) {
    const days = Math.max(1, Math.round((new Date(todayStr) - new Date(d)) / 86400000))
    return { text: `已逾期 ${days} 天`, cls: 'due-over' }
  }
  if (d === todayStr) return { text: `今天 ${hm}`, cls: 'due-today' }
  if (d === tomorrowStr) return { text: `明天 ${hm}`, cls: 'due-soon' }
  return { text: `${Number(d.slice(5, 7))}月${Number(d.slice(8))}日 ${hm}`, cls: 'due-normal' }
}

const PRIORITY_META = {
  high: { label: '高', cls: 'pri-high' },
  low: { label: '低', cls: 'pri-low' },
}

// ---------- 日程（今日/指定日） ----------
const todoDate = ref(todayStr)
const todoDateLabel = computed(() => {
  const d = new Date(todoDate.value + 'T00:00:00')
  const names = '日一二三四五六'
  const prefix = todoDate.value === todayStr ? '今天 · ' : ''
  return `${prefix}${d.getMonth() + 1}月${d.getDate()}日 周${names[d.getDay()]}`
})

function timeLabel(n) {
  return String(n.due_at || '').slice(11, 16) || '18:00'
}

const dayTasks = computed(() =>
  openTodos.value
    .filter(n => n.due_at && String(n.due_at).slice(0, 10) === todoDate.value)
    .sort((a, b) => String(a.due_at).localeCompare(String(b.due_at))))

const overdueTasks = computed(() =>
  openTodos.value.filter(n => n.due_at && String(n.due_at).slice(0, 10) < todayStr))

const unscheduledTasks = computed(() => openTodos.value.filter(n => !n.due_at))

function shiftTodoDate(delta) { todoDate.value = addDays(todoDate.value, delta) }
function resetTodoDate() { todoDate.value = todayStr }

// ---------- 统计 ----------
const openCount = computed(() => openTodos.value.length)
const doneCount = computed(() => doneTodos.value.length)
const overdueCount = computed(() => overdueTasks.value.length)
const donePct = computed(() => {
  const total = openCount.value + doneCount.value
  return total ? Math.round(doneCount.value / total * 100) : 0
})
const ringStyle = computed(() =>
  `conic-gradient(#8B7FE8 0% ${donePct.value}%, rgba(255,255,255,.35) ${donePct.value}% 100%)`)

// ---------- 清单/看板 ----------
const listGroups = computed(() => {
  const g = { overdue: [], today: [], week: [], later: [] }
  const weekEnd = addDays(todayStr, 7)
  for (const n of openTodos.value) {
    const d = n.due_at ? String(n.due_at).slice(0, 10) : ''
    if (!d) g.later.push(n)
    else if (d < todayStr) g.overdue.push(n)
    else if (d === todayStr) g.today.push(n)
    else if (d <= weekEnd) g.week.push(n)
    else g.later.push(n)
  }
  return [
    { key: 'overdue', label: '已逾期', items: g.overdue, cls: 'g-over' },
    { key: 'today', label: '今天', items: g.today, cls: 'g-today' },
    { key: 'week', label: '本周', items: g.week, cls: 'g-week' },
    { key: 'later', label: '以后 / 未安排', items: g.later, cls: 'g-later' },
  ].filter(x => x.items.length)
})

function isOverdue(n) {
  const d = n.due_at ? String(n.due_at).slice(0, 10) : ''
  return !!d && d < todayStr
}
const boardColumns = computed(() => [
  { key: 'overdue', label: '逾期', cls: 'col-over', items: openTodos.value.filter(isOverdue) },
  { key: 'open', label: '待办', cls: 'col-open', items: openTodos.value.filter(n => !isOverdue(n)) },
  { key: 'done', label: '已完成', cls: 'col-done', items: doneTodos.value },
])

// ---------- 便签日历条 ----------
const selectedDate = ref(todayStr)
const weekOffset = ref(0)

const weekStart = computed(() => {
  const base = nowLocal()
  base.setHours(0, 0, 0, 0)
  const offset = (base.getDay() + 6) % 7
  base.setDate(base.getDate() - offset + weekOffset.value * 7)
  return base
})

const noteDateCounts = computed(() => {
  const map = {}
  for (const n of noteItems.value) {
    const d = String(n.created_at).slice(0, 10)
    map[d] = (map[d] || 0) + 1
  }
  return map
})

const weekDays = computed(() => Array.from({ length: 7 }, (_, i) => {
  const d = new Date(weekStart.value)
  d.setDate(d.getDate() + i)
  const date = fmtDate(d)
  return {
    date,
    day: d.getDate(),
    weekday: ['一', '二', '三', '四', '五', '六', '日'][i],
    hasNotes: !!noteDateCounts.value[date],
    isToday: date === todayStr,
    selected: date === selectedDate.value,
  }
}))

const monthLabel = computed(() =>
  `${weekStart.value.getFullYear()}年${weekStart.value.getMonth() + 1}月`)

const selectedDateLabel = computed(() => {
  const d = new Date(selectedDate.value + 'T00:00:00')
  const names = '日一二三四五六'
  return `${d.getMonth() + 1}月${d.getDate()}日 周${names[d.getDay()]}`
})

const dayNotes = computed(() =>
  noteItems.value.filter(n => String(n.created_at).slice(0, 10) === selectedDate.value))

const searchActive = computed(() => keyword.value.trim().length > 0)

const searchGroups = computed(() => {
  if (!searchActive.value) return []
  const map = new Map()
  for (const n of noteItems.value) {
    const d = String(n.created_at).slice(0, 10)
    if (!map.has(d)) map.set(d, [])
    map.get(d).push(n)
  }
  return Array.from(map.entries())
    .sort((a, b) => b[0].localeCompare(a[0]))
    .map(([date, items]) => ({ date, label: dateLabel(date), items }))
})

function dateLabel(d) {
  if (d === todayStr) return '今天'
  if (d === tomorrowStr) return '明天'
  const y = addDays(todayStr, -1)
  if (d === y) return '昨天'
  return `${d.slice(0, 4)}年${Number(d.slice(5, 7))}月${Number(d.slice(8))}日`
}

function selectDate(date) { selectedDate.value = date }
function shiftWeek(delta) {
  weekOffset.value += delta
  selectedDate.value = addDays(selectedDate.value, delta * 7)
}

function goEdit(id) {
  let url = '/pages/notes/edit'
  if (id) url += '?id=' + id
  else url += '?type=' + tab.value
  uni.navigateTo({ url })
}

onShow(load)
</script>

<template>
  <view class="page">
    <!-- 顶部 Tab + 搜索 -->
    <view class="top-bar">
      <view class="main-tabs">
        <text :class="['m-tab', tab === 'todo' && 'm-active']" @click="setTab('todo')">待办任务</text>
        <text :class="['m-tab', tab === 'note' && 'm-active']" @click="setTab('note')">生活便签</text>
      </view>
      <view class="search-box">
        <input class="search-input" v-model="keyword" confirm-type="search"
          :placeholder="tab === 'todo' ? '搜索任务' : '搜索便签'" placeholder-class="ph" @confirm="load" />
        <text class="search-btn" @click="load">搜索</text>
      </view>
    </view>

    <!-- ===== 待办 ===== -->
    <block v-if="tab === 'todo'">
      <!-- 统计条 -->
      <view class="glass stat-bar">
        <view class="ring" :style="{ background: ringStyle }">
          <view class="ring-hole"><text class="ring-pct">{{ donePct }}%</text></view>
        </view>
        <view class="stat-items">
          <view class="stat-item"><text class="stat-num">{{ openCount }}</text><text class="stat-label">待办中</text></view>
          <view class="stat-item"><text class="stat-num over">{{ overdueCount }}</text><text class="stat-label">已逾期</text></view>
          <view class="stat-item"><text class="stat-num done">{{ doneCount }}</text><text class="stat-label">已完成</text></view>
        </view>
      </view>

      <!-- 视图切换 -->
      <view class="view-switch">
        <text :class="['v-btn', viewMode === 'schedule' && 'v-active']" @click="setView('schedule')">日程</text>
        <text :class="['v-btn', viewMode === 'list' && 'v-active']" @click="setView('list')">清单</text>
        <text :class="['v-btn', viewMode === 'board' && 'v-active']" @click="setView('board')">看板</text>
      </view>

      <!-- 日程视图 -->
      <block v-if="viewMode === 'schedule'">
        <view class="glass day-nav">
          <text class="nav-arrow" @click="shiftTodoDate(-1)">‹</text>
          <view class="day-nav-main">
            <text class="day-nav-date">{{ todoDateLabel }}</text>
            <text v-if="todoDate !== todayStr" class="back-today" @click="resetTodoDate">回到今天</text>
          </view>
          <text class="nav-arrow" @click="shiftTodoDate(1)">›</text>
        </view>

        <view v-if="overdueTasks.length" class="glass overdue-block">
          <view class="block-head"><view class="g-dot g-over" /><text>逾期未完成</text><text class="block-count">{{ overdueTasks.length }}</text></view>
          <view class="sched-task" v-for="n in overdueTasks" :key="n.id" @click="goEdit(n.id)">
            <view class="sched-task-main">
              <text class="sched-title">{{ n.title }}</text>
              <text class="due due-over">⏰ {{ dueInfo(n).text }}</text>
            </view>
            <text class="done-btn" @click.stop="toggleDone(n)">完成</text>
          </view>
        </view>

        <view class="schedule">
          <view class="sched-row" v-for="n in dayTasks" :key="n.id">
            <text class="sched-time">{{ timeLabel(n) }}</text>
            <view class="sched-axis"><view class="sched-node" /></view>
            <view class="glass sched-card" @click="goEdit(n.id)">
              <view class="sched-card-head">
                <text class="sched-title">{{ n.title }}</text>
                <text v-if="PRIORITY_META[n.priority]" class="pri-tag" :class="PRIORITY_META[n.priority].cls">
                  {{ PRIORITY_META[n.priority].label }}
                </text>
                <image v-if="n.pinned" class="pin-mark" src="/static/icons/act_pin.png" mode="widthFix" />
              </view>
              <text class="sched-content" v-if="n.content">{{ n.content }}</text>
              <view class="sched-foot">
                <text class="due" :class="dueInfo(n).cls">{{ dueInfo(n).text }}</text>
                <text class="done-btn" @click.stop="toggleDone(n)">完成</text>
              </view>
            </view>
          </view>
          <view v-if="!dayTasks.length" class="glass sched-empty">
            <image class="empty-animal" src="/static/doodles/rabbit.png" mode="widthFix" />
            <text>这一天还没有安排，点右下角新建一个吧</text>
          </view>
        </view>

        <view v-if="unscheduledTasks.length" class="glass unsched-block">
          <view class="block-head"><view class="g-dot g-later" /><text>随时 / 未安排</text><text class="block-count">{{ unscheduledTasks.length }}</text></view>
          <view class="sched-task" v-for="n in unscheduledTasks" :key="n.id" @click="goEdit(n.id)">
            <view class="sched-task-main">
              <text class="sched-title">{{ n.title }}</text>
              <text class="due due-none">未设置时间</text>
            </view>
            <text class="done-btn" @click.stop="toggleDone(n)">完成</text>
          </view>
        </view>
      </block>

      <!-- 清单视图 -->
      <block v-else-if="viewMode === 'list'">
        <view v-for="g in listGroups" :key="g.key" class="group">
          <view class="group-head">
            <view class="g-dot" :class="g.cls" />
            <text class="group-title">{{ g.label }}</text>
            <text class="group-count">{{ g.items.length }}</text>
          </view>
          <view class="glass task-card" v-for="n in g.items" :key="n.id" @click="goEdit(n.id)">
            <view class="check" @click.stop="toggleDone(n)"></view>
            <view class="task-main">
              <view class="title-row">
                <text class="task-title">{{ n.title }}</text>
                <text v-if="PRIORITY_META[n.priority]" class="pri-tag" :class="PRIORITY_META[n.priority].cls">
                  {{ PRIORITY_META[n.priority].label }}
                </text>
                <image v-if="n.pinned" class="pin-mark" src="/static/icons/act_pin.png" mode="widthFix" />
              </view>
              <text class="task-content" v-if="n.content">{{ n.content }}</text>
              <view class="meta-row">
                <text v-if="dueInfo(n)" class="due" :class="dueInfo(n).cls">⏰ {{ dueInfo(n).text }}</text>
                <text v-else class="due due-none">无截止时间</text>
              </view>
            </view>
            <text class="pin-btn" :class="n.pinned && 'pin-on'" @click.stop="togglePin(n)">
              {{ n.pinned ? '取消' : '置顶' }}
            </text>
          </view>
        </view>
        <view v-if="!listGroups.length && !loading" class="glass sched-empty">
          <image class="empty-animal" src="/static/doodles/rabbit.png" mode="widthFix" />
          <text>今天没有待办，轻松一天</text>
        </view>
      </block>

      <!-- 看板视图 -->
      <block v-else>
        <scroll-view scroll-x class="board" v-if="openCount || doneCount">
          <view class="board-col glass" v-for="col in boardColumns" :key="col.key">
            <view class="board-head" :class="col.cls">
              <text>{{ col.label }}</text><text class="board-count">{{ col.items.length }}</text>
            </view>
            <view class="b-card" v-for="n in col.items" :key="n.id" @click="goEdit(n.id)">
              <text class="b-title">{{ n.title }}</text>
              <view class="b-meta">
                <text v-if="dueInfo(n)" class="due" :class="dueInfo(n).cls">{{ dueInfo(n).text }}</text>
                <text v-if="PRIORITY_META[n.priority]" class="pri-tag" :class="PRIORITY_META[n.priority].cls">
                  {{ PRIORITY_META[n.priority].label }}
                </text>
              </view>
              <view class="b-actions" v-if="col.key === 'overdue' || col.key === 'open'">
                <text class="b-btn" @click.stop="toggleDone(n)">完成</text>
              </view>
            </view>
            <view v-if="!col.items.length" class="b-empty">暂无</view>
          </view>
        </scroll-view>
        <view v-else class="glass sched-empty">
          <image class="empty-animal" src="/static/doodles/rabbit.png" mode="widthFix" />
          <text>还没有任务，点右下角新建</text>
        </view>
      </block>
    </block>

    <!-- ===== 生活便签 ===== -->
    <block v-else>
      <!-- 7 日日历条 -->
      <view class="glass week-bar">
        <text class="week-arrow" @click="shiftWeek(-1)">‹</text>
        <view class="week-days">
          <view v-for="d in weekDays" :key="d.date"
            :class="['day-cell', d.selected && 'day-active', d.isToday && 'day-today']"
            @click="selectDate(d.date)">
            <text class="day-wd">{{ d.weekday }}</text>
            <text class="day-dd">{{ d.day }}</text>
            <view v-if="d.hasNotes" class="note-dot" />
          </view>
        </view>
        <text class="week-arrow" @click="shiftWeek(1)">›</text>
      </view>

      <view class="notes-head">
        <view class="notes-head-left">
          <text class="notes-date">{{ searchActive ? '搜索结果' : monthLabel }}</text>
          <text class="notes-sub">{{ searchActive ? `“${keyword}” 相关便签` : `${selectedDateLabel} · ${dayNotes.length} 条便签` }}</text>
        </view>
        <image class="week-rabbit" src="/static/doodles/rabbit.png" mode="widthFix" />
      </view>

      <!-- 当天便签 -->
      <block v-if="!searchActive">
        <view v-if="dayNotes.length" class="note-list">
          <view class="glass note-card" v-for="n in dayNotes" :key="n.id" @click="goEdit(n.id)">
            <view class="note-head">
              <text class="note-title">{{ n.title }}</text>
              <text class="note-time">{{ String(n.created_at).slice(11, 16) }}</text>
            </view>
            <text class="note-body" v-if="n.content">{{ n.content }}</text>
          </view>
        </view>
        <view v-else class="glass notes-empty">
          <image class="empty-animal" src="/static/doodles/rabbit.png" mode="widthFix" />
          <text>这一天还没有便签，写点什么吧</text>
        </view>
      </block>

      <!-- 搜索结果（跨日期） -->
      <block v-else>
        <view v-for="g in searchGroups" :key="g.date" class="search-group">
          <view class="search-date">{{ g.label }}</view>
          <view class="glass note-card" v-for="n in g.items" :key="n.id" @click="goEdit(n.id)">
            <view class="note-head">
              <text class="note-title">{{ n.title }}</text>
              <text class="note-time">{{ String(n.created_at).slice(11, 16) }}</text>
            </view>
            <text class="note-body" v-if="n.content">{{ n.content }}</text>
          </view>
        </view>
        <view v-if="!searchGroups.length && !loading" class="glass notes-empty">
          <text>没有找到相关便签</text>
        </view>
      </block>

      <image class="page-bear" src="/static/doodles/bear.png" mode="widthFix" />
    </block>

    <view class="fab" @click="goEdit()">＋</view>
  </view>
</template>

<style scoped>
.page { padding-bottom: 260rpx; }

/* 磨砂玻璃 */
.glass {
  background: rgba(255, 253, 248, 0.62);
  -webkit-backdrop-filter: blur(18px) saturate(120%);
  backdrop-filter: blur(18px) saturate(120%);
  border: 1rpx solid rgba(255, 255, 255, 0.78);
  box-shadow: 0 12rpx 30rpx rgba(124, 139, 255, 0.12);
  border-radius: 28rpx;
}

.top-bar { background: rgba(255, 253, 248, 0.72);
  -webkit-backdrop-filter: blur(16px); backdrop-filter: blur(16px);
  padding: 22rpx 24rpx 16rpx; border-bottom: 1rpx dashed rgba(231, 227, 244, .8); }
.main-tabs { display: flex; background: rgba(244, 241, 251, .8); border-radius: 999rpx; padding: 6rpx; margin-bottom: 18rpx; }
.m-tab { flex: 1; text-align: center; padding: 14rpx 0; font-size: 27rpx; color: #8A90A8;
  border-radius: 999rpx; letter-spacing: 1rpx; }
.m-active { background: #FFFDF8; color: #5A54B8; font-weight: 800;
  box-shadow: 0 6rpx 16rpx rgba(124, 139, 255, .16); }
.search-box { display: flex; align-items: center; gap: 16rpx; }
.search-input { flex: 1; height: 72rpx; background: rgba(246, 244, 251, .9); border-radius: 36rpx;
  padding: 0 28rpx; font-size: 26rpx; }
.ph { color: #C3C7DA; }
.search-btn { color: #6C7BF5; font-size: 26rpx; font-weight: 600; }

/* 统计条 */
.stat-bar { display: flex; align-items: center; margin: 18rpx 24rpx 0; padding: 20rpx 24rpx; }
.ring { width: 110rpx; height: 110rpx; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; }
.ring-hole { width: 82rpx; height: 82rpx; border-radius: 50%; background: rgba(255, 253, 248, .95);
  display: flex; align-items: center; justify-content: center; }
.ring-pct { font-size: 24rpx; font-weight: 800; color: #5A54B8; }
.stat-items { flex: 1; display: flex; justify-content: space-around; margin-left: 14rpx; }
.stat-item { display: flex; flex-direction: column; align-items: center; gap: 2rpx; }
.stat-num { font-size: 32rpx; font-weight: 800; color: #4A4F6B; }
.stat-num.over { color: #E45858; }
.stat-num.done { color: #1FA97F; }
.stat-label { font-size: 21rpx; color: #A6AAC2; }

/* 视图切换 */
.view-switch { display: flex; justify-content: flex-end; margin: 6rpx 28rpx 8rpx; gap: 12rpx; }
.v-btn { font-size: 23rpx; color: #8A90A8; background: rgba(255, 253, 248, .55); border-radius: 999rpx; padding: 8rpx 26rpx;
  border: 1rpx solid rgba(255,255,255,.7); }
.v-active { background: #8B7FE8; color: #fff; font-weight: 700; }

/* 日程 */
.day-nav { display: flex; align-items: center; justify-content: space-between;
  margin: 6rpx 24rpx 14rpx; padding: 18rpx 24rpx; }
.nav-arrow { font-size: 40rpx; color: #6B7089; padding: 0 16rpx; }
.day-nav-main { display: flex; flex-direction: column; align-items: center; gap: 4rpx; }
.day-nav-date { font-size: 29rpx; font-weight: 800; color: #4A4F6B; letter-spacing: 1rpx; }
.back-today { font-size: 21rpx; color: #6C7BF5; }

.schedule { padding: 0 24rpx; }
.sched-row { display: flex; align-items: flex-start; }
.sched-time { width: 92rpx; flex-shrink: 0; text-align: right; padding-top: 22rpx;
  font-size: 22rpx; color: #8A90A8; }
.sched-axis { width: 44rpx; flex-shrink: 0; position: relative; align-self: stretch;
  display: flex; flex-direction: column; align-items: center; }
.sched-node { width: 14rpx; height: 14rpx; border-radius: 7rpx; background: #8B7FE8; margin-top: 30rpx;
  box-shadow: 0 0 0 6rpx rgba(242, 238, 252, .9); }
.sched-axis::after { content: ''; flex: 1; width: 0; border-left: 2rpx dashed #DCD3F2; margin-top: 6rpx; }
.sched-row:last-child .sched-axis::after { display: none; }
.sched-card { flex: 1; padding: 20rpx 22rpx; margin-bottom: 18rpx; }
.sched-card:active { opacity: .85; }
.sched-card-head { display: flex; align-items: center; gap: 10rpx; flex-wrap: wrap; }
.sched-title { font-size: 28rpx; font-weight: 700; color: #3A3F58; }
.sched-content { display: block; font-size: 23rpx; color: #7A7F96; margin-top: 8rpx; line-height: 1.6;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sched-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 12rpx; }
.done-btn { font-size: 22rpx; color: #6C7BF5; background: rgba(255, 253, 248, .8);
  border: 2rpx solid #C9CFFF; border-radius: 999rpx; padding: 6rpx 20rpx; }
.sched-empty { margin: 10rpx 0; padding: 40rpx 20rpx; text-align: center; font-size: 24rpx; color: #A6AAC2; }

.overdue-block, .unsched-block { margin: 0 24rpx 16rpx; padding: 20rpx 22rpx; }
.block-head { display: flex; align-items: center; gap: 10rpx; font-size: 25rpx; font-weight: 700;
  color: #4A4F6B; margin-bottom: 8rpx; }
.block-count { margin-left: auto; font-size: 21rpx; color: #8A90A8; font-weight: 400; }
.sched-task { display: flex; align-items: center; justify-content: space-between; gap: 14rpx;
  padding: 14rpx 0; border-bottom: 1rpx dashed rgba(231, 227, 244, .9); }
.sched-task:last-child { border-bottom: none; }
.sched-task-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 6rpx; }
.sched-task .sched-title { font-size: 26rpx; }

/* 动效点的颜色 */
.g-dot { width: 14rpx; height: 14rpx; border-radius: 7rpx; }
.g-over { background: #E45858; }
.g-today { background: #F2B45C; }
.g-week { background: #6C7BF5; }
.g-later { background: #B9AEDC; }

/* 清单 */
.group { margin-top: 8rpx; }
.group-head { display: flex; align-items: center; gap: 10rpx; margin: 16rpx 28rpx 6rpx; }
.group-title { font-size: 25rpx; font-weight: 700; color: #4A4F6B; }
.group-count { font-size: 21rpx; color: #A6AAC2; }
.task-card { display: flex; align-items: flex-start; margin: 12rpx 24rpx; padding: 22rpx 20rpx;
  border-left: 10rpx solid #FFD98E; }
.task-card:active { opacity: .85; }
.check { width: 44rpx; height: 44rpx; border-radius: 22rpx; border: 3rpx solid #D6D9E8;
  margin-right: 16rpx; margin-top: 2rpx; flex-shrink: 0; }
.task-main { flex: 1; min-width: 0; }
.title-row { display: flex; align-items: center; gap: 12rpx; flex-wrap: wrap; }
.task-title { font-size: 28rpx; font-weight: 600; }
.pri-tag { font-size: 20rpx; border-radius: 8rpx; padding: 2rpx 12rpx; font-weight: 700; }
.pri-high { background: #FFEDEE; color: #E45858; }
.pri-low { background: rgba(244, 242, 250, .9); color: #8A90A8; }
.pin-mark { width: 28rpx; height: 28rpx; }
.task-content { display: block; font-size: 23rpx; color: #8A90A8; margin-top: 8rpx;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meta-row { display: flex; align-items: center; margin-top: 10rpx; }
.due { font-size: 22rpx; }
.due-over { color: #E45858; font-weight: 700; }
.due-today { color: #F2A93B; font-weight: 600; }
.due-soon { color: #6C7BF5; }
.due-normal { color: #A6AAC2; }
.due-none { color: #C3C7DA; }
.pin-btn { font-size: 22rpx; color: #A6AAC2; padding: 6rpx 0 6rpx 14rpx; flex-shrink: 0; }
.pin-on { color: #6C7BF5; font-weight: 700; }

/* 看板 */
.board { white-space: nowrap; padding: 8rpx 0 10rpx; }
.board-col { display: inline-block; vertical-align: top; width: 300rpx; margin-left: 20rpx;
  padding: 16rpx 14rpx 20rpx; white-space: normal; }
.board-head { display: flex; justify-content: space-between; align-items: center;
  font-size: 25rpx; font-weight: 700; padding: 6rpx 8rpx 14rpx; }
.board-count { font-size: 21rpx; color: #8A90A8; }
.col-over .board-head { color: #E45858; }
.col-open .board-head { color: #6C7BF5; }
.col-done .board-head { color: #1FA97F; }
.b-card { background: rgba(255, 253, 248, .85); border-radius: 20rpx; padding: 18rpx 16rpx; margin-bottom: 14rpx;
  box-shadow: 0 6rpx 16rpx rgba(124, 139, 255, .08); }
.b-card:active { opacity: .85; }
.b-title { display: block; font-size: 25rpx; font-weight: 600; line-height: 1.5; }
.b-meta { display: flex; align-items: center; gap: 10rpx; margin-top: 10rpx; flex-wrap: wrap; }
.b-actions { display: flex; justify-content: flex-end; margin-top: 10rpx; }
.b-btn { font-size: 22rpx; color: #6C7BF5; background: #EFF1FF; border-radius: 999rpx; padding: 6rpx 20rpx; }
.b-empty { text-align: center; font-size: 22rpx; color: #C3C7DA; padding: 26rpx 0; }

/* 便签日历条 */
.week-bar { display: flex; align-items: center; margin: 18rpx 24rpx 0; padding: 16rpx 12rpx; }
.week-arrow { font-size: 38rpx; color: #6B7089; padding: 0 10rpx; flex-shrink: 0; }
.week-days { flex: 1; display: flex; justify-content: space-between; }
.day-cell { display: flex; flex-direction: column; align-items: center; gap: 4rpx;
  padding: 10rpx 6rpx; border-radius: 18rpx; min-width: 68rpx; position: relative; }
.day-wd { font-size: 20rpx; color: #8A90A8; }
.day-dd { font-size: 28rpx; font-weight: 700; color: #4A4F6B; }
.day-today .day-dd { color: #8B7FE8; }
.day-active { background: rgba(139, 127, 232, .16); border: 2rpx dashed #8B7FE8; }
.note-dot { width: 8rpx; height: 8rpx; border-radius: 4rpx; background: #F2B45C; }

.notes-head { display: flex; align-items: flex-end; justify-content: space-between;
  padding: 16rpx 30rpx 4rpx; }
.notes-date { display: block; font-size: 30rpx; font-weight: 800; color: #4A4F6B; letter-spacing: 1rpx; }
.notes-sub { display: block; font-size: 22rpx; color: #8A90A8; margin-top: 4rpx; }
.week-rabbit { width: 104rpx; height: 108rpx; margin-bottom: -18rpx; }

.note-list { padding: 4rpx 24rpx 0; }
.note-card { padding: 24rpx 26rpx; margin-bottom: 18rpx; }
.note-card:active { opacity: .85; }
.note-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12rpx; }
.note-title { font-size: 29rpx; font-weight: 700; color: #3A3F58; }
.note-time { font-size: 21rpx; color: #A6AAC2; flex-shrink: 0; }
/* 长便签自适应：完整换行，不截断 */
.note-body { display: block; font-size: 25rpx; color: #5A5F78; line-height: 1.8; margin-top: 10rpx;
  white-space: pre-wrap; word-break: break-all; }
.notes-empty { margin: 10rpx 24rpx; padding: 46rpx 20rpx; text-align: center;
  font-size: 24rpx; color: #A6AAC2; }
.empty-animal { width: 150rpx; display: block; margin: 0 auto 12rpx; }
.search-group { padding: 0 24rpx; }
.search-date { font-size: 24rpx; font-weight: 700; color: #8A90A8; margin: 18rpx 6rpx 10rpx; }

.page-bear { position: fixed; left: 6rpx; bottom: 178rpx; width: 116rpx; opacity: .9;
  pointer-events: none; }

.fab { position: fixed; right: 40rpx; bottom: 200rpx; width: 108rpx; height: 108rpx;
  border-radius: 54rpx; background: linear-gradient(135deg, #7C8BFF, #A78BFA); color: #fff;
  font-size: 56rpx; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 12rpx 28rpx rgba(124, 139, 255, .35); }
.fab:active { opacity: .85; }
</style>
