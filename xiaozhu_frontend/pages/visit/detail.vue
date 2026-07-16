<template>
  <view class="detail-container">
    <view class="detail-header">
      <view class="back-btn" @click="goBack">
        <text class="back-icon">‹</text>
      </view>
      <text class="detail-title">走访详情</text>
      <view class="header-placeholder"></view>
    </view>

    <scroll-view class="detail-content" scroll-y>
      <view class="info-card">
        <view class="info-row">
          <text class="info-label">走访名称</text>
          <text class="info-value">{{ record.name }}</text>
        </view>
        <view class="info-divider"></view>
        <view class="info-row">
          <text class="info-label">走访时间</text>
          <text class="info-value">{{ record.visitTime }}</text>
        </view>
        <view class="info-divider"></view>
        <view class="info-row">
          <text class="info-label">沟通时长</text>
          <text class="info-value">{{ record.durationText }}</text>
        </view>
        <view class="info-divider"></view>
        <view class="info-row">
          <text class="info-label">处理状态</text>
          <text class="info-value status-tag" :class="record.status === 'done' ? 'tag-done' : 'tag-processing'">
            {{ record.status === 'done' ? '已提取' : '处理中' }}
          </text>
        </view>
      </view>

      <view class="section-card">
        <view class="section-header">
          <view class="section-indicator"></view>
          <text class="section-title">音频文件</text>
        </view>
        <view class="audio-player">
          <view class="audio-play-btn">
            <text class="audio-play-icon">▶</text>
          </view>
          <view class="audio-progress-wrap">
            <view class="audio-progress-bar">
              <view class="audio-progress-fill" :style="{ width: '30%' }"></view>
            </view>
            <view class="audio-time-row">
              <text class="audio-time">01:23</text>
              <text class="audio-time">{{ record.durationText }}</text>
            </view>
          </view>
        </view>
      </view>

      <view class="section-card">
        <view class="section-header">
          <view class="section-indicator"></view>
          <text class="section-title">录音转写</text>
        </view>
        <view class="transcript-content">
          <text class="transcript-text">{{ record.content || '暂无转写内容' }}</text>
        </view>
      </view>

      <view class="section-card">
        <view class="section-header">
          <view class="section-indicator"></view>
          <text class="section-title">智能总结</text>
        </view>
        <view class="summary-content" v-if="record.status === 'done'">
          <view class="summary-block">
            <text class="summary-label">走访纪要</text>
            <text class="summary-text">{{ summaryData.meetingSummary }}</text>
          </view>
          <view class="summary-block">
            <text class="summary-label">关键事项</text>
            <view class="key-points">
              <view class="key-point-item" v-for="(item, idx) in summaryData.keyPoints" :key="idx">
                <text class="point-dot">•</text>
                <text class="point-text">{{ item }}</text>
              </view>
            </view>
          </view>
          <view class="summary-block">
            <text class="summary-label">待办事项</text>
            <view class="todo-list">
              <view class="todo-item" v-for="(item, idx) in summaryData.todoList" :key="idx">
                <view class="todo-checkbox">
                  <text class="todo-check-icon">✓</text>
                </view>
                <text class="todo-text">{{ item }}</text>
              </view>
            </view>
          </view>
        </view>
        <view class="processing-wrap" v-else>
          <view class="processing-spinner"></view>
          <text class="processing-text">总结内容处理中...</text>
          <text class="processing-desc">AI正在智能分析转写内容，请稍候</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      recordId: '',
      record: {
        id: '',
        name: '',
        status: 'processing',
        visitTime: '',
        durationText: '',
        content: '',
        audioPath: '',
        latitude: 0,
        longitude: 0
      },
      summaryData: {
        meetingSummary: '本次走访主要讨论了项目推进情况，客户对当前的合作进展表示满意，并提出了一些优化建议。双方就下一阶段的工作计划达成了共识，明确了各自的责任分工和时间节点。',
        keyPoints: [
          '客户对产品功能表示认可，希望增加数据导出功能',
          '下一阶段重点推进系统集成测试',
          '预计下周三前完成需求确认文档',
          '客户方对接人为张经理'
        ],
        todoList: [
          '整理本次走访会议纪要并发送给客户',
          '跟进数据导出功能的排期',
          '准备下周三的需求确认文档',
          '同步项目进度给内部团队'
        ]
      }
    };
  },
  onLoad(options) {
    if (options && options.id) {
      this.recordId = options.id;
      this.loadRecordDetail();
    }
  },
  methods: {
    goBack() {
      uni.navigateBack();
    },
    loadRecordDetail() {
      try {
        const historyData = uni.getStorageSync('visit_history');
        if (historyData) {
          const list = JSON.parse(historyData);
          const found = list.find(item => item.id === this.recordId);
          if (found) {
            this.record = found;
          }
        }
      } catch (e) {
        console.error('加载走访详情失败:', e);
      }
    }
  }
};
</script>

