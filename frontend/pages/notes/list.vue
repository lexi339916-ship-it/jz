<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { apiNotes, apiUpdateNote, apiDeleteNote } from '../../api/index.js'

const typeFilter = ref('')        // '' 全部 / todo / note
const keyword = ref('')
const items = ref([])
const total = ref(0)
const pendingCount = ref(0)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await apiNotes({
      q: keyword.value,
      note_type: typeFilter.value,
      page: 1,
      page_size: 50,
    })
    items.value = res.items
    total.value = res.total
    pendingCount.value = res.pending_count
  } catch (e) { /* 统一提示 */ } finally { loading.value = false }
}

function setType(t) { typeFilter.value = t; load() }

async function toggle(n) {
  if (n.note_type !== 'todo') return
  const next = n.status === 'open' ? 'done' : 'open'
  try {
    await apiUpdateNote(n.id, {
      title: n.title,
      content: n.content,
      note_type: n.note_type,
      status: next,
      due_at: n.due_at,
    })
    n.status = next
    if (next === 'done') {
      uni.showToast({ title: '已完成 ✓', icon: 'none' })
      pendingCount.value = Math.max(0, pendingCount.value - 1)
    } else {
      pendingCount.value += 1
    }
  } catch (e) { /* 统一提示 */ }
}

function removeNote(n) {
  uni.showModal({
    title: '确认删除',
    content: `删除“${n.title}”？`,
    success: async (res) => {
      if (res.confirm) {
        await apiDeleteNote(n.id)
        load()
      }
    },
  })
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
          placeholder="搜索便签内容" placeholder-class="ph" @confirm="load" />
        <text class="search-btn" @click="load">搜索</text>
      </view>
      <view class="type-tabs">
        <text :class="['tab', typeFilter === '' && 'tab-active']" @click="setType('')">
          全部（{{ total }}）
        </text>
        <text :class="['tab', typeFilter === 'todo' && 'tab-active']" @click="setType('todo')">
          待办（{{ pendingCount }}）
        </text>
        <text :class="['tab', typeFilter === 'note' && 'tab-active']" @click="setType('note')">便签</text>
      </view>
    </view>

    <view class="list" v-if="items.length">
      <view class="note-card" v-for="n in items" :key="n.id" @click="goEdit(n.id)">
        <view class="check" v-if="n.note_type === 'todo'"
          :class="n.status === 'done' && 'check-done'"
          @click.stop="toggle(n)">
          {{ n.status === 'done' ? '✓' : '' }}
        </view>
        <view class="note-main">
          <view class="note-title-row">
            <text class="note-title" :class="{ 'done-title': n.status === 'done' }">{{ n.title }}</text>
            <text class="note-type-tag" :class="n.note_type === 'todo' ? 'tag-todo' : 'tag-note'">
              {{ n.note_type === 'todo' ? '待办' : '便签' }}
            </text>
          </view>
          <text class="note-content" v-if="n.content">{{ n.content }}</text>
          <text class="note-due" v-if="n.note_type === 'todo' && n.due_at">
            截止：{{ String(n.due_at).slice(0, 16).replace('T', ' ') }}
          </text>
        </view>
        <text class="del" @click.stop="removeNote(n)">×</text>
      </view>
    </view>
    <view v-else class="empty">暂无便签，点右下角新建</view>

    <view class="fab" @click="goEdit()">＋</view>
  </view>
</template>

<style scoped>
.page { padding-bottom: 140rpx; }
.top-bar { background: #fff; padding: 20rpx 24rpx 8rpx; }
.search-box { display: flex; align-items: center; gap: 16rpx; }
.search-input { flex: 1; height: 72rpx; background: #f5f7fb; border-radius: 36rpx;
  padding: 0 28rpx; font-size: 26rpx; }
.ph { color: #b6bdcc; }
.search-btn { color: #2f6fed; font-size: 26rpx; font-weight: 600; }
.type-tabs { display: flex; gap: 20rpx; justify-content: center; margin: 18rpx 0 14rpx; }
.tab { font-size: 26rpx; color: #7c8595; padding: 8rpx 28rpx; border-radius: 26rpx; background: #f5f7fb; }
.tab-active { color: #fff; background: #2f6fed; font-weight: 600; }

.list { margin-top: 16rpx; }
.note-card { display: flex; align-items: flex-start; background: #fff; margin: 14rpx 24rpx;
  border-radius: 18rpx; padding: 26rpx 24rpx; box-shadow: 0 6rpx 24rpx rgba(40, 70, 120, .06); }
.note-card:active { opacity: .85; }
.check { width: 44rpx; height: 44rpx; border-radius: 22rpx; border: 3rpx solid #cbd2e0;
  margin-right: 20rpx; margin-top: 4rpx; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; color: #fff; font-size: 26rpx; }
.check-done { background: #16b07a; border-color: #16b07a; }
.note-main { flex: 1; min-width: 0; }
.note-title-row { display: flex; align-items: center; gap: 14rpx; }
.note-title { font-size: 28rpx; font-weight: 600; }
.done-title { color: #9aa3b5; text-decoration: line-through; }
.note-type-tag { font-size: 20rpx; padding: 2rpx 12rpx; border-radius: 8rpx; }
.tag-todo { background: #fdf6ec; color: #d97706; }
.tag-note { background: #eef3ff; color: #2f6fed; }
.note-content { display: block; font-size: 24rpx; color: #7c8595; margin-top: 10rpx;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.note-due { display: block; font-size: 22rpx; color: #d97706; margin-top: 10rpx; }
.del { color: #c4ccda; font-size: 40rpx; padding: 0 8rpx; }

.fab { position: fixed; right: 40rpx; bottom: 200rpx; width: 108rpx; height: 108rpx;
  border-radius: 54rpx; background: #2f6fed; color: #fff; font-size: 56rpx;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 10rpx 30rpx rgba(47, 111, 237, .4); }
.fab:active { opacity: .85; }
</style>
