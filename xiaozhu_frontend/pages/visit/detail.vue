<template>
  <view class="detail-container">
    <view class="detail-header">
      <view class="back-btn" @click="goBack">
        <text class="back-icon">‹</text>
      </view>
      <text class="detail-title">走访详情</text>
      <view class="header-edit-btn" @click="toggleEdit">
        <text class="header-edit-text">{{ isEditing ? '取消' : '编辑' }}</text>
      </view>
    </view>

    <scroll-view class="detail-content" scroll-y>
      <view class="info-card">
        <view class="info-row">
          <text class="info-label">走访名称</text>
          <view class="info-value-wrap">
            <text class="info-value" v-if="!isEditing">{{ record.name }}</text>
            <input
              class="info-input"
              v-else
              v-model="editedName"
              placeholder="请输入走访名称"
            />
          </view>
        </view>
        <view class="info-divider"></view>
        <view class="info-row">
          <text class="info-label">走访时间</text>
          <view class="info-value-wrap">
            <text class="info-value" v-if="!isEditing">{{ record.visitTime }}</text>
            <picker v-if="isEditing" mode="date" :value="editedTime" @change="onDateChange">
              <view class="info-value picker-trigger">{{ editedTime || '请选择日期' }}</view>
            </picker>
          </view>
        </view>
        <view class="info-divider"></view>
        <view class="info-row">
          <text class="info-label">沟通时长</text>
          <text class="info-value">{{ record.durationText }}</text>
        </view>
        <view class="info-divider"></view>
        <view class="info-row">
          <text class="info-label">处理状态</text>
          <text class="info-value status-tag" :class="record.status === 'done' ? 'tag-done' : (record.status === 'summarized' ? 'tag-summarized' : (record.status === 'failed' ? 'tag-failed' : 'tag-processing'))">
            {{ record.status === 'done' ? '已提取' : (record.status === 'summarized' ? '已总结' : (record.status === 'failed' ? '转写失败' : '处理中')) }}
          </text>
        </view>
      </view>

      <view class="section-card">
        <view class="section-header">
          <view class="section-indicator"></view>
          <text class="section-title">音频文件</text>
        </view>
        <view class="audio-player">
          <view class="audio-play-btn" @click="toggleAudioPlay">
            <text class="audio-play-icon">{{ isAudioPlaying ? '❚❚' : '▶' }}</text>
          </view>
          <view class="audio-progress-wrap">
            <view class="audio-progress-bar" @click="seekAudio">
              <view class="audio-progress-fill" :style="{ width: progress + '%' }"></view>
              <view class="audio-progress-thumb" :style="{ left: progress + '%' }"></view>
            </view>
            <view class="audio-time-row">
              <text class="audio-time">{{ formatTime(currentTime) }}</text>
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
          <view v-if="!isEditing && record.originalSegments && record.originalSegments.length > 0" class="chat-list">
            <view v-for="(segment, index) in record.originalSegments" :key="index" class="chat-item" :class="getSpeakerClass(segment.speaker_label)">
              <view class="chat-bubble">
                <text v-if="shouldShowSpeaker(index, segment.speaker_label)" class="bubble-speaker">{{ formatSpeaker(segment.speaker_label) }}</text>
                <view class="bubble-content">
                  <text class="bubble-text">{{ segment.text || '' }}</text>
                </view>
                <view class="bubble-tail"></view>
              </view>
            </view>
          </view>
          <text v-else-if="!isEditing" class="transcript-text">{{ record.content || '暂无转写内容' }}</text>
          <view v-else-if="editedSegments && editedSegments.length > 0" class="chat-list">
            <view v-for="(segment, index) in editedSegments" :key="index" class="chat-item" :class="getSpeakerClass(segment.speaker_label)">
              <view class="chat-bubble">
                <text class="bubble-speaker">{{ formatSpeaker(segment.speaker_label) }}</text>
                <textarea
                  class="bubble-textarea"
                  v-model="editedSegments[index].text"
                  :auto-height="true"
                  placeholder="请输入转写内容"
                  :maxlength="-1"
                  @input="handleSegmentInput(index)"
                />
                <view class="bubble-tail"></view>
              </view>
            </view>
          </view>
          <textarea
            v-else
            class="transcript-textarea"
            v-model="editedContent"
            :auto-height="true"
            placeholder="请输入转写内容"
            :maxlength="-1"
          />
        </view>
        <view class="summarize-btn-wrap" v-if="!isEditing">
          <button class="summarize-btn" :disabled="isSummarizing || !record.content" @click="handleSummarize">
            <text class="summarize-btn-text">{{ isSummarizing ? 'AI总结中...' : (aiSummary ? '重新生成总结' : '智能总结') }}</text>
          </button>
          <button class="retranscribe-btn" :disabled="isReTranscribing" @click="handleReTranscribe">
            <text class="retranscribe-btn-text">{{ isReTranscribing ? '重新转写中...' : '重新转写' }}</text>
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

    <view class="bottom-save-bar" v-if="isEditing">
      <button class="save-btn" :disabled="isSaving" @click="saveAllChanges">
        <text class="save-btn-text">{{ isSaving ? '保存中...' : '保存修改' }}</text>
      </button>
    </view>
  </view>
