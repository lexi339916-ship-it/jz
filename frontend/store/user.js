/**
 * 轻量用户状态管理（基于 Vue3 reactive 的模块级单例）。
 * 职责：保存 token 与用户信息，同步本地缓存，供各页面共享。
 */
import { reactive } from 'vue'

const state = reactive({
  token: uni.getStorageSync('token') || '',
  user: uni.getStorageSync('user') || null,
})

export function setLogin(token, user) {
  state.token = token
  state.user = user
  uni.setStorageSync('token', token)
  uni.setStorageSync('user', user)
}

export function clearLogin() {
  state.token = ''
  state.user = null
  uni.removeStorageSync('token')
  uni.removeStorageSync('user')
}

export function isLogged() {
  return !!state.token
}

export default state
