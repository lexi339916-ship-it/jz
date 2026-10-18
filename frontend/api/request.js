/**
 * 统一网络请求封装。
 * - 自动携带 Authorization: Bearer <token>
 * - 401 统一清空登录态并跳转登录页
 * - 非 2xx 统一 toast 错误信息并 reject（后端错误格式 {"code":..,"message":..}）
 */
import { BASE_URL } from '../common/config.js'
import store from '../store/user.js'
import { clearLogin } from '../store/user.js'

function request({ url, method = 'GET', data = {}, header = {} }) {
  return new Promise((resolve, reject) => {
    const token = store.token
    uni.request({
      url: BASE_URL + url,
      method,
      data,
      timeout: 35000,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: 'Bearer ' + token } : {}),
        ...header,
      },
      success(res) {
        const status = res.statusCode
        const body = res.data
        if (status >= 200 && status < 300) {
          resolve(body)
          return
        }
        const message = (body && body.message) || `请求失败（${status}）`
        if (status === 401) {
          clearLogin()
          uni.showToast({ title: '请先登录', icon: 'none' })
          setTimeout(() => {
            uni.reLaunch({ url: '/pages/login/login' })
          }, 600)
        } else if (status !== 429 && status !== 503) {
          uni.showToast({ title: message, icon: 'none' })
        }
        reject({ status, message, body })
      },
      fail(err) {
        const message = '网络连接失败，请检查后端服务是否启动'
        uni.showToast({ title: message, icon: 'none' })
        reject({ status: -1, message, body: null })
      },
    })
  })
}

export default {
  get(url, data) { return request({ url, method: 'GET', data }) },
  post(url, data) { return request({ url, method: 'POST', data }) },
  put(url, data) { return request({ url, method: 'PUT', data }) },
  delete(url) { return request({ url, method: 'DELETE' }) },
}
