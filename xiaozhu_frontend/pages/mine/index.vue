<template>
  <view class="container">
    <!-- 个人信息头部 -->
    <view class="profile-header">
      <view class="avatar">{{ userInfo ? userInfo.name.charAt(0) : '用' }}</view>
      <view class="profile-info">
        <view class="profile-name">
          <text class="name-text">{{ userInfo ? userInfo.name : '未登录' }}</text>
          <text class="role-badge" v-if="userInfo">{{ userInfo.role }}</text>
        </view>
        <text class="profile-dept" v-if="userInfo">{{ userInfo.dept }}</text>
        <text class="profile-id" v-if="userInfo">工号：{{ userInfo.empId }}</text>
      </view>
    </view>

    <!-- 设置组 1 -->
    <view class="menu-group">
      <view class="menu-item" @click="goToNotificationSettings">
        <view class="menu-left">
          <view class="menu-icon">通</view>
          <text class="menu-label">通知与提醒设置</text>
        </view>
        <view class="menu-right">
          <text class="menu-value">{{ notificationSummary }}</text>
          <text class="menu-arrow">></text>
        </view>
      </view>
      <view class="menu-item">
        <view class="menu-left">
          <view class="menu-icon">密</view>
          <text class="menu-label">隐私与安全</text>
        </view>
        <text class="menu-arrow">></text>
      </view>
    </view>

    <!-- 设置组 2 -->
    <view class="menu-group">
      <view class="menu-item">
        <view class="menu-left">
          <view class="menu-icon">存</view>
          <text class="menu-label">清理缓存</text>
        </view>
        <view class="menu-right">
          <text class="menu-value">12.5 MB</text>
          <text class="menu-arrow">></text>
        </view>
      </view>
      <view class="menu-item">
        <view class="menu-left">
          <view class="menu-icon">新</view>
          <text class="menu-label">版本更新</text>
        </view>
        <view class="menu-right">
          <text class="menu-value">当前 v1.0.0</text>
          <text class="menu-arrow">></text>
        </view>
      </view>
      <view class="menu-item">
        <view class="menu-left">
          <view class="menu-icon">关</view>
          <text class="menu-label">关于榕小助</text>
        </view>
        <text class="menu-arrow">></text>
      </view>
    </view>

    <!-- 退出登录 -->
    <view class="logout-panel">
      <view class="logout-btn" @click="handleLogout">退出当前账号</view>
    </view>
  </view>
</template>

<script>
import { mapState, mapMutations } from 'vuex';
import loginApi from '@/api/login.js';

const STORAGE_KEY = 'notification_settings';

export default {
  data() {
    return {
      notificationSettings: {
        notificationEnabled: true,
        soundEnabled: true,
        vibrateEnabled: true
      }
    };
  },
  computed: {
    ...mapState(['userInfo']),
    notificationSummary() {
      const { notificationEnabled, soundEnabled, vibrateEnabled } = this.notificationSettings;
      if (!notificationEnabled) return '已关闭';
      if (soundEnabled && vibrateEnabled) return '声音+震动';
      if (soundEnabled) return '仅声音';
      if (vibrateEnabled) return '仅震动';
      return '已静音';
    }
  },
  onShow() {
    this.loadNotificationSettings();
  },
  methods: {
    ...mapMutations(['logout']),
    loadNotificationSettings() {
      const saved = uni.getStorageSync(STORAGE_KEY);
      if (saved) {
        this.notificationSettings = {
          notificationEnabled: saved.notificationEnabled !== undefined ? saved.notificationEnabled : true,
          soundEnabled: saved.soundEnabled !== undefined ? saved.soundEnabled : true,
          vibrateEnabled: saved.vibrateEnabled !== undefined ? saved.vibrateEnabled : true
        };
      }
    },
    goToNotificationSettings() {
      uni.navigateTo({
        url: '/pages/mine/notification-settings'
      });
    },
    handleLogout() {
      uni.showModal({
        title: '提示',
        content: '确定要退出登录吗？',
        success: (res) => {
          if (res.confirm) {
            loginApi.logout().finally(() => {
              this.logout();
              uni.reLaunch({
                url: '/pages/login/index'
              });
            });
          }
        }
      });
    }
  }
};
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #F5F6F8;
  padding-bottom: 50px;
}
.profile-header {
  background-color: #0085D0;
  padding: calc(32px + var(--status-bar-height)) 16px 40px;
  display: flex;
  align-items: center;
}
.avatar {
  width: 64px;
  height: 64px;
  background-color: #ffffff;
  color: #0085d0;
  font-size: 24px;
  font-weight: bold;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 2px;
  margin-right: 16px;
  border: 2px solid rgba(255, 255, 255, 0.8);
}
.profile-info {
  display: flex;
  flex-direction: column;
}
.profile-name {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}
.name-text {
  font-size: 20px;
  color: #ffffff;
  font-weight: bold;
  margin-right: 12px;
}
.role-badge {
  font-size: 11px;
  background-color: rgba(255, 255, 255, 0.2);
  color: #ffffff;
  padding: 2px 6px;
  border-radius: 2px;
  border: 1px solid rgba(255, 255, 255, 0.4);
}
.profile-dept {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
  margin-bottom: 4px;
}
.profile-id {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}
.menu-group {
  background-color: #ffffff;
  margin-top: 12px;
  border-top: 1px solid #eeeeee;
  border-bottom: 1px solid #eeeeee;
}
.menu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f5f5f5;
}
.menu-item:last-child {
  border-bottom: none;
}
.menu-left {
  display: flex;
  align-items: center;
}
.menu-icon {
  width: 24px;
  height: 24px;
  background-color: #f0f2f5;
  color: #666666;
  font-size: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 2px;
  margin-right: 12px;
}
.menu-label {
  font-size: 15px;
  color: #333333;
}
.menu-right {
  display: flex;
  align-items: center;
}
.menu-value {
  font-size: 13px;
  color: #999999;
  margin-right: 8px;
}
.menu-arrow {
  font-size: 14px;
  color: #cccccc;
}
.logout-panel {
  margin-top: 24px;
  padding: 0 16px;
}
.logout-btn {
  background-color: #ffffff;
  color: #f5222d;
  text-align: center;
  padding: 14px 0;
  font-size: 16px;
  border-radius: 2px;
  border: 1px solid #eeeeee;
}
</style>