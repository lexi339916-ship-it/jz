<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { apiParseBill, apiParseNote, apiAddBill, apiAddNote, apiCategories, apiSummary, apiAsk } from '../../api/index.js'

const mode = ref('bill')           // bill 记账 / note 便签 / ask 问账本 / summary 总结
const text = ref('')
const loading = ref(false)
const error = ref(null)            // { status, message }
const result = ref(null)           // 解析结果
const notice = ref('')
const meta = ref(null)             // { prompt_version, model, latency_ms }
const categories = ref([])
const savingIndex = ref(-1)
const today = new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
  .toISOString().slice(0, 10)

// 月度总结
const summaryMonth = ref('')
const summaryData = ref(null)
const summaryLoading = ref(false)

// 问账本
const askText = ref('')
const askLoading = ref(false)
const askError = ref(null)
const askResult = ref(null)
const askExamples = ['本月餐饮花了多少？', '本月收支情况怎么样？', '最大的支出是什么？']

const TOOL_LABELS = {
  monthly_summary: '月度收支汇总',
  category_summary: '分类花费查询',
  top_categories: '支出分类排行',
  largest_bill: '最大支出查询',
}

function toolLabel(tool) {
  return TOOL_LABELS[tool] || tool
}

function dataSummary(res) {
  const d = res.data_used || {}
  if (res.tool === 'monthly_summary') {
    return `收入 ¥${d.income} · 支出 ¥${d.expense} · 结余 ¥${d.net} · 共 ${d.count} 笔`
  }
  if (res.tool === 'category_summary') {
    return d.found ? `${d.category}：¥${d.amount}（${d.count} 笔）` : '没有找到该分类的记录'
  }
  if (res.tool === 'top_categories') {
    const items = d.items || []
    return items.length ? items.map(i => `${i.category} ¥${i.amount}`).join(' · ') : '该月没有支出记录'
  }
  if (res.tool === 'largest_bill') {
    return d.found
      ? `${d.category} ¥${d.amount}（${d.bill_date}${d.remark ? ' · ' + d.remark : ''}）`
      : '该月没有支出记录'
  }
  return ''
}

async function ask() {
  const q = askText.value.trim()
  if (!q) {
    uni.showToast({ title: '请先输入问题', icon: 'none' })
    return
  }
  askLoading.value = true
  askError.value = null
  askResult.value = null
  try {
    askResult.value = await apiAsk(q)
  } catch (e) {
    askError.value = e
    if (e.status !== 503 && e.status !== 429) {
      uni.showToast({ title: e.message || '查询失败，请重试', icon: 'none' })
    }
  } finally {
    askLoading.value = false
  }
}

function currentMonth() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

async function loadCategories() {
  try {
    const res = await apiCategories()
    categories.value = res.items
  } catch (e) { /* 忽略 */ }
}

const typeCategories = computed(() =>
  categories.value.filter(c => c.type === (result.value?.drafts?.[0]?.type || 'expense')))

const examples = {
  bill: ['午饭花了32元', '昨天打车21块，买咖啡18元', '收到兼职工资800元'],
  note: ['周五之前要交房租2500', '明天提醒我取快递'],
}

async function parse() {
  const input = text.value.trim()
  if (!input) {
    uni.showToast({ title: '请先输入内容', icon: 'none' })
    return
  }
  loading.value = true
  error.value = null
  result.value = null
  try {
    const res = mode.value === 'bill' ? await apiParseBill(input) : await apiParseNote(input)
    result.value = mode.value === 'bill'
      ? { drafts: res.drafts }
      : { draft: res.draft }
    notice.value = res.notice || ''
    meta.value = { prompt_version: res.prompt_version, model: res.model, latency_ms: res.latency_ms }
    if (res.notice) {
      uni.showToast({ title: res.notice, icon: 'none', duration: 2500 })
    }
  } catch (e) {
    error.value = e
    // 503/429 由页面内专门区域展示，其余错误已在 request.js toast
    if (e.status !== 503 && e.status !== 429) {
      uni.showToast({ title: e.message || '解析失败，请重试', icon: 'none' })
    }
  } finally {
    loading.value = false
  }
}

