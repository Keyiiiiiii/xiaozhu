<template>
  <view class="force-mask" v-if="visible" @touchstart.stop>
    <view class="force-modal" @click.stop>
      <view class="force-header">
        <view class="force-tag" :class="tagClass">{{ tagText }}</view>
        <text class="force-title">{{ current.title || '重要通知' }}</text>
      </view>

      <scroll-view class="force-body" scroll-y :show-scrollbar="false">
        <view class="force-body-inner">
          <view class="force-meta" v-if="current.publisher || current.publish_time">
            <text v-if="current.publisher">{{ current.publisher }}</text>
            <text v-if="current.publisher && current.publish_time"> · </text>
            <text v-if="current.publish_time">{{ formatTime(current.publish_time) }}</text>
          </view>
          <view class="force-content">
            <text>{{ current.content || '暂无内容' }}</text>
          </view>
        </view>
      </scroll-view>

      <view class="force-footer">
        <view class="force-checkbox-row" @click="toggleConfirmed">
          <view class="force-checkbox" :class="{ checked: hasConfirmed }">
            <text v-if="hasConfirmed" class="force-checkbox-icon">✓</text>
          </view>
          <text class="force-checkbox-label">我已阅读并知悉</text>
        </view>
        <view class="force-btn" :class="{ 'force-btn-disabled': !hasConfirmed }" @click="handleConfirm">
          <text class="force-btn-text">确 认</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import notificationApi from '@/api/notification.js';

const EVENT_CHECK = 'app:check-force-notification';
const STORAGE_LAST_SHOWN = 'force_notification_last_shown_id';

export default {
  name: 'ForceNotification',
  data() {
    return {
      visible: false,
      pendingList: [],
      currentIndex: 0,
      hasConfirmed: false,
      isProcessing: false
    };
  },
  computed: {
    current() {
      return this.pendingList[this.currentIndex] || {};
    },
    tagText() {
      const tag = this.current.tag || this.current.level;
      if (tag === 'urgent' || tag === '紧急') return '紧急';
      if (tag === 'city' || tag === '市级') return '市级';
      if (tag === 'district' || tag === '区县') return '区县';
      return '通知';
    },
    tagClass() {
      const tag = this.current.tag || this.current.level;
      if (tag === 'urgent' || tag === '紧急') return 'tag-urgent';
      if (tag === 'city' || tag === '市级') return 'tag-city';
      if (tag === 'district' || tag === '区县') return 'tag-district';
      return 'tag-normal';
    }
  },
  mounted() {
    // 监听全局事件：App 启动 / 登录成功 / 切回前台时触发
    uni.$on(EVENT_CHECK, this.handleCheck);
    // 自身挂载后兜底检查一次（避免 App.onLaunch 的 emit 早于组件挂载）
    setTimeout(this.handleCheck, 300);
  },
  beforeDestroy() {
    uni.$off(EVENT_CHECK, this.handleCheck);
    // 组件销毁前确保恢复 tabBar，避免遮挡被遗留
    this.restoreTabBar();
  },
  watch: {
    visible(val) {
      if (val) {
        this.hideTabBar();
      } else {
        this.restoreTabBar();
      }
    }
  },
  methods: {
    hideTabBar() {
      // 隐藏原生 tabBar，禁止用户在强制通知展示期间切换页面
      // 只在 tabBar 页面有效；非 tabBar 页调用会静默失败
      try {
        uni.hideTabBar({ animation: false });
      } catch (e) {
        console.warn('[force-notification] hideTabBar failed:', e);
      }
    },
    restoreTabBar() {
      try {
        uni.showTabBar({ animation: false });
      } catch (e) {
        console.warn('[force-notification] showTabBar failed:', e);
      }
    },
    handleCheck() {
      // 未登录不触发
      const token = uni.getStorageSync('token');
      if (!token) return;
      if (this.isProcessing) return;
      this.isProcessing = true;

      notificationApi.getPendingForce()
        .then((list) => {
          const filtered = Array.isArray(list) ? list : [];
          if (filtered.length === 0) return;
          this.pendingList = filtered;
          this.currentIndex = 0;
          this.hasConfirmed = false;
          this.visible = true;
        })
        .catch((err) => {
          console.warn('[force-notification] 获取强制通知失败:', err && err.message);
        })
        .finally(() => {
          this.isProcessing = false;
        });
    },
    toggleConfirmed() {
      this.hasConfirmed = !this.hasConfirmed;
    },
    handleConfirm() {
      if (!this.hasConfirmed) {
        uni.showToast({ title: '请先勾选已阅读', icon: 'none' });
        return;
      }
      const id = this.current.id;
      const next = () => {
        if (this.currentIndex < this.pendingList.length - 1) {
          this.currentIndex += 1;
          this.hasConfirmed = false;
        } else {
          this.visible = false;
          this.pendingList = [];
          this.currentIndex = 0;
          this.hasConfirmed = false;
        }
        if (id != null) {
          uni.setStorageSync(STORAGE_LAST_SHOWN, String(id));
        }
      };

      if (id == null) {
        next();
        return;
      }

      notificationApi.markDisplayed(id)
        .then(next)
        .catch((err) => {
          console.warn('[force-notification] 标记已展示失败:', err && err.message);
          // 即使接口失败也允许用户关闭，避免阻塞
          next();
        });
    },
    formatTime(timeStr) {
      if (!timeStr) return '';
      // 兼容 ISO 字符串，仅展示 MM-DD HH:mm
      const d = new Date(String(timeStr).replace(' ', 'T'));
      if (isNaN(d.getTime())) return String(timeStr).slice(5, 16) || '';
      const pad = (n) => (n < 10 ? '0' + n : '' + n);
      return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    }
  }
};
</script>

