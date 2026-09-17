<template>
  <view class="container">
    <view class="state-row" v-if="loading">
      <text class="state-text">加载中...</text>
    </view>
    <view class="state-row" v-else-if="loadError">
      <text class="state-text">{{ loadError }}</text>
      <view class="retry-btn" @click="fetchDetail"><text class="retry-text">重试</text></view>
    </view>

    <view v-else class="detail-card">
      <view class="detail-head">
        <view class="notice-tag" :class="tagClass">{{ tagText }}</view>
        <text class="detail-title">{{ detail.title }}</text>
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
      loadError: ''
    };
  },
  computed: {
    tagText() {
      const tag = this.detail.tag || this.detail.level;
      if (tag === 'urgent' || tag === '紧急') return '紧急';
      if (tag === 'city' || tag === '市级') return '市级';
      if (tag === 'district' || tag === '区县') return '区县';
      return '通知';
    },
    tagClass() {
      const tag = this.detail.tag || this.detail.level;
      if (tag === 'urgent' || tag === '紧急') return 'tag-urgent';
      if (tag === 'city' || tag === '市级') return 'tag-city';
      if (tag === 'district' || tag === '区县') return 'tag-district';
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
    fetchDetail() {
      this.loading = true;
      this.loadError = '';
      notificationApi.getDetail(this.id)
        .then((data) => {
          this.detail = data || {};
        })
        .catch((err) => {
          this.loadError = err.message || '加载失败';
        })
        .finally(() => {
          this.loading = false;
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
.tag-urgent { background-color: #FFF1F0; color: #F5222D; }
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