function setDraftDate(draft) { draft.bill_date = draft.bill_date || today }
function setDraftCategory(draft) { if (!draft.category) draft.category = '其他' }

const missingText = (fields) => {
  const map = { amount: '金额', bill_date: '日期', category: '分类', title: '标题' }
  return fields.map(f => map[f] || f).join('、')
}

async function confirmDraft(index) {
  const d = result.value.drafts[index]
  if (d.amount === null || d.amount === '' || Number(d.amount) <= 0) {
    uni.showToast({ title: '请补全金额', icon: 'none' }); return
  }
  if (!d.bill_date) { uni.showToast({ title: '请选择日期', icon: 'none' }); return }
  savingIndex.value = index
  try {
    await apiAddBill({
      type: d.type,
      amount: Number(d.amount).toFixed(2),
      category: d.category,
      bill_date: d.bill_date,
      remark: d.remark,
      source: 'ai',   // 标记来源为 AI 草稿确认保存，便于追溯
    })
    uni.showToast({ title: '已保存账单', icon: 'success' })
    result.value.drafts.splice(index, 1)
    if (!result.value.drafts.length) reset()
  } catch (e) { /* 统一提示 */ } finally { savingIndex.value = -1 }
}

async function confirmNote() {
  const d = result.value.draft
  if (!d.title) { uni.showToast({ title: '请补全标题', icon: 'none' }); return }
  try {
    await apiAddNote({
      title: d.title,
      content: d.content,
      note_type: d.note_type,
      status: 'open',
      due_at: d.due_at,
    })
    uni.showToast({ title: '已保存便签', icon: 'success' })
    reset()
  } catch (e) { /* 统一提示 */ }
}

async function genSummary() {
  summaryLoading.value = true
  try {
    summaryData.value = await apiSummary(summaryMonth.value)
  } catch (e) {
    if (e.status !== 503 && e.status !== 429) {
      uni.showToast({ title: e.message || '生成失败，请重试', icon: 'none' })
    } else {
      summaryData.value = { error: e }
    }
  } finally { summaryLoading.value = false }
}

function reset() {
  text.value = ''
  result.value = null
  error.value = null
  notice.value = ''
  meta.value = null
}

function goManual() { uni.navigateTo({ url: '/pages/bills/edit' }) }

onShow(() => {
  if (!summaryMonth.value) summaryMonth.value = currentMonth()
  if (!categories.value.length) loadCategories()
})
</script>

