<template>
  <view class="container">
    <!-- 录音主面板 (增加高级质感) -->
    <view class="record-panel">
      <view class="record-header">
        <text class="record-title">客户走访智能记录</text>
        <text class="record-desc">自动转写 · 智能提取纪要与待办</text>
      </view>
      
      <!-- 录音按钮区域 -->
      <view class="record-action">
        <!-- 按钮外框：根据状态切换水波纹/脉冲/背景色样式 -->
        <view class="record-btn-outer" :class="{ 'ripple-effect': !isRecording, 'recording-pulse': isRecording && !isLongPressing, 'recording-outer': isRecording }">
          <!-- 长按结束录音的圆形进度条（仅录音中显示） -->
          <view class="progress-ring" v-if="isRecording">
            <!-- SVG 圆形进度条：viewBox 定义 120x120 坐标系 -->
            <svg class="progress-ring-svg" viewBox="0 0 120 120">
              <circle class="progress-ring-bg" cx="60" cy="60" r="55" fill="none" stroke-width="3" />
              <!-- 进度圆弧：通过 stroke-dashoffset 控制显示比例 -->
              <circle
                class="progress-ring-circle"
                cx="60"
                cy="60"
                r="55"
                fill="none"
                stroke-width="3"
                :stroke-dasharray="circumference"
                :stroke-dashoffset="progressDashOffset"
                stroke-linecap="round"
              />
            </svg>
          </view>
          <!-- 录音按钮内圈 -->
          <view
            class="record-btn-inner"
            :class="{ 'recording-btn': isRecording }"
            @click="handleRecordClick"
            @touchstart="handleTouchStart"
            @touchend="handleTouchEnd"
            @touchcancel="handleTouchEnd"
          >
            <!-- 未录音时显示"录音"文字 -->
            <text v-if="!isRecording" class="record-btn-text">录音</text>
            <!-- 录音中显示计时器 -->
            <text v-else class="record-timer">{{ formatTime(recordDuration) }}</text>
          </view>
        </view>
        <!-- 状态提示文字，根据录音状态动态切换 -->
        <text class="record-status">
          {{ isRecording ? '长按按钮结束录音' : '点击上方按钮开始录音' }}
        </text>
      </view>
    </view>

    <!-- 历史记录 (卡片化与层次感) -->
    <view class="history-panel">
      <view class="panel-head">
        <text class="panel-title">最近走访</text>
        <view class="panel-filter">
          <text class="filter-text">筛选</text>
          <text class="filter-icon">▼</text>
        </view>
      </view>
      <view class="history-list">
        <view class="history-card">
          <view class="history-card-head">
            <text class="history-name">福州某某科技有限公司</text>
            <text class="history-state state-done">已提取</text>
          </view>
          <view class="history-card-body">
            <view class="meta-row">
              <text class="meta-label">走访时间：</text>
              <text class="meta-val">2026-06-01 14:30</text>
            </view>
            <view class="meta-row">
              <text class="meta-label">沟通时长：</text>
              <text class="meta-val">45分12秒</text>
            </view>
          </view>
        </view>
        
        <view class="history-card">
          <view class="history-card-head">
            <text class="history-name">仓山区某街道办事处</text>
            <text class="history-state state-processing">处理中</text>
          </view>
          <view class="history-card-body">
            <view class="meta-row">
              <text class="meta-label">走访时间：</text>
              <text class="meta-val">2026-05-28 09:15</text>
            </view>
            <view class="meta-row">
              <text class="meta-label">沟通时长：</text>
              <text class="meta-val">15分30秒</text>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      // 是否正在录音
      isRecording: false,
      // 录音时长（秒）
      recordDuration: 0,
      // 录音计时器引用
      timer: null,
      // 是否正在长按（用于触发结束录音的进度条）
      isLongPressing: false,
      // 长按进度（0~1）
      longPressProgress: 0,
      // 长按进度定时器引用
      longPressTimer: null,
      // 长按开始时间戳
      longPressStartTime: 0,
      // 长按时长阈值（毫秒），达到后触发结束录音
      longPressDuration: 1000,
      // 圆形进度条的周长（2 * π * 半径）
      circumference: 2 * Math.PI * 55,
    };
  },
  computed: {
    // 计算进度条的 dashoffset，控制圆弧显示长度
    // 原理：stroke-dasharray = 周长，stroke-dashoffset 从周长递减到0
    progressDashOffset() {
      return this.circumference * (1 - this.longPressProgress);
    },
  },
  methods: {
    // 将秒数格式化为 mm:ss 格式
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    },
    // 点击录音按钮处理
    handleRecordClick() {
      // 仅在未录音状态下，点击开始录音
      if (!this.isRecording) {
        this.startRecording();
      }
    },
    // 开始录音
    startRecording() {
      this.isRecording = true;
      this.recordDuration = 0;
      this.longPressProgress = 0;
      // 启动秒表计时器
      this.timer = setInterval(() => {
        this.recordDuration++;
      }, 1000);
      // TODO: 调用录音API开始录音
      // TODO: 初始化录音管理器
      // TODO: 录音文件路径设置
    },
    // 触摸开始（按下按钮）
    handleTouchStart() {
      // 仅在录音中响应长按事件
      if (!this.isRecording) return;
      this.isLongPressing = true;
      this.longPressStartTime = Date.now();
      this.longPressProgress = 0;
      // 清除之前可能存在的定时器
      if (this.longPressTimer) {
        clearInterval(this.longPressTimer);
      }
      // 每16ms更新一次进度（约60fps）
      this.longPressTimer = setInterval(() => {
        const elapsed = Date.now() - this.longPressStartTime;
        this.longPressProgress = Math.min(elapsed / this.longPressDuration, 1);
        // 进度满100%时，触发结束录音
        if (this.longPressProgress >= 1) {
          this.stopRecording();
          this.resetLongPress();
        }
      }, 16);
    },
    // 触摸结束（松开按钮）
    handleTouchEnd() {
      if (!this.isRecording) return;
      // 如果进度未满就松手，重置长按状态，继续录音
      if (this.longPressProgress < 1) {
        this.resetLongPress();
      }
    },
    // 重置长按状态
    resetLongPress() {
      this.isLongPressing = false;
      this.longPressProgress = 0;
      if (this.longPressTimer) {
        clearInterval(this.longPressTimer);
        this.longPressTimer = null;
      }
    },
    // 停止录音
    stopRecording() {
      this.isRecording = false;
      // 清除录音计时器
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }
      // 重置长按状态
      this.resetLongPress();
      // TODO: 调用录音API停止录音
      // TODO: 保存录音文件
      // TODO: 上传录音文件到服务器
      // TODO: 处理录音转写逻辑
    },
  },
  // 组件销毁前清理定时器，防止内存泄漏
  beforeDestroy() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    if (this.longPressTimer) {
      clearInterval(this.longPressTimer);
      this.longPressTimer = null;
    }
  },
};
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #F4F6F9;
  display: flex;
  flex-direction: column;
  padding-top: var(--status-bar-height);
  padding-bottom: 50px;
  box-sizing: border-box;
}

