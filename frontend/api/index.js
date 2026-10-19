/** 与后端 REST API 一一对应的接口封装 */
import http, { getBaseUrl } from './request.js'
import store from '../store/user.js'

// ---- 认证 ----
export const apiRegister = (data) => http.post('/api/auth/register', data)
export const apiLogin = (data) => http.post('/api/auth/login', data)
export const apiMe = () => http.get('/api/auth/me')
export const apiUpdateMe = (data) => http.put('/api/auth/me', data)

// ---- 分类 ----
export const apiCategories = (type) => http.get('/api/categories', type ? { type } : {})
export const apiAddCategory = (data) => http.post('/api/categories', data)

// ---- 账单 ----
export const apiBills = (params) => http.get('/api/bills', params)
export const apiAddBill = (data) => http.post('/api/bills', data)
export const apiBill = (id) => http.get(`/api/bills/${id}`)
export const apiUpdateBill = (id, data) => http.put(`/api/bills/${id}`, data)
export const apiDeleteBill = (id) => http.delete(`/api/bills/${id}`)

// ---- 便签 ----
export const apiNotes = (params) => http.get('/api/notes', params)
export const apiAddNote = (data) => http.post('/api/notes', data)
export const apiNote = (id) => http.get(`/api/notes/${id}`)
export const apiUpdateNote = (id, data) => http.put(`/api/notes/${id}`, data)
export const apiDeleteNote = (id) => http.delete(`/api/notes/${id}`)

// ---- 预算 ----
export const apiBudget = (month) => http.get('/api/budgets', { month })
export const apiSetBudget = (data) => http.put('/api/budgets', data)

// ---- 储蓄目标 ----
export const apiGoals = () => http.get('/api/goals')
export const apiAddGoal = (data) => http.post('/api/goals', data)
export const apiDepositGoal = (id, amount) => http.post(`/api/goals/${id}/deposit`, { amount })
export const apiDeleteGoal = (id) => http.delete(`/api/goals/${id}`)

// ---- 生活挑战 ----
export const apiChallenges = () => http.get('/api/challenges')
export const apiAddChallenge = (data) => http.post('/api/challenges', data)
export const apiDeleteChallenge = (id) => http.delete(`/api/challenges/${id}`)

// ---- 统计 ----
export const apiMonthlyStats = (month) => http.get('/api/statistics/monthly', { month })
export const apiCategoryStats = (month, type) => http.get('/api/statistics/categories', { month, type })
export const apiChannelStats = (month, type) => http.get('/api/statistics/channels', { month, type })
export const apiProfileStats = () => http.get('/api/statistics/profile')

// ---- AI ----
export const apiParseBill = (text) => http.post('/api/ai/parse-bill', { text })
export const apiParseNote = (text) => http.post('/api/ai/parse-note', { text })
export const apiSummary = (period = 'month') => http.get('/api/ai/summary', { period })
export const apiInsight = (refresh = false) => http.get('/api/ai/insight', refresh ? { refresh: 1 } : {})
export const apiAsk = (question) => http.post('/api/ai/ask', { question })

/** 上传支付截图（multipart），返回识别草稿 */
export const apiParseReceipt = (filePath) => new Promise((resolve, reject) => {
  uni.uploadFile({
    url: getBaseUrl() + '/api/ai/parse-receipt',
    filePath,
    name: 'file',
    timeout: 60000,
    header: store.token ? { Authorization: 'Bearer ' + store.token } : {},
    success(res) {
      let body = {}
      try { body = JSON.parse(res.data) } catch (e) { body = {} }
      if (res.statusCode >= 200 && res.statusCode < 300) {
        resolve(body)
      } else {
        const message = body.message || `上传失败（${res.statusCode}）`
        uni.showToast({ title: message, icon: 'none' })
        reject({ status: res.statusCode, message, body })
      }
    },
    fail() {
      const message = '网络连接失败，请检查后端服务'
      uni.showToast({ title: message, icon: 'none' })
      reject({ status: -1, message, body: null })
    },
  })
})
