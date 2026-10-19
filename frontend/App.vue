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
  background-color: #F3F0FB;
  background-image:
    radial-gradient(rgba(150, 142, 200, 0.055) 1rpx, transparent 1.6rpx),
    linear-gradient(178deg, #EAF0FF 0%, #F2EEFF 34%, #FDFBF6 72%, #FFFDF9 100%);
  background-size: 24rpx 24rpx, 100% 100%;
  color: #3A3F58;
  font-size: 30rpx;
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

/* 手绘卡片：不规则圆角 + 墨线描边 + 贴纸式偏移阴影 */
.card-sketch {
  background: #FFFDF8;
  padding: 30rpx;
  margin: 20rpx 24rpx;
  border: 3rpx solid #4E5170;
  border-radius: 255rpx 22rpx 235rpx 18rpx / 18rpx 235rpx 20rpx 255rpx;
  box-shadow: 6rpx 8rpx 0 rgba(120, 110, 180, 0.12);
}

/* 手绘贴纸（图片装饰定位助手） */
.doodle {
  position: absolute;
  pointer-events: none;
  user-select: none;
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
  font-size: 32rpx;
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
  font-size: 30rpx;
  color: #3A3F58;
  box-sizing: border-box;
}

/* 标签 */
.tag {
  display: inline-flex;
  align-items: center;
  padding: 4rpx 16rpx;
  border-radius: 12rpx;
  font-size: 25rpx;
}

/* AI 生成内容标识 */
.ai-badge {
  display: inline-flex;
  align-items: center;
  padding: 8rpx 20rpx;
  border-radius: 999rpx;
  background: #EFF1FF;
  color: #6C7BF5;
  font-size: 25rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
}

/* 空状态 */
.empty {
  text-align: center;
  color: #A6AAC2;
  padding: 80rpx 0;
  font-size: 28rpx;
  letter-spacing: 1rpx;
}

/* 分区标题 */
.section-title {
  font-size: 32rpx;
  font-weight: 800;
  color: #3A3F58;
  margin: 8rpx 4rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  letter-spacing: 1rpx;
}
.section-more {
  font-size: 26rpx;
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
  font-size: 48rpx;
  font-weight: 800;
  color: #3A3F58;
  letter-spacing: 2rpx;
  margin: 10rpx 8rpx 24rpx;
}
</style>
