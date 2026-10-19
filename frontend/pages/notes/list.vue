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

const view = ref('today')          // today / upcoming / done / all
const keyword = ref('')
const items = ref([])
const total = ref(0)
const pendingCount = ref(0)
const loading = ref(false)

const VIEWS = [
  { key: 'today', label: '今天' },
  { key: 'upcoming', label: '近期' },
  { key: 'done', label: '已完成' },
  { key: 'all', label: '全部' },
]

const emptyText = computed(() => {
  if (view.value === 'today') return '今天没有待办，轻松一天'
  if (view.value === 'upcoming') return '近期没有安排，点右下角新建任务'
  if (view.value === 'done') return '还没有完成的任务'
  return '暂无便签与任务'
})

async function load() {
  loading.value = true
  try {
    const res = await apiNotes({
      view: view.value === 'all' ? '' : view.value,
      q: keyword.value,
      page: 1,
      page_size: 50,
    })
    items.value = res.items
    total.value = res.total
    pendingCount.value = res.pending_count
  } catch (e) { /* 统一提示 */ } finally { loading.value = false }
}

function setView(v) { view.value = v; load() }

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

// 截止时间展示：逾期红 / 今天橙 / 明天蓝 / 其他灰
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

function goEdit(id) {
  uni.navigateTo({ url: '/pages/notes/edit' + (id ? '?id=' + id : '') })
}

onShow(load)
</script>

<template>
  <view class="page">
    <view class="top-bar">
      <view class="search-box">
        <input class="search-input" v-model="keyword" confirm-type="search"
          placeholder="搜索任务或便签" placeholder-class="ph" @confirm="load" />
        <text class="search-btn" @click="load">搜索</text>
      </view>
      <view class="type-tabs">
        <text v-for="v in VIEWS" :key="v.key"
          :class="['tab', view === v.key && 'tab-active']" @click="setView(v.key)">
          {{ v.label }}
        </text>
      </view>
      <view class="pending-line" v-if="pendingCount > 0">
        未完成任务 <text class="pending-num">{{ pendingCount }}</text> 项
      </view>
    </view>

    <view class="list" v-if="items.length">
      <view class="task-card" v-for="n in items" :key="n.id" @click="goEdit(n.id)">
        <view v-if="n.note_type === 'todo'" class="check"
          :class="n.status === 'done' && 'check-done'" @click.stop="toggleDone(n)">
          {{ n.status === 'done' ? '✓' : '' }}
        </view>
        <view v-else class="note-mark">📄</view>
        <view class="task-main">
          <view class="title-row">
            <text class="task-title" :class="{ 'done-title': n.status === 'done' }">{{ n.title }}</text>
            <text v-if="PRIORITY_META[n.priority]" class="pri-tag" :class="PRIORITY_META[n.priority].cls">
              {{ PRIORITY_META[n.priority].label }}
            </text>
            <text v-if="n.pinned" class="pin-mark">📌</text>
          </view>
          <text class="task-content" v-if="n.content">{{ n.content }}</text>
          <view class="meta-row">
            <text v-if="dueInfo(n)" class="due" :class="dueInfo(n).cls">⏰ {{ dueInfo(n).text }}</text>
            <text v-else class="due due-none">{{ n.note_type === 'note' ? '便签' : '无截止时间' }}</text>
          </view>
        </view>
        <text class="pin-btn" :class="n.pinned && 'pin-on'" @click.stop="togglePin(n)">
          {{ n.pinned ? '取消' : '置顶' }}
        </text>
      </view>
    </view>
    <view v-else-if="!loading" class="empty">{{ emptyText }}</view>

    <view class="fab" @click="goEdit()">＋</view>
  </view>
</template>

<style scoped>
.page { padding-bottom: 140rpx; }
.top-bar { background: #FFFDF8; padding: 20rpx 24rpx 10rpx; }
.search-box { display: flex; align-items: center; gap: 16rpx; }
.search-input { flex: 1; height: 72rpx; background: #F6F4FB; border-radius: 36rpx;
  padding: 0 28rpx; font-size: 26rpx; }
.ph { color: #C3C7DA; }
.search-btn { color: #6C7BF5; font-size: 26rpx; font-weight: 600; }
.type-tabs { display: flex; gap: 16rpx; justify-content: center; margin: 18rpx 0 6rpx; }
.tab { font-size: 26rpx; color: #8A90A8; padding: 8rpx 28rpx; border-radius: 30rpx; background: #F6F4FB; }
.tab-active { color: #fff; background: #6C7BF5; font-weight: 600; }
.pending-line { text-align: center; font-size: 22rpx; color: #A6AAC2; padding: 10rpx 0 4rpx; }
.pending-num { color: #6C7BF5; font-weight: 700; }

.list { margin-top: 16rpx; }
.task-card { display: flex; align-items: flex-start; background: #FFFDF8; margin: 14rpx 24rpx;
  border-radius: 26rpx; padding: 26rpx 22rpx; box-shadow: 0 10rpx 26rpx rgba(124, 139, 255, .10);
  border-left: 10rpx solid #FFD98E; }
.task-card:active { opacity: .85; }
.check { width: 44rpx; height: 44rpx; border-radius: 26rpx; border: 3rpx solid #D6D9E8;
  margin-right: 18rpx; margin-top: 2rpx; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; color: #fff; font-size: 26rpx; }
.check-done { background: #45C39A; border-color: #45C39A; }
.note-mark { width: 44rpx; margin-right: 18rpx; margin-top: 2rpx; flex-shrink: 0;
  font-size: 30rpx; text-align: center; }
.task-main { flex: 1; min-width: 0; }
.title-row { display: flex; align-items: center; gap: 12rpx; flex-wrap: wrap; }
.task-title { font-size: 29rpx; font-weight: 600; }
.done-title { color: #A6AAC2; text-decoration: line-through; }
.pri-tag { font-size: 20rpx; border-radius: 8rpx; padding: 2rpx 12rpx; font-weight: 700; }
.pri-high { background: #FFEDEE; color: #F27E7E; }
.pri-low { background: #F4F2FA; color: #8b93a5; }
.pin-mark { font-size: 22rpx; }
.task-content { display: block; font-size: 24rpx; color: #8A90A8; margin-top: 10rpx;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meta-row { display: flex; align-items: center; margin-top: 12rpx; }
.due { font-size: 22rpx; }
.due-over { color: #F27E7E; font-weight: 700; }
.due-today { color: #F2B45C; font-weight: 600; }
.due-soon { color: #6C7BF5; }
.due-normal { color: #A6AAC2; }
.due-none { color: #C3C7DA; }
.pin-btn { font-size: 22rpx; color: #A6AAC2; padding: 8rpx 0 8rpx 16rpx; flex-shrink: 0; }
.pin-on { color: #6C7BF5; font-weight: 700; }

.fab { position: fixed; right: 40rpx; bottom: 200rpx; width: 108rpx; height: 108rpx;
  border-radius: 54rpx; background: #6C7BF5; color: #fff; font-size: 56rpx;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 10rpx 30rpx rgba(124, 139, 255, .35); }
.fab:active { opacity: .85; }
</style>