<style scoped>
.force-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.55);
  z-index: 9999;
  display: flex;
  justify-content: center;
  align-items: center;
  /* 减去状态栏与底部安全区，避免压到 home indicator / 状态栏 */
  padding: calc(16px + env(safe-area-inset-top)) 20px calc(16px + env(safe-area-inset-bottom));
  box-sizing: border-box;
}
.force-modal {
  width: 100%;
  max-width: 360px;
  background-color: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  /* 不再用固定 80vh，改由各子块 flex 自然收缩 */
  max-height: 100%;
  max-height: calc(100vh - 32px - env(safe-area-inset-top) - env(safe-area-inset-bottom));
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
}
.force-header {
  flex-shrink: 0;
  padding: 18px 18px 14px;
  border-bottom: 1px solid #F0F0F0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.force-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  margin-bottom: 8px;
  line-height: 1.6;
}
.tag-urgent { background-color: #FFF1F0; color: #F5222D; }
.tag-city   { background-color: #FFF7E6; color: #FA8C16; }
.tag-district { background-color: #F0F5FF; color: #0085D0; }
.tag-normal { background-color: #F5F5F5; color: #666666; }

.force-title {
  font-size: 16px;
  font-weight: 600;
  color: #222222;
  line-height: 1.45;
  word-break: break-word;
}
.force-body {
  /* 关键：让正文区在 flex 列中收缩并独立滚动，避免撑爆整个弹窗 */
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  /* 滚动条占位会让右侧文字被切；这里统一留出右内边距 */
  padding: 14px 22px 14px 18px;
  box-sizing: border-box;
  width: 100%;
}
/* H5 端隐藏滚动条，避免占位 */
/* #ifdef H5 */
.force-body ::-webkit-scrollbar {
  width: 0;
  height: 0;
  display: none;
}
/* #endif */
.force-body-inner {
  width: 100%;
  box-sizing: border-box;
}
.force-meta {
  display: block;
  font-size: 12px;
  color: #AAAAAA;
  margin-bottom: 8px;
  width: 100%;
  box-sizing: border-box;
}
.force-content {
  display: block;
  width: 100%;
  box-sizing: border-box;
  font-size: 14px;
  color: #333333;
  line-height: 1.7;
  /* uni-app 的 text 在 view 内默认 inline，强制 block 才会按宽度换行 */
  word-break: break-word;
  word-wrap: break-word;
  white-space: pre-wrap;
}
.force-content text {
  display: inline;
  word-break: break-word;
  word-wrap: break-word;
}
.force-footer {
  flex-shrink: 0;
  padding: 12px 18px calc(14px + env(safe-area-inset-bottom));
  border-top: 1px solid #F0F0F0;
  background-color: #FFFFFF;
}
.force-checkbox-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
.force-checkbox {
  width: 18px;
  height: 18px;
  border: 1px solid #CCCCCC;
  border-radius: 3px;
  margin-right: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #ffffff;
  flex-shrink: 0;
}
.force-checkbox.checked {
  background-color: #0085D0;
  border-color: #0085D0;
}
.force-checkbox-icon {
  color: #ffffff;
  font-size: 12px;
  line-height: 1;
}
.force-checkbox-label {
  font-size: 13px;
  color: #666666;
}
.force-btn {
  height: 42px;
  background: linear-gradient(135deg, #0085D0 0%, #006BB3 100%);
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
}
.force-btn-disabled {
  background: #CCCCCC;
}
.force-btn-text {
  color: #ffffff;
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 2px;
}

/* 超小屏（如 iPhone SE 320×568）进一步收紧 */
@media (max-height: 600px) {
  .force-header {
    padding: 14px 16px 10px;
  }
  .force-body {
    padding: 10px 16px;
  }
  .force-footer {
    padding: 10px 16px calc(10px + env(safe-area-inset-bottom));
  }
  .force-checkbox-row {
    margin-bottom: 8px;
  }
  .force-btn {
    height: 38px;
  }
  .force-title {
    font-size: 15px;
  }
  .force-content {
    font-size: 13px;
    line-height: 1.65;
  }
}
</style>