<style scoped>
.detail-container {
  min-height: 100vh;
  background-color: #F4F6F9;
  display: flex;
  flex-direction: column;
}

.detail-header {
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

.detail-title {
  font-size: 17px;
  font-weight: 600;
  color: #222222;
}

.header-placeholder {
  width: 40px;
}

.detail-content {
  flex: 1;
  padding: 16px;
  box-sizing: border-box;
}

.info-card {
  background-color: #FFFFFF;
  border-radius: 12px;
  padding: 4px 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 0;
}

.info-label {
  font-size: 14px;
  color: #888888;
}

.info-value {
  font-size: 14px;
  color: #333333;
  font-weight: 500;
  max-width: 60%;
  text-align: right;
}

.info-divider {
  height: 1px;
  background-color: #F5F5F5;
}

.status-tag {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 12px;
}

.tag-done {
  background-color: #F6FFED;
  color: #52C41A;
}

.tag-processing {
  background-color: #FFF7E6;
  color: #FA8C16;
}

.section-card {
  background-color: #FFFFFF;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.section-indicator {
  width: 3px;
  height: 16px;
  background: linear-gradient(180deg, #0099FF 0%, #0077B3 100%);
  border-radius: 2px;
  margin-right: 10px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #222222;
}

.audio-player {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background-color: #F8FAFC;
  border-radius: 10px;
  border: 1px solid #E2E8F0;
}

.audio-play-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0099FF 0%, #0077B3 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 14px;
  box-shadow: 0 4px 10px rgba(0, 133, 208, 0.3);
}

.audio-play-icon {
  color: #FFFFFF;
  font-size: 16px;
  margin-left: 2px;
}

.audio-progress-wrap {
  flex: 1;
}

.audio-progress-bar {
  width: 100%;
  height: 4px;
  background-color: #E2E8F0;
  border-radius: 2px;
  overflow: hidden;
}

.audio-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0099FF 0%, #0077B3 100%);
  border-radius: 2px;
}

.audio-time-row {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
}

.audio-time {
  font-size: 12px;
  color: #999999;
}

.transcript-content {
  background-color: #F8FAFC;
  border-radius: 10px;
  padding: 16px;
  border: 1px solid #E2E8F0;
}

.transcript-text {
  font-size: 14px;
  color: #444444;
  line-height: 1.8;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary-block {
  display: flex;
  flex-direction: column;
}

.summary-label {
  font-size: 14px;
  font-weight: 600;
  color: #333333;
  margin-bottom: 8px;
}

.summary-text {
  font-size: 14px;
  color: #555555;
  line-height: 1.8;
  background-color: #F8FAFC;
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
}

.key-points {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background-color: #F8FAFC;
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
}

.key-point-item {
  display: flex;
  align-items: flex-start;
}

.point-dot {
  color: #0099FF;
  font-size: 14px;
  margin-right: 8px;
  line-height: 1.6;
}

.point-text {
  font-size: 14px;
  color: #555555;
  line-height: 1.6;
  flex: 1;
}

.todo-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background-color: #F8FAFC;
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
}

.todo-item {
  display: flex;
  align-items: flex-start;
}

.todo-checkbox {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  background-color: #22C55E;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
  margin-top: 1px;
  flex-shrink: 0;
}

.todo-check-icon {
  color: #FFFFFF;
  font-size: 12px;
  font-weight: bold;
}

.todo-text {
  font-size: 14px;
  color: #555555;
  line-height: 1.6;
  text-decoration: line-through;
  opacity: 0.7;
}

.processing-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
}

.processing-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #E2E8F0;
  border-top-color: #0099FF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.processing-text {
  font-size: 15px;
  font-weight: 500;
  color: #333333;
  margin-bottom: 8px;
}

.processing-desc {
  font-size: 13px;
  color: #999999;
}
</style>
