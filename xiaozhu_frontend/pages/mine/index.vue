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
      <view class="menu-item" @click="handleClearCache">
        <view class="menu-left">
          <view class="menu-icon">存</view>
          <text class="menu-label">清理缓存</text>
        </view>
        <view class="menu-right">
          <text class="menu-value">{{ cacheSizeText }}</text>
          <text class="menu-arrow">></text>
        </view>
      </view>
      <view class="menu-item" @click="handleCheckUpdate">
        <view class="menu-left">
          <view class="menu-icon">新</view>
          <text class="menu-label">版本更新</text>
        </view>
        <view class="menu-right">
          <text class="menu-value" v-if="checkingUpdate">检查中...</text>
          <text class="menu-value" v-else>当前 v{{ currentVersion }}</text>
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
import versionApi, { getAppVersionInfo } from '@/api/version.js';
import cacheUtil from '@/common/cache.js';

const STORAGE_KEY = 'notification_settings';

export default {
  data() {
    return {
      notificationSettings: {
        notificationEnabled: true,
        soundEnabled: true,
        vibrateEnabled: true
      },
      cacheSizeText: '0 B',
      currentVersion: '1.0.0',
      checkingUpdate: false
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
    this.refreshCacheSize();
    this.loadCurrentVersion();
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
    // 缓存管理
    refreshCacheSize() {
      try {
        const size = cacheUtil.getCacheSize();
        this.cacheSizeText = cacheUtil.formatSize(size);
      } catch (e) {
        console.error('获取缓存大小失败:', e);
        this.cacheSizeText = '0 B';
      }
    },
    handleClearCache() {
      uni.showModal({
        title: '清理缓存',
        content: `当前占用 ${this.cacheSizeText}，将清理录音临时文件及非关键缓存。`,
        confirmText: '清理',
        confirmColor: '#0085D0',
        success: (res) => {
          if (!res.confirm) return;
          uni.showLoading({ title: '清理中...', mask: true });
          cacheUtil
            .clearCache()
            .then((remain) => {
              this.cacheSizeText = cacheUtil.formatSize(remain);
              uni.hideLoading();
              uni.showToast({ title: '清理完成', icon: 'success' });
            })
            .catch(() => {
              uni.hideLoading();
              uni.showToast({ title: '清理失败', icon: 'none' });
            });
        }
      });
    },
    // 版本管理
    loadCurrentVersion() {
      try {
        const info = getAppVersionInfo();
        this.currentVersion = info.version || '1.0.0';
      } catch (e) {
        this.currentVersion = '1.0.0';
      }
    },
    handleCheckUpdate() {
      if (this.checkingUpdate) return;

      // #ifndef APP-PLUS
      uni.showModal({
        title: '版本更新',
        content: `当前版本 v${this.currentVersion}，非 App 环境暂不支持在线更新。`,
        showCancel: false,
        confirmText: '知道了',
        confirmColor: '#0085D0'
      });
      return;
      // #endif

      // #ifdef APP-PLUS
      this.checkingUpdate = true;
      uni.showLoading({ title: '检查更新中...', mask: true });

      versionApi
        .checkUpdate()
        .then((result) => {
          uni.hideLoading();
          this.checkingUpdate = false;

          if (!result || !result.update_type) {
            uni.showModal({
              title: '版本更新',
              content: `当前已是最新版本 v${this.currentVersion}`,
              showCancel: false,
              confirmText: '知道了',
              confirmColor: '#0085D0'
            });
            return;
          }
          this.handleUpdateResult(result);
        })
        .catch((err) => {
          uni.hideLoading();
          this.checkingUpdate = false;
          uni.showModal({
            title: '检查更新失败',
            content: err.message || '请稍后重试',
            showCancel: false,
            confirmText: '知道了',
            confirmColor: '#0085D0'
          });
        });
      // #endif
    },
    handleUpdateResult(result) {
      const updateType = parseInt(result.update_type, 10);
      // 0:提示热更 1:强制热更 2:提示整包 3:强制整包
      const isWgt = updateType === 0 || updateType === 1;
      const isForce = updateType === 1 || updateType === 3;
      const downloadUrl = result.download_url || result.url;
      const updateLog = result.update_log || result.note || '发现新版本，请更新';

      if (!downloadUrl) {
        uni.showModal({
          title: '版本更新',
          content: '已发现新版本，但暂无下载地址，请稍后重试。',
          showCancel: false,
          confirmColor: '#0085D0'
        });
        return;
      }

      if (isWgt) {
        // 热更新：静默或强制
        this.startWgtUpdate(downloadUrl, updateLog, isForce);
      } else {
        // 整包更新：提示或强制
        this.startApkUpdate(downloadUrl, updateLog, isForce);
      }
    },
    // 热更新流程
    startWgtUpdate(url, updateLog, isForce) {
      const doDownload = () => {
        uni.showLoading({ title: '下载中...', mask: true });
        const task = uni.downloadFile({
          url,
          success: (res) => {
            uni.hideLoading();
            if (res.statusCode !== 200) {
              uni.showToast({ title: '下载失败', icon: 'none' });
              return;
            }
            // #ifdef APP-PLUS
            plus.runtime.install(
              res.tempFilePath,
              { force: false },
              () => {
                if (isForce) {
                  plus.runtime.restart();
                  return;
                }
                uni.showModal({
                  title: '更新完成',
                  content: '已准备好新版本，立即重启应用？',
                  showCancel: true,
                  confirmText: '立即重启',
                  confirmColor: '#0085D0',
                  success: (r) => {
                    if (r.confirm) {
                      plus.runtime.restart();
                    }
                  }
                });
              },
              (err) => {
                uni.showModal({
                  title: '安装失败',
                  content: (err && err.message) || '请稍后重试',
                  showCancel: false,
                  confirmColor: '#0085D0'
                });
              }
            );
            // #endif
          },
          fail: () => {
            uni.hideLoading();
            uni.showToast({ title: '下载失败', icon: 'none' });
          }
        });
        task.onProgressUpdate((res) => {
          uni.showLoading({ title: `下载中 ${res.progress}%`, mask: true });
        });
      };

      if (isForce) {
        // 强制热更：直接静默下载
        doDownload();
      } else {
        uni.showModal({
          title: '发现新版本',
          content: updateLog,
          showCancel: true,
          confirmText: '立即更新',
          confirmColor: '#0085D0',
          success: (r) => {
            if (r.confirm) {
              doDownload();
            }
          }
        });
      }
    },
    // 整包更新流程
    startApkUpdate(url, updateLog, isForce) {
      // #ifdef APP-PLUS
      const info = uni.getSystemInfoSync();
      const isIOS = info.platform === 'ios';

      const doOpenUrl = () => {
        plus.runtime.openURL(url, () => {
          uni.showToast({ title: '跳转下载失败', icon: 'none' });
        });
      };

      if (isIOS) {
        // iOS 必须跳转应用商店或下载链接
        uni.showModal({
          title: '发现新版本',
          content: updateLog,
          showCancel: !isForce,
          confirmText: '立即跳转',
          confirmColor: '#0085D0',
          success: (r) => {
            if (r.confirm) {
              doOpenUrl();
            }
          }
        });
        return;
      }

      // Android：弹出不可关闭对话框引导跳转下载
      uni.showModal({
        title: '发现新版本',
        content: updateLog + (isForce ? '\n（此版本为强制更新，需下载安装后方可继续使用）' : ''),
        showCancel: !isForce,
        confirmText: '立即下载',
        confirmColor: '#0085D0',
        success: (r) => {
          if (r.confirm) {
            doOpenUrl();
          }
        }
      });
      // #endif
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