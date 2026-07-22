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
          <text class="info-value status-tag" :class="record.status === 'done' ? 'tag-done' : (record.status === 'failed' ? 'tag-failed' : 'tag-processing')">
            {{ record.status === 'done' ? '已提取' : (record.status === 'failed' ? '转写失败' : '处理中') }}
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
          <view class="section-action" v-if="record.content && !isEditing" @click="startEdit">
            <text class="action-text">编辑</text>
          </view>
        </view>
        <view class="transcript-content">
          <text class="transcript-text" v-if="!isEditing">{{ record.content || '暂无转写内容' }}</text>
          <textarea
            class="transcript-textarea"
            v-else
            v-model="editedContent"
            :auto-height="true"
            placeholder="请输入转写内容"
            :maxlength="-1"
          />
        </view>
        <view class="edit-btn-row" v-if="isEditing">
          <button class="cancel-btn" @click="cancelEdit">
            <text class="cancel-btn-text">取消</text>
          </button>
          <button class="save-btn" :disabled="isSaving || !editedContent" @click="saveEdit">
            <text class="save-btn-text">{{ isSaving ? '保存中...' : '保存' }}</text>
          </button>
        </view>
        <view class="summarize-btn-wrap" v-else>
          <button class="summarize-btn" :disabled="isSummarizing || !record.content" @click="handleSummarize">
            <text class="summarize-btn-text">{{ isSummarizing ? 'AI总结中...' : (aiSummary ? '重新生成总结' : '智能总结') }}</text>
          </button>
        </view>
      </view>

      <view class="section-card" v-if="aiSummary || isSummarizing">
        <view class="section-header">
          <view class="section-indicator"></view>
          <text class="section-title">智能总结</text>
        </view>
        <view class="summary-content" v-if="aiSummary">
          <view class="summary-block">
            <text class="summary-text">{{ aiSummary }}</text>
          </view>
        </view>
        <view class="processing-wrap" v-else>
          <view class="processing-spinner"></view>
          <text class="processing-text">AI总结中...</text>
          <text class="processing-desc">正在智能分析转写内容，请稍候</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { summarizeRecording, getRecordDetail, updateOriginalText } from '@/api/file.js';

