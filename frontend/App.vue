<script>
export default {
  onLaunch() {
    console.log('App Launch')
  },
}
</script>

<style>
/* ============================================================
   手账风设计系统
   配色：浅蓝紫渐变底 / 奶油白卡片 / 蓝紫主色 / 薄荷绿与暖黄点缀
   ============================================================ */
page {
  min-height: 100vh;
  background: linear-gradient(178deg, #EAF0FF 0%, #F2EEFF 34%, #FDFBF6 72%, #FFFDF9 100%);
  color: #3A3F58;
  font-size: 28rpx;
  font-family: -apple-system, 'PingFang SC', 'Helvetica Neue', 'Microsoft YaHei', sans-serif;
}

/* 奶油白卡片 */
.card {
  background: #FFFDF8;
  border-radius: 34rpx;
  padding: 30rpx;
  margin: 20rpx 24rpx;
  box-shadow: 0 12rpx 32rpx rgba(124, 139, 255, 0.10);
  border: 1rpx solid rgba(255, 255, 255, 0.95);
}

/* 手账胶带装饰（放在卡片内部顶部） */
.washi {
  position: absolute;
  top: -13rpx;
  left: 50%;
  width: 132rpx;
  height: 26rpx;
  border-radius: 8rpx;
  background: rgba(167, 139, 250, 0.30);
  transform: translateX(-50%) rotate(-2.5deg);
}

/* 按钮体系 */
.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 92rpx;
  border-radius: 999rpx;
  font-size: 30rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
  border: none;
}
.btn-primary {
  background: linear-gradient(135deg, #7C8BFF 0%, #A78BFA 100%);
  color: #FFFFFF;
  box-shadow: 0 12rpx 26rpx rgba(124, 139, 255, 0.30);
}
.btn-primary:active { opacity: 0.88; }
.btn-outline {
  background: #FFFDF8;
  color: #6C7BF5;
  border: 2rpx solid #C9CFFF;
}
.btn-ghost {
  background: #EFF1FF;
  color: #6C7BF5;
}
.btn-disabled {
  background: #E2E4F0;
  color: #A6AAC2;
  box-shadow: none;
}
.btn-danger {
  background: #FFFDF8;
  color: #F27E7E;
  border: 2rpx solid #F7C7C7;
}

/* 输入框 */
.input {
  height: 92rpx;
  background: #FAF9FF;
  border: 1rpx solid #E9E6F4;
  border-radius: 22rpx;
  padding: 0 26rpx;
  font-size: 28rpx;
  color: #3A3F58;
  box-sizing: border-box;
}

/* 标签 */
.tag {
  display: inline-flex;
  align-items: center;
  padding: 4rpx 16rpx;
  border-radius: 12rpx;
  font-size: 22rpx;
}

/* AI 生成内容标识 */
.ai-badge {
  display: inline-flex;
  align-items: center;
  padding: 8rpx 20rpx;
  border-radius: 999rpx;
  background: #EFF1FF;
  color: #6C7BF5;
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
}

/* 空状态 */
.empty {
  text-align: center;
  color: #A6AAC2;
  padding: 80rpx 0;
  font-size: 26rpx;
  letter-spacing: 1rpx;
}

/* 分区标题 */
.section-title {
  font-size: 30rpx;
  font-weight: 800;
  color: #3A3F58;
  margin: 8rpx 4rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  letter-spacing: 1rpx;
}
.section-more {
  font-size: 24rpx;
  color: #8A90A8;
  font-weight: 400;
}

/* 虚分割线 */
.divider-dash {
  border-top: 2rpx dashed #E7E3F4;
  margin: 20rpx 0;
}

/* 通用页面大标题（手账页眉） */
.page-title {
  display: block;
  font-size: 46rpx;
  font-weight: 800;
  color: #3A3F58;
  letter-spacing: 2rpx;
  margin: 10rpx 8rpx 24rpx;
}
</style>
