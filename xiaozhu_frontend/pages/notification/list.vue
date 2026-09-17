<template>
  <view class="container">
    <!-- 自定义顶部导航栏（含返回按钮） -->
    <view class="nav-header">
      <view class="back-btn" @click="goBack">
        <text class="back-icon">‹</text>
      </view>
      <text class="nav-title">通知列表</text>
      <view class="nav-placeholder"></view>
    </view>

    <!-- 顶部筛选条 (样式与待办 tab-header 保持一致) -->
    <view class="tab-header">
      <view
        v-for="opt in tagFilters"
        :key="opt.value"
        class="tab-item"
        :class="{ active: currentTag === opt.value }"
        @click="switchTag(opt.value)"
      >
        <text class="tab-text">{{ opt.label }}</text>
      </view>
    </view>

    <!-- 通知列表 -->
    <scroll-view
      class="notice-scroll"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
      refresher-default-style="black"
      @refresherrefresh="onRefresh"
      @scrolltolower="onScrollToLower"
      :lower-threshold="80"
    >
      <view class="notice-list" v-if="list.length > 0">
        <view class="notice-card" v-for="item in list" :key="item.id" @click="goDetail(item.id)">
          <view class="notice-card-head">
            <view class="notice-tag" :class="getTagClass(item)">{{ getTagText(item) }}</view>
            <text class="notice-time">{{ formatTime(item.publish_time || item.created_at) }}</text>
          </view>
          <view class="notice-title">{{ item.title }}</view>
          <view class="notice-summary">{{ stripSummary(item.content) }}</view>
          <view class="notice-foot" v-if="item.publisher">
            <text class="notice-publisher">{{ item.publisher }}</text>
            <text class="notice-arrow">›</text>
          </view>
        </view>
      </view>

      <!-- 加载与空态 -->
      <view class="state-row" v-if="loading && list.length === 0">
        <text class="state-text">加载中...</text>
      </view>
      <view class="state-row" v-else-if="!loading && list.length === 0">
        <text class="state-text">暂无通知</text>
      </view>
      <view class="state-row" v-else-if="loading && list.length > 0">
        <text class="state-text">加载中...</text>
      </view>
      <view class="state-row" v-else-if="!hasMore && list.length > 0">
        <text class="state-text">— 没有更多了 —</text>
      </view>
    </scroll-view>

    <!-- 下发通知浮动按钮 (仅 city/district 可见) -->
    <view
      class="fab-publish"
      v-if="canPublish"
      @click="goPublish"
    >
      <text class="fab-text">下发</text>
    </view>
  </view>
</template>

<script>
import notificationApi from '@/api/notification.js';
import { mapState } from 'vuex';

const PAGE_SIZE = 10;

