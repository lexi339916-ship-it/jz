<script>
export default {
  onLaunch() {
    console.log('App Launch')
  },
}
</script>

<style>
/* ===== 全局设计规范：统一的字体、颜色、卡片、按钮 ===== */
page {
  background: #f5f7fb;
  color: #263246;
  font-size: 28rpx;
  font-family: -apple-system, 'PingFang SC', 'Helvetica Neue', 'Microsoft YaHei', sans-serif;
}

/* 通用卡片 */
.card {
  background: #fff;
  border-radius: 20rpx;
  padding: 28rpx;
  margin: 18rpx 24rpx;
  box-shadow: 0 6rpx 24rpx rgba(40, 70, 120, 0.06);
}

/* 通用按钮 */
.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  border-radius: 44rpx;
  font-size: 30rpx;
  font-weight: 600;
}
.btn-primary { background: #2f6fed; color: #fff; }
.btn-primary:active { opacity: 0.85; }
.btn-outline {
  background: #fff; color: #2f6fed;
  border: 2rpx solid #2f6fed;
}
.btn-ghost { background: #eef3ff; color: #2f6fed; }
.btn-disabled { background: #c4ccda; color: #fff; }
.btn-danger { background: #fff; color: #e5484d; border: 2rpx solid #e5484d; }

/* 通用输入框 */
.input {
  height: 88rpx;
  background: #f5f7fb;
  border-radius: 16rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
}

/* 标签 */
.tag {
  display: inline-flex;
  align-items: center;
  padding: 4rpx 16rpx;
  border-radius: 10rpx;
  font-size: 22rpx;
}

/* AI 生成内容统一标识 */
.ai-badge {
  display: inline-flex;
  align-items: center;
  padding: 6rpx 18rpx;
  border-radius: 20rpx;
  background: #eef3ff;
  color: #2f6fed;
  font-size: 22rpx;
  font-weight: 600;
}

/* 空状态 */
.empty {
  text-align: center;
  color: #9aa3b5;
  padding: 80rpx 0;
  font-size: 26rpx;
}

/* 分区标题 */
.section-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #263246;
  margin: 8rpx 4rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.section-more { font-size: 24rpx; color: #7c8595; font-weight: 400; }
</style>
