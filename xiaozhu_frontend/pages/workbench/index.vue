<template>
  <view class="container">
    <!-- 顶部欢迎区 (增加柔和渐变与水波纹装饰) -->
    <view class="header-panel">
      <view class="header-bg-shape"></view>
      <view class="header-content">
        <view class="header-left">
          <text class="greeting">您好，{{ userName }}</text>
          <text class="date">2026-06-02 星期二</text>
        </view>
        <view class="header-right">
          <!-- 预留天气或消息铃铛图标 -->
        </view>
      </view>
    </view>

    <!-- 核心数据看板 (提升悬浮感与留白) -->
    <view class="dashboard">
      <view class="dash-item">
        <text class="dash-val">12</text>
        <text class="dash-label">本月走访(次)</text>
      </view>
      <view class="dash-divider"></view>
      <view class="dash-item">
        <text class="dash-val">85<text class="dash-unit">%</text></text>
        <text class="dash-label">待办完成率</text>
      </view>
      <view class="dash-divider"></view>
      <view class="dash-item">
        <text class="dash-val">3</text>
        <text class="dash-label">新增商机(个)</text>
      </view>
    </view>

    <!-- 快捷操作区 (优化图标质感) -->
    <view class="section">
      <view class="section-head">
        <text class="section-title">快捷操作</text>
      </view>
      <view class="grid-panel">
        <view class="grid-item" @click="goToVisit">
          <view class="grid-icon bg-blue-light"><text class="icon-text text-blue">录</text></view>
          <text class="grid-text">走访录音</text>
        </view>
        <view class="grid-item">
          <view class="grid-icon bg-cyan-light"><text class="icon-text text-cyan">查</text></view>
          <text class="grid-text">政策查询</text>
        </view>
        <view class="grid-item">
          <view class="grid-icon bg-orange-light"><text class="icon-text text-orange">办</text></view>
          <text class="grid-text">新建待办</text>
        </view>
        <view class="grid-item">
          <view class="grid-icon bg-gray-light"><text class="icon-text text-gray">数</text></view>
          <text class="grid-text">数据统计</text>
        </view>
      </view>
    </view>

    <!-- 通知公告 (增强层次感) -->
    <view class="section">
      <view class="section-head">
        <text class="section-title">重要通知</text>
        <text class="section-more">全部 ></text>
      </view>
      <view class="notice-list">
        <view class="notice-item">
          <view class="notice-tag urgent">紧急</view>
          <view class="notice-content">关于下发2026年6月政企宽带最新营销方案的通知</view>
          <view class="notice-time">06-01</view>
        </view>
        <view class="notice-item">
          <view class="notice-tag normal">市级</view>
          <view class="notice-content">关于规范走访录音上传要求的说明</view>
          <view class="notice-time">05-28</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { mapState } from 'vuex';

export default {
  data() {
    return {};
  },
  computed: {
    ...mapState(['userInfo']),
    userName() {
      return this.userInfo ? this.userInfo.name : '用户';
    }
  },
  methods: {
    goToVisit() {
      uni.switchTab({
        url: '/pages/visit/index'
      });
    }
  }
};
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #F4F6F9;
  padding-bottom: 50px;
}

/* 顶部区域优化 */
.header-panel {
  position: relative;
  background: linear-gradient(135deg, #006BB3 0%, #0085D0 100%);
  padding: calc(32px + var(--status-bar-height)) 20px 60px;
  overflow: hidden;
}
.header-bg-shape {
  position: absolute;
  right: -20px;
  top: -20px;
  width: 150px;
  height: 150px;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 70%);
  border-radius: 50%;
}
.header-content {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.greeting {
  font-size: 24px;
  color: #FFFFFF;
  font-weight: 600;
  display: block;
  margin-bottom: 6px;
  letter-spacing: 0.5px;
}
.date {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

/* 数据看板优化 */
.dashboard {
  display: flex;
  background-color: #FFFFFF;
  margin: -30px 16px 20px;
  padding: 24px 0;
  border-radius: 8px; /* 适度圆角增加现代感 */
  box-shadow: 0 4px 16px rgba(0, 133, 208, 0.08);
  position: relative;
  z-index: 2;
}
.dash-item {
  flex: 1;
  text-align: center;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.dash-val {
  font-size: 26px;
  font-weight: bold;
  color: #333333; /* 数字改为深色，更稳重 */
  margin-bottom: 6px;
  font-family: 'DIN Alternate', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.dash-unit {
  font-size: 14px;
  margin-left: 2px;
}
.dash-label {
  font-size: 12px;
  color: #888888;
}
.dash-divider {
  width: 1px;
  background-color: #F0F0F0;
  margin: 12px 0;
}

/* 通用区块优化 */
.section {
  margin: 0 16px 20px;
  background-color: #FFFFFF;
  border-radius: 8px;
  padding: 20px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.section-title {
  font-size: 17px;
  font-weight: 600;
  color: #222222;
  position: relative;
  padding-left: 12px;
}
.section-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 16px;
  background-color: #0085D0;
  border-radius: 2px;
}
.section-more {
  font-size: 13px;
  color: #999999;
}

/* 快捷操作优化 */
.grid-panel {
  display: flex;
  justify-content: space-between;
}
.grid-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 25%;
}
.grid-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px; /* 增加高级感 */
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 10px;
}
.icon-text {
  font-size: 20px;
  font-weight: bold;
}
/* 莫兰迪色系搭配 */
.bg-blue-light { background-color: #E6F4FF; }
.text-blue { color: #0085D0; }
.bg-cyan-light { background-color: #E6FFFB; }
.text-cyan { color: #13C2C2; }
.bg-orange-light { background-color: #FFF2E8; }
.text-orange { color: #FA8C16; }
.bg-gray-light { background-color: #F5F5F5; }
.text-gray { color: #888888; }
.grid-text {
  font-size: 13px;
  color: #444444;
}

/* 通知公告优化 */
.notice-item {
  display: flex;
  align-items: flex-start;
  padding: 16px 0;
  border-bottom: 1px solid #F5F5F5;
}
.notice-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}
.notice-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  margin-right: 10px;
  white-space: nowrap;
  margin-top: 2px;
}
.urgent {
  background-color: #FFF1F0;
  color: #F5222D;
}
.normal {
  background-color: #F0F5FF;
  color: #0085D0;
}
.notice-content {
  flex: 1;
  font-size: 15px;
  color: #333333;
  line-height: 1.5;
  margin-right: 12px;
}
.notice-time {
  font-size: 12px;
  color: #AAAAAA;
  white-space: nowrap;
  margin-top: 2px;
}
</style>