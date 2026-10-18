/** 与后端 REST API 一一对应的接口封装 */
import http from './request.js'

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

// ---- 统计 ----
export const apiMonthlyStats = (month) => http.get('/api/statistics/monthly', { month })
export const apiCategoryStats = (month, type) => http.get('/api/statistics/categories', { month, type })

// ---- AI ----
export const apiParseBill = (text) => http.post('/api/ai/parse-bill', { text })
export const apiParseNote = (text) => http.post('/api/ai/parse-note', { text })
export const apiSummary = (month) => http.get('/api/ai/summary', { month })
export const apiInsight = (refresh = false) => http.get('/api/ai/insight', refresh ? { refresh: 1 } : {})
export const apiAsk = (question) => http.post('/api/ai/ask', { question })