<template>
  <view class="page">
    <!-- 模式切换 -->
    <view class="mode-bar">
      <text :class="['mode', mode === 'bill' && 'mode-active']" @click="mode = 'bill'; reset()">智能记账</text>
      <text :class="['mode', mode === 'note' && 'mode-active']" @click="mode = 'note'; reset()">便签整理</text>
      <text :class="['mode', mode === 'ask' && 'mode-active']" @click="mode = 'ask'">问账本</text>
      <text :class="['mode', mode === 'summary' && 'mode-active']" @click="mode = 'summary'">月度总结</text>
    </view>

    <!-- ===== 记账 / 便签 模式 ===== -->
    <view class="card" v-if="mode === 'bill' || mode === 'note'">
      <text class="hint">
        {{ mode === 'bill'
          ? '用一句话描述消费，AI 帮你生成账单草稿，确认后才会保存'
          : '把一段话交给 AI 整理成便签或待办，确认后保存' }}
      </text>
      <textarea class="ta" v-model="text" :maxlength="500"
        :placeholder="mode === 'bill' ? '例如：午饭花了32元，打车回家12块' : '例如：周五之前要给室友转房租2500'"
        placeholder-class="ph" />
      <view class="example-row" v-if="mode !== 'summary'">
        <text class="example" v-for="e in examples[mode]" :key="e" @click="text = e">{{ e }}</text>
      </view>
      <button class="btn btn-primary" :class="{ 'btn-disabled': loading }" :disabled="loading" @click="parse">
        {{ loading ? 'AI 解析中…' : 'AI 解析' }}
      </button>

      <!-- 失败/降级状态 -->
      <view class="state-box" v-if="error">
        <text class="state-text">{{ error.message }}</text>
        <view class="state-actions">
          <button class="mini-btn" v-if="error.status === 503 || error.status === 504" @click="parse">重试</button>
          <button class="mini-btn" @click="goManual">手动记账</button>
        </view>
      </view>

      <!-- AI 草稿（账单） -->
      <view v-if="mode === 'bill' && result && result.drafts">
        <view class="ai-badge">AI 生成草稿 · 请核对后保存</view>
        <view v-if="!result.drafts.length" class="empty">未识别到记账内容，换个说法试试</view>
        <view class="draft" v-for="(d, i) in result.drafts" :key="i">
          <view class="draft-row">
            <text :class="['d-type', d.type === 'income' && 'd-income']"
              @click="d.type = d.type === 'expense' ? 'income' : 'expense'">
              {{ d.type === 'income' ? '收入' : '支出' }}
            </text>
            <input class="d-amount" type="digit" v-model="d.amount" placeholder="补金额" placeholder-class="ph" />
            <text class="d-yen">元</text>
          </view>
          <view class="draft-row">
            <picker mode="selector" :range="typeCategories" range-key="name"
              @change="d.category = typeCategories[$event.detail.value]?.name || d.category">
              <text class="d-field">分类：{{ d.category || '请选择' }} ▾</text>
            </picker>
            <picker mode="date" :value="d.bill_date || today" @change="d.bill_date = $event.detail.value">
              <text class="d-field">{{ d.bill_date || '选日期' }} ▾</text>
            </picker>
          </view>
          <input class="d-remark" v-model="d.remark" placeholder="备注（可编辑）" placeholder-class="ph" />
          <view class="missing" v-if="d.missing_fields && d.missing_fields.length">
            ⚠ 待补充：{{ missingText(d.missing_fields) }}
          </view>
          <button class="btn btn-primary draft-save"
            :class="{ 'btn-disabled': savingIndex === i }" :disabled="savingIndex === i"
            @click="confirmDraft(i)">
            {{ savingIndex === i ? '保存中…' : '确认保存该账单' }}
          </button>
        </view>
      </view>

      <!-- AI 草稿（便签） -->
      <view v-if="mode === 'note' && result && result.draft">
        <view class="ai-badge">AI 生成草稿 · 请核对后保存</view>
        <view class="draft">
          <input class="d-remark" v-model="result.draft.title" placeholder="标题（可编辑）" placeholder-class="ph" />
          <textarea class="ta d-content" v-model="result.draft.content" placeholder="内容（可编辑）" />
          <view class="draft-row">
            <text :class="['d-type', result.draft.note_type === 'todo' && 'd-todo']"
              @click="result.draft.note_type = result.draft.note_type === 'todo' ? 'note' : 'todo'">
              {{ result.draft.note_type === 'todo' ? '待办' : '便签' }}
            </text>
            <picker mode="date" :value="(result.draft.due_at || '').slice(0, 10) || today"
              @change="result.draft.due_at = $event.detail.value + ' 09:00:00'"
              v-if="result.draft.note_type === 'todo'">
              <text class="d-field">截止：{{ (result.draft.due_at || '').slice(0, 10) || '选日期' }} ▾</text>
            </picker>
          </view>
          <view class="missing" v-if="result.draft.missing_fields && result.draft.missing_fields.length">
            ⚠ 待补充：{{ missingText(result.draft.missing_fields) }}
          </view>
          <button class="btn btn-primary draft-save" @click="confirmNote">确认保存便签</button>
        </view>
      </view>

      <!-- 元信息：提示词版本 / 模型 / 耗时（可解释性） -->
      <view class="meta" v-if="meta">
        模型 {{ meta.model }} · 提示词 {{ meta.prompt_version }} · 耗时 {{ meta.latency_ms }}ms
      </view>
    </view>

    <!-- ===== 问账本模式（AI 工具调用） ===== -->
    <view class="card" v-else-if="mode === 'ask'">
      <text class="hint">用自然语言问你的账本，AI 会先选择查询工具、读取真实数据，再组织回答</text>
      <textarea class="ta ask-ta" v-model="askText" :maxlength="200"
        placeholder="例如：本月餐饮花了多少？" placeholder-class="ph" />
      <view class="example-row">
        <text class="example" v-for="e in askExamples" :key="e" @click="askText = e">{{ e }}</text>
      </view>
      <button class="btn btn-primary" :class="{ 'btn-disabled': askLoading }"
        :disabled="askLoading" @click="ask">
        {{ askLoading ? '查询中…' : '向账本提问' }}
      </button>

      <view class="state-box" v-if="askError">
        <text class="state-text">{{ askError.message }}</text>
        <view class="state-actions">
          <button class="mini-btn" @click="ask">重试</button>
        </view>
      </view>

      <view v-if="askResult">
        <view class="ai-badge">AI 回答 · 数据来自你的账本</view>
        <view class="answer-card">
          <text class="answer-text">{{ askResult.answer }}</text>
          <view class="steps-row">
            <text class="step-chip" v-for="(s, i) in askResult.steps" :key="i">✓ {{ s }}</text>
          </view>
          <view class="data-used" v-if="askResult.tool !== 'unsupported'">
            <text class="data-title">数据依据：{{ toolLabel(askResult.tool) }}</text>
            <text class="data-line">{{ dataSummary(askResult) }}</text>
          </view>
        </view>
        <text class="meta">模型 {{ askResult.model }} · 提示词 {{ askResult.prompt_version }} · 耗时 {{ askResult.latency_ms }}ms</text>
      </view>
      <view v-if="!askResult && !askError" class="empty">提个问题试试，例如“本月餐饮花了多少”</view>
    </view>

    <!-- ===== 月度总结模式 ===== -->
    <view class="card" v-else>
      <view class="sum-head">
        <text class="sum-month">{{ summaryMonth }}</text>
        <button class="btn btn-primary sum-btn" :class="{ 'btn-disabled': summaryLoading }"
          :disabled="summaryLoading" @click="genSummary">
          {{ summaryLoading ? '生成中…' : '生成本月分析' }}
        </button>
      </view>
      <view class="state-box" v-if="summaryData && summaryData.error">
        <text class="state-text">{{ summaryData.error.message }}</text>
        <view class="state-actions">
          <button class="mini-btn" v-if="summaryData.error.status === 503 || summaryData.error.status === 504"
            @click="genSummary">重试</button>
        </view>
      </view>
      <view v-if="summaryData && !summaryData.error">
        <view class="sum-nums">
          <text class="sum-item">收入 ¥{{ Number(summaryData.income).toFixed(2) }}</text>
          <text class="sum-item">支出 ¥{{ Number(summaryData.expense).toFixed(2) }}</text>
          <text class="sum-item">结余 ¥{{ Number(summaryData.net).toFixed(2) }}</text>
        </view>
        <view class="ai-badge">AI 生成 · 基于真实统计数据，仅供参考</view>
        <text class="sum-text">{{ summaryData.summary }}</text>
        <text class="meta" v-if="summaryData.model">模型 {{ summaryData.model }}</text>
      </view>
      <view v-if="!summaryData" class="empty">点击上方按钮，AI 将基于本月的真实账单数据生成分析</view>
    </view>
  </view>