export default {
  data() {
    return {
      recordId: '',
      serverRecordId: null,
      record: {
        id: '',
        name: '',
        status: 'processing',
        visitTime: '',
        durationText: '',
        content: '',
        audioPath: '',
        latitude: 0,
        longitude: 0,
        originalSegments: null
      },
      isSummarizing: false,
      aiSummary: '',
      isEditing: false,
      editedContent: '',
      isSaving: false
    };
  },
  onLoad(options) {
    if (options && options.id) {
      this.recordId = options.id;
      this.serverRecordId = options.recordId ? Number(options.recordId) : null;
      this.loadRecordDetail();
    }
  },
  methods: {
    goBack() {
      uni.navigateBack();
    },
    async loadRecordDetail() {
      try {
        if (this.serverRecordId) {
          const serverRecord = await getRecordDetail(this.serverRecordId, 1);
          this.record = this.mapServerRecordToLocal(serverRecord);
          this.aiSummary = serverRecord.ai_summary || '';
          return;
        }
        const historyData = uni.getStorageSync('visit_history');
        if (historyData) {
          const list = JSON.parse(historyData);
          const found = list.find(item => item.id === this.recordId);
          if (found) {
            this.record = found;
            this.aiSummary = found.aiSummary || '';
          }
        }
      } catch (e) {
        console.error('加载走访详情失败:', e);
      }
    },
    mapServerRecordToLocal(serverRecord) {
      let content = "";
      let originalSegments = null;
      if (serverRecord.original_text) {
        let segments = serverRecord.original_text;
        if (typeof segments === 'string') {
          try {
            segments = JSON.parse(segments);
          } catch (e) {
            segments = null;
            content = serverRecord.original_text;
          }
        }
        if (Array.isArray(segments)) {
          originalSegments = segments;
          content = segments.map(s => s.text || "").join("");
        } else if (!content && typeof segments === 'string') {
          content = segments;
        }
      }

      let status = "processing";
      if (serverRecord.status === "success") {
        status = "done";
      } else if (serverRecord.status === "failed" || serverRecord.status === "error") {
        status = "failed";
      }

      let visitTime = "";
      if (serverRecord.visit_time) {
        const d = new Date(serverRecord.visit_time);
        if (!isNaN(d.getTime())) {
          const year = d.getFullYear();
          const month = String(d.getMonth() + 1).padStart(2, '0');
          const day = String(d.getDate()).padStart(2, '0');
          const hour = String(d.getHours()).padStart(2, '0');
          const minute = String(d.getMinutes()).padStart(2, '0');
          visitTime = `${year}-${month}-${day} ${hour}:${minute}`;
        }
      }

      const duration = serverRecord.duration_seconds || 0;
      let durationText = "--";
      if (duration > 0) {
        const mins = Math.floor(duration / 60);
        const secs = duration % 60;
        if (mins === 0) {
          durationText = `${secs}秒`;
        } else {
          durationText = `${mins}分${secs}秒`;
        }
      }

      return {
        id: "record_" + serverRecord.id,
        recordId: serverRecord.id,
        name: serverRecord.customer_name || "走访记录",
        status: status,
        visitTime: visitTime,
        duration: duration,
        durationText: durationText,
        content: content,
        audioPath: serverRecord.audio_url || "",
        latitude: 0,
        longitude: 0,
        originalSegments: originalSegments
      };
    },
    async handleSummarize() {
      if (this.isSummarizing || !this.record.content) {
        return;
      }
      this.isSummarizing = true;
      this.aiSummary = '';
      try {
        const result = await summarizeRecording(this.serverRecordId || this.record.recordId, 1);
        this.aiSummary = result.aiSummary || '';
        uni.showToast({
          title: '总结成功',
          icon: 'success'
        });
      } catch (e) {
        console.error('智能总结失败:', e);
        uni.showToast({
          title: e.message || '总结失败',
          icon: 'none'
        });
      } finally {
        this.isSummarizing = false;
      }
    },
    startEdit() {
      this.editedContent = this.record.content || '';
      this.isEditing = true;
    },
    cancelEdit() {
      this.isEditing = false;
      this.editedContent = '';
    },
    async saveEdit() {
      if (this.isSaving || !this.editedContent) {
        return;
      }
      this.isSaving = true;
      try {
        const recordId = this.serverRecordId || this.record.recordId;
        const newSegments = [{ text: this.editedContent }];
        const originalTextJson = JSON.stringify(newSegments);
        if (recordId) {
          await updateOriginalText(recordId, 1, originalTextJson);
        }
        this.record.content = this.editedContent;
        this.record.originalSegments = newSegments;
        this.updateLocalStorage();
        uni.showToast({
          title: '保存成功',
          icon: 'success'
        });
        this.isEditing = false;
        this.editedContent = '';
      } catch (e) {
        console.error('保存失败:', e);
        uni.showToast({
          title: e.message || '保存失败',
          icon: 'none'
        });
      } finally {
        this.isSaving = false;
      }
    },
    updateLocalStorage() {
      try {
        const historyData = uni.getStorageSync('visit_history');
        if (historyData) {
          const list = JSON.parse(historyData);
          const index = list.findIndex(item => item.id === this.recordId);
          if (index !== -1) {
            list[index].content = this.record.content;
            list[index].originalSegments = this.record.originalSegments;
            uni.setStorageSync('visit_history', JSON.stringify(list));
          }
        }
      } catch (e) {
        console.error('更新本地存储失败:', e);
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

.tag-failed {
  background-color: #FFF1F0;
  color: #FF4D4F;
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
  justify-content: space-between;
}

.section-header > view:first-child {
  display: flex;
  align-items: center;
}

.section-action {
  padding: 4px 12px;
}

.action-text {
  font-size: 14px;
  color: #0099FF;
  font-weight: 500;
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

.transcript-textarea {
  width: 100%;
  min-height: 120px;
  font-size: 14px;
  color: #444444;
  line-height: 1.8;
  background-color: transparent;
  border: none;
  outline: none;
  padding: 0;
  box-sizing: border-box;
}

.edit-btn-row {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.cancel-btn {
  flex: 1;
  height: 44px;
  background-color: #F5F5F5;
  border-radius: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}

.cancel-btn-text {
  color: #666666;
  font-size: 15px;
  font-weight: 500;
}

.save-btn {
  flex: 1;
  height: 44px;
  background: linear-gradient(135deg, #0099FF 0%, #0077B3 100%);
  border-radius: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 133, 208, 0.3);
}

.save-btn[disabled] {
  opacity: 0.6;
}

.save-btn-text {
  color: #FFFFFF;
  font-size: 15px;
  font-weight: 500;
}

.summarize-btn-wrap {
  margin-top: 16px;
}

.summarize-btn {
  width: 100%;
  height: 44px;
  background: linear-gradient(135deg, #0099FF 0%, #0077B3 100%);
  border-radius: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 133, 208, 0.3);
}

.summarize-btn[disabled] {
  opacity: 0.6;
}

.summarize-btn-text {
  color: #FFFFFF;
  font-size: 15px;
  font-weight: 500;
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

.summary-text {
  font-size: 14px;
  color: #555555;
  line-height: 1.8;
  background-color: #F8FAFC;
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
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
