<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { apiBill, apiAddBill, apiUpdateBill, apiDeleteBill, apiCategories } from '../../api/index.js'
import { categoryMeta } from '../../common/category-icons.js'

const editId = ref(null)
const type = ref('expense')
const amount = ref('')
const category = ref('')
const billDate = ref('')
const remark = ref('')
const payChannel = ref('')
const fundingAccount = ref('')
const categories = ref([])
const saving = ref(false)
const CHANNELS = ['微信支付', '支付宝', '银行卡', '云闪付', '现金', '其他']
// 取本地日期（toISOString 会按 UTC 计算，凌晨时段会差一天）
const today = new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
  .toISOString().slice(0, 10)

const typeCategories = computed(() => categories.value.filter(c => c.type === type.value))

async function loadCategories() {
  const res = await apiCategories()
  categories.value = res.items
}

function switchType(t) {
  type.value = t
  // 切换收支类型后，若当前分类不属于该类型则清空
  if (!typeCategories.value.some(c => c.name === category.value)) {
    category.value = ''
  }
}

function pickCategory(name) { category.value = name }

async function loadBill(id) {
  const b = await apiBill(id)
  type.value = b.type
  amount.value = String(Number(b.amount))
  category.value = b.category
  billDate.value = b.bill_date
  remark.value = b.remark
  payChannel.value = b.pay_channel || ''
  fundingAccount.value = b.funding_account || ''
}

async function save() {
  if (!amount.value || Number(amount.value) <= 0) {
    uni.showToast({ title: '请输入正确的金额', icon: 'none' }); return
  }
  if (!category.value) {
    uni.showToast({ title: '请选择分类', icon: 'none' }); return
  }
  if (!billDate.value) {
    uni.showToast({ title: '请选择日期', icon: 'none' }); return
  }
  const payload = {
    type: type.value,
    amount: Number(amount.value).toFixed(2),
    category: category.value,
    bill_date: billDate.value,
    remark: remark.value,
    source: 'manual',
    pay_channel: payChannel.value,
    funding_account: fundingAccount.value,
  }
  saving.value = true
  try {
    if (editId.value) {
      await apiUpdateBill(editId.value, payload)
      uni.showToast({ title: '修改成功', icon: 'success' })
    } else {
      await apiAddBill(payload)
      uni.showToast({ title: '记账成功', icon: 'success' })
    }
    setTimeout(() => uni.navigateBack(), 700)
  } catch (e) { /* 统一提示 */ } finally { saving.value = false }
}

function removeBill() {
  uni.showModal({
    title: '确认删除',
    content: '删除后无法恢复，确定删除该账单吗？',
    success: async (res) => {
      if (res.confirm) {
        await apiDeleteBill(editId.value)
        uni.showToast({ title: '已删除', icon: 'success' })
        setTimeout(() => uni.navigateBack(), 700)
      }
    },
  })
}

onLoad(async (options) => {
  billDate.value = today
  // 支持从日历"为这天记一笔"进入：?date=YYYY-MM-DD 预填日期
  if (options && options.date && /^\d{4}-\d{2}-\d{2}$/.test(options.date)) {
    billDate.value = options.date
  }
  await loadCategories()
  if (options && options.id) {
    editId.value = Number(options.id)
    uni.setNavigationBarTitle({ title: '编辑账单' })
    await loadBill(editId.value)
  }
})
</script>

<template>
  <view class="page">
    <view class="card">
      <!-- 收支类型 -->
      <view class="type-switch">
        <text :class="['type-btn', type === 'expense' && 'type-expense']" @click="switchType('expense')">支出</text>
        <text :class="['type-btn', type === 'income' && 'type-income']" @click="switchType('income')">收入</text>
      </view>

      <!-- 金额 -->
      <view class="amount-box">
        <text class="yen">¥</text>
        <input class="amount-input" type="digit" v-model="amount" placeholder="0.00"
          placeholder-class="ph" />
      </view>

      <!-- 分类 -->
      <text class="field-label">分类</text>
      <view class="cat-grid">
        <view v-for="c in typeCategories" :key="c.id"
          :class="['cat-item', category === c.name && 'cat-selected']"
          @click="pickCategory(c.name)">
          <text class="cat-emoji">{{ categoryMeta(c.name).icon }}</text>
          <text>{{ c.name }}</text>
        </view>
      </view>

      <!-- 日期 -->
      <text class="field-label">日期</text>
      <picker mode="date" :value="billDate" @change="e => billDate = e.detail.value">
        <view class="picker-value">{{ billDate }} ▾</view>
      </picker>

      <!-- 备注 -->
      <text class="field-label">备注</text>
      <input class="input" v-model="remark" placeholder="选填，如：午饭" placeholder-class="ph" />

      <!-- 支付渠道 -->
      <text class="field-label">支付渠道（选填）</text>
      <view class="cat-grid">
        <view :class="['cat-item', payChannel === '' && 'cat-selected']" @click="payChannel = ''">
          <text>未记录</text>
        </view>
        <view v-for="c in CHANNELS" :key="c"
          :class="['cat-item', payChannel === c && 'cat-selected']"
          @click="payChannel = c">
          <text>{{ c }}</text>
        </view>
      </view>
      <input v-if="payChannel" class="input channel-account" v-model="fundingAccount"
        placeholder="扣款账户（选填），如：零钱 / 工商银行储蓄卡" placeholder-class="ph" />
    </view>

    <view class="actions">
      <button class="btn btn-primary" :class="{ 'btn-disabled': saving }" :disabled="saving" @click="save">
        {{ saving ? '保存中…' : (editId ? '保存修改' : '保存账单') }}
      </button>
      <button class="btn btn-danger" v-if="editId" @click="removeBill">删除账单</button>
    </view>
  </view>
</template>

<style scoped>
.page { padding-bottom: 60rpx; }
.type-switch { display: flex; background: #f5f7fb; border-radius: 16rpx; padding: 8rpx; }
.type-btn { flex: 1; text-align: center; padding: 16rpx 0; border-radius: 12rpx;
  font-size: 28rpx; color: #7c8595; }
.type-expense { background: #2f6fed; color: #fff; font-weight: 700; }
.type-income { background: #16b07a; color: #fff; font-weight: 700; }

.amount-box { display: flex; align-items: center; margin: 36rpx 0 10rpx; border-bottom: 2rpx solid #eef0f5; padding-bottom: 16rpx; }
.yen { font-size: 52rpx; font-weight: 800; color: #263246; margin-right: 16rpx; }
.amount-input { flex: 1; font-size: 64rpx; font-weight: 800; }
.ph { color: #d3d8e2; }

.field-label { display: block; font-size: 26rpx; color: #4a5568; margin: 30rpx 0 16rpx; }
.cat-grid { display: flex; flex-wrap: wrap; gap: 16rpx; }
.cat-item { display: flex; align-items: center; gap: 8rpx; padding: 14rpx 26rpx;
  background: #f5f7fb; border-radius: 18rpx; font-size: 26rpx; color: #4a5568; }
.cat-emoji { font-size: 30rpx; }
.cat-selected { background: #2f6fed; color: #fff; font-weight: 700; }
.channel-account { margin-top: 16rpx; }
.picker-value { height: 88rpx; background: #f5f7fb; border-radius: 16rpx;
  display: flex; align-items: center; padding: 0 24rpx; font-size: 28rpx; }

.actions { margin: 30rpx 24rpx; display: flex; flex-direction: column; gap: 20rpx; }
</style>
