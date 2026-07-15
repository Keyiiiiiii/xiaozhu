<template>
  <view class="container">
    <view class="tab-header">
      <view
        class="tab-item"
        :class="{ active: currentTab === 0 }"
        @click="switchTab(0)"
      >
        <text class="tab-text">未办 (2)</text>
      </view>
      <view
        class="tab-item"
        :class="{ active: currentTab === 1 }"
        @click="switchTab(1)"
      >
        <text class="tab-text">进行中 (1)</text>
      </view>
      <view
        class="tab-item"
        :class="{ active: currentTab === 2 }"
        @click="switchTab(2)"
      >
        <text class="tab-text">已闭环</text>
      </view>
    </view>

    <view class="todo-list" v-if="currentTab === 0">
      <!-- 卡片1：高优、AI提取 -->
      <view class="todo-card">
        <view class="todo-head">
          <view class="todo-tags">
            <text class="tag tag-high">高优</text>
            <text class="tag tag-source">AI提取</text>
          </view>
          <text class="todo-deadline">截止: 06-03 18:00</text>
        </view>
        <view class="todo-title">核实软件园二期A区装机地址的宽带资源情况</view>
        <view class="todo-foot">
          <text class="todo-meta">来源：福州某某科技走访</text>
          <view class="todo-btn">开始办理</view>
        </view>
      </view>

      <!-- 卡片2：常规、手动创建 -->
      <view class="todo-card">
        <view class="todo-head">
          <view class="todo-tags">
            <text class="tag tag-normal">常规</text>
            <text class="tag tag-source">手动创建</text>
          </view>
          <text class="todo-deadline">截止: 06-05 12:00</text>
        </view>
        <view class="todo-title"
          >联系福建某某实业集团财务确认开票信息及款项进度</view
        >
        <view class="todo-foot">
          <text class="todo-meta">来源：张三</text>
          <view class="todo-btn">开始办理</view>
        </view>
      </view>
    </view>

    <!-- 进行中占位 -->
    <view class="todo-list" v-if="currentTab === 1">
      <view class="empty-state">
        <text class="empty-text">暂无进行中的待办</text>
      </view>
    </view>

    <!-- 已闭环占位 -->
    <view class="todo-list" v-if="currentTab === 2">
      <view class="empty-state">
        <text class="empty-text">暂无已闭环的待办</text>
      </view>
    </view>

    <!-- 底部悬浮按钮 -->
    <view class="fab-wrapper">
      <view class="fab-btn">新增待办</view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      currentTab: 0,
    };
  },
  methods: {
    switchTab(index) {
      this.currentTab = index;
    },
  },
};
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #F5F6F8;
  display: flex;
  flex-direction: column;
  padding-top: var(--status-bar-height);
  padding-bottom: 50px;
  box-sizing: border-box;
}
.tab-header {
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
.todo-list {
  padding: 16px;
  flex: 1;
}
.todo-card {
  background-color: #ffffff;
  padding: 16px;
  border-radius: 2px;
  margin-bottom: 16px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
  border: 1px solid #eeeeee;
}
.todo-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.todo-tags {
  display: flex;
}
.tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 2px;
  margin-right: 8px;
}
.tag-high {
  background-color: #fff1f0;
  color: #f5222d;
  border: 1px solid #ffa39e;
}
.tag-normal {
  background-color: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}
.tag-source {
  background-color: #f5f5f5;
  color: #666666;
  border: 1px solid #d9d9d9;
}
.todo-deadline {
  font-size: 12px;
  color: #fa8c16;
}
.todo-title {
  font-size: 16px;
  color: #333333;
  font-weight: bold;
  line-height: 1.4;
  margin-bottom: 16px;
}
.todo-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px dashed #eeeeee;
  padding-top: 12px;
}
.todo-meta {
  font-size: 12px;
  color: #999999;
}
.todo-btn {
  background-color: #0085d0;
  color: #ffffff;
  font-size: 13px;
  padding: 6px 16px;
  border-radius: 2px;
}
.fab-wrapper {
  padding: 16px;
  background-color: #ffffff;
  border-top: 1px solid #eeeeee;
}
.fab-btn {
  background-color: #0085d0;
  color: #ffffff;
  text-align: center;
  padding: 12px 0;
  font-size: 16px;
  border-radius: 2px;
  font-weight: bold;
}
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}
.empty-text {
  color: #999999;
  font-size: 14px;
}
</style>