import { createSSRApp } from 'vue'
import App from './App.vue'

// 旧版 Android WebView 兼容：补齐 String.prototype.padStart
if (!String.prototype.padStart) {
  String.prototype.padStart = function (targetLength, padString) {
    var str = String(this)
    var target = targetLength >> 0
    var pad = padString === undefined ? ' ' : String(padString)
    if (str.length >= target) return str
    var need = target - str.length
    var fill = ''
    while (fill.length < need) fill += pad
    return fill.slice(0, need) + str
  }
}

export function createApp() {
  const app = createSSRApp(App)
  return { app }
}
