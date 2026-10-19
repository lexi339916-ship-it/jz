/**
 * 分类视觉规范：手绘图标 + 主题色。
 * 账单列表、记账分类选择、统计图例、首页账单共用，保证全站一致。
 */
export const CATEGORY_META = {
  餐饮: { icon: '🍜', img: '/static/icons/cat_food.png', color: '#ff9f43' },
  交通: { icon: '🚕', img: '/static/icons/cat_transport.png', color: '#54a0ff' },
  购物: { icon: '🛍️', img: '/static/icons/cat_shopping.png', color: '#ff6b81' },
  住房: { icon: '🏠', img: '/static/icons/cat_home.png', color: '#a29bfe' },
  学习: { icon: '📚', img: '/static/icons/cat_study.png', color: '#26c6da' },
  娱乐: { icon: '🎮', img: '/static/icons/cat_fun.png', color: '#fd79a8' },
  医疗: { icon: '💊', img: '/static/icons/cat_medical.png', color: '#41b883' },
  通讯: { icon: '📱', img: '/static/icons/cat_comm.png', color: '#778beb' },
  其他: { icon: '📦', img: '/static/icons/cat_other.png', color: '#95a5a6' },
  工资: { icon: '💰', img: '/static/icons/cat_salary.png', color: '#16b07a' },
  兼职: { icon: '💼', img: '/static/icons/cat_parttime.png', color: '#2ecc71' },
  理财: { icon: '📈', img: '/static/icons/cat_finance.png', color: '#f39c12' },
  红包: { icon: '🧧', img: '/static/icons/cat_redpacket.png', color: '#e74c3c' },
  退款: { icon: '💸', img: '/static/icons/cat_refund.png', color: '#00b894' },
  其他收入: { icon: '🪙', img: '/static/icons/cat_otherincome.png', color: '#b2bec3' },
}

export function categoryMeta(name) {
  return CATEGORY_META[name] || {
    icon: '🏷️', img: '/static/icons/cat_default.png', color: '#95a5a6',
  }
}

/** 功能入口手绘图标 */
export const ACTION_ICONS = {
  pencil: '/static/icons/act_pencil.png',
  sparkle: '/static/icons/act_sparkle.png',
  note: '/static/icons/act_note.png',
  chart: '/static/icons/act_chart.png',
  camera: '/static/icons/act_camera.png',
  lock: '/static/icons/act_lock.png',
  wallet: '/static/icons/act_wallet.png',
  target: '/static/icons/act_target.png',
  info: '/static/icons/act_info.png',
}

/** 支付渠道配色（统计环形图与标签统一） */
export const CHANNEL_META = {
  微信支付: { color: '#07c160' },
  支付宝: { color: '#1677ff' },
  银行卡: { color: '#f59f0b' },
  云闪付: { color: '#e5484d' },
  现金: { color: '#8b93a5' },
  其他: { color: '#b2bec3' },
  未记录: { color: '#d3d8e2' },
}

export function channelMeta(name) {
  return CHANNEL_META[name] || { color: '#b2bec3' }
}
