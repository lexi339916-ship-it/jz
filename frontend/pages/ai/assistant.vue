<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import {
  apiParseBill, apiParseNote, apiAddBill, apiAddNote, apiCategories,
  apiSummary, apiAsk, apiParseReceipt,
} from '../../api/index.js'

const mode = ref('home')           // home / bill / note / ask / summary
const text = ref('')
const loading = ref(false)
const error = ref(null)            // { status, message }
const result = ref(null)           // 解析结果
const notice = ref('')
const meta = ref(null)             // { prompt_version, model, latency_ms }
const categories = ref([])
const savingIndex = ref(-1)
const uploading = ref(false)
const receiptPreview = ref('')
const today = new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
  .toISOString().slice(0, 10)

const MODE_LABELS = {
  bill: '智能记账', note: '任务提取', ask: '问账本', summary: '消费总结',
}

const MODES = [
  { key: 'bill', name: '智能记账', desc: '一句话记账 · 支持截图识别', icon: '/static/icons/act_pencil.png', bg: '#EEF1FF' },
  { key: 'note', name: '任务提取', desc: '一段话拆成待办与便签', icon: '/static/icons/act_note.png', bg: '#FFF6E7' },
  { key: 'ask', name: '问账本', desc: '自然语言查询你的账目', icon: '/static/icons/act_chart.png', bg: '#E9F8F2' },
  { key: 'summary', name: '消费总结', desc: '本周 / 本月消费分析', icon: '/static/icons/act_sparkle.png', bg: '#F4F0FF' },
]

// ---------- 常用语（本机保存，无需后端） ----------
const PHRASE_KEY = 'ai_phrases'
const phrases = ref(JSON.parse(uni.getStorageSync(PHRASE_KEY) || '[]'))

function persistPhrases() {
  uni.setStorageSync(PHRASE_KEY, JSON.stringify(phrases.value))
}

function savePhrase() {
  const t = text.value.trim()
  if (!t) { uni.showToast({ title: '先输入内容再收藏', icon: 'none' }); return }
  if (phrases.value.includes(t)) { uni.showToast({ title: '已经在常用语里了', icon: 'none' }); return }
  phrases.value = [t, ...phrases.value].slice(0, 8)
  persistPhrases()
  uni.showToast({ title: '已收藏为常用语', icon: 'success' })
}

function removePhrase(index) {
  phrases.value.splice(index, 1)
  persistPhrases()
}

function usePhrase(p) {
  text.value = p
  mode.value = 'bill'
  clearResult()
}

// ---------- 最近生成的草稿（本机保存） ----------
const RECENT_KEY = 'ai_recent_drafts'
const recentDrafts = ref(JSON.parse(uni.getStorageSync(RECENT_KEY) || '[]'))

function rememberDrafts(kind, drafts) {
  if (!drafts || !drafts.length) return
  recentDrafts.value = [{ kind, drafts, ts: Date.now() }, ...recentDrafts.value].slice(0, 3)
  uni.setStorageSync(RECENT_KEY, JSON.stringify(recentDrafts.value))
}

function recentSummary(r) {
  const d = r.drafts[0] || {}
  if (r.kind === 'bill' || r.kind === 'receipt') {
    return `${d.category || '未分类'} · ¥${d.amount || '?'}${d.remark ? ' · ' + d.remark : ''}`
  }
  return d.title || '任务草稿'
}

function recentLabel(r) {
  if (r.kind === 'receipt') return '截图识别草稿'
  if (r.kind === 'bill') return '记账草稿'
  return '任务草稿'
}

function useRecent(r) {
  mode.value = (r.kind === 'bill' || r.kind === 'receipt') ? 'bill' : 'note'
  error.value = null
  notice.value = ''
  meta.value = null
  result.value = { drafts: JSON.parse(JSON.stringify(r.drafts)) }
  if (r.kind === 'receipt') result.value.isReceipt = true
}

function clearRecent() {
  recentDrafts.value = []
  uni.removeStorageSync(RECENT_KEY)
}

// ---------- 模式切换 ----------
function enterMode(key) {
  mode.value = key
  clearResult()
}

function goHome() {
  mode.value = 'home'
}

function clearResult() {
  result.value = null
  error.value = null
  notice.value = ''
  meta.value = null
}

