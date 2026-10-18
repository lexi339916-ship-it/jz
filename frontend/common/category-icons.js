/**
 * 分类视觉规范：emoji 图标 + 主题色。
 * 账单列表、记账分类选择、统计图例、首页账单共用，保证全站一致。
 */
export const CATEGORY_META = {
  餐饮: { icon: '🍜', color: '#ff9f43' },
  交通: { icon: '🚕', color: '#54a0ff' },
  购物: { icon: '🛍️', color: '#ff6b81' },
  住房: { icon: '🏠', color: '#a29bfe' },
  学习: { icon: '📚', color: '#26c6da' },
  娱乐: { icon: '🎮', color: '#fd79a8' },
  医疗: { icon: '💊', color: '#41b883' },
  通讯: { icon: '📱', color: '#778beb' },
  其他: { icon: '📦', color: '#95a5a6' },
  工资: { icon: '💰', color: '#16b07a' },
  兼职: { icon: '💼', color: '#2ecc71' },
  理财: { icon: '📈', color: '#f39c12' },
  红包: { icon: '🧧', color: '#e74c3c' },
  退款: { icon: '💸', color: '#00b894' },
  其他收入: { icon: '🪙', color: '#b2bec3' },
}

export function categoryMeta(name) {
  return CATEGORY_META[name] || { icon: '🏷️', color: '#95a5a6' }
}
