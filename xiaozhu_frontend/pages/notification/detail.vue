<template>
  <view class="container">
    <!-- 自定义顶部导航栏（与列表页保持一致） -->
    <view class="nav-header">
      <view class="back-btn" @click="goBack">
        <text class="back-icon">‹</text>
      </view>
      <text class="nav-title">通知详情</text>
      <view class="nav-placeholder"></view>
    </view>

    <view class="state-row" v-if="loading">
      <text class="state-text">加载中...</text>
    </view>
    <view class="state-row" v-else-if="loadError">
      <text class="state-text">{{ loadError }}</text>
      <view class="retry-btn" @click="fetchDetail"><text class="retry-text">重试</text></view>
    </view>

    <view v-else class="detail-card">
      <view class="detail-head">
        <view class="detail-tag-row">
          <view class="notice-tag" :class="urgencyClass">{{ urgencyText }}</view>
          <view class="notice-tag notice-tag-source" :class="sourceClass" v-if="sourceText">{{ sourceText }}</view>
        </view>
        <text class="detail-title">{{ detail.title }}</text>
        <view class="read-state" v-if="readMarked">
          <text class="read-state-text">已读</text>
        </view>
      </view>
      <view class="detail-meta">
        <text v-if="detail.publisher" class="meta-item">发布人：{{ detail.publisher }}</text>
        <text v-if="detail.publish_time" class="meta-item">{{ formatTime(detail.publish_time) }}</text>
        <text v-if="detail.audience" class="meta-item">面向：{{ audienceText }}</text>
      </view>
      <view class="detail-divider"></view>
      <view class="detail-body">
        <text class="detail-content">{{ detail.content }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import notificationApi from '@/api/notification.js';

export default {
  data() {
    return {
      id: null,
      detail: {},
      loading: false,
      loadError: '',
      readMarked: false
    };
  },
  computed: {
    urgencyText() {
      const u = this.detail.urgency || this.detail.tag || this.detail.level;
      if (u === 'urgent' || u === '紧急') return '紧急';
      if (u === 'important' || u === '重要') return '重要';
      return '通知';
    },
    urgencyClass() {
      const u = this.detail.urgency || this.detail.tag || this.detail.level;
      if (u === 'urgent' || u === '紧急') return 'tag-urgent';
      if (u === 'important' || u === '重要') return 'tag-important';
      return 'tag-normal';
    },
    sourceText() {
      const s = this.detail.source || this.detail.tag;
      if (s === 'city' || s === '市级') return '市级';
      if (s === 'district' || s === '区县') return '区县';
      return '';
    },
    sourceClass() {
      const s = this.detail.source || this.detail.tag;
      if (s === 'city' || s === '市级') return 'tag-city';
      if (s === 'district' || s === '区县') return 'tag-district';
      return 'tag-normal';
    },
    audienceText() {
      const aud = this.detail.audience;
      if (!aud) return '';
      if (aud === 'frontline' || aud === '一线') return '一线人员';
      if (aud === 'district' || aud === '区县') return '区县专项';
      if (aud === 'city' || aud === '市级') return '市公司';
      if (aud === 'all' || aud === '全部') return '全部人员';
      return aud;
    }
  },
  onLoad(options) {
    this.id = options && options.id ? options.id : null;
    if (!this.id) {
      this.loadError = '参数缺失';
      return;
    }
    this.fetchDetail();
  },
  methods: {
    goBack() {
      const pages = getCurrentPages();
      if (pages.length > 1) {
        uni.navigateBack();
      } else {
        uni.switchTab({ url: '/pages/workbench/index' });
      }
    },
    fetchDetail() {
      this.loading = true;
      this.loadError = '';
      notificationApi.getDetail(this.id)
        .then((data) => {
          this.detail = data || {};
          // 详情加载完成后自动标记已读（不需要用户手动点击）
          // 已读过的不再重复调接口
          if (this.detail && this.detail.id != null && !this.detail.is_read) {
            this.markRead(this.detail.id);
          } else if (this.detail && this.detail.is_read) {
            this.readMarked = true;
          }
        })
        .catch((err) => {
          this.loadError = err.message || '加载失败';
        })
        .finally(() => {
          this.loading = false;
        });
    },
    markRead(id) {
      notificationApi.markRead(id)
        .then(() => {
          this.readMarked = true;
          // 通知列表页/工作台页刷新未读数（如打开过列表页）
          uni.$emit('notification:read-updated', { id });
        })
        .catch((err) => {
          console.warn('[notification/detail] markRead failed:', err && err.message);
        });
    },
    formatTime(timeStr) {
      if (!timeStr) return '';
      const d = new Date(String(timeStr).replace(' ', 'T'));
      if (isNaN(d.getTime())) return String(timeStr).slice(0, 16) || '';
      const pad = (n) => (n < 10 ? '0' + n : '' + n);
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    }
  }
};
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #F4F6F9;
  padding: 16px;
  /* 留出顶部导航栏空间 */
  padding-top: calc(16px + 44px + var(--status-bar-height));
  box-sizing: border-box;
}

/* 自定义顶部导航栏（与列表页保持一致） */
.nav-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 44px;
  padding-top: var(--status-bar-height);
  background-color: #FFFFFF;
  border-bottom: 1px solid #EEEEEE;
}
.back-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}
.back-icon {
  font-size: 28px;
  color: #333333;
  font-weight: 300;
}
.nav-title {
  font-size: 17px;
  font-weight: 600;
  color: #222222;
}
.nav-placeholder {
  width: 40px;
  height: 40px;
}

.detail-card {
  background-color: #FFFFFF;
  border-radius: 8px;
  padding: 20px 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
.detail-head {
  margin-bottom: 14px;
}
.notice-tag {
  display: inline-block;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  margin-bottom: 10px;
  line-height: 1.6;
}
.detail-tag-row {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}
.detail-tag-row .notice-tag {
  margin-bottom: 0;
  margin-right: 6px;
}
.notice-tag-source {
  opacity: 0.85;
}
.tag-urgent { background-color: #FFF1F0; color: #F5222D; }
.tag-important { background-color: #E6F4FF; color: #0085D0; }
.tag-city   { background-color: #FFF7E6; color: #FA8C16; }
.tag-district { background-color: #F0F5FF; color: #0085D0; }
.tag-normal { background-color: #F5F5F5; color: #666666; }

.detail-title {
  display: block;
  font-size: 19px;
  font-weight: 600;
  color: #222222;
  line-height: 1.5;
}
.read-state {
  margin-top: 8px;
}
.read-state-text {
  display: inline-block;
  font-size: 11px;
  color: #0085D0;
  background-color: #E6F4FF;
  padding: 2px 8px;
  border-radius: 3px;
}
.detail-meta {
  display: flex;
  flex-wrap: wrap;
  font-size: 12px;
  color: #999999;
  margin-bottom: 12px;
}
.meta-item {
  margin-right: 14px;
  margin-bottom: 4px;
}
.detail-divider {
  height: 1px;
  background-color: #F0F0F0;
  margin-bottom: 16px;
}
.detail-body {
  padding: 4px 0 8px;
}
.detail-content {
  font-size: 15px;
  color: #333333;
  line-height: 1.85;
  white-space: pre-wrap;
  word-break: break-word;
}
.state-row {
  padding: 60px 24px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.state-text {
  font-size: 14px;
  color: #AAAAAA;
  margin-bottom: 14px;
}
.retry-btn {
  padding: 8px 20px;
  border: 1px solid #0085D0;
  border-radius: 4px;
}
.retry-text {
  color: #0085D0;
  font-size: 14px;
}
</style>
