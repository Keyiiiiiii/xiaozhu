<template>
  <view class="container">
    <!-- 自定义导航栏 -->
    <view class="nav-bar">
      <view class="nav-status-bar"></view>
      <view class="nav-content">
        <view class="nav-back" @click="goBack">
          <text class="back-icon">‹</text>
        </view>
        <text class="nav-title">通知与提醒设置</text>
        <view class="nav-placeholder"></view>
      </view>
    </view>

    <!-- 通知总开关 -->
    <view class="settings-group">
      <view class="setting-item main-item">
        <view class="setting-info">
          <text class="setting-label main-label">通知选项</text>
          <text class="setting-desc">开启后可接收通知并配置提醒方式</text>
        </view>
        <switch
          :checked="notificationEnabled"
          color="#0085D0"
          @change="onNotificationChange"
        />
      </view>
    </view>

    <!-- 提醒方式子选项 -->
    <view class="settings-group" :class="{ 'group-disabled': !notificationEnabled }">
      <view class="setting-item sub-item">
        <view class="setting-info">
          <text class="setting-label">声音提醒</text>
          <text class="setting-desc">收到通知时播放提示音</text>
        </view>
        <switch
          :checked="soundEnabled"
          :disabled="!notificationEnabled"
          color="#0085D0"
          @change="onSoundChange"
        />
      </view>

      <view class="setting-divider sub-divider"></view>

      <view class="setting-item sub-item">
        <view class="setting-info">
          <text class="setting-label">震动提醒</text>
          <text class="setting-desc">收到通知时震动反馈</text>
        </view>
        <switch
          :checked="vibrateEnabled"
          :disabled="!notificationEnabled"
          color="#0085D0"
          @change="onVibrateChange"
        />
      </view>
    </view>

    <!-- 提示说明 -->
    <view class="tips-area">
      <text class="tips-text">
        以上设置仅影响本地推送提醒方式，不影响消息接收。
      </text>
    </view>
  </view>
</template>

<script>
const STORAGE_KEY = 'notification_settings';

export default {
  data() {
    return {
      notificationEnabled: true,
      soundEnabled: true,
      vibrateEnabled: true
    };
  },
  onLoad() {
    this.loadSettings();
  },
  methods: {
    goBack() {
      uni.navigateBack();
    },
    loadSettings() {
      const saved = uni.getStorageSync(STORAGE_KEY);
      if (saved) {
        this.notificationEnabled = saved.notificationEnabled !== undefined ? saved.notificationEnabled : true;
        this.soundEnabled = saved.soundEnabled !== undefined ? saved.soundEnabled : true;
        this.vibrateEnabled = saved.vibrateEnabled !== undefined ? saved.vibrateEnabled : true;
      }
    },
    saveSettings() {
      uni.setStorageSync(STORAGE_KEY, {
        notificationEnabled: this.notificationEnabled,
        soundEnabled: this.soundEnabled,
        vibrateEnabled: this.vibrateEnabled
      });
    },
    onNotificationChange(e) {
      this.notificationEnabled = e.detail.value;
      this.saveSettings();
    },
    onSoundChange(e) {
      this.soundEnabled = e.detail.value;
      this.saveSettings();
    },
    onVibrateChange(e) {
      this.vibrateEnabled = e.detail.value;
      this.saveSettings();
      if (this.vibrateEnabled) {
        uni.vibrateShort({
          success: () => {},
          fail: () => {}
        });
      }
    }
  }
};
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #F5F6F8;
  padding-bottom: 40px;
}

/* 自定义导航栏 */
.nav-bar {
  background: linear-gradient(135deg, #006BB3 0%, #0085D0 100%);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-status-bar {
  height: var(--status-bar-height);
}

.nav-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 44px;
  padding: 0 8px;
}

.nav-back {
  width: 40px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-icon {
  font-size: 32px;
  color: #FFFFFF;
  font-weight: 300;
  line-height: 1;
}

.nav-title {
  font-size: 17px;
  font-weight: 500;
  color: #FFFFFF;
  flex: 1;
  text-align: center;
  margin-right: 40px;
}

.nav-placeholder {
  width: 40px;
}

/* 设置组 */
.settings-group {
  background-color: #ffffff;
  margin: 16px 16px 0;
  border-radius: 8px;
  overflow: hidden;
}

.settings-group.group-disabled {
  opacity: 0.5;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
}

.setting-item.main-item {
  padding: 16px;
}

.setting-item.sub-item {
  padding-left: 32px;
}

.setting-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  margin-right: 16px;
}

.setting-label {
  font-size: 15px;
  color: #222222;
  font-weight: 500;
  margin-bottom: 4px;
}

.setting-label.main-label {
  font-size: 16px;
  font-weight: 600;
}

.setting-desc {
  font-size: 12px;
  color: #999999;
}

.setting-divider {
  height: 1px;
  background-color: #F0F0F0;
}

.setting-divider.sub-divider {
  margin-left: 32px;
}

/* 提示说明 */
.tips-area {
  margin: 16px 24px 0;
}

.tips-text {
  font-size: 12px;
  color: #AAAAAA;
  line-height: 1.6;
}
</style>