export default {
  data() {
    return {
      currentTag: 'all',
      tagFilters: [
        { value: 'all', label: '全部' },
        { value: 'urgent', label: '紧急' },
        { value: 'city', label: '市级' },
        { value: 'district', label: '区县' }
      ],
      list: [],
      page: 1,
      hasMore: true,
      loading: false,
      refreshing: false
    };
  },
  computed: {
    ...mapState(['userInfo']),
    canPublish() {
      const role = this.userInfo && this.userInfo.role;
      return role === 'city' || role === 'district';
    }
  },
  onLoad() {
    this.fetchList(true);
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
    switchTag(tag) {
      if (this.currentTag === tag) return;
      this.currentTag = tag;
      this.fetchList(true);
    },
    onRefresh() {
      this.refreshing = true;
      this.fetchList(true).finally(() => {
        this.refreshing = false;
      });
    },
    fetchList(reset) {
      if (this.loading) return Promise.resolve();
      this.loading = true;
      if (reset) {
        this.page = 1;
        this.hasMore = true;
      }
      const params = { page: this.page, page_size: PAGE_SIZE };
      if (this.currentTag !== 'all') params.tag = this.currentTag;

      return notificationApi.getList(params)
        .then((res) => {
          const items = res.results || [];
          if (reset) {
            this.list = items;
          } else {
            this.list = this.list.concat(items);
          }
          const totalCount = typeof res.count === 'number' ? res.count : this.list.length;
          this.hasMore = items.length >= PAGE_SIZE && this.list.length < totalCount;
          if (items.length > 0) this.page += 1;
        })
        .catch((err) => {
          uni.showToast({ title: err.message || '加载失败', icon: 'none' });
          if (reset) this.list = [];
        })
        .finally(() => {
          this.loading = false;
        });
    },
    onScrollToLower() {
      if (this.loading || !this.hasMore) return;
      this.fetchList(false);
    },
    goDetail(id) {
      uni.navigateTo({
        url: `/pages/notification/detail?id=${id}`
      });
    },
    goPublish() {
      uni.navigateTo({
        url: '/pages/notification/publish'
      });
    },
    getTagText(item) {
      const tag = item.tag || item.level;
      if (tag === 'urgent' || tag === '紧急') return '紧急';
      if (tag === 'city' || tag === '市级') return '市级';
      if (tag === 'district' || tag === '区县') return '区县';
      return '通知';
    },
    getTagClass(item) {
      const tag = item.tag || item.level;
      if (tag === 'urgent' || tag === '紧急') return 'tag-urgent';
      if (tag === 'city' || tag === '市级') return 'tag-city';
      if (tag === 'district' || tag === '区县') return 'tag-district';
      return 'tag-normal';
    },
    stripSummary(content) {
      if (!content) return '';
      const txt = String(content).replace(/[#*`>\-\s]+/g, ' ').trim();
      return txt.length > 60 ? txt.slice(0, 60) + '...' : txt;
    },
    formatTime(timeStr) {
      if (!timeStr) return '';
      const d = new Date(String(timeStr).replace(' ', 'T'));
      if (isNaN(d.getTime())) return String(timeStr).slice(5, 10) || '';
      const pad = (n) => (n < 10 ? '0' + n : '' + n);
      return `${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    }
  }
};
</script>

<style scoped>
.container {
  height: 100vh;
  overflow: hidden;
  background-color: #F5F6F8;
  display: flex;
  flex-direction: column;
}

/* 自定义顶部导航栏 */
.nav-header {
  flex-shrink: 0;
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

/* 顶部筛选条 (与待办 tab-header 样式一致) */
.tab-header {
  flex-shrink: 0;
  display: flex;
  background-color: #ffffff;
  border-bottom: 1px solid #eeeeee;
}
.tab-item {
  flex: 1;
  text-align: center;
  padding: 14px 0;
}
.tab-item.active {
  border-bottom: 2px solid #0085d0;
}
.tab-item.active .tab-text {
  color: #0085d0;
  font-weight: bold;
}
.tab-text {
  font-size: 15px;
  color: #666666;
}

.notice-scroll {
  flex: 1;
  min-height: 0;
}
.notice-list {
  padding: 16px;
}
.notice-card {
  background-color: #FFFFFF;
  border-radius: 2px;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid #eeeeee;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}
.notice-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.notice-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 2px;
  line-height: 1.5;
}
.tag-urgent { background-color: #fff1f0; color: #f5222d; border: 1px solid #ffa39e; }
.tag-city   { background-color: #fff7e6; color: #fa8c16; border: 1px solid #ffd591; }
.tag-district { background-color: #f0f5ff; color: #0085D0; border: 1px solid #adc6ff; }
.tag-normal { background-color: #f5f5f5; color: #666666; border: 1px solid #d9d9d9; }

.notice-time {
  font-size: 12px;
  color: #AAAAAA;
}
.notice-title {
  font-size: 16px;
  font-weight: bold;
  color: #222222;
  line-height: 1.5;
  margin-bottom: 8px;
}
.notice-summary {
  font-size: 13px;
  color: #888888;
  line-height: 1.6;
}
.notice-foot {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px dashed #EEEEEE;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.notice-publisher {
  font-size: 12px;
  color: #999999;
}
.notice-arrow {
  font-size: 16px;
  color: #CCCCCC;
}
.state-row {
  padding: 24px 0;
  text-align: center;
}
.state-text {
  font-size: 13px;
  color: #AAAAAA;
}
.fab-publish {
  position: fixed;
  right: 20px;
  bottom: calc(40px + var(--window-bottom));
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #0085D0 0%, #006BB3 100%);
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4px 12px rgba(0, 133, 208, 0.35);
  z-index: 100;
}
.fab-text {
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
}
</style>
