<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { apiNotes, apiUpdateNote } from '../../api/index.js'

const todayStr = new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
  .toISOString().slice(0, 10)
const tomorrowStr = (() => {
  const d = new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
})()
const weekEndStr = (() => {
  const d = new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
  d.setDate(d.getDate() + 7)
  return d.toISOString().slice(0, 10)
})()

const tab = ref('todo')            // todo 待办 / note 便签
const boardMode = ref('list')      // list 清单 / board 看板
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
function setBoard(m) { boardMode.value = m }

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

// ---------- 截止时间展示 ----------
function dueInfo(n) {
  if (!n.due_at || n.note_type !== 'todo') return null
  const s = String(n.due_at)
  const d = s.slice(0, 10)
  const hm = s.slice(11, 16) || '18:00'
  if (n.status === 'open' && d < todayStr) {
    const days = Math.max(1, Math.round(
      (new Date(todayStr) - new Date(d)) / 86400000))
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

// ---------- 待办分组与统计 ----------
const todoGroups = computed(() => {
  const g = { overdue: [], today: [], week: [], later: [] }
  for (const n of openTodos.value) {
    const d = n.due_at ? String(n.due_at).slice(0, 10) : ''
    if (!d) g.later.push(n)
    else if (d < todayStr) g.overdue.push(n)
    else if (d === todayStr) g.today.push(n)
    else if (d <= weekEndStr) g.week.push(n)
    else g.later.push(n)
  }
  return [
    { key: 'overdue', label: '已逾期', items: g.overdue, cls: 'g-over' },
    { key: 'today', label: '今天', items: g.today, cls: 'g-today' },
    { key: 'week', label: '本周', items: g.week, cls: 'g-week' },
    { key: 'later', label: '以后 / 未安排', items: g.later, cls: 'g-later' },
  ].filter(x => x.items.length)
})

const openCount = computed(() => openTodos.value.length)
const doneCount = computed(() => doneTodos.value.length)
const overdueCount = computed(() =>
  todoGroups.value.find(g => g.key === 'overdue')?.items.length || 0)
const donePct = computed(() => {
  const total = openCount.value + doneCount.value
  return total ? Math.round(doneCount.value / total * 100) : 0
})
const ringStyle = computed(() =>
  `conic-gradient(#8B7FE8 0% ${donePct.value}%, #EDEAF7 ${donePct.value}% 100%)`)

function isOverdue(n) {
  const d = n.due_at ? String(n.due_at).slice(0, 10) : ''
  return !!d && d < todayStr
}

const boardColumns = computed(() => [
  { key: 'overdue', label: '逾期', cls: 'col-over',
    items: openTodos.value.filter(isOverdue) },
  { key: 'open', label: '待办', cls: 'col-open',
    items: openTodos.value.filter(n => !isOverdue(n)) },
  { key: 'done', label: '已完成', cls: 'col-done', items: doneTodos.value },
])

// ---------- 便签时间线 ----------
const noteGroups = computed(() => {
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
  const y = new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
  y.setDate(y.getDate() - 1)
  if (d === y.toISOString().slice(0, 10)) return '昨天'
  return `${d.slice(0, 4)}年${Number(d.slice(5, 7))}月${Number(d.slice(8))}日`
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
    <!-- 顶部大 Tab + 搜索 -->
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
      <view class="card stat-card">
        <view class="ring" :style="{ background: ringStyle }">
          <view class="ring-hole">
            <text class="ring-pct">{{ donePct }}%</text>
            <text class="ring-label">完成度</text>
          </view>
        </view>
        <view class="stat-items">
          <view class="stat-item">
            <text class="stat-num">{{ openCount }}</text><text class="stat-label">待办中</text>
          </view>
          <view class="stat-item">
            <text class="stat-num over">{{ overdueCount }}</text><text class="stat-label">已逾期</text>
          </view>
          <view class="stat-item">
            <text class="stat-num done">{{ doneCount }}</text><text class="stat-label">已完成</text>
          </view>
        </view>
      </view>

      <view class="view-switch">
        <text :class="['v-btn', boardMode === 'list' && 'v-active']" @click="setBoard('list')">清单</text>
        <text :class="['v-btn', boardMode === 'board' && 'v-active']" @click="setBoard('board')">看板</text>
      </view>

      <!-- 清单视图 -->
      <block v-if="boardMode === 'list'">
        <view v-for="g in todoGroups" :key="g.key" class="group">
          <view class="group-head">
            <view class="g-dot" :class="g.cls" />
            <text class="group-title">{{ g.label }}</text>
            <text class="group-count">{{ g.items.length }}</text>
          </view>
          <view class="task-card" v-for="n in g.items" :key="n.id" @click="goEdit(n.id)">
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
        <view v-if="!todoGroups.length && !loading" class="empty">
          <image class="empty-doodle" src="/static/doodles/sticky.png" mode="widthFix" />
          <text>今天没有待办，轻松一天</text>
        </view>
      </block>

      <!-- 看板视图 -->
      <block v-else>
        <scroll-view scroll-x class="board" v-if="openCount || doneCount">
          <view class="board-col" v-for="col in boardColumns" :key="col.key">
            <view class="board-head" :class="col.cls">
              <text>{{ col.label }}</text>
              <text class="board-count">{{ col.items.length }}</text>
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
        <view v-else class="empty">
          <image class="empty-doodle" src="/static/doodles/sticky.png" mode="widthFix" />
          <text>还没有任务，点右下角新建</text>
        </view>
      </block>
    </block>

    <!-- ===== 便签时间线 ===== -->
    <block v-else>
      <view v-if="noteGroups.length" class="timeline">
        <view v-for="g in noteGroups" :key="g.date" class="tl-group">
          <view class="tl-date">
            <view class="tl-date-dot" />
            <text>{{ g.label }}</text>
            <text class="tl-date-count">{{ g.items.length }} 条</text>
          </view>
          <view class="tl-item" v-for="n in g.items" :key="n.id" @click="goEdit(n.id)">
            <view class="tl-line"><view class="tl-node" /></view>
            <view class="tl-card">
              <view class="tl-head">
                <text class="tl-title">{{ n.title }}</text>
                <text class="tl-time">{{ String(n.created_at).slice(11, 16) }}</text>
              </view>
              <text class="tl-content" v-if="n.content">{{ n.content }}</text>
            </view>
          </view>
        </view>
      </view>
      <view v-else-if="!loading" class="empty">
        <image class="empty-doodle" src="/static/doodles/sticky.png" mode="widthFix" />
        <text>还没有便签，记录一下今天吧</text>
      </view>
    </block>

    <view class="fab" @click="goEdit()">＋</view>
  </view>
</template>

<style scoped>
.page { padding-bottom: 150rpx; }
.top-bar { background: #FFFDF8; padding: 22rpx 24rpx 16rpx; border-bottom: 1rpx dashed #E7E3F4; }
.main-tabs { display: flex; background: #F4F1FB; border-radius: 999rpx; padding: 6rpx; margin-bottom: 18rpx; }
.m-tab { flex: 1; text-align: center; padding: 14rpx 0; font-size: 27rpx; color: #8A90A8;
  border-radius: 999rpx; letter-spacing: 1rpx; }
.m-active { background: #FFFDF8; color: #5A54B8; font-weight: 800;
  box-shadow: 0 6rpx 16rpx rgba(124, 139, 255, .16); }
.search-box { display: flex; align-items: center; gap: 16rpx; }
.search-input { flex: 1; height: 72rpx; background: #F6F4FB; border-radius: 36rpx;
  padding: 0 28rpx; font-size: 26rpx; }
.ph { color: #C3C7DA; }
.search-btn { color: #6C7BF5; font-size: 26rpx; font-weight: 600; }

/* 待办统计 */
.stat-card { display: flex; align-items: center; padding: 28rpx; }
.ring { width: 150rpx; height: 150rpx; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; }
.ring-hole { width: 112rpx; height: 112rpx; border-radius: 50%; background: #FFFDF8;
  display: flex; flex-direction: column; align-items: center; justify-content: center; }
.ring-pct { font-size: 32rpx; font-weight: 800; color: #5A54B8; }
.ring-label { font-size: 20rpx; color: #A6AAC2; margin-top: 2rpx; }
.stat-items { flex: 1; display: flex; justify-content: space-around; margin-left: 18rpx; }
.stat-item { display: flex; flex-direction: column; align-items: center; gap: 4rpx; }
.stat-num { font-size: 38rpx; font-weight: 800; color: #4A4F6B; }
.stat-num.over { color: #E45858; }
.stat-num.done { color: #1FA97F; }
.stat-label { font-size: 22rpx; color: #A6AAC2; }

/* 视图切换 */
.view-switch { display: flex; justify-content: flex-end; margin: 4rpx 28rpx 10rpx; gap: 12rpx; }
.v-btn { font-size: 23rpx; color: #8A90A8; background: #F4F1FB; border-radius: 999rpx; padding: 8rpx 26rpx; }
.v-active { background: #8B7FE8; color: #fff; font-weight: 700; }

/* 分组 */
.group { margin-top: 10rpx; }
.group-head { display: flex; align-items: center; gap: 10rpx; margin: 18rpx 28rpx 6rpx; }
.g-dot { width: 14rpx; height: 14rpx; border-radius: 7rpx; }
.g-over { background: #E45858; }
.g-today { background: #F2B45C; }
.g-week { background: #6C7BF5; }
.g-later { background: #B9AEDC; }
.group-title { font-size: 26rpx; font-weight: 700; color: #4A4F6B; letter-spacing: 1rpx; }
.group-count { font-size: 21rpx; color: #A6AAC2; }

/* 任务卡 */
.task-card { display: flex; align-items: flex-start; background: #FFFDF8; margin: 12rpx 24rpx;
  border-radius: 26rpx; padding: 24rpx 20rpx; box-shadow: 0 10rpx 26rpx rgba(124, 139, 255, .10);
  border-left: 10rpx solid #FFD98E; }
.task-card:active { opacity: .85; }
.check { width: 44rpx; height: 44rpx; border-radius: 22rpx; border: 3rpx solid #D6D9E8;
  margin-right: 16rpx; margin-top: 2rpx; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; color: #fff; font-size: 26rpx; }
.task-main { flex: 1; min-width: 0; }
.title-row { display: flex; align-items: center; gap: 12rpx; flex-wrap: wrap; }
.task-title { font-size: 29rpx; font-weight: 600; }
.pri-tag { font-size: 20rpx; border-radius: 8rpx; padding: 2rpx 12rpx; font-weight: 700; }
.pri-high { background: #FFEDEE; color: #E45858; }
.pri-low { background: #F4F2FA; color: #8A90A8; }
.pin-mark { width: 28rpx; height: 28rpx; }
.task-content { display: block; font-size: 24rpx; color: #8A90A8; margin-top: 10rpx;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meta-row { display: flex; align-items: center; margin-top: 12rpx; }
.due { font-size: 22rpx; }
.due-over { color: #E45858; font-weight: 700; }
.due-today { color: #F2A93B; font-weight: 600; }
.due-soon { color: #6C7BF5; }
.due-normal { color: #A6AAC2; }
.due-none { color: #C3C7DA; }
.pin-btn { font-size: 22rpx; color: #A6AAC2; padding: 8rpx 0 8rpx 14rpx; flex-shrink: 0; }
.pin-on { color: #6C7BF5; font-weight: 700; }

/* 看板 */
.board { white-space: nowrap; padding: 8rpx 0 10rpx; }
.board-col { display: inline-block; vertical-align: top; width: 300rpx; margin-left: 20rpx;
  background: #F7F4FC; border-radius: 26rpx; padding: 16rpx 14rpx 20rpx; white-space: normal; }
.board-head { display: flex; justify-content: space-between; align-items: center;
  font-size: 25rpx; font-weight: 700; padding: 6rpx 8rpx 14rpx; }
.board-count { font-size: 21rpx; color: #8A90A8; }
.col-over .board-head { color: #E45858; }
.col-open .board-head { color: #6C7BF5; }
.col-done .board-head { color: #1FA97F; }
.b-card { background: #FFFDF8; border-radius: 20rpx; padding: 18rpx 16rpx; margin-bottom: 14rpx;
  box-shadow: 0 6rpx 16rpx rgba(124, 139, 255, .08); }
.b-card:active { opacity: .85; }
.b-title { display: block; font-size: 25rpx; font-weight: 600; line-height: 1.5; }
.b-meta { display: flex; align-items: center; gap: 10rpx; margin-top: 10rpx; flex-wrap: wrap; }
.b-actions { display: flex; justify-content: flex-end; margin-top: 10rpx; }
.b-btn { font-size: 22rpx; color: #6C7BF5; background: #EFF1FF; border-radius: 999rpx; padding: 6rpx 20rpx; }
.b-empty { text-align: center; font-size: 22rpx; color: #C3C7DA; padding: 26rpx 0; }

/* 时间线 */
.timeline { padding: 18rpx 24rpx 0; }
.tl-group { margin-bottom: 8rpx; }
.tl-date { display: flex; align-items: center; gap: 12rpx; margin: 18rpx 4rpx 12rpx; }
.tl-date-dot { width: 16rpx; height: 16rpx; border-radius: 8rpx; background: #8B7FE8; }
.tl-date text { font-size: 28rpx; font-weight: 800; color: #4A4F6B; letter-spacing: 1rpx; }
.tl-date-count { font-size: 21rpx; color: #A6AAC2; font-weight: 400; }
.tl-item { display: flex; }
.tl-line { width: 44rpx; display: flex; flex-direction: column; align-items: center; flex-shrink: 0; }
.tl-node { width: 14rpx; height: 14rpx; border-radius: 7rpx; background: #C7B7F7; margin-top: 26rpx;
  box-shadow: 0 0 0 6rpx #F2EEFC; }
.tl-line::after { content: ''; flex: 1; width: 0; border-left: 2rpx dashed #DCD3F2; margin-top: 8rpx; }
.tl-item:last-child .tl-line::after { display: none; }
.tl-card { flex: 1; background: #FFFDF8; border-radius: 24rpx; padding: 22rpx 22rpx;
  margin-bottom: 16rpx; box-shadow: 0 10rpx 24rpx rgba(124, 139, 255, .09);
  border-left: 8rpx solid #DCD3F2; }
.tl-card:active { opacity: .85; }
.tl-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12rpx; }
.tl-title { font-size: 28rpx; font-weight: 700; }
.tl-time { font-size: 21rpx; color: #A6AAC2; }
.tl-content { font-size: 24rpx; color: #7A7F96; line-height: 1.7; margin-top: 10rpx;
  overflow: hidden; text-overflow: ellipsis; display: -webkit-box;
  -webkit-line-clamp: 2; -webkit-box-orient: vertical; }

.empty-doodle { width: 150rpx; display: block; margin: 0 auto 14rpx; opacity: .9; }

.fab { position: fixed; right: 40rpx; bottom: 200rpx; width: 108rpx; height: 108rpx;
  border-radius: 54rpx; background: linear-gradient(135deg, #7C8BFF, #A78BFA); color: #fff;
  font-size: 56rpx; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 12rpx 28rpx rgba(124, 139, 255, .35); }
.fab:active { opacity: .85; }
</style>
