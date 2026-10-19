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
function dateOf(y, m, d) {
  return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
}

const todayStr = fmtDate(nowLocal())
const tomorrowStr = addDays(todayStr, 1)

const tab = ref('todo')               // todo / note
const viewMode = ref('calendar')      // calendar 月历 / list 清单 / board 看板
const keyword = ref('')
const loading = ref(false)

const openTodos = ref([])
const doneTodos = ref([])
const noteItems = ref([])

// 任务颜色（与编辑页一致）
const TASK_COLORS = {
  lilac: '#B9A7FF', sky: '#9DB7F5', mint: '#8FDCC2',
  peach: '#F6B8A8', sand: '#F2D48A', rose: '#F3B8CB',
}
function taskColor(c) { return TASK_COLORS[c] || TASK_COLORS.lilac }

// ---------- 数据 ----------
async function load() {
  loading.value = true
  try {
    if (tab.value === 'todo') {
      const [openRes, doneRes] = await Promise.all([
        apiNotes({ note_type: 'todo', status: 'open', q: keyword.value, page: 1, page_size: 100 }),
        apiNotes({ note_type: 'todo', status: 'done', q: keyword.value, page: 1, page_size: 100 }),
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
      status: next, due_at: n.due_at, priority: n.priority,
      pinned: n.pinned, color: n.color || 'lilac',
    })
    if (next === 'done') uni.showToast({ title: '已完成 ✓', icon: 'none' })
    load()
  } catch (e) { /* 统一提示 */ }
}

async function togglePin(n) {
  try {
    await apiUpdateNote(n.id, {
      title: n.title, content: n.content, note_type: n.note_type,
      status: n.status, due_at: n.due_at, priority: n.priority,
      pinned: !n.pinned, color: n.color || 'lilac',
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

// ---------- 月历 ----------
const calToday = nowLocal()
const calYear = ref(calToday.getFullYear())
const calMonth = ref(calToday.getMonth() + 1)   // 1-12
const calSelected = ref(todayStr)

const calTitle = computed(() => `${calYear.value}年${calMonth.value}月`)

const calSelectedLabel = computed(() => {
  const d = new Date(calSelected.value + 'T00:00:00')
  const names = '日一二三四五六'
  const prefix = calSelected.value === todayStr ? '今天 · ' : ''
  return `${prefix}${d.getMonth() + 1}月${d.getDate()}日 周${names[d.getDay()]}`
})

const tasksByDate = computed(() => {
  const map = {}
  for (const n of [...openTodos.value, ...doneTodos.value]) {
    if (!n.due_at) continue
    const d = String(n.due_at).slice(0, 10)
    if (!map[d]) map[d] = []
    map[d].push(n)
  }
  for (const key of Object.keys(map)) {
    map[key].sort((a, b) =>
      (a.status === 'done') - (b.status === 'done') ||
      String(a.due_at).localeCompare(String(b.due_at)))
  }
  return map
})

const calCells = computed(() => {
  const first = new Date(calYear.value, calMonth.value - 1, 1)
  const offset = (first.getDay() + 6) % 7   // 周一开头
  const start = new Date(first)
  start.setDate(1 - offset)
  const cells = []
  for (let i = 0; i < 42; i += 1) {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    const date = fmtDate(d)
    const tasks = tasksByDate.value[date] || []
    cells.push({
      key: date,
      date,
      day: d.getDate(),
      inMonth: d.getMonth() === calMonth.value - 1,
      isToday: date === todayStr,
      selected: date === calSelected.value,
      tags: tasks.slice(0, 2),
      more: Math.max(0, tasks.length - 2),
    })
  }
  return cells
})

const dayTaskList = computed(() => tasksByDate.value[calSelected.value] || [])

const weekDaysHeader = ['一', '二', '三', '四', '五', '六', '日']

function shiftMonth(delta) {
  let y = calYear.value
  let m = calMonth.value + delta
  if (m < 1) { y -= 1; m = 12 }
  else if (m > 12) { y += 1; m = 1 }
  calYear.value = y
  calMonth.value = m
  const daysInMonth = new Date(y, m, 0).getDate()
  const day = Math.min(Number(calSelected.value.slice(8)), daysInMonth)
  calSelected.value = dateOf(y, m, day)
}

function goToday() {
  const d = nowLocal()
  calYear.value = d.getFullYear()
  calMonth.value = d.getMonth() + 1
  calSelected.value = todayStr
}

function selectCell(c) {
  calSelected.value = c.date
  if (!c.inMonth) {
    calYear.value = Number(c.date.slice(0, 4))
    calMonth.value = Number(c.date.slice(5, 7))
  }
}

function shortTitle(title) {
  return title.length > 5 ? title.slice(0, 5) : title
}

function taskTime(n) {
  return String(n.due_at || '').slice(11, 16) || '18:00'
}

// ---------- 统计 ----------
const openCount = computed(() => openTodos.value.length)
const doneCount = computed(() => doneTodos.value.length)
const overdueCount = computed(() =>
  openTodos.value.filter(n => n.due_at && String(n.due_at).slice(0, 10) < todayStr).length)

// ---------- 清单 / 看板 ----------
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
  for (const key of Object.keys(g)) {
    g[key].sort((a, b) => String(a.due_at || '9999').localeCompare(String(b.due_at || '9999')))
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

// ---------- 生活便签 ----------
const noteDate = ref(todayStr)
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
    selected: date === noteDate.value,
  }
}))

const monthLabel = computed(() =>
  `${weekStart.value.getFullYear()}年${weekStart.value.getMonth() + 1}月`)

const noteDateLabel = computed(() => {
  const d = new Date(noteDate.value + 'T00:00:00')
  const names = '日一二三四五六'
  return `${d.getMonth() + 1}月${d.getDate()}日 周${names[d.getDay()]}`
})

const dayNotes = computed(() =>
  noteItems.value.filter(n => String(n.created_at).slice(0, 10) === noteDate.value))

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
  if (d === addDays(todayStr, -1)) return '昨天'
  return `${d.slice(0, 4)}年${Number(d.slice(5, 7))}月${Number(d.slice(8))}日`
}

function selectNoteDate(date) { noteDate.value = date }

function shiftWeek(delta) {
  weekOffset.value += delta
  noteDate.value = addDays(noteDate.value, delta * 7)
}

function jumpNoteDate(e) {
  const value = e.detail.value
  noteDate.value = value
  const target = new Date(value + 'T00:00:00')
  const base = nowLocal()
  base.setHours(0, 0, 0, 0)
  const thisMonday = new Date(base)
  thisMonday.setDate(base.getDate() - ((base.getDay() + 6) % 7))
  const targetMonday = new Date(target)
  targetMonday.setDate(target.getDate() - ((target.getDay() + 6) % 7))
  weekOffset.value = Math.round((targetMonday - thisMonday) / (7 * 86400000))
}

// ---------- 跳转 ----------
function goEdit(id) {
  uni.navigateTo({ url: '/pages/notes/edit?id=' + id })
}

function goNewTask() {
  uni.navigateTo({ url: `/pages/notes/edit?type=todo&date=${calSelected.value}` })
}

function goNewNote() {
  uni.navigateTo({ url: '/pages/notes/edit?type=note' })
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
      <view class="view-switch">
        <text :class="['v-btn', viewMode === 'calendar' && 'v-active']" @click="setView('calendar')">月历</text>
        <text :class="['v-btn', viewMode === 'list' && 'v-active']" @click="setView('list')">清单</text>
        <text :class="['v-btn', viewMode === 'board' && 'v-active']" @click="setView('board')">看板</text>
        <text class="v-stat">待办 {{ openCount }} · 逾期 {{ overdueCount }} · 完成 {{ doneCount }}</text>
      </view>

      <!-- 月历视图 -->
      <block v-if="viewMode === 'calendar'">
        <!-- 工具栏 -->
        <view class="glass cal-head">
          <text class="cal-title">{{ calTitle }}</text>
          <view class="cal-actions">
            <text class="cal-btn" @click="shiftMonth(-1)">‹</text>
            <text class="cal-today-btn" @click="goToday">今天</text>
            <text class="cal-btn" @click="shiftMonth(1)">›</text>
            <text class="cal-add" @click="goNewTask">＋</text>
          </view>
        </view>

        <!-- 月历 -->
        <view class="glass cal-panel">
          <view class="cal-week">
            <text v-for="w in weekDaysHeader" :key="w" :class="{ wk: w === '六' || w === '日' }">{{ w }}</text>
          </view>
          <view class="cal-grid">
            <view v-for="c in calCells" :key="c.key"
              class="cal-cell"
              :class="{ dim: !c.inMonth, sel: c.selected, today: c.isToday }"
              @click="selectCell(c)">
              <text class="cal-num">{{ c.day }}</text>
              <view class="cal-tags" v-if="c.tags.length">
                <view class="cal-tag" v-for="t in c.tags" :key="t.id"
                  :style="{ background: taskColor(t.color) + '55' }">
                  <text class="tag-text">{{ shortTitle(t.title) }}</text>
                </view>
                <text v-if="c.more" class="cal-more">+{{ c.more }}</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 当日任务清单 -->
        <view class="glass day-tasks">
          <view class="day-head">
            <view class="day-head-left">
              <text class="day-date">{{ calSelectedLabel }}</text>
              <text class="day-count">{{ dayTaskList.length }} 项任务</text>
            </view>
            <text class="day-add" @click="goNewTask">＋ 新建任务</text>
          </view>
          <view v-if="dayTaskList.length" class="day-list">
            <view class="task-row" v-for="n in dayTaskList" :key="n.id"
              :class="{ 'task-done': n.status === 'done' }" @click="goEdit(n.id)">
              <view class="check" :class="{ checked: n.status === 'done' }" @click.stop="toggleDone(n)">
                {{ n.status === 'done' ? '✓' : '' }}
              </view>
              <view class="task-color" :style="{ background: taskColor(n.color) }" />
              <view class="task-main">
                <view class="t-title-row">
                  <text class="t-title">{{ n.title }}</text>
                  <text v-if="PRIORITY_META[n.priority]" class="pri-tag" :class="PRIORITY_META[n.priority].cls">
                    {{ PRIORITY_META[n.priority].label }}
                  </text>
                  <image v-if="n.pinned" class="pin-mark" src="/static/icons/act_pin.png" mode="widthFix" />
                </view>
                <text class="t-note" v-if="n.content">{{ n.content }}</text>
                <view class="t-meta">
                  <text class="t-time">⏰ {{ taskTime(n) }}</text>
                  <text v-if="n.status === 'done'" class="t-done-label">已完成</text>
                </view>
              </view>
            </view>
          </view>
          <view v-else class="day-empty">
            <image class="empty-animal" src="/static/doodles/rabbit.png" mode="widthFix" />
            <text>这一天没有任务，点「＋新建任务」添加</text>
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
            <view class="task-color" :style="{ background: taskColor(n.color) }" />
            <view class="task-main">
              <view class="t-title-row">
                <text class="t-title">{{ n.title }}</text>
                <text v-if="PRIORITY_META[n.priority]" class="pri-tag" :class="PRIORITY_META[n.priority].cls">
                  {{ PRIORITY_META[n.priority].label }}
                </text>
                <image v-if="n.pinned" class="pin-mark" src="/static/icons/act_pin.png" mode="widthFix" />
              </view>
              <text class="t-note" v-if="n.content">{{ n.content }}</text>
              <view class="t-meta">
                <text v-if="dueInfo(n)" class="due" :class="dueInfo(n).cls">⏰ {{ dueInfo(n).text }}</text>
                <text v-else class="due due-none">无截止时间</text>
              </view>
            </view>
            <text class="pin-btn" :class="n.pinned && 'pin-on'" @click.stop="togglePin(n)">
              {{ n.pinned ? '取消' : '置顶' }}
            </text>
          </view>
        </view>
        <view v-if="!listGroups.length && !loading" class="glass day-empty">
          <image class="empty-animal" src="/static/doodles/rabbit.png" mode="widthFix" />
          <text>今天没有待办，轻松一天</text>
        </view>
      </block>

      <!-- 看板视图（竖向） -->
      <block v-else>
        <view class="board-v" v-if="openCount || doneCount">
          <view class="glass board-sec" v-for="col in boardColumns" :key="col.key">
            <view class="board-head" :class="col.cls">
              <text>{{ col.label }}</text>
              <text class="board-count">{{ col.items.length }}</text>
            </view>
            <view class="b-row" v-for="n in col.items" :key="n.id"
              :class="{ 'task-done': n.status === 'done' }" @click="goEdit(n.id)">
              <view class="task-color" :style="{ background: taskColor(n.color) }" />
              <view class="b-main">
                <text class="b-title">{{ n.title }}</text>
                <view class="b-meta">
                  <text v-if="dueInfo(n)" class="due" :class="dueInfo(n).cls">{{ dueInfo(n).text }}</text>
                  <text v-else class="due due-none">无截止时间</text>
                  <text v-if="PRIORITY_META[n.priority]" class="pri-tag" :class="PRIORITY_META[n.priority].cls">
                    {{ PRIORITY_META[n.priority].label }}
                  </text>
                </view>
              </view>
              <text class="b-done-btn" v-if="col.key !== 'done'" @click.stop="toggleDone(n)">完成</text>
            </view>
            <view v-if="!col.items.length" class="b-empty">暂无</view>
          </view>
        </view>
        <view v-else class="glass day-empty">
          <image class="empty-animal" src="/static/doodles/rabbit.png" mode="widthFix" />
          <text>还没有任务，点右下角新建</text>
        </view>
      </block>
    </block>

    <!-- ===== 生活便签 ===== -->
    <block v-else>
      <view class="glass week-bar">
        <text class="week-arrow" @click="shiftWeek(-1)">‹</text>
        <view class="week-days">
          <view v-for="d in weekDays" :key="d.date"
            :class="['day-cell', d.selected && 'day-active', d.isToday && 'day-today']"
            @click="selectNoteDate(d.date)">
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
          <text class="notes-sub">{{ searchActive ? `“${keyword}” 相关便签` : `${noteDateLabel} · ${dayNotes.length} 条便签` }}</text>
        </view>
        <view class="notes-head-right">
          <picker mode="date" :value="noteDate" @change="jumpNoteDate">
            <text class="pick-date">选择日期 ▾</text>
          </picker>
          <image class="week-rabbit" src="/static/doodles/rabbit.png" mode="widthFix" />
        </view>
      </view>

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

    <view class="fab" @click="tab === 'todo' ? goNewTask() : goNewNote()">＋</view>
  </view>
</template>

<style scoped>
.page { padding-bottom: 260rpx; }

/* 不透明奶油卡片：取消磨砂玻璃，保证文字清晰 */
.glass {
  background: #FFFDF8;
  border: 1rpx solid #E9E5F4;
  box-shadow: 0 10rpx 26rpx rgba(124, 139, 255, 0.10);
  border-radius: 28rpx;
}

.top-bar { background: #FFFDF8;
  padding: 22rpx 24rpx 16rpx; border-bottom: 1rpx dashed #E9E5F4; }
.main-tabs { display: flex; background: #F4F1FB; border-radius: 999rpx; padding: 6rpx; margin-bottom: 18rpx; }
.m-tab { flex: 1; text-align: center; padding: 14rpx 0; font-size: 29rpx; color: #6F748C;
  border-radius: 999rpx; letter-spacing: 1rpx; }
.m-active { background: #FFFDF8; color: #5A54B8; font-weight: 800;
  box-shadow: 0 6rpx 16rpx rgba(124, 139, 255, .16); }
.search-box { display: flex; align-items: center; gap: 16rpx; }
.search-input { flex: 1; height: 72rpx; background: #F6F4FB; border-radius: 36rpx;
  padding: 0 28rpx; font-size: 28rpx; }
.ph { color: #C3C7DA; }
.search-btn { color: #6C7BF5; font-size: 28rpx; font-weight: 600; }

/* 视图切换 */
.view-switch { display: flex; align-items: center; gap: 12rpx; margin: 16rpx 24rpx 6rpx; flex-wrap: wrap; }
.v-btn { font-size: 26rpx; color: #6F748C; background: #FFFDF8; border-radius: 999rpx;
  padding: 8rpx 24rpx; border: 1rpx solid rgba(255,255,255,.7); }
.v-active { background: #8B7FE8; color: #fff; font-weight: 700; }
.v-stat { margin-left: auto; font-size: 24rpx; color: #6F748C; }

/* 月历工具栏 */
.cal-head { display: flex; align-items: center; justify-content: space-between;
  margin: 8rpx 24rpx 12rpx; padding: 18rpx 22rpx; }
.cal-title { font-size: 32rpx; font-weight: 800; color: #4A4F6B; letter-spacing: 1rpx; }
.cal-actions { display: flex; align-items: center; gap: 12rpx; }
.cal-btn { font-size: 38rpx; color: #6B7089; padding: 0 10rpx; }
.cal-today-btn { font-size: 25rpx; color: #6C7BF5; background: #EFF1FF; border-radius: 999rpx;
  padding: 8rpx 20rpx; }
.cal-add { font-size: 40rpx; color: #fff; background: linear-gradient(135deg, #7C8BFF, #A78BFA);
  width: 62rpx; height: 62rpx; border-radius: 28rpx; display: flex; align-items: center;
  justify-content: center; line-height: 1; margin-left: 6rpx; }

/* 月历 */
.cal-panel { margin: 0 8rpx 14rpx; padding: 12rpx 4rpx 10rpx; }
.cal-week { display: grid; grid-template-columns: repeat(7, 1fr); margin-bottom: 8rpx; }
.cal-week text { text-align: center; font-size: 24rpx; color: #6F748C; }
.cal-week .wk { color: #C77BA6; }
.cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2rpx; }
.cal-cell { min-height: 136rpx; border-radius: 16rpx; padding: 6rpx 0; overflow: hidden;
  display: flex; flex-direction: column; align-items: stretch; box-sizing: border-box;
  border: 2rpx solid transparent; }
.cal-cell.dim .cal-num { color: #C3C7DA; }
.cal-cell.today { border-color: #C9BFF0; }
.cal-cell.sel { background: #EFEAFE; border: 2rpx dashed #8B7FE8; }
.cal-num { font-size: 26rpx; font-weight: 700; color: #4A4F6B; text-align: center; line-height: 32rpx; }
.cal-cell.today .cal-num { color: #8B7FE8; font-weight: 800; }
.cal-tags { display: flex; flex-direction: column; gap: 3rpx; margin-top: 2rpx; min-width: 0; }
.cal-tag { display: flex; align-items: center; border-radius: 8rpx;
  padding: 2rpx 2rpx; overflow: hidden; max-width: 100%; box-sizing: border-box; }
.tag-dot { width: 7rpx; height: 7rpx; border-radius: 4rpx; flex-shrink: 0; }
.tag-text { flex: 1; min-width: 0; font-size: 18rpx; color: #333850; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap; }
.cal-more { font-size: 20rpx; color: #6F748C; padding-left: 4rpx; }

/* 当日任务清单 */
.day-tasks { margin: 0 24rpx; padding: 22rpx 22rpx 12rpx; }
.day-head { display: flex; align-items: center; justify-content: space-between;
  padding-bottom: 14rpx; border-bottom: 1rpx dashed rgba(231, 227, 244, .9); }
.day-head-left { display: flex; flex-direction: column; gap: 4rpx; }
.day-date { font-size: 30rpx; font-weight: 800; color: #4A4F6B; }
.day-count { font-size: 24rpx; color: #7A7F96; }
.day-add { font-size: 26rpx; color: #6C7BF5; font-weight: 600; }
.day-list { display: flex; flex-direction: column; }
.task-row { display: flex; align-items: flex-start; gap: 14rpx; padding: 18rpx 0;
  border-bottom: 1rpx dashed rgba(231, 227, 244, .8); }
.task-row:last-child { border-bottom: none; }
.task-done .t-title { text-decoration: line-through; color: #A6AAC2; }
.task-done { opacity: .78; }
.check { width: 42rpx; height: 42rpx; border-radius: 21rpx; border: 3rpx solid #D6D9E8;
  flex-shrink: 0; margin-top: 2rpx; display: flex; align-items: center;
  justify-content: center; color: #fff; font-size: 26rpx; background: rgba(255,253,248,.7); }
.check.checked { background: #1FA97F; border-color: #1FA97F; }
.task-color { width: 8rpx; align-self: stretch; border-radius: 4rpx; flex-shrink: 0; margin-top: 2rpx; }
.task-main { flex: 1; min-width: 0; }
.t-title-row { display: flex; align-items: center; gap: 10rpx; flex-wrap: wrap; }
.t-title { font-size: 29rpx; font-weight: 600; color: #3A3F58; }
.t-note { display: block; font-size: 25rpx; color: #6F748C; margin-top: 6rpx;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.t-meta { display: flex; align-items: center; gap: 14rpx; margin-top: 8rpx; }
.t-time { font-size: 24rpx; color: #6F748C; }
.t-done-label { font-size: 23rpx; color: #1FA97F; background: #E9F8F2; border-radius: 8rpx;
  padding: 2rpx 10rpx; }
.pri-tag { font-size: 22rpx; border-radius: 8rpx; padding: 2rpx 10rpx; font-weight: 700; }
.pri-high { background: #FFEDEE; color: #E45858; }
.pri-low { background: rgba(244, 242, 250, .9); color: #8A90A8; }
.pin-mark { width: 26rpx; height: 26rpx; }
.day-empty { padding: 40rpx 10rpx; text-align: center; font-size: 26rpx; color: #A6AAC2; }
.empty-animal { width: 140rpx; display: block; margin: 0 auto 10rpx; }

/* 清单 */
.group { margin-top: 8rpx; }
.group-head { display: flex; align-items: center; gap: 10rpx; margin: 16rpx 28rpx 6rpx; }
.g-dot { width: 14rpx; height: 14rpx; border-radius: 7rpx; }
.g-over { background: #E45858; }
.g-today { background: #F2B45C; }
.g-week { background: #6C7BF5; }
.g-later { background: #B9AEDC; }
.group-title { font-size: 27rpx; font-weight: 700; color: #4A4F6B; }
.group-count { font-size: 24rpx; color: #A6AAC2; }
.task-card { display: flex; align-items: flex-start; margin: 12rpx 24rpx; padding: 20rpx 18rpx; gap: 12rpx; }
.task-card:active { opacity: .85; }
.due { font-size: 24rpx; }
.due-over { color: #E45858; font-weight: 700; }
.due-today { color: #F2A93B; font-weight: 600; }
.due-soon { color: #6C7BF5; }
.due-normal { color: #7A7F96; }
.due-none { color: #9AA0B5; }
.pin-btn { font-size: 25rpx; color: #A6AAC2; padding: 6rpx 0 6rpx 10rpx; flex-shrink: 0; }
.pin-on { color: #6C7BF5; font-weight: 700; }

/* 看板（竖向） */
.board-v { padding: 0 24rpx; display: flex; flex-direction: column; gap: 16rpx; margin-top: 10rpx; }
.board-sec { padding: 20rpx 22rpx 12rpx; }
.board-head { display: flex; justify-content: space-between; align-items: center;
  font-size: 28rpx; font-weight: 800; padding-bottom: 12rpx;
  border-bottom: 1rpx dashed rgba(231, 227, 244, .9); }
.board-count { font-size: 24rpx; color: #8A90A8; }
.col-over .board-head { color: #E45858; }
.col-open .board-head { color: #6C7BF5; }
.col-done .board-head { color: #1FA97F; }
.b-row { display: flex; align-items: flex-start; gap: 14rpx; padding: 16rpx 0;
  border-bottom: 1rpx dashed rgba(231, 227, 244, .8); }
.b-row:last-child { border-bottom: none; }
.b-main { flex: 1; min-width: 0; }
.b-title { font-size: 28rpx; font-weight: 600; color: #3A3F58; }
.b-meta { display: flex; align-items: center; gap: 10rpx; margin-top: 8rpx; flex-wrap: wrap; }
.b-done-btn { font-size: 25rpx; color: #6C7BF5; border: 2rpx solid #C9CFFF; border-radius: 999rpx;
  padding: 6rpx 18rpx; flex-shrink: 0; }
.b-empty { text-align: center; font-size: 25rpx; color: #C3C7DA; padding: 22rpx 0; }

/* 便签日历条 */
.week-bar { display: flex; align-items: center; margin: 18rpx 24rpx 0; padding: 16rpx 12rpx; }
.week-arrow { font-size: 40rpx; color: #6B7089; padding: 0 10rpx; flex-shrink: 0; }
.week-days { flex: 1; display: flex; justify-content: space-between; }
.day-cell { display: flex; flex-direction: column; align-items: center; gap: 4rpx;
  padding: 10rpx 6rpx; border-radius: 18rpx; min-width: 68rpx; position: relative; }
.day-wd { font-size: 23rpx; color: #6F748C; }
.day-dd { font-size: 30rpx; font-weight: 700; color: #4A4F6B; }
.day-today .day-dd { color: #8B7FE8; }
.day-active { background: rgba(139, 127, 232, .16); border: 2rpx dashed #8B7FE8; }
.note-dot { width: 8rpx; height: 8rpx; border-radius: 4rpx; background: #F2B45C; }

.notes-head { display: flex; align-items: flex-end; justify-content: space-between;
  padding: 16rpx 30rpx 4rpx; }
.notes-head-left { display: flex; flex-direction: column; }
.notes-date { display: block; font-size: 32rpx; font-weight: 800; color: #4A4F6B; letter-spacing: 1rpx; }
.notes-sub { display: block; font-size: 25rpx; color: #6F748C; margin-top: 4rpx; }
.notes-head-right { display: flex; align-items: flex-end; gap: 8rpx; }
.pick-date { font-size: 24rpx; color: #6C7BF5; background: rgba(255,253,248,.75);
  border: 1rpx solid rgba(255,255,255,.8); border-radius: 999rpx; padding: 8rpx 18rpx; }
.week-rabbit { width: 104rpx; height: 108rpx; margin-bottom: -18rpx; }

.note-list { padding: 4rpx 24rpx 0; }
.note-card { padding: 24rpx 26rpx; margin-bottom: 18rpx; }
.note-card:active { opacity: .85; }
.note-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12rpx; }
.note-title { font-size: 31rpx; font-weight: 700; color: #3A3F58; }
.note-time { font-size: 24rpx; color: #7A7F96; flex-shrink: 0; }
/* 长便签自适应：完整换行，不截断 */
.note-body { display: block; font-size: 27rpx; color: #5A5F78; line-height: 1.8; margin-top: 10rpx;
  white-space: pre-wrap; word-break: break-all; }
.notes-empty { margin: 10rpx 24rpx; padding: 46rpx 20rpx; text-align: center;
  font-size: 26rpx; color: #A6AAC2; }
.search-group { padding: 0 24rpx; }
.search-date { font-size: 26rpx; font-weight: 700; color: #8A90A8; margin: 18rpx 6rpx 10rpx; }

.page-bear { position: fixed; left: 6rpx; bottom: 178rpx; width: 116rpx; opacity: .9;
  pointer-events: none; }

.fab { position: fixed; right: 40rpx; bottom: 200rpx; width: 108rpx; height: 108rpx;
  border-radius: 54rpx; background: linear-gradient(135deg, #7C8BFF, #A78BFA); color: #fff;
  font-size: 56rpx; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 12rpx 28rpx rgba(124, 139, 255, .35); }
.fab:active { opacity: .85; }
</style>
