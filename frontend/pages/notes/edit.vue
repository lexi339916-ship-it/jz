<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { apiNote, apiAddNote, apiUpdateNote, apiDeleteNote } from '../../api/index.js'

const editId = ref(null)
const title = ref('')
const content = ref('')
const noteType = ref('note')
const dueDate = ref('')
const dueTime = ref('09:00')
const saving = ref(false)
const today = new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
  .toISOString().slice(0, 10)

async function loadNote(id) {
  const n = await apiNote(id)
  title.value = n.title
  content.value = n.content
  noteType.value = n.note_type
  if (n.due_at) {
    dueDate.value = String(n.due_at).slice(0, 10)
    dueTime.value = String(n.due_at).slice(11, 16) || '09:00'
  }
}

function switchType(t) { noteType.value = t }

async function save() {
  if (!title.value.trim()) {
    uni.showToast({ title: '请输入标题', icon: 'none' }); return
  }
  const dueAt = noteType.value === 'todo' && dueDate.value
    ? `${dueDate.value} ${dueTime.value}:00`
    : null
  const payload = {
    title: title.value.trim(),
    content: content.value,
    note_type: noteType.value,
    status: 'open',
    due_at: dueAt,
  }
  saving.value = true
  try {
    if (editId.value) {
      // 保留原状态：先读后写
      const old = await apiNote(editId.value)
      payload.status = old.status
      await apiUpdateNote(editId.value, payload)
      uni.showToast({ title: '修改成功', icon: 'success' })
    } else {
      await apiAddNote(payload)
      uni.showToast({ title: '保存成功', icon: 'success' })
    }
    setTimeout(() => uni.navigateBack(), 700)
  } catch (e) { /* 统一提示 */ } finally { saving.value = false }
}

function removeIt() {
  uni.showModal({
    title: '确认删除',
    content: '删除后无法恢复，确定删除吗？',
    success: async (res) => {
      if (res.confirm) {
        await apiDeleteNote(editId.value)
        uni.showToast({ title: '已删除', icon: 'success' })
        setTimeout(() => uni.navigateBack(), 700)
      }
    },
  })
}

onLoad(async (options) => {
  if (options && options.id) {
    editId.value = Number(options.id)
    uni.setNavigationBarTitle({ title: '编辑便签' })
    await loadNote(editId.value)
  }
})
</script>

<template>
  <view class="page">
    <view class="card">
      <view class="type-switch">
        <text :class="['type-btn', noteType === 'note' && 'type-note']" @click="switchType('note')">普通便签</text>
        <text :class="['type-btn', noteType === 'todo' && 'type-todo']" @click="switchType('todo')">待办事项</text>
      </view>

      <text class="field-label">标题</text>
      <input class="input" v-model="title" placeholder="例如：周五交房租" placeholder-class="ph" />

      <text class="field-label">内容</text>
      <textarea class="ta" v-model="content" placeholder="选填" placeholder-class="ph" />

      <block v-if="noteType === 'todo'">
        <text class="field-label">截止时间</text>
        <view class="due-row">
          <picker mode="date" :value="dueDate || today" @change="dueDate = $event.detail.value">
            <view class="picker-value">{{ dueDate || '选择日期' }} ▾</view>
          </picker>
          <picker mode="time" :value="dueTime" @change="dueTime = $event.detail.value">
            <view class="picker-value">{{ dueTime }} ▾</view>
          </picker>
        </view>
      </block>
    </view>

    <view class="actions">
      <button class="btn btn-primary" :class="{ 'btn-disabled': saving }" :disabled="saving" @click="save">
        {{ saving ? '保存中…' : (editId ? '保存修改' : '保存便签') }}
      </button>
      <button class="btn btn-danger" v-if="editId" @click="removeIt">删除便签</button>
    </view>
  </view>
</template>

<style scoped>
.page { padding-bottom: 60rpx; }
.type-switch { display: flex; background: #f5f7fb; border-radius: 16rpx; padding: 8rpx; }
.type-btn { flex: 1; text-align: center; padding: 16rpx 0; border-radius: 12rpx;
  font-size: 28rpx; color: #7c8595; }
.type-note { background: #2f6fed; color: #fff; font-weight: 700; }
.type-todo { background: #f59f0b; color: #fff; font-weight: 700; }

.field-label { display: block; font-size: 26rpx; color: #4a5568; margin: 30rpx 0 16rpx; }
.ph { color: #b6bdcc; }
.ta { width: 100%; min-height: 200rpx; background: #f5f7fb; border-radius: 16rpx;
  padding: 24rpx; font-size: 28rpx; box-sizing: border-box; }
.due-row { display: flex; gap: 20rpx; }
.picker-value { height: 88rpx; background: #f5f7fb; border-radius: 16rpx;
  display: flex; align-items: center; justify-content: center; padding: 0 30rpx; font-size: 28rpx; }

.actions { margin: 30rpx 24rpx; display: flex; flex-direction: column; gap: 20rpx; }
</style>
