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
        <view class="status-row">
          <text class="record-status">
            {{ statusText }}
          </text>
        </view>

        <!-- 上传录音按钮 -->
        <view class="upload-section" v-if="!isRecording">
          <view class="upload-btn" :class="{ 'upload-btn-disabled': isUploading }" @click="handleUpload">
            <text class="upload-icon">📁</text>
            <text class="upload-btn-text">{{ isUploading ? '上传中...' : '上传录音' }}</text>
          </view>
        </view>
      </view>

      <!-- 实时转写文本区域 -->
      <view class="transcript-panel" :class="{ 'panel-collapsed': transcriptCollapsed }" v-if="recognizedText || isRecording || hasRecorded">
        <view class="transcript-header">
          <text class="transcript-title">走访记录</text>
          <view class="transcript-status" :class="{ 'status-active': isRecognizing }">
            <view class="status-dot"></view>
            <text class="status-text">{{ isRecognizing ? '识别中' : (isRecording ? '录音中' : '可编辑') }}</text>
          </view>
        </view>
        <textarea
          class="transcript-textarea"
          v-model="recognizedText"
          :placeholder="isRecording ? '正在识别语音...' : '点击编辑记录内容...'"
          :disabled="isRecording"
          auto-height
          maxlength="-1"
        />
        <view class="transcript-footer" v-if="hasRecorded && !isRecording">
          <view class="complete-btn" @click="handleComplete">
            <text class="complete-btn-text">完成</text>
          </view>
        </view>
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
        <view class="swipe-card" v-for="(item, index) in historyList" :key="item.id">
          <view class="swipe-delete-btn" @click="confirmDelete(item)">
            <text class="swipe-delete-text">删除</text>
          </view>
          <view 
            class="swipe-content" 
            :style="{ transform: `translateX(${swipeOffsets[item.id] || 0}px)` }"
            @touchstart="onTouchStart($event, item.id)"
            @touchmove="onTouchMove($event, item.id)"
            @touchend="onTouchEnd($event, item.id)"
            @click="goToDetail(item.id)"
          >
            <view class="history-card">
              <view class="history-card-head">
                <text class="history-name">{{ item.name }}</text>
                <text class="history-state" :class="item.status === 'done' ? 'state-done' : (item.status === 'failed' ? 'state-failed' : 'state-processing')">
                  {{ item.status === 'done' ? '已提取' : (item.status === 'failed' ? '转写失败' : '处理中') }}
                </text>
              </view>
              <view class="history-card-body">
                <view class="meta-row">
                  <text class="meta-label">走访时间：</text>
                  <text class="meta-val">{{ item.visitTime }}</text>
                </view>
                <view class="meta-row">
                  <text class="meta-label">沟通时长：</text>
                  <text class="meta-val">{{ item.durationText }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>
        <view class="empty-history" v-if="historyList.length === 0">
          <text class="empty-text">暂无走访记录</text>
        </view>
      </view>
    </view>

    <!-- 输入走访名称遮罩层 -->
    <view class="modal-mask" v-if="showNameModal" @click="closeNameModal">
      <view class="modal-content" @click.stop>
        <view class="modal-header">
          <text class="modal-title">输入走访名称</text>
        </view>
        <view class="modal-body">
          <input
            class="modal-input"
            v-model="editingName"
            placeholder="请输入走访名称"
            :maxlength="50"
            focus
          />
        </view>
        <view class="modal-footer">
          <view class="modal-btn modal-btn-cancel" @click="closeNameModal">
            <text class="modal-btn-text">取消</text>
          </view>
          <view class="modal-btn modal-btn-confirm" @click="confirmEditName">
            <text class="modal-btn-text">确定</text>
          </view>
        </view>
      </view>
    </view>

  </view>
</template>

<script>
// #ifdef APP-PLUS
import permission from "@/common/permission.js"
// #endif
import { getVoiceWsUrl } from "@/api/voice.js";
import { uploadAudioFile, submitSpeechToText, connectAsrWebSocket, getRecordIds, getRecordDetail, deleteRecord } from "@/api/file.js";
import { showNotification } from "@/common/notification.js";

const FRAME = { FIRST: 0, CONTINUE: 1, LAST: 2 };
const APPID = "speechvoice2";

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
      
      // 缓存的 WebSocket URL
      cachedWsUrl: "",
      // 是否正在识别
      isRecognizing: false,
      // 识别出的文本
      recognizedText: "",
      // 识别文本片段数组
      textSegments: [],
      // 是否是第一帧音频
      firstFrame: true,
      
      // H5 端录音相关
      // #ifdef H5
      audioContext: null,
      mediaStream: null,
      processor: null,
      h5Socket: null,
      audioChunks: [],
      // #endif
      
      // App 端录音相关
      // #ifdef APP-PLUS
      recorderManager: null,
      recordFilePath: "",
      // #endif
      
      // 通用 WebSocket 状态（uni.connectSocket）
      socketConnected: false,
      socketTask: null,
      
      // 录音文件本地保存路径
      savedAudioPath: "",
      // H5 端录音的 File 对象（带正确文件名后缀）
      savedAudioFile: null,
      savedAudioFileName: "",
      // 是否已完成录音（用于显示完成按钮）
      hasRecorded: false,
      // 走访记录面板是否收起
      transcriptCollapsed: false,
      
      // 历史记录列表
      historyList: [],
      // 左划删除相关
      swipeOffsets: {},
      touchStartX: {},
      touchStartY: {},
      deleteRecordItem: null,
      // 编辑中的名称
      editingName: "",
      // 是否显示名称修改弹窗
      showNameModal: false,
      // 名称弹窗模式：create（新建时输入名称）
      nameModalMode: "create",
      // 当前定位地址
      currentAddress: "",
      
      pendingRecord: null,
      isUploading: false,
      asrWebSocketMap: null,
      isAsrProcessing: false,
    };
  },
  computed: {
    progressDashOffset() {
      return this.circumference * (1 - this.longPressProgress);
    },
    statusText() {
      if (this.isRecording) {
        return this.isRecognizing ? '正在识别...长按按钮结束录音' : '录音中...长按按钮结束录音';
      }
      return '点击上方按钮开始录音';
    },
  },
  methods: {
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    },
    
    handleRecordClick() {
      if (!this.isRecording) {
        this.startRecording();
      }
    },

    handleUpload() {
      if (this.isUploading) return;
      this.chooseAudioFile();
    },

    chooseAudioFile() {
      // #ifdef H5
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.m4a,.mp3,.wav,.ogg,.flac,audio/*';
      input.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
          const blobUrl = URL.createObjectURL(file);
          this.processUploadFile(blobUrl, file.name, file.size, file);
        }
      };
      input.click();
      // #endif

      // #ifdef APP-PLUS
      if (typeof plus !== 'undefined' && plus.io) {
        plus.io.chooseFile({
          filter: ['m4a', 'mp3', 'wav', 'ogg', 'flac'],
          multiple: false,
          success: (res) => {
            if (res.files && res.files.length > 0) {
              const file = res.files[0];
              this.processUploadFile(file, file.split('/').pop(), 0);
            }
          },
          fail: (err) => {
            console.warn("选择文件失败:", err);
            uni.showToast({
              title: "选择文件失败",
              icon: "none"
            });
          }
        });
      } else {
        uni.chooseMessageFile({
          count: 1,
          type: 'file',
          extension: ['m4a', 'mp3', 'wav', 'ogg', 'flac'],
          success: (res) => {
            const file = res.tempFiles[0];
            this.processUploadFile(file.path, file.name, file.size);
          },
          fail: (err) => {
            console.warn("选择文件失败:", err);
            if (err.errMsg && err.errMsg.indexOf('cancel') === -1) {
              uni.showToast({
                title: "选择文件失败",
                icon: "none"
              });
            }
          }
        });
      }
      // #endif

      // #ifdef MP-WEIXIN
      uni.chooseMessageFile({
        count: 1,
        type: 'file',
        extension: ['m4a', 'mp3', 'wav', 'ogg', 'flac'],
        success: (res) => {
          const file = res.tempFiles[0];
          this.processUploadFile(file.path, file.name, file.size);
        },
        fail: (err) => {
          console.warn("选择文件失败:", err);
          if (err.errMsg && err.errMsg.indexOf('cancel') === -1) {
            uni.showToast({
              title: "选择文件失败",
              icon: "none"
            });
          }
        }
      });
      // #endif
    },

    async processUploadFile(filePath, fileName, fileSize, fileObject) {
      if (!filePath) {
        uni.showToast({
          title: "文件路径无效",
          icon: "none"
        });
        return;
      }

      try {
        const duration = await this.getAudioDuration(filePath);
        console.log("音频时长:", duration);

        this.savedAudioPath = filePath;
        this.savedAudioFile = fileObject || null;
        this.recognizedText = "";
        this.hasRecorded = true;
        this.recordDuration = Math.floor(duration);
        this.transcriptCollapsed = false;

        const now = new Date();
        this.pendingRecord = {
          id: Date.now().toString(),
          status: "processing",
          visitTime: this.formatDateTime(now),
          duration: Math.floor(duration),
          durationText: this.formatDurationText(Math.floor(duration)),
          content: "",
          audioPath: filePath,
          isAudioUploaded: false,
          createTime: now.getTime()
        };

        // 弹出名称输入框
        this.editingName = "走访记录";
        this.showNameModal = true;
        this.nameModalMode = "create";
      } catch (error) {
        console.error("处理上传文件失败:", error);
        uni.showToast({
          title: error.message || "处理文件失败",
          icon: "none"
        });
      }
    },

    getAudioDuration(filePath) {
      return new Promise((resolve) => {
        // #ifdef H5
        const audio = new Audio(filePath);
        audio.addEventListener('loadedmetadata', () => {
          resolve(audio.duration || 0);
        });
        audio.addEventListener('error', () => {
          resolve(0);
        });
        audio.src = filePath;
        // #endif

        // #ifndef H5
        uni.getFileInfo({
          filePath: filePath,
          success: () => {
            resolve(0);
          },
          fail: () => {
            resolve(0);
          }
        });
        // #endif
      });
    },
    
    async startRecording() {
      try {
        // 重置状态
        this.recognizedText = "";
        this.textSegments = [];
        this.firstFrame = true;
        this.isRecognizing = false;
        this.hasRecorded = false;
        this.savedAudioPath = "";
        this.savedAudioFile = null;
        this.savedAudioFileName = "";
        this.transcriptCollapsed = false;
        
        // 先获取 WebSocket URL
        await this.fetchWebSocketUrl();
        
        // 建立 WebSocket 连接
        await this.openSocket();
        
        // #ifdef H5
        await this.startH5Recording();
        // #endif
        
        // #ifdef APP-PLUS
        await this.startAppRecording();
        // #endif
        
        this.isRecording = true;
        this.recordDuration = 0;
        this.longPressProgress = 0;
        this.isRecognizing = true;
        
        this.timer = setInterval(() => {
          this.recordDuration++;
        }, 1000);
      } catch (error) {
        console.error("开始录音失败:", error);
        uni.showToast({
          title: error.message || "开始录音失败",
          icon: "none"
        });
        this.cleanupRecording();
      }
    },
    
    async fetchWebSocketUrl() {
      const wsUrl = await getVoiceWsUrl();
      this.cachedWsUrl = wsUrl;
      console.log("WebSocket URL:", wsUrl);
      return wsUrl;
    },
    
    openSocket() {
      return new Promise((resolve, reject) => {
        const wsUrl = this.cachedWsUrl;
        if (!wsUrl) {
          reject(new Error("WebSocket URL 为空"));
          return;
        }
        
        // #ifdef H5
        try {
          this.h5Socket = new WebSocket(wsUrl);
          this.h5Socket.onopen = () => {
            console.log("H5 WebSocket 连接成功");
            this.socketConnected = true;
            resolve();
          };
          this.h5Socket.onerror = (error) => {
            console.error("H5 WebSocket 错误:", error);
            reject(new Error("WebSocket 连接失败"));
          };
          this.h5Socket.onmessage = (event) => {
            this.handleMessage(event.data);
          };
          this.h5Socket.onclose = () => {
            console.log("H5 WebSocket 连接关闭");
            this.socketConnected = false;
            this.isRecognizing = false;
          };
        } catch (e) {
          reject(e);
        }
        // #endif
        
        // #ifndef H5
        this.socketTask = uni.connectSocket({
          url: wsUrl,
          success: () => {
            console.log("uni.connectSocket 调用成功");
          },
          fail: (err) => {
            console.error("uni.connectSocket 调用失败:", err);
            reject(new Error("WebSocket 连接失败"));
          }
        });
        
        this.socketTask.onOpen(() => {
          console.log("WebSocket 连接成功");
          this.socketConnected = true;
          resolve();
        });
        
        this.socketTask.onError((err) => {
          console.error("WebSocket 错误:", err);
          if (!this.socketConnected) {
            reject(new Error("WebSocket 连接失败"));
          }
        });
        
        this.socketTask.onMessage((res) => {
          this.handleMessage(res.data);
        });
        
        this.socketTask.onClose(() => {
          console.log("WebSocket 连接关闭");
          this.socketConnected = false;
          this.isRecognizing = false;
        });
        // #endif
      });
    },
    
    handleMessage(data) {
      console.log("【WebSocket原始数据】:", data);
      let result;
      try {
        result = JSON.parse(data);
      } catch (error) {
        console.error("JSON 解析失败:", error);
        return;
      }
      
      if (result.code !== 0) {
        console.error(`识别错误 ${result.code}: ${result.message || "unknown"}`);
        if (result.sid) console.log("sid:", result.sid);
        return;
      }
      
      const text = this.parseText(result);
      if (text) {
        this.textSegments.push(text);
        this.recognizedText = this.textSegments.join("");
      }
      
      if (result.data && result.data.status === FRAME.LAST) {
        this.isRecognizing = false;
        console.log("识别完成");
      } else {
        this.isRecognizing = true;
      }
    },
    
    parseText(result) {
      const ws = result && result.data && result.data.result && result.data.result.ws;
      if (!Array.isArray(ws)) {
        return "";
      }
      return ws.map((item) => {
        const cw = item && item.cw;
        return Array.isArray(cw) && cw[0] && typeof cw[0].w === "string" ? cw[0].w : "";
      }).join("");
    },
    
    arrayBufferToBase64(buffer) {
      let binary = "";
      const bytes = new Uint8Array(buffer);
      for (let i = 0; i < bytes.byteLength; i += 1) {
        binary += String.fromCharCode(bytes[i]);
      }
      return btoa(binary);
    },
    
    resampleAndConvertTo16kPCM(float32Data, inputSampleRate) {
      const targetRate = 16000;
      const ratio = inputSampleRate / targetRate;
      const newLength = Math.max(1, Math.round(float32Data.length / ratio));
      const result = new Int16Array(newLength);
      for (let i = 0; i < newLength; i += 1) {
        const srcIndex = Math.min(Math.round(i * ratio), float32Data.length - 1);
        const sample = Math.max(-1, Math.min(1, float32Data[srcIndex] || 0));
        result[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
      }
      return result.buffer;
    },
    
    sendFrame(audioData, frameStatus) {
      const frame = {
        data: {
          status: frameStatus,
          format: "audio/L16;rate=16000",
          encoding: "raw",
          audio: audioData ? this.arrayBufferToBase64(audioData) : ""
        }
      };
      if (frameStatus === FRAME.FIRST) {
        frame.common = { app_id: APPID };
        frame.business = {
          language: "zh_cn",
          domain: "iat",
          accent: "mandarin",
          dwa: "wpgs",
          vad_eos: 5000
        };
      }
      const frameStr = JSON.stringify(frame);
      
      // #ifdef H5
      if (this.h5Socket && this.h5Socket.readyState === WebSocket.OPEN) {
        this.h5Socket.send(frameStr);
      }
      // #endif
      
      // #ifndef H5
      if (this.socketConnected && this.socketTask) {
        this.socketTask.send({
          data: frameStr,
          fail: (err) => {
            console.error("发送 WebSocket 消息失败:", err);
          }
        });
      }
      // #endif
    },
    
    // #ifdef H5
    async startH5Recording() {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("当前浏览器不支持录音功能");
      }
      
      this.audioChunks = [];
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        }
      });
      
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
      
      this.processor.onaudioprocess = (event) => {
        const float32Data = event.inputBuffer.getChannelData(0);
        const pcm = this.resampleAndConvertTo16kPCM(float32Data, this.audioContext.sampleRate);
        
        this.audioChunks.push(new Int16Array(pcm));
        
        this.sendFrame(pcm, this.firstFrame ? FRAME.FIRST : FRAME.CONTINUE);
        this.firstFrame = false;
      };
      
      source.connect(this.processor);
      this.processor.connect(this.audioContext.destination);
    },
    
    async stopH5Recording(sendLastFrame = true) {
      if (sendLastFrame && this.h5Socket && this.h5Socket.readyState === WebSocket.OPEN) {
        this.sendFrame(new ArrayBuffer(0), FRAME.LAST);
      }
      
      if (this.processor) {
        this.processor.disconnect();
        this.processor = null;
      }
      if (this.audioContext) {
        await this.audioContext.close().catch(() => {});
        this.audioContext = null;
      }
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach((track) => track.stop());
        this.mediaStream = null;
      }
      
      await this.saveH5Audio();
      
      if (this.h5Socket) {
        setTimeout(() => {
          if (this.h5Socket) {
            this.h5Socket.close();
            this.h5Socket = null;
          }
        }, sendLastFrame ? 1800 : 0);
      }
    },
    
    async saveH5Audio() {
      if (this.audioChunks.length === 0) return;
      
      const sampleRate = 16000;
      const numChannels = 1;
      const bytesPerSample = 2;
      
      let totalLength = 0;
      for (const chunk of this.audioChunks) {
        totalLength += chunk.length;
      }
      
      const pcmData = new Int16Array(totalLength);
      let offset = 0;
      for (const chunk of this.audioChunks) {
        pcmData.set(chunk, offset);
        offset += chunk.length;
      }
      
      const wavBuffer = this.pcmToWav(pcmData.buffer, sampleRate, numChannels, bytesPerSample);
      const blob = new Blob([wavBuffer], { type: 'audio/wav' });
      
      const fileName = `record_${Date.now()}.wav`;
      const file = new File([blob], fileName, { type: 'audio/wav' });
      this.savedAudioFile = file;
      this.savedAudioFileName = fileName;
      this.savedAudioPath = URL.createObjectURL(blob);
      
      try {
        const link = document.createElement('a');
        link.href = this.savedAudioPath;
        link.download = fileName;
        link.click();
        console.log("H5 音频已保存（触发下载）:", fileName);
      } catch (e) {
        console.error("保存音频失败:", e);
      }
    },
    
    pcmToWav(pcmBuffer, sampleRate, numChannels, bytesPerSample) {
      const buffer = new ArrayBuffer(44 + pcmBuffer.byteLength);
      const view = new DataView(buffer);
      
      this.writeString(view, 0, 'RIFF');
      view.setUint32(4, 36 + pcmBuffer.byteLength, true);
      this.writeString(view, 8, 'WAVE');
      this.writeString(view, 12, 'fmt ');
      view.setUint32(16, 16, true);
      view.setUint16(20, 1, true);
      view.setUint16(22, numChannels, true);
      view.setUint32(24, sampleRate, true);
      view.setUint32(28, sampleRate * numChannels * bytesPerSample, true);
      view.setUint16(32, numChannels * bytesPerSample, true);
      view.setUint16(34, bytesPerSample * 8, true);
      this.writeString(view, 36, 'data');
      view.setUint32(40, pcmBuffer.byteLength, true);
      
      const pcmView = new Uint8Array(pcmBuffer);
      const wavView = new Uint8Array(buffer);
      for (let i = 0; i < pcmView.length; i++) {
        wavView[44 + i] = pcmView[i];
      }
      
      return buffer;
    },
    
    writeString(view, offset, string) {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    },
    // #endif
    
    // #ifdef APP-PLUS
    async startAppRecording() {
      let status = await this.checkPermission();
      if (status !== 1) {
        throw new Error("没有麦克风权限");
      }
      
      if (!this.recorderManager) {
        this.recorderManager = uni.getRecorderManager();
        
        this.recorderManager.onStart(() => {
          console.log('App 录音开始');
        });
        
        this.recorderManager.onStop((res) => {
          console.log('App 录音停止:', res);
          this.recordFilePath = res.tempFilePath;
          this.saveAppAudio();
        });
        
        this.recorderManager.onError((err) => {
          console.error('App 录音错误:', err);
        });
        
        this.recorderManager.onFrameRecorded((res) => {
          if (res.frameBuffer) {
            this.sendFrame(res.frameBuffer, this.firstFrame ? FRAME.FIRST : FRAME.CONTINUE);
            this.firstFrame = false;
          }
        });
      }
      
      this.recorderManager.start({
        duration: 600000,
        sampleRate: 16000,
        numberOfChannels: 1,
        encodeBitRate: 48000,
        format: 'wav',
        frameSize: 4
      });
    },
    
    stopAppRecording(sendLastFrame = true) {
      if (this.recorderManager) {
        this.recorderManager.stop();
      }
      
      if (sendLastFrame && this.socketConnected) {
        this.sendFrame(new ArrayBuffer(0), FRAME.LAST);
      }
      
      setTimeout(() => {
        if (this.socketTask) {
          this.socketTask.close();
          this.socketTask = null;
        }
      }, sendLastFrame ? 1800 : 0);
    },
    
    async saveAppAudio() {
      if (!this.recordFilePath) return;
      
      try {
        const fs = uni.getFileSystemManager();
        const fileName = `record_${Date.now()}.wav`;
        const savedPath = `${uni.env.USER_DATA_PATH}/${fileName}`;
        
        fs.saveFile({
          tempFilePath: this.recordFilePath,
          filePath: savedPath,
          success: (res) => {
            this.savedAudioPath = res.savedFilePath;
            console.log("App 音频已保存:", this.savedAudioPath);
          },
          fail: (err) => {
            console.error("保存音频失败:", err);
            this.savedAudioPath = this.recordFilePath;
          }
        });
      } catch (e) {
        console.error("保存音频异常:", e);
        this.savedAudioPath = this.recordFilePath;
      }
    },
    
    async checkPermission() {
      let status = permission.isIOS ? await permission.requestIOS('record') :
        await permission.requestAndroid('android.permission.RECORD_AUDIO');
      
      if (status === null || status === 1) {
        status = 1;
      } else if (status === 2) {
        uni.showModal({
          content: "系统麦克风已关闭",
          confirmText: "确定",
          showCancel: false
        });
      } else {
        uni.showModal({
          content: "需要麦克风权限",
          confirmText: "设置",
          success: (res) => {
            if (res.confirm) {
              permission.gotoAppSetting();
            }
          }
        });
      }
      return status;
    },
    // #endif
    
    handleTouchStart() {
      if (!this.isRecording) return;
      this.isLongPressing = true;
      this.longPressStartTime = Date.now();
      this.longPressProgress = 0;
      if (this.longPressTimer) {
        clearInterval(this.longPressTimer);
      }
      this.longPressTimer = setInterval(() => {
        const elapsed = Date.now() - this.longPressStartTime;
        this.longPressProgress = Math.min(elapsed / this.longPressDuration, 1);
        if (this.longPressProgress >= 1) {
          this.stopRecording();
          this.resetLongPress();
        }
      }, 16);
    },
    
    handleTouchEnd() {
      if (!this.isRecording) return;
      if (this.longPressProgress < 1) {
        this.resetLongPress();
      }
    },
    
    resetLongPress() {
      this.isLongPressing = false;
      this.longPressProgress = 0;
      if (this.longPressTimer) {
        clearInterval(this.longPressTimer);
        this.longPressTimer = null;
      }
    },
    
    async stopRecording() {
      this.isRecording = false;
      
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }
      
      this.resetLongPress();
      
      try {
        // #ifdef H5
        await this.stopH5Recording(true);
        // #endif
        
        // #ifdef APP-PLUS
        this.stopAppRecording(true);
        // #endif
        
        setTimeout(() => {
          this.isRecognizing = false;
          this.hasRecorded = true;
        }, 2000);
        
      } catch (error) {
        console.error("停止录音失败:", error);
        uni.showToast({
          title: "停止录音失败",
          icon: "none"
        });
        this.cleanupRecording();
      }
    },
    
    async handleComplete() {
      console.log("点击完成");
      
      if (!this.recognizedText && !this.savedAudioPath) {
        uni.showToast({
          title: "没有可提交的内容",
          icon: "none"
        });
        return;
      }
      
      // 暂存当前录音数据
      const now = new Date();
      this.pendingRecord = {
        id: Date.now().toString(),
        status: "processing",
        visitTime: this.formatDateTime(now),
        duration: this.recordDuration,
        durationText: this.formatDurationText(this.recordDuration),
        content: "",
        audioPath: this.savedAudioPath,
        isAudioUploaded: false,
        createTime: now.getTime()
      };
      
      // 弹出名称输入框
      this.editingName = "走访记录";
      this.showNameModal = true;
      this.nameModalMode = "create";
    },
    
    async uploadVisitRecord() {
      if (!this.pendingRecord) {
        return;
      }

      const audioPath = this.pendingRecord.audioPath;
      const isAudioUploaded = this.pendingRecord.isAudioUploaded;

      if (!audioPath) {
        uni.showToast({
          title: "没有录音文件可上传",
          icon: "none"
        });
        return;
      }

      try {
        uni.showLoading({
          title: "正在上传...",
          mask: true
        });

        let finalAudioUrl = audioPath;
        let serverRecordId = this.pendingRecord.recordId || null;
        let jobId = this.pendingRecord.jobId || null;

        if (!isAudioUploaded) {
          const visitDate = this.pendingRecord.visitTime
            ? this.pendingRecord.visitTime.split(' ')[0]
            : new Date().toISOString().split('T')[0];

          const formData = {
            creator_id: 1,
            customer_name: this.pendingRecord.name || "走访记录",
            visit_time: visitDate,
            status: 1,
            duration_seconds: this.pendingRecord.duration || 0
          };

          const res = await uploadAudioFile(audioPath, formData, this.savedAudioFile);
          console.log("走访记录上传成功:", res);
          finalAudioUrl = res.file_url || audioPath;
          serverRecordId = res.record_id;

          const sttResult = await submitSpeechToText(serverRecordId, 1);
          jobId = sttResult.job_id;
        }

        const record = {
          ...this.pendingRecord,
          name: this.pendingRecord.name || "走访记录",
          latitude: 0,
          longitude: 0,
          audioPath: finalAudioUrl,
          recordId: serverRecordId,
          content: this.recognizedText || this.pendingRecord.content,
          status: "processing",
          jobId: jobId
        };

        this.historyList.unshift(record);
        this.saveHistoryToStorage();

        if (jobId && serverRecordId && !this.pendingRecord.content) {
          this.listenForAsrResult(jobId, serverRecordId, record.id);
        }

        this.pendingRecord = null;

        this.resetRecordState();

        uni.hideLoading();
        uni.showToast({
          title: "上传成功",
          icon: "success"
        });
      } catch (error) {
        console.error("上传走访记录失败:", error);
        uni.hideLoading();
        uni.showToast({
          title: error.message || "上传失败",
          icon: "none"
        });
      }
    },
    
    formatDateTime(date) {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    },
    
    formatDurationText(seconds) {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      if (mins === 0) {
        return `${secs}秒`;
      }
      return `${mins}分${secs}秒`;
    },
    
    goToDetail(id) {
      if (this.swipeOffsets[id] && this.swipeOffsets[id] !== 0) {
        this.closeSwipe(id);
        return;
      }
      const record = this.historyList.find(item => item.id === id);
      const recordIdParam = record && record.recordId ? `&recordId=${record.recordId}` : '';
      uni.navigateTo({
        url: `/pages/visit/detail?id=${id}${recordIdParam}`
      });
    },

    onTouchStart(e, id) {
      this.touchStartX[id] = e.touches[0].clientX;
      this.touchStartY[id] = e.touches[0].clientY;
    },

    onTouchMove(e, id) {
      const deltaX = e.touches[0].clientX - this.touchStartX[id];
      const deltaY = e.touches[0].clientY - this.touchStartY[id];

      if (Math.abs(deltaY) > Math.abs(deltaX)) {
        return;
      }

      let offset = Math.max(-80, Math.min(0, deltaX));
      if (this.swipeOffsets[id] === -80 && deltaX < 0) {
        offset = -80 + deltaX * 0.3;
      }
      this.$set(this.swipeOffsets, id, offset);
    },

    onTouchEnd(e, id) {
      const deltaX = e.changedTouches[0].clientX - this.touchStartX[id];
      if (deltaX < -40) {
        this.$set(this.swipeOffsets, id, -80);
      } else {
        this.$set(this.swipeOffsets, id, 0);
      }
    },

    closeSwipe(id) {
      this.$set(this.swipeOffsets, id, 0);
    },

    closeAllSwipes() {
      Object.keys(this.swipeOffsets).forEach(id => {
        this.$set(this.swipeOffsets, id, 0);
      });
    },

    confirmDelete(item) {
      this.deleteRecordItem = item;
      uni.showModal({
        title: '确认删除',
        content: `确定要删除走访记录「${item.name}」吗？`,
        confirmText: '删除',
        confirmColor: '#FF4D4F',
        cancelText: '取消',
        success: (res) => {
          if (res.confirm) {
            this.doDelete(item);
          }
        }
      });
    },

    async doDelete(item) {
      try {
        uni.showLoading({
          title: '删除中...',
          mask: true
        });

        if (item.recordId) {
          await deleteRecord(item.recordId, 1);
        }

        const index = this.historyList.findIndex(r => r.id === item.id);
        if (index !== -1) {
          this.historyList.splice(index, 1);
          this.saveHistoryToStorage();
        }

        this.$set(this.swipeOffsets, item.id, 0);

        uni.hideLoading();
        uni.showToast({
          title: '删除成功',
          icon: 'success'
        });
      } catch (error) {
        console.error('删除失败:', error);
        uni.hideLoading();
        uni.showToast({
          title: error.message || '删除失败',
          icon: 'none'
        });
      }
    },

    closeNameModal() {
      this.showNameModal = false;
      this.editingName = "";
      
      if (this.nameModalMode === "create" && !this.isUploading) {
        this.pendingRecord = null;
        this.resetRecordState();
      }
      
      this.nameModalMode = "create";
    },
    
    async confirmEditName() {
      const name = this.editingName.trim();
      if (!name) {
        uni.showToast({
          title: "名称不能为空",
          icon: "none"
        });
        return;
      }
      
      if (this.nameModalMode === "create" && this.pendingRecord) {
        this.pendingRecord.name = name;
        this.showNameModal = false;
        this.editingName = "";
        await this.uploadVisitRecord();
        return;
      }
      
      this.closeNameModal();
    },
    
    saveHistoryToStorage() {
      try {
        uni.setStorageSync('visit_history', JSON.stringify(this.historyList));
      } catch (e) {
        console.error("保存历史记录失败:", e);
      }
    },
    
    loadHistoryFromStorage() {
      this.loadHistoryFromApi();
    },

    async loadHistoryFromApi() {
      try {
        const records = await getRecordIds(1);
        this.historyList = records.map(r => this.mapListRecordToLocal(r)).sort((a, b) => {
          return new Date(b.visitTime).getTime() - new Date(a.visitTime).getTime();
        });
      } catch (e) {
        console.error("从API加载历史记录失败:", e);
      }
    },

    mapListRecordToLocal(listRecord) {
      let visitTime = "";
      if (listRecord.visit_time) {
        const d = new Date(listRecord.visit_time);
        if (!isNaN(d.getTime())) {
          visitTime = this.formatDateTime(d);
        }
      }

      const duration = listRecord.duration_seconds || 0;
      let durationText = "--";
      if (duration > 0) {
        durationText = this.formatDurationText(duration);
      }

      let status = "processing";
      if (listRecord.status === "success") {
        status = "done";
      } else if (listRecord.status === "failed" || listRecord.status === "error") {
        status = "failed";
      }

      return {
        id: "record_" + listRecord.id,
        recordId: listRecord.id,
        name: listRecord.customer_name || "走访记录",
        status: status,
        visitTime: visitTime,
        duration: duration,
        durationText: durationText,
        content: "",
        audioPath: "",
        aiSummary: "",
        latitude: 0,
        longitude: 0
      };
    },

    mapServerRecordToLocal(serverRecord) {
      let content = "";
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
          visitTime = this.formatDateTime(d);
        }
      }

      const duration = serverRecord.duration_seconds || 0;
      let durationText = "--";
      if (duration > 0) {
        durationText = this.formatDurationText(duration);
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
        aiSummary: serverRecord.ai_summary || "",
        latitude: 0,
        longitude: 0
      };
    },
    
    resetRecordState() {
      this.hasRecorded = false;
      this.recognizedText = "";
      this.textSegments = [];
      this.savedAudioPath = "";
      this.savedAudioFile = null;
      this.savedAudioFileName = "";
      this.recordDuration = 0;
      this.transcriptCollapsed = false;
    },
    
    listenForAsrResult(jobId, recordId, localRecordId) {
      if (!jobId) {
        return;
      }

      const existingWs = this.asrWebSocketMap && this.asrWebSocketMap[jobId];
      if (existingWs) {
        return;
      }

      this.isAsrProcessing = true;

      if (!this.asrWebSocketMap) {
        this.asrWebSocketMap = {};
      }

      const ws = connectAsrWebSocket(jobId, {
        onMessage: (data) => {
          console.log("ASR WebSocket 消息:", data);
          if (data.status === "success") {
            const segments = (data.data && data.data.segments) || [];
            const text = segments.map(s => s.text || "").join("");
            this.handleAsrSuccess(jobId, recordId, localRecordId, text);
          } else if (data.status === "error") {
            console.warn("ASR 转写失败:", data.message);
            this.handleAsrError(jobId, recordId, localRecordId, data.message);
          }
        },
        onError: (error) => {
          console.error("ASR WebSocket 错误:", error);
          this.cleanupAsrWebSocket(jobId);
        },
        onClose: () => {
          this.cleanupAsrWebSocket(jobId);
        }
      });

      this.asrWebSocketMap[jobId] = ws;
    },

    handleAsrSuccess(jobId, recordId, localRecordId, text) {
      console.log("转写完成:", text);

      let recordName = "走访记录";
      let updated = false;

      if (localRecordId) {
        const index = this.historyList.findIndex(item => item.id === localRecordId);
        if (index !== -1) {
          recordName = this.historyList[index].name || recordName;
          this.historyList[index].content = text || "(未识别到语音内容)";
          this.historyList[index].status = "done";
          updated = true;
        }
      }

      if (!updated && recordId) {
        const index = this.historyList.findIndex(item => item.recordId === recordId);
        if (index !== -1) {
          recordName = this.historyList[index].name || recordName;
          this.historyList[index].content = text || "(未识别到语音内容)";
          this.historyList[index].status = "done";
          updated = true;
        }
      }

      if (updated) {
        this.saveHistoryToStorage();
      }

      showNotification("转写完成", `${recordName} 的语音转写已完成`);
      this.cleanupAsrWebSocket(jobId);
    },

    handleAsrError(jobId, recordId, localRecordId, errorMessage) {
      console.warn("转写失败:", errorMessage);

      let recordName = "走访记录";

      if (localRecordId) {
        const index = this.historyList.findIndex(item => item.id === localRecordId);
        if (index !== -1) {
          recordName = this.historyList[index].name || recordName;
          this.historyList[index].status = "failed";
        }
      }

      if (recordId) {
        const index = this.historyList.findIndex(item => item.recordId === recordId);
        if (index !== -1) {
          recordName = this.historyList[index].name || recordName;
          this.historyList[index].status = "failed";
        }
      }

      this.saveHistoryToStorage();
      showNotification("转写失败", `${recordName} 的语音转写失败: ${errorMessage || "未知错误"}`);
      this.cleanupAsrWebSocket(jobId);
    },

    cleanupAsrWebSocket(jobId) {
      if (this.asrWebSocketMap && this.asrWebSocketMap[jobId]) {
        try {
          this.asrWebSocketMap[jobId].close();
        } catch (e) {
          console.error("关闭 ASR WebSocket 失败:", e);
        }
        delete this.asrWebSocketMap[jobId];
      }

      if (this.asrWebSocketMap && Object.keys(this.asrWebSocketMap).length === 0) {
        this.isAsrProcessing = false;
      }
    },

    resumePendingAsrTasks() {
      if (!this.historyList || this.historyList.length === 0) {
        return;
      }

      const pendingRecords = this.historyList.filter(item => 
        item.status === "processing" && item.jobId && item.recordId
      );

      console.log("恢复待处理的转写任务:", pendingRecords.length);

      pendingRecords.forEach(record => {
        this.listenForAsrResult(record.jobId, record.recordId, record.id);
      });
    },

    closeAsrWebSocket() {
      if (this.asrWebSocketMap) {
        Object.keys(this.asrWebSocketMap).forEach(jobId => {
          try {
            this.asrWebSocketMap[jobId].close();
          } catch (e) {
            console.error("关闭 ASR WebSocket 失败:", e);
          }
        });
        this.asrWebSocketMap = {};
      }
      this.isAsrProcessing = false;
    },

    cleanupRecording() {
      this.isRecording = false;
      this.isRecognizing = false;
      
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }
      
      this.resetLongPress();
      
      // #ifdef H5
      if (this.processor) {
        this.processor.disconnect();
        this.processor = null;
      }
      if (this.audioContext) {
        this.audioContext.close().catch(() => {});
        this.audioContext = null;
      }
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach((track) => track.stop());
        this.mediaStream = null;
      }
      if (this.h5Socket) {
        this.h5Socket.close();
        this.h5Socket = null;
      }
      // #endif
      
      // #ifndef H5
      if (this.socketTask) {
        this.socketTask.close();
        this.socketTask = null;
      }
      // #endif
    },
  },
  onLoad() {
    this.loadHistoryFromApi().then(() => {
      this.resumePendingAsrTasks();
    });
  },
  onShow() {
    this.loadHistoryFromApi();
  },
  beforeDestroy() {
    this.closeAsrWebSocket();
    this.cleanupRecording();
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
.status-row {
  margin-top: 8px;
}

.upload-section {
  margin-top: 24px;
}
.upload-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 32px;
  background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);
  border-radius: 24px;
  border: 1px solid #E2E8F0;
  transition: all 0.3s ease;
}
.upload-btn:active {
  opacity: 0.8;
  transform: scale(0.98);
}
.upload-btn-disabled {
  opacity: 0.6;
  pointer-events: none;
}
.upload-icon {
  font-size: 16px;
}
.upload-btn-text {
  font-size: 14px;
  color: #475569;
  font-weight: 500;
}

/* 实时转写面板 */
.transcript-panel {
  margin-top: 32px;
  width: 100%;
  background-color: #F8FAFC;
  border-radius: 16px;
  border: 1px solid #E2E8F0;
  overflow: hidden;
}
.transcript-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background-color: #FFFFFF;
  border-bottom: 1px solid #E2E8F0;
}
.transcript-title {
  font-size: 16px;
  font-weight: 600;
  color: #1E293B;
}
.transcript-status {
  display: flex;
  align-items: center;
  gap: 6px;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #94A3B8;
}
.transcript-status.status-active .status-dot {
  background-color: #22C55E;
  animation: statusPulse 1.5s infinite ease-in-out;
}
@keyframes statusPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.2); }
}
.status-text {
  font-size: 13px;
  color: #64748B;
}
.transcript-textarea {
  width: 100%;
  min-height: 180px;
  padding: 16px 20px;
  box-sizing: border-box;
  font-size: 15px;
  line-height: 1.8;
  color: #334155;
  background-color: #F8FAFC;
  border: none;
  outline: none;
}
.transcript-textarea:disabled {
  color: #64748B;
  background-color: #F1F5F9;
}
.transcript-footer {
  padding: 12px 20px 20px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #E2E8F0;
  background-color: #FFFFFF;
}
.complete-btn {
  padding: 10px 32px;
  background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
  border-radius: 24px;
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
}
.complete-btn:active {
  opacity: 0.85;
  transform: scale(0.98);
}
.complete-btn-text {
  color: #FFFFFF;
  font-size: 15px;
  font-weight: 600;
}
/* 走访记录面板收起状态 */
.panel-collapsed {
  max-height: 60px;
  overflow: hidden;
  opacity: 0.6;
  transition: all 0.3s ease;
}
.panel-collapsed .transcript-textarea,
.panel-collapsed .transcript-footer {
  display: none;
}