/* 录音主面板 */
.record-panel {
  background-color: #FFFFFF;
  padding: 40px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  border-bottom-left-radius: 24px;
  border-bottom-right-radius: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
  z-index: 10;
}
.record-header {
  text-align: center;
  margin-bottom: 48px;
}
.record-title {
  font-size: 22px;
  font-weight: 600;
  color: #222222;
  display: block;
  margin-bottom: 10px;
}
.record-desc {
  font-size: 14px;
  color: #888888;
  letter-spacing: 0.5px;
}
.record-action {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 录音按钮水波纹与阴影质感 */
.record-btn-outer {
  width: 110px;
  height: 110px;
  border-radius: 50%;
  background-color: #E6F4FF;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 24px;
  position: relative;
  transition: background-color 0.3s ease;
}
/* 录音按钮外框背景色（录音中状态） */
.recording-outer {
  background-color: #FFECEC;
}
/* 长按圆形进度条容器：绝对定位在按钮外围 */
.progress-ring {
  position: absolute;
  top: -10px;
  left: -10px;
  width: 130px;
  height: 130px;
  z-index: 20;
  /* 让进度条不响应点击事件，穿透到下方按钮 */
  pointer-events: none;
}
/* SVG 进度条整体旋转 -90度，使进度从顶部开始绘制 */
.progress-ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
/* 进度条背景轨道 */
.progress-ring-bg {
  stroke: rgba(255, 107, 107, 0.2);
}
/* 进度条前景圆弧 */
.progress-ring-circle {
  stroke: #FF6B6B;
  /* 平滑过渡动画 */
  transition: stroke-dashoffset 0.05s linear;
}
/* 未录音状态水波纹动画 */
.ripple-effect::before {
  content: '';
  position: absolute;
  top: -10px; right: -10px; bottom: -10px; left: -10px;
  border-radius: 50%;
  border: 1px solid rgba(0, 133, 208, 0.2);
  animation: ripple 2s infinite ease-in-out;
  /* 不响应点击事件，穿透到下方按钮（关键：否则会阻挡点击） */
  pointer-events: none;
}
@keyframes ripple {
  0% { transform: scale(0.8); opacity: 1; }
  100% { transform: scale(1.2); opacity: 0; }
}
.record-btn-inner {
  width: 86px;
  height: 86px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0099FF 0%, #0077B3 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 8px 20px rgba(0, 133, 208, 0.4);
}
.record-btn-text {
  color: #FFFFFF;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 2px;
}
/* 录音中计时器文字样式 */
.record-timer {
  color: #FFFFFF;
  font-size: 20px;
  font-weight: 600;
  /* 等宽字体，防止数字跳动 */
  font-family: 'Courier New', monospace;
  letter-spacing: 1px;
}
/* 录音中按钮内圈样式（红色渐变） */
.recording-btn {
  background: linear-gradient(135deg, #FF6B6B 0%, #EE5A5A 100%) !important;
  box-shadow: 0 8px 20px rgba(255, 107, 107, 0.4) !important;
}
/* 录音中脉冲动画（长按时不显示，避免视觉干扰） */
.recording-pulse::before {
  content: '';
  position: absolute;
  top: -10px; right: -10px; bottom: -10px; left: -10px;
  border-radius: 50%;
  border: 2px solid rgba(255, 107, 107, 0.3);
  animation: recordingPulse 1.5s infinite ease-in-out;
  /* 不响应点击事件，穿透到下方按钮 */
  pointer-events: none;
}
@keyframes recordingPulse {
  0% { transform: scale(0.9); opacity: 1; }
  50% { transform: scale(1.15); opacity: 0.5; }
  100% { transform: scale(0.9); opacity: 1; }
}
.record-status {
  font-size: 14px;
  color: #999999;
}

/* 历史记录卡片化 */
.history-panel {
  flex: 1;
  padding: 24px 16px;
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #222222;
}
.panel-filter {
  display: flex;
  align-items: center;
  background-color: #FFFFFF;
  padding: 4px 10px;
  border-radius: 12px;
  border: 1px solid #EEEEEE;
}
.filter-text {
  font-size: 13px;
  color: #666666;
  margin-right: 4px;
}
.filter-icon {
  font-size: 10px;
  color: #999999;
}
.history-card {
  background-color: #FFFFFF;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}
.history-card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  border-bottom: 1px dashed #F0F0F0;
  padding-bottom: 12px;
}
.history-name {
  font-size: 16px;
  color: #333333;
  font-weight: 600;
  flex: 1;
  margin-right: 12px;
}
.history-state {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
}
.state-done {
  background-color: #F6FFED;
  color: #52C41A;
}
.state-processing {
  background-color: #FFF7E6;
  color: #FA8C16;
}
.history-card-body {
  display: flex;
  flex-direction: column;
}
.meta-row {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
}
.meta-row:last-child {
  margin-bottom: 0;
}
.meta-label {
  font-size: 13px;
  color: #999999;
  width: 70px;
}
.meta-val {
  font-size: 13px;
  color: #444444;
}
</style>