</template>

<style scoped>
.page { padding-bottom: 60rpx; }
.mode-bar { display: flex; background: #fff; margin: 20rpx 24rpx; border-radius: 18rpx; padding: 8rpx; }
.mode { flex: 1; text-align: center; padding: 18rpx 0; font-size: 27rpx; color: #7c8595; border-radius: 14rpx; }
.mode-active { background: #2f6fed; color: #fff; font-weight: 700; }

.hint { display: block; font-size: 24rpx; color: #7c8595; margin-bottom: 20rpx; }
.ta { width: 100%; min-height: 160rpx; background: #f5f7fb; border-radius: 16rpx;
  padding: 24rpx; font-size: 28rpx; box-sizing: border-box; }
.ph { color: #b6bdcc; }
.example-row { display: flex; flex-wrap: wrap; gap: 14rpx; margin: 20rpx 0; }
.example { font-size: 22rpx; color: #2f6fed; background: #eef3ff; border-radius: 20rpx; padding: 8rpx 20rpx; }

.state-box { margin-top: 24rpx; background: #fdf2f2; border-radius: 16rpx; padding: 24rpx; }
.state-text { font-size: 24rpx; color: #c53030; }
.state-actions { display: flex; gap: 20rpx; margin-top: 18rpx; }
.mini-btn { margin: 0; font-size: 24rpx; color: #2f6fed; background: #fff;
  border: 2rpx solid #2f6fed; border-radius: 30rpx; padding: 0 30rpx; height: 60rpx; line-height: 60rpx; }

.ai-badge { margin: 26rpx 0 16rpx; }
.draft { background: #f8faff; border: 2rpx solid #e3ebfd; border-radius: 18rpx; padding: 24rpx; margin-bottom: 22rpx; }
.draft-row { display: flex; align-items: center; gap: 20rpx; margin-bottom: 18rpx; }
.d-type { padding: 10rpx 24rpx; border-radius: 12rpx; background: #2f6fed; color: #fff; font-size: 24rpx; font-weight: 700; }
.d-income { background: #16b07a; }
.d-todo { background: #f59f0b; }
.d-amount { flex: 1; height: 72rpx; background: #fff; border-radius: 12rpx;
  padding: 0 20rpx; font-size: 30rpx; font-weight: 700; }
.d-yen { font-size: 26rpx; color: #7c8595; }
.d-field { font-size: 25rpx; color: #2f4f8f; background: #fff; border-radius: 12rpx; padding: 14rpx 20rpx; }
.d-remark { width: 100%; height: 76rpx; background: #fff; border-radius: 12rpx;
  padding: 0 20rpx; font-size: 26rpx; margin-bottom: 18rpx; box-sizing: border-box; }
.d-content { min-height: 140rpx; margin-bottom: 18rpx; background: #fff; }
.missing { font-size: 23rpx; color: #d97706; background: #fdf6ec; border-radius: 10rpx; padding: 12rpx 18rpx; margin-bottom: 18rpx; }
.draft-save { margin-top: 6rpx; height: 78rpx; font-size: 27rpx; }

.meta { font-size: 21rpx; color: #9aa3b5; margin-top: 20rpx; }

.sum-head { display: flex; align-items: center; justify-content: space-between; }
.sum-month { font-size: 32rpx; font-weight: 700; }
.sum-btn { margin: 0; width: 300rpx; height: 76rpx; font-size: 26rpx; }
.sum-nums { display: flex; gap: 26rpx; margin: 26rpx 0; flex-wrap: wrap; }
.sum-item { font-size: 24rpx; color: #4a5568; background: #f5f7fb; border-radius: 12rpx; padding: 12rpx 20rpx; }
.sum-text { display: block; font-size: 27rpx; line-height: 1.8; color: #263246; margin-top: 14rpx; }

/* 问账本 */
.ask-ta { min-height: 120rpx; }
.answer-card { background: #f8faff; border: 2rpx solid #e3ebfd; border-radius: 18rpx;
  padding: 26rpx 24rpx; }
.answer-text { display: block; font-size: 29rpx; line-height: 1.75; color: #263246; font-weight: 500; }
.steps-row { display: flex; flex-wrap: wrap; gap: 12rpx; margin-top: 22rpx; }
.step-chip { font-size: 21rpx; color: #2f6fed; background: #eef3ff; border-radius: 20rpx;
  padding: 6rpx 18rpx; }
.data-used { margin-top: 22rpx; padding-top: 18rpx; border-top: 1rpx dashed #d9e3f8; }
.data-title { display: block; font-size: 22rpx; color: #7c8595; }
.data-line { display: block; font-size: 24rpx; color: #33415c; margin-top: 8rpx; }
</style>