</template>

<script>
import { summarizeRecording, getRecordDetail, updateOriginalText, fetchAudioData, submitSpeechToText } from '@/api/file.js';

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
      isReTranscribing: false,
      isEditing: false,
      editedContent: '',
      editedSegments: [],
      editedName: '',
      editedTime: '',
      isSaving: false,
      audioContext: null,
      audioSrc: '',
      isAudioPlaying: false,
      currentTime: 0,
      duration: 0,
      progress: 0,
    };
  },
  onLoad(options) {
    if (options && options.id) {
      this.recordId = options.id;
      this.serverRecordId = options.recordId ? Number(options.recordId) : null;
      this.loadRecordDetail();
    }
  },
  onShow() {
    if (this.isAudioPlaying && this.audioContext) {
      this.audioContext.play().catch(() => {});
    }
  },
  onHide() {
    if (this.audioContext) {
      this.audioContext.pause();
    }
  },
  onUnload() {
    this.destroyAudio();
  },
  methods: {
    goBack() {
      uni.navigateBack();
    },
    async loadRecordDetail() {
      try {
        if (this.serverRecordId) {
          const serverRecord = await getRecordDetail(this.serverRecordId);
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
        let data = serverRecord.original_text;
        if (typeof data === 'string') {
          try {
            data = JSON.parse(data);
          } catch (e) {
            data = null;
            content = serverRecord.original_text;
          }
        }
        if (Array.isArray(data)) {
          originalSegments = data;
          content = data.map(s => s.text || "").join("");
        } else if (data && typeof data === 'object' && data.segments && Array.isArray(data.segments)) {
          originalSegments = data.segments;
          content = data.segments.map(s => s.text || "").join("");
        } else if (!content && typeof data === 'string') {
          content = data;
        }
      }

      let status = "processing";
      if (serverRecord.status === "success") {
        status = "done";
      } else if (serverRecord.status === "summarized") {
        status = "summarized";
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
          visitTime = `${year}-${month}-${day}`;
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
        const result = await summarizeRecording(this.serverRecordId || this.record.recordId);
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
    async handleReTranscribe() {
      if (this.isReTranscribing) {
        return;
      }
      const recordId = this.serverRecordId || this.record.recordId;
      if (!recordId) {
        uni.showToast({
          title: '记录ID不存在',
          icon: 'none'
        });
        return;
      }
      this.isReTranscribing = true;
      try {
        await submitSpeechToText(recordId);
        uni.showToast({
          title: '转写任务已提交',
          icon: 'success'
        });
        this.record.status = 'processing';
        this.record.content = '';
        this.record.originalSegments = null;
        this.aiSummary = '';
        this.updateLocalStorage();
        setTimeout(() => {
          this.loadRecordDetail();
        }, 3000);
      } catch (e) {
        console.error('重新转写失败:', e);
        uni.showToast({
          title: e.message || '转写失败',
          icon: 'none'
        });
      } finally {
        this.isReTranscribing = false;
      }
    },
    toggleEdit() {
      if (this.isEditing) {
        this.isEditing = false;
        this.editedContent = '';
        this.editedSegments = [];
        this.editedName = '';
        this.editedTime = '';
      } else {
        this.editedContent = this.record.content || '';
        if (this.record.originalSegments && this.record.originalSegments.length > 0) {
          this.editedSegments = JSON.parse(JSON.stringify(this.record.originalSegments));
        } else {
          this.editedSegments = [];
        }
        this.editedName = this.record.name || '';
        this.editedTime = this.record.visitTime ? this.record.visitTime.split(' ')[0] : '';
        this.isEditing = true;
      }
    },
    formatSpeaker(speakerLabel) {
      if (!speakerLabel) {
        return '未知';
      }
      if (speakerLabel.startsWith('speaker_')) {
        const num = speakerLabel.replace('speaker_', '');
        return `说话人${num}`;
      }
      return speakerLabel;
    },
    getSpeakerClass(speakerLabel) {
      if (!speakerLabel) {
        return 'speaker-unknown';
      }
      if (speakerLabel.startsWith('speaker_')) {
        const num = parseInt(speakerLabel.replace('speaker_', ''));
        return `speaker-${num % 3 + 1}`;
      }
      return 'speaker-unknown';
    },
    formatSegmentTime(seconds) {
      if (!seconds || isNaN(seconds)) {
        return '--:--';
      }
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    },
    shouldShowSpeaker(index, currentSpeaker) {
      if (index === 0) {
        return true;
      }
      const segments = this.isEditing ? this.editedSegments : this.record.originalSegments;
      if (!segments || segments.length <= index) {
        return true;
      }
      const prevSegment = segments[index - 1];
      const prevSpeaker = prevSegment ? prevSegment.speaker_label : null;
      return prevSpeaker !== currentSpeaker;
    },
    handleSegmentInput(index) {
      if (!this.editedSegments || !this.editedSegments[index]) {
        return;
      }
      const text = this.editedSegments[index].text;
      if (!text || text.trim() === '') {
        this.editedSegments.splice(index, 1);
        if (this.editedSegments.length === 0) {
          this.editedContent = '';
        }
      }
    },
    onDateChange(e) {
      this.editedTime = e.detail.value;
    },
    async saveAllChanges() {
      if (this.isSaving) {
        return;
      }
      this.isSaving = true;
      try {
        const recordId = this.serverRecordId || this.record.recordId;
        if (!recordId) {
          uni.showToast({
            title: '记录ID不存在',
            icon: 'none'
          });
          return;
        }

        const updateData = {};

        if (this.editedName.trim() && this.editedName.trim() !== this.record.name) {
          updateData.customer_name = this.editedName.trim();
        }

        if (this.editedTime && this.editedTime !== (this.record.visitTime ? this.record.visitTime.split(' ')[0] : '')) {
          updateData.visit_time = this.editedTime;
        }

        if (this.editedSegments && this.editedSegments.length > 0) {
          const hasContentChanges = this.editedSegments.some((seg, idx) => {
            const original = this.record.originalSegments && this.record.originalSegments[idx];
            return !original || seg.text !== original.text;
          });
          if (hasContentChanges) {
            updateData.original_text = JSON.stringify({ segments: this.editedSegments });
          }
        } else if (this.editedContent && this.editedContent !== this.record.content) {
          const newSegments = [{ text: this.editedContent }];
          updateData.original_text = JSON.stringify({ segments: newSegments });
        }

        if (Object.keys(updateData).length > 0) {
          await updateOriginalText(recordId, updateData);

          if (updateData.customer_name) {
            this.record.name = updateData.customer_name;
          }
          if (updateData.visit_time) {
            this.record.visitTime = updateData.visit_time;
          }
          if (updateData.original_text) {
            if (this.editedSegments && this.editedSegments.length > 0) {
              this.record.content = this.editedSegments.map(s => s.text || '').join('');
              this.record.originalSegments = JSON.parse(JSON.stringify(this.editedSegments));
            } else {
              this.record.content = this.editedContent;
              this.record.originalSegments = [{ text: this.editedContent }];
            }
          }

          this.updateLocalStorage();
          uni.showToast({
            title: '保存成功',
            icon: 'success'
          });
        } else {
          uni.showToast({
            title: '未修改任何内容',
            icon: 'none'
          });
        }

        this.isEditing = false;
        this.editedContent = '';
        this.editedSegments = [];
        this.editedName = '';
        this.editedTime = '';
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
            list[index].name = this.record.name;
            list[index].visitTime = this.record.visitTime;
            list[index].content = this.record.content;
            list[index].originalSegments = this.record.originalSegments;
            uni.setStorageSync('visit_history', JSON.stringify(list));
          }
        }
      } catch (e) {
        console.error('更新本地存储失败:', e);
      }
    },
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    },
    async initAudio() {
      if (this.audioContext) {
        return;
      }
      const recordId = this.serverRecordId || this.record.recordId;
      if (!recordId) {
        uni.showToast({
          title: '无法获取音频文件',
          icon: 'none'
        });
        return;
      }

      try {
        uni.showLoading({ title: '加载音频...' });
        const audioData = await fetchAudioData(recordId);
        
        let audioSrc = '';
        // #ifdef H5
        const blob = new Blob([audioData], { type: 'audio/m4a' });
        audioSrc = URL.createObjectURL(blob);
        this.audioSrc = audioSrc;
        // #endif
        
        // #ifndef H5
        const fs = uni.getFileSystemManager();
        const tempFilePath = `${uni.env.USER_DATA_PATH}/audio_${recordId}_${Date.now()}.m4a`;
        fs.writeFile({
          filePath: tempFilePath,
          data: audioData,
          encoding: 'binary',
          success: () => {
            audioSrc = tempFilePath;
            this.createAudioContext(audioSrc);
            uni.hideLoading();
          },
          fail: (err) => {
            console.error('写入音频文件失败:', err);
            uni.hideLoading();
            uni.showToast({ title: '音频加载失败', icon: 'none' });
          }
        });
        return;
        // #endif
        
        this.createAudioContext(audioSrc);
        uni.hideLoading();
      } catch (e) {
        console.error('获取音频数据失败:', e);
        uni.hideLoading();
        uni.showToast({ title: e.message || '音频加载失败', icon: 'none' });
      }
    },
    createAudioContext(src) {
      this.audioContext = uni.createInnerAudioContext();
      this.audioContext.src = src;
      this.audioContext.autoplay = false;
      this.audioContext.loop = false;
      
      this.audioContext.onCanplay(() => {
        this.duration = this.audioContext.duration || 0;
        console.log('音频可播放，时长:', this.duration);
      });
      
      this.audioContext.onPlay(() => {
        this.isAudioPlaying = true;
        this.startProgressTimer();
      });
      
      this.audioContext.onPause(() => {
        this.isAudioPlaying = false;
        this.stopProgressTimer();
      });
      
      this.audioContext.onEnded(() => {
        this.isAudioPlaying = false;
        this.currentTime = 0;
        this.progress = 0;
        this.stopProgressTimer();
      });
      
      this.audioContext.onError((err) => {
        console.error('音频播放错误:', err);
        this.isAudioPlaying = false;
        this.stopProgressTimer();
        uni.showToast({
          title: '音频播放失败',
          icon: 'none'
        });
      });
      
      this.audioContext.onTimeUpdate(() => {
        this.currentTime = this.audioContext.currentTime || 0;
        if (this.duration > 0) {
          this.progress = (this.currentTime / this.duration) * 100;
        }
      });
    },
    toggleAudioPlay() {
      const recordId = this.serverRecordId || this.record.recordId;
      if (!recordId) {
        uni.showToast({
          title: '没有音频文件',
          icon: 'none'
        });
        return;
      }
      
      this.initAudio();
      
      if (this.isAudioPlaying) {
        this.audioContext.pause();
      } else {
        this.audioContext.play().catch((err) => {
          console.error('播放失败:', err);
          uni.showToast({
            title: '播放失败',
            icon: 'none'
          });
        });
      }
    },
    seekAudio(e) {
      if (!this.audioContext || !this.duration) {
        return;
      }
      
      const touch = e.touches ? e.touches[0] : e;
      const query = uni.createSelectorQuery();
      query.select('.audio-progress-bar').boundingClientRect((rect) => {
        if (rect) {
          const percent = (touch.clientX - rect.left) / rect.width;
          const newTime = Math.max(0, Math.min(this.duration, percent * this.duration));
          this.audioContext.seek(newTime);
        }
      }).exec();
    },
    startProgressTimer() {
      if (this.progressTimer) {
        return;
      }
      this.progressTimer = setInterval(() => {
        if (this.audioContext && this.isAudioPlaying) {
          this.currentTime = this.audioContext.currentTime || 0;
          if (this.duration > 0) {
            this.progress = (this.currentTime / this.duration) * 100;
          }
        }
      }, 100);
    },
    stopProgressTimer() {
      if (this.progressTimer) {
        clearInterval(this.progressTimer);
        this.progressTimer = null;
      }
    },
    destroyAudio() {
      this.stopProgressTimer();
      if (this.audioContext) {
        try {
          this.audioContext.destroy();
        } catch (e) {
          console.error('销毁音频上下文失败:', e);
        }
        this.audioContext = null;
      }
      // #ifdef H5
      if (this.audioSrc && this.audioSrc.startsWith('blob:')) {
        URL.revokeObjectURL(this.audioSrc);
        this.audioSrc = '';
      }
      // #endif
      this.isAudioPlaying = false;
      this.currentTime = 0;
      this.progress = 0;
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

.header-edit-btn {
  padding: 6px 16px;
}

.header-edit-text {
  font-size: 15px;
  color: #0099FF;
  font-weight: 500;
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
  text-align: right;
}

.info-value-wrap {
  display: flex;
  align-items: center;
  flex: 1;
  justify-content: flex-end;
  gap: 8px;
}

.info-input {
  font-size: 14px;
  color: #333333;
  font-weight: 500;
  text-align: right;
  padding: 4px 8px;
  border: 1px solid #0099FF;
  border-radius: 4px;
  background-color: #FFFFFF;
}

.picker-trigger {
  color: #0099FF;
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
.tag-summarized {
  background-color: #E6F7FF;
  color: #1890FF;
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
  position: relative;
}

.audio-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0099FF 0%, #0077B3 100%);
  border-radius: 2px;
}
.audio-progress-thumb {
  position: absolute;
  top: 50%;
  width: 12px;
  height: 12px;
  background-color: #FFFFFF;
  border-radius: 50%;
  border: 2px solid #0099FF;
  transform: translate(-50%, -50%);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
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

.chat-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-item {
  display: flex;
  position: relative;
  width: 100%;
}

.chat-bubble {
  position: relative;
  width: 100%;
  border-radius: 0 16px 16px 16px;
  padding: 12px 16px;
  box-sizing: border-box;
}

.bubble-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.bubble-speaker {
  font-size: 13px;
  font-weight: 600;
}

.bubble-time {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.4);
}

.bubble-content {
  position: relative;
}

.bubble-text {
  font-size: 14px;
  line-height: 1.6;
  color: #333333;
}

.bubble-tail {
  position: absolute;
  left: -8px;
  top: 20px;
  width: 0;
  height: 0;
  border-top: 12px solid transparent;
  border-right: 12px solid;
}

.bubble-textarea {
  width: 100%;
  min-height: 60px;
  max-height: 200px;
  font-size: 14px;
  line-height: 1.6;
  color: #333333;
  background-color: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  outline: none;
  padding: 8px 10px;
  box-sizing: border-box;
  overflow-y: auto;
}

.chat-item.speaker-1 .chat-bubble {
  background-color: #E6F7FF;
}

.chat-item.speaker-1 .bubble-speaker {
  color: #1890FF;
}

.chat-item.speaker-1 .bubble-tail {
  border-right-color: #E6F7FF;
}

.chat-item.speaker-2 .chat-bubble {
  background-color: #F6FFED;
}

.chat-item.speaker-2 .bubble-speaker {
  color: #52C41A;
}

.chat-item.speaker-2 .bubble-tail {
  border-right-color: #F6FFED;
}

.chat-item.speaker-3 .chat-bubble {
  background-color: #FFF7E6;
}

.chat-item.speaker-3 .bubble-speaker {
  color: #FA8C16;
}

.chat-item.speaker-3 .bubble-tail {
  border-right-color: #FFF7E6;
}

.chat-item.speaker-unknown .chat-bubble {
  background-color: #F5F5F5;
}

.chat-item.speaker-unknown .bubble-speaker {
  color: #999999;
}

.chat-item.speaker-unknown .bubble-tail {
  border-right-color: #F5F5F5;
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

.retranscribe-btn {
  width: 100%;
  height: 44px;
  background-color: #FFFFFF;
  border: 1px solid #0099FF;
  border-radius: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 12px;
}

.retranscribe-btn[disabled] {
  opacity: 0.6;
}

.retranscribe-btn-text {
  color: #0099FF;
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

.bottom-save-bar {
  padding: 16px;
  padding-bottom: calc(16px + env(safe-area-inset-bottom));
  background-color: #FFFFFF;
  border-top: 1px solid #EEEEEE;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.05);
}

.bottom-save-bar .save-btn {
  width: 100%;
}
</style>