// ---------- 截图识别 ----------
const RECEIPT_STATUS_LABEL = {
  success: '交易成功', pending: '处理中', refunded: '已退款',
  failed: '交易失败', unknown: '状态未知',
}

function chooseReceipt() {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    success: async (res) => {
      const path = res.tempFilePaths && res.tempFilePaths[0]
      if (!path) return
      receiptPreview.value = path
      uploading.value = true
      error.value = null
      result.value = null
      try {
        const data = await apiParseReceipt(path)
        if (!data.found) {
          receiptPreview.value = ''
          uni.showToast({ title: data.notice || '未识别到支付信息', icon: 'none', duration: 2500 })
          return
        }
        result.value = { drafts: data.drafts || [], isReceipt: true }
        notice.value = data.notice || ''
        meta.value = { prompt_version: data.prompt_version, model: data.model, latency_ms: data.latency_ms }
        rememberDrafts('receipt', data.drafts || [])
        if (!data.drafts || !data.drafts.length) {
          uni.showToast({ title: data.notice || '未生成账单草稿', icon: 'none', duration: 2500 })
        }
      } catch (e) {
        receiptPreview.value = ''
      } finally {
        uploading.value = false
      }
    },
  })
}

function statusLabel(s) {
  return RECEIPT_STATUS_LABEL[s] || s || '状态未知'
}

// ---------- 解析 ----------
const examples = {
  bill: ['午饭花了32元', '昨天打车21块，买咖啡18元', '收到兼职工资800元'],
  note: ['周五之前要交房租2500', '明天提醒我取快递', '周五之前交课程设计报告，明天下午去超市买生活用品'],
}

const typeCategories = computed(() =>
  categories.value.filter(c => c.type === (result.value?.drafts?.[0]?.type || 'expense')))

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
    result.value = { drafts: res.drafts }
    notice.value = res.notice || ''
    meta.value = { prompt_version: res.prompt_version, model: res.model, latency_ms: res.latency_ms }
    rememberDrafts('bill', res.drafts)
    if (res.notice) {
      uni.showToast({ title: res.notice, icon: 'none', duration: 2500 })
    }
  } catch (e) {
    error.value = e
    if (e.status !== 503 && e.status !== 429) {
      uni.showToast({ title: e.message || '解析失败，请重试', icon: 'none' })
    }
  } finally {
    loading.value = false
  }
}

const missingText = (fields) => {
  const map = {
    amount: '金额', bill_date: '日期', category: '分类', title: '标题', due_at: '时间',
    pay_channel: '支付渠道', funding_account: '扣款账户', merchant: '商户',
  }
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
    const remark = [d.remark, d.bill_time].filter(Boolean).join(' ')
    await apiAddBill({
      type: d.type,
      amount: Number(d.amount).toFixed(2),
      category: d.category,
      bill_date: d.bill_date,
      remark: remark.slice(0, 200),
      source: result.value.isReceipt ? 'receipt' : 'ai',
      pay_channel: d.pay_channel || '',
      funding_account: d.funding_account || '',
    })
    uni.showToast({ title: '已保存账单', icon: 'success' })
    result.value.drafts.splice(index, 1)
    if (!result.value.drafts.length) clearResult()
  } catch (e) { /* 统一提示 */ } finally { savingIndex.value = -1 }
}

async function confirmNote(index) {
  const d = result.value.drafts[index]
  if (!d.title || !d.title.trim()) { uni.showToast({ title: '请补全标题', icon: 'none' }); return }
  savingIndex.value = index
  try {
    await apiAddNote({
      title: d.title.trim(),
      content: d.content || '',
      note_type: d.note_type,
      status: 'open',
      due_at: d.note_type === 'todo' ? d.due_at : null,
      priority: d.priority || 'medium',
      pinned: false,
    })
    uni.showToast({ title: '已保存任务', icon: 'success' })
    result.value.drafts.splice(index, 1)
    if (!result.value.drafts.length) clearResult()
  } catch (e) { /* 统一提示 */ } finally { savingIndex.value = -1 }
}

// ---------- 总结 ----------
const summaryPeriod = ref('month')
const summaryData = ref(null)
const summaryLoading = ref(false)