/* 空状态 */
.empty-history {
  padding: 60px 20px;
  text-align: center;
}
.empty-text {
  font-size: 14px;
  color: #999999;
}

/* 遮罩层弹窗 */
.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
}
.modal-content {
  width: 80%;
  max-width: 320px;
  background-color: #FFFFFF;
  border-radius: 16px;
  overflow: hidden;
}
.modal-header {
  padding: 20px 20px 12px;
  text-align: center;
}
.modal-title {
  font-size: 17px;
  font-weight: 600;
  color: #222222;
}
.modal-body {
  padding: 12px 20px 20px;
}
.modal-input {
  width: 100%;
  height: 44px;
  padding: 0 16px;
  box-sizing: border-box;
  font-size: 15px;
  color: #333333;
  background-color: #F5F7FA;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  outline: none;
}
.modal-footer {
  display: flex;
  border-top: 1px solid #F0F0F0;
}
.modal-btn {
  flex: 1;
  padding: 14px 0;
  display: flex;
  justify-content: center;
  align-items: center;
}
.modal-btn:active {
  background-color: #F5F7FA;
}
.modal-btn-cancel {
  border-right: 1px solid #F0F0F0;
}
.modal-btn-cancel .modal-btn-text {
  color: #666666;
}
.modal-btn-confirm .modal-btn-text {
  color: #0099FF;
  font-weight: 600;
}
.modal-btn-text {
  font-size: 16px;
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
.state-failed {
  background-color: #FFF1F0;
  color: #FF4D4F;
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

/* 左划删除 */
.swipe-card {
  position: relative;
  overflow: hidden;
  margin-bottom: 12px;
  border-radius: 8px;
}
.swipe-delete-btn {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 80px;
  background-color: #FF4D4F;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  border-radius: 0 10px 10px 0;
}
.swipe-delete-text {
  color: #FFFFFF;
  font-size: 15px;
  font-weight: 500;
}
.swipe-content {
  position: relative;
  z-index: 2;
  transition: transform 0.2s ease;
}
</style>