async function genSummary() {
  summaryLoading.value = true
  try {
    summaryData.value = await apiSummary(summaryPeriod.value)
  } catch (e) {
    if (e.status !== 503 && e.status !== 429) {
      uni.showToast({ title: e.message || '生成失败，请重试', icon: 'none' })
    } else {
      summaryData.value = { error: e }
    }
  } finally { summaryLoading.value = false }
}

// ---------- 问账本 ----------
const askText = ref('')
const askLoading = ref(false)
const askError = ref(null)
const askResult = ref(null)
const lastAskQuestion = ref('')
const askExamples = [
  '这个月钱主要花在哪里？',
  '和上个月相比餐饮增加了多少？',
  '微信支付花了多少？',
  '帮我制定下个月预算',
]

const TOOL_LABELS = {
  monthly_summary: '月度收支汇总',
  category_summary: '分类花费查询',
  top_categories: '支出分类排行',
  largest_bill: '最大支出查询',
  category_compare: '分类环比对比',
  budget_suggestion: '预算建议数据',
  savings_calc: '储蓄计算',
  channel_summary: '渠道花费汇总',
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
  if (res.tool === 'category_compare') {
    if (d.found === false) return '没有找到该分类'
    const pctText = d.change_pct === null ? '上月无记录' :
      `${d.change_pct > 0 ? '+' : ''}${d.change_pct}%`
    return `${d.category}：本月 ¥${d.current_amount} vs 上月 ¥${d.previous_amount}（${pctText}，差额 ¥${d.diff}）`
  }
  if (res.tool === 'budget_suggestion') {
    const items = d.items || []
    return `近 ${d.months} 个月月均：` +
      items.map(i => `${i.category} ¥${i.monthly_avg}`).join(' · ') +
      ` · 合计 ¥${d.total_monthly_avg}`
  }
  if (res.tool === 'savings_calc') {
    return `每天 ¥${d.daily_amount} → 每月省 ¥${d.monthly_saving} · 每年 ¥${d.yearly_saving}（${d.basis}）`
  }
  if (res.tool === 'channel_summary') {
    const items = d.items || []
    return items.length
      ? items.map(i => `${i.channel} ¥${i.amount}（${i.count}笔）`).join(' · ')
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
  lastAskQuestion.value = q
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

function useAskExample(e) {
  askText.value = e
}

function goManual() { uni.navigateTo({ url: '/pages/bills/edit' }) }

onShow(() => {
  if (!categories.value.length) loadCategories()
})

async function loadCategories() {
  try {
    const res = await apiCategories()
    categories.value = res.items
  } catch (e) { /* 忽略 */ }
}
</script>

<template>
  <view class="page">
    <!-- 工作区顶部返回 -->
    <view class="work-top" v-if="mode !== 'home'">
      <text class="back-btn" @click="goHome">‹ 助手首页</text>
      <text class="work-title">{{ MODE_LABELS[mode] }}</text>
      <text class="work-spacer" />
    </view>

    <!-- ===== 助手首页 ===== -->
    <block v-if="mode === 'home'">
      <view class="ai-hero">
        <image class="ai-hero-cat" src="/static/doodles/cat.png" mode="widthFix" />
        <view class="ai-hero-text">
          <text class="ai-hero-title">AI 小助手</text>
          <text class="ai-hero-sub">记账、整理、问答、总结，都可以交给它</text>
        </view>
      </view>

      <view class="mode-grid">
        <view class="mode-card" v-for="m in MODES" :key="m.key"
          :style="{ background: m.bg }" @click="enterMode(m.key)">
          <image class="mode-icon" :src="m.icon" mode="widthFix" />
          <text class="mode-name">{{ m.name }}</text>
          <text class="mode-desc">{{ m.desc }}</text>
        </view>
      </view>

      <!-- 常用语 -->
      <view class="card">
        <view class="section-title">
          <text>常用语</text>
          <text class="section-more">点一下直接使用</text>
        </view>
        <view v-if="phrases.length" class="phrase-list">
          <view class="phrase-chip" v-for="(p, i) in phrases" :key="i">
            <text class="phrase-text" @click="usePhrase(p)">{{ p }}</text>
            <text class="phrase-del" @click="removePhrase(i)">×</text>
          </view>
        </view>
        <text v-else class="phrase-empty">还没有常用语：在智能记账输入一句话后，点「收藏为常用语」</text>
      </view>

      <!-- 最近草稿 -->
      <view class="card" v-if="recentDrafts.length">
        <view class="section-title">
          <text>最近生成</text>
          <text class="section-more" @click="clearRecent">清空</text>
        </view>
        <view class="recent-item" v-for="(r, i) in recentDrafts" :key="i" @click="useRecent(r)">
          <image class="recent-icon" :src="r.kind === 'note' ? '/static/icons/act_note.png' : (r.kind === 'receipt' ? '/static/icons/act_camera.png' : '/static/icons/act_pencil.png')" mode="widthFix" />
          <view class="recent-main">
            <text class="recent-label">{{ recentLabel(r) }}</text>
            <text class="recent-summary">{{ recentSummary(r) }}</text>
          </view>
          <text class="recent-use">再用一次 ›</text>
        </view>
      </view>
    </block>

    <!-- ===== 记账 / 任务 ===== -->
    <view class="card" v-else-if="mode === 'bill' || mode === 'note'">
      <text class="hint">
        {{ mode === 'bill'
          ? '用一句话描述消费，AI 帮你生成账单草稿，确认后才会保存'
          : '把一段话交给 AI，拆成待办任务或便签，逐条确认保存' }}
      </text>
      <textarea class="ta" v-model="text" :maxlength="500"
        :placeholder="mode === 'bill' ? '例如：午饭花了32元，打车回家12块' : '例如：周五之前要交房租2500'"
        placeholder-class="ph" />
      <view class="example-row">
        <text class="example" v-for="e in examples[mode]" :key="e" @click="text = e">{{ e }}</text>
      </view>

      <!-- 截图记账 -->
      <view class="upload-row" v-if="mode === 'bill'">
        <button class="upload-btn" :disabled="uploading" @click="chooseReceipt">
          <image class="upload-btn-img" src="/static/icons/act_camera.png" mode="widthFix" />
          <text>{{ uploading ? '识别中…' : '上传支付截图识别' }}</text>
        </button>
        <text class="upload-hint">支持支付截图、小票照片，自动提取金额/商户/日期/渠道</text>
      </view>
      <view v-if="receiptPreview" class="receipt-preview">
        <image :src="receiptPreview" mode="widthFix" class="receipt-img" />
      </view>

      <view class="btn-row">
        <button class="btn btn-primary" :class="{ 'btn-disabled': loading }" :disabled="loading" @click="parse">
          {{ loading ? 'AI 解析中…' : 'AI 解析' }}
        </button>
        <text class="phrase-save" @click="savePhrase">☆ 收藏为常用语</text>
      </view>

      <!-- 失败/降级状态 -->
      <view class="state-box" v-if="error">
        <text class="state-text">{{ error.message }}</text>
        <view class="state-actions">
          <button class="mini-btn" v-if="error.status === 503 || error.status === 504" @click="parse">重试</button>
          <button class="mini-btn" @click="goManual">手动记账</button>
        </view>
      </view>

      <!-- 账单草稿 -->
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
          <view class="receipt-info" v-if="result.isReceipt">
            <view class="ri-row">
              <text class="ri-label">交易状态</text>
              <text class="ri-val">{{ statusLabel(d.status) }}</text>
            </view>
            <view class="ri-row">
              <text class="ri-label">支付渠道</text>
              <text class="ri-val" :class="{ 'ri-wait': !d.pay_channel }">{{ d.pay_channel || '待确认' }}</text>
            </view>
            <view class="ri-row">
              <text class="ri-label">扣款账户</text>
              <text class="ri-val" :class="{ 'ri-wait': !d.funding_account }">
                {{ d.funding_account || '待确认（截图中未显示）' }}
              </text>
            </view>
            <view class="dup-warn" v-if="d.duplicate_suspect">⚠ {{ d.duplicate_hint }}</view>
          </view>
          <view class="missing" v-if="d.missing_fields && d.missing_fields.length">
            ⚠ 待补充：{{ missingText(d.missing_fields) }}
          </view>
          <button class="btn btn-primary draft-save"
            :class="{ 'btn-disabled': savingIndex === i }" :disabled="savingIndex === i"
            @click="confirmDraft(i)">
            {{ savingIndex === i ? '保存中…' : '确认保存该账单' }}
          </button>
        </view>
        <view class="receipt-actions" v-if="result.isReceipt">
          <button class="mini-btn" @click="chooseReceipt">重新识别</button>
          <button class="mini-btn" @click="clearResult(); receiptPreview = ''">取消本次识别</button>
        </view>
      </view>

      <!-- 任务草稿 -->
      <view v-if="mode === 'note' && result && result.drafts">
        <view class="ai-badge">AI 生成任务草稿 · 请逐条核对后保存</view>
        <view v-if="!result.drafts.length" class="empty">未识别到任务内容，换个说法试试</view>
        <view class="draft" v-for="(d, i) in result.drafts" :key="i">
          <input class="d-remark" v-model="d.title" placeholder="标题（可编辑）" placeholder-class="ph" />
          <textarea class="ta d-content" v-model="d.content" placeholder="内容（可编辑）" />
          <view class="draft-row">
            <text :class="['d-type', d.note_type === 'todo' && 'd-todo']"
              @click="d.note_type = d.note_type === 'todo' ? 'note' : 'todo'">
              {{ d.note_type === 'todo' ? '待办' : '便签' }}
            </text>
            <picker v-if="d.note_type === 'todo'" mode="date"
              :value="(d.due_at || '').slice(0, 10) || today"
              @change="d.due_at = $event.detail.value + ' 18:00:00'">
              <text class="d-field">截止：{{ (d.due_at || '').slice(0, 10) || '选日期' }} ▾</text>
            </picker>
          </view>
          <view class="pri-chips" v-if="d.note_type === 'todo'">
            <text v-for="p in ['high', 'medium', 'low']" :key="p"
              :class="['pri-chip', 'chip-' + p, d.priority === p && 'chip-active']"
              @click="d.priority = p">
              {{ { high: '高', medium: '中', low: '低' }[p] }}
            </text>
          </view>
          <view class="missing" v-if="d.missing_fields && d.missing_fields.length">
            ⚠ 待补充：{{ missingText(d.missing_fields) }}
          </view>
          <button class="btn btn-primary draft-save"
            :class="{ 'btn-disabled': savingIndex === i }" :disabled="savingIndex === i"
            @click="confirmNote(i)">
            {{ savingIndex === i ? '保存中…' : '确认保存该任务' }}
          </button>
        </view>
      </view>

      <view class="meta" v-if="meta">
        模型 {{ meta.model }} · 提示词 {{ meta.prompt_version }} · 耗时 {{ meta.latency_ms }}ms
      </view>
    </view>

    <!-- ===== 问账本（聊天气泡） ===== -->
    <view class="card" v-else-if="mode === 'ask'">
      <text class="hint">用自然语言问你的账本，AI 会先查数据再回答</text>

      <view class="chat" v-if="askResult || askError || askLoading">
        <view class="bubble user" v-if="lastAskQuestion">
          <text>{{ lastAskQuestion }}</text>
        </view>
        <view class="bubble ai" v-if="askLoading">
          <text class="typing">正在查账本…</text>
        </view>
        <view class="bubble ai" v-else-if="askResult">
          <text class="answer-text">{{ askResult.answer }}</text>
          <view class="steps-row">
            <text class="step-chip" v-for="(s, i) in askResult.steps" :key="i">✓ {{ s }}</text>
          </view>
          <view class="data-used" v-if="askResult.tool !== 'unsupported'">
            <text class="data-title">数据依据：{{ toolLabel(askResult.tool) }}</text>
            <text class="data-line">{{ dataSummary(askResult) }}</text>
          </view>
          <text class="bubble-meta">模型 {{ askResult.model }} · 提示词 {{ askResult.prompt_version }} · 耗时 {{ askResult.latency_ms }}ms</text>
        </view>
        <view class="bubble ai error" v-else-if="askError">
          <text>{{ askError.message }}</text>
          <text class="retry-link" @click="ask">重试</text>
        </view>
      </view>

      <textarea class="ta ask-ta" v-model="askText" :maxlength="200"
        placeholder="例如：本月餐饮花了多少？" placeholder-class="ph" />
      <view class="example-row">
        <text class="example" v-for="e in askExamples" :key="e" @click="useAskExample(e)">{{ e }}</text>
      </view>
      <button class="btn btn-primary" :class="{ 'btn-disabled': askLoading }"
        :disabled="askLoading" @click="ask">
        {{ askLoading ? '查询中…' : '向账本提问' }}
      </button>
    </view>

    <!-- ===== 总结 ===== -->
    <view class="card" v-else>
      <view class="sum-head">
        <view class="period-tabs">
          <text :class="['p-tab', summaryPeriod === 'week' && 'p-active']"
            @click="summaryPeriod = 'week'; summaryData = null">本周</text>
          <text :class="['p-tab', summaryPeriod === 'month' && 'p-active']"
            @click="summaryPeriod = 'month'; summaryData = null">本月</text>
        </view>
        <button class="btn btn-primary sum-btn" :class="{ 'btn-disabled': summaryLoading }"
          :disabled="summaryLoading" @click="genSummary">
          {{ summaryLoading ? '生成中…' : '生成分析' }}
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
        <text class="sum-month">{{ summaryData.month }}</text>
        <view class="sum-nums">
          <text class="sum-item">收入 ¥{{ Number(summaryData.income).toFixed(2) }}</text>
          <text class="sum-item">支出 ¥{{ Number(summaryData.expense).toFixed(2) }}</text>
          <text class="sum-item">结余 ¥{{ Number(summaryData.net).toFixed(2) }}</text>
        </view>
        <view class="ai-badge">AI 生成 · 基于真实统计数据，仅供参考</view>
        <text class="sum-text">{{ summaryData.summary }}</text>
        <text class="meta" v-if="summaryData.model">模型 {{ summaryData.model }}</text>
      </view>
      <view v-if="!summaryData" class="empty">
        点击上方按钮，AI 将基于{{ summaryPeriod === 'week' ? '本周' : '本月' }}的真实账单数据生成分析
      </view>
    </view>
  </view>
</template>

<style scoped>
.page { padding-bottom: 60rpx; }

/* 工作区顶部 */
.work-top { display: flex; align-items: center; justify-content: space-between;
  padding: 22rpx 28rpx 4rpx; }
.back-btn { font-size: 27rpx; color: #6C7BF5; font-weight: 600; }
.work-title { font-size: 30rpx; font-weight: 800; color: #4A4F6B; letter-spacing: 1rpx; }
.work-spacer { width: 120rpx; }

/* 首页 */
.ai-hero { display: flex; align-items: center; padding: 26rpx 34rpx 8rpx; }
.ai-hero-cat { width: 150rpx; height: 121rpx; }
.ai-hero-text { margin-left: 20rpx; flex: 1; }
.ai-hero-title { display: block; font-size: 46rpx; font-weight: 800; color: #5A54B8; letter-spacing: 2rpx; }
.ai-hero-sub { display: block; font-size: 26rpx; color: #8A90A8; margin-top: 8rpx; }
.mode-grid { display: flex; flex-wrap: wrap; gap: 18rpx; margin: 22rpx 24rpx 0; }
.mode-card { width: calc(50% - 9rpx); box-sizing: border-box; border-radius: 30rpx;
  padding: 26rpx 24rpx; display: flex; flex-direction: column; gap: 8rpx;
  box-shadow: 0 10rpx 26rpx rgba(124, 139, 255, .10); }
.mode-card:active { opacity: .85; }
.mode-icon { width: 62rpx; height: 62rpx; margin-bottom: 6rpx; }
.mode-name { font-size: 32rpx; font-weight: 800; color: #3A3F58; letter-spacing: 1rpx; }
.mode-desc { font-size: 25rpx; color: #7A7F96; line-height: 1.5; }

.phrase-list { display: flex; flex-wrap: wrap; gap: 14rpx; margin-top: 6rpx; }
.phrase-chip { display: flex; align-items: center; background: #F6F4FB; border-radius: 999rpx;
  padding: 8rpx 8rpx 8rpx 22rpx; }
.phrase-text { font-size: 26rpx; color: #4A4F6B; }
.phrase-del { color: #C3C7DA; font-size: 32rpx; padding: 0 12rpx; }
.phrase-empty { display: block; font-size: 26rpx; color: #A6AAC2; line-height: 1.7; margin-top: 6rpx; }

.recent-item { display: flex; align-items: center; padding: 18rpx 0; border-bottom: 1rpx dashed #EFEDF7; }
.recent-item:last-child { border-bottom: none; }
.recent-icon { width: 56rpx; height: 56rpx; margin-right: 16rpx; }
.recent-main { flex: 1; min-width: 0; }
.recent-label { display: block; font-size: 27rpx; font-weight: 700; color: #4A4F6B; }
.recent-summary { display: block; font-size: 25rpx; color: #A6AAC2; margin-top: 6rpx;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.recent-use { font-size: 25rpx; color: #6C7BF5; flex-shrink: 0; }

/* 通用 */
.hint { display: block; font-size: 26rpx; color: #8A90A8; margin-bottom: 20rpx; line-height: 1.6; }
.ta { width: 100%; min-height: 160rpx; background: #FAF9FF; border: 1rpx solid #E9E6F4;
  border-radius: 22rpx; padding: 24rpx; font-size: 30rpx; box-sizing: border-box; }
.ph { color: #C3C7DA; }
.example-row { display: flex; flex-wrap: wrap; gap: 14rpx; margin: 18rpx 0; }
.example { font-size: 25rpx; color: #6C7BF5; background: #EFF1FF; border-radius: 999rpx; padding: 8rpx 20rpx; }
.btn-row { display: flex; flex-direction: column; gap: 14rpx; }
.phrase-save { align-self: flex-end; font-size: 26rpx; color: #8A90A8; padding: 4rpx 10rpx; }

.state-box { margin-top: 24rpx; background: #FFEDEE; border-radius: 18rpx; padding: 24rpx; }
.state-text { font-size: 26rpx; color: #C94F4F; }
.state-actions { display: flex; gap: 20rpx; margin-top: 18rpx; }
.mini-btn { margin: 0; font-size: 26rpx; color: #6C7BF5; background: #FFFDF8;
  border: 2rpx solid #6C7BF5; border-radius: 999rpx; padding: 0 30rpx; height: 60rpx; line-height: 60rpx; }

.upload-row { display: flex; flex-direction: column; gap: 8rpx; margin-bottom: 22rpx; }
.upload-btn { margin: 0; height: 84rpx; border-radius: 42rpx; display: flex; align-items: center; justify-content: center; gap: 12rpx;
  background: #EFF1FF; color: #6C7BF5; font-size: 29rpx; font-weight: 600;
  border: 2rpx dashed #A9B0F0; }
.upload-btn-img { width: 44rpx; height: 44rpx; }
.upload-hint { font-size: 24rpx; color: #A6AAC2; text-align: center; }
.receipt-preview { margin-bottom: 20rpx; border-radius: 18rpx; overflow: hidden;
  border: 2rpx solid #E9E6F4; background: #FBFAFF; }
.receipt-img { width: 100%; display: block; }

.ai-badge { margin: 26rpx 0 16rpx; }
.draft { background: #FBFAFF; border: 2rpx solid #E4E7FB; border-radius: 22rpx; padding: 24rpx; margin-bottom: 22rpx; }
.draft-row { display: flex; align-items: center; gap: 20rpx; margin-bottom: 18rpx; }
.d-type { padding: 10rpx 24rpx; border-radius: 14rpx; background: #6C7BF5; color: #fff; font-size: 26rpx; font-weight: 700; }
.d-income { background: #1FA97F; }
.d-todo { background: #F2A93B; }
.d-amount { flex: 1; height: 72rpx; background: #FFFDF8; border-radius: 14rpx;
  padding: 0 20rpx; font-size: 32rpx; font-weight: 700; }
.d-yen { font-size: 28rpx; color: #8A90A8; }
.d-field { font-size: 27rpx; color: #4A5A9F; background: #FFFDF8; border-radius: 14rpx; padding: 14rpx 20rpx; }
.d-remark { width: 100%; height: 76rpx; background: #FFFDF8; border-radius: 14rpx;
  padding: 0 20rpx; font-size: 28rpx; margin-bottom: 18rpx; box-sizing: border-box; }
.d-content { min-height: 140rpx; margin-bottom: 18rpx; background: #FFFDF8; }
.receipt-info { background: #FFFDF8; border-radius: 16rpx; padding: 16rpx 20rpx; margin-bottom: 18rpx; }
.ri-row { display: flex; justify-content: space-between; align-items: center; padding: 8rpx 0; }
.ri-label { font-size: 26rpx; color: #8A90A8; }
.ri-val { font-size: 26rpx; color: #3A3F58; font-weight: 500; }
.ri-wait { color: #D98A32; font-weight: 600; }
.dup-warn { margin-top: 10rpx; background: #FFF6E7; color: #C1823F; border-radius: 10rpx;
  padding: 12rpx 16rpx; font-size: 25rpx; }
.missing { font-size: 26rpx; color: #D98A32; background: #FFF6E7; border-radius: 12rpx; padding: 12rpx 18rpx; margin-bottom: 18rpx; }
.draft-save { margin-top: 6rpx; height: 78rpx; font-size: 29rpx; }
.receipt-actions { display: flex; justify-content: flex-end; gap: 18rpx; margin-top: 6rpx; }
.pri-chips { display: flex; gap: 14rpx; margin-bottom: 18rpx; }
.pri-chip { font-size: 26rpx; padding: 8rpx 30rpx; border-radius: 24rpx;
  background: #FFFDF8; color: #8A90A8; border: 2rpx solid #E9E6F4; }
.chip-high.chip-active { background: #FFEDEE; color: #E45858; border-color: #F5B8B8; font-weight: 700; }
.chip-medium.chip-active { background: #FFF6E7; color: #F2A93B; border-color: #F5D9A8; font-weight: 700; }
.chip-low.chip-active { background: #F4F2FA; color: #6B7089; border-color: #D6D9E8; font-weight: 700; }
.meta { font-size: 24rpx; color: #A6AAC2; margin-top: 20rpx; }

/* 聊天气泡 */
.chat { display: flex; flex-direction: column; gap: 16rpx; margin: 8rpx 0 20rpx; }
.bubble { max-width: 86%; border-radius: 24rpx; padding: 20rpx 24rpx; font-size: 28rpx; line-height: 1.7; }
.bubble.user { align-self: flex-end; background: #8B7FE8; color: #fff;
  border-bottom-right-radius: 8rpx; }
.bubble.ai { align-self: flex-start; background: #F6F4FB; color: #3A3F58;
  border-bottom-left-radius: 8rpx; }
.bubble.ai.error { background: #FFEDEE; color: #C94F4F; }
.typing { color: #8A90A8; }
.answer-text { display: block; font-weight: 500; }
.bubble-meta { display: block; font-size: 22rpx; color: #A6AAC2; margin-top: 14rpx; }
.steps-row { display: flex; flex-wrap: wrap; gap: 10rpx; margin-top: 16rpx; }
.step-chip { font-size: 23rpx; color: #6C7BF5; background: #EFF1FF; border-radius: 999rpx; padding: 5rpx 16rpx; }
.data-used { margin-top: 16rpx; padding-top: 14rpx; border-top: 1rpx dashed #DCD3F2; }
.data-title { display: block; font-size: 24rpx; color: #8A90A8; }
.data-line { display: block; font-size: 26rpx; color: #4A4F6B; margin-top: 8rpx; }
.retry-link { color: #6C7BF5; font-size: 26rpx; margin-left: 18rpx; }
.ask-ta { min-height: 120rpx; }

/* 总结 */
.sum-head { display: flex; align-items: center; justify-content: space-between; }
.sum-month { display: block; font-size: 28rpx; font-weight: 700; color: #5A5F78; margin-top: 22rpx; }
.sum-btn { margin: 0; width: 260rpx; height: 76rpx; font-size: 28rpx; }
.period-tabs { display: flex; background: #F6F4FB; border-radius: 16rpx; padding: 6rpx; }
.p-tab { font-size: 27rpx; color: #8A90A8; padding: 12rpx 30rpx; border-radius: 12rpx; }
.p-active { background: #6C7BF5; color: #fff; font-weight: 600; }
.sum-nums { display: flex; gap: 26rpx; margin: 26rpx 0; flex-wrap: wrap; }
.sum-item { font-size: 26rpx; color: #5A5F78; background: #F6F4FB; border-radius: 14rpx; padding: 12rpx 20rpx; }
.sum-text { display: block; font-size: 29rpx; line-height: 1.8; color: #3A3F58; margin-top: 14rpx; }
</style>
