<template>
  <view class="chat-page" :style="{ height: pageHeight + 'px' }">
    <view class="navbar">
      <text class="navbar-title">知识库</text>
    </view>
    
    <scroll-view 
      class="chat-list" 
      scroll-y 
      :scroll-into-view="scrollToId"
      scroll-with-animation
    >
      <view v-for="(msg, index) in messages" :key="index">
        <view v-if="shouldShowTime(index)" class="chat-time">
          {{ formatMsgTime(msg.timestamp) }}
        </view>
        
        <view :class="['msg-row', msg.role === 'ai' ? 'ai-row' : 'user-row']">
          <view v-if="msg.role === 'ai'" class="avatar ai-avatar">助</view>
          <view :class="['msg-box', msg.role === 'ai' ? 'ai-msg' : 'user-msg']">
            <text class="msg-text">{{ msg.content }}</text>
            <view v-if="msg.role === 'ai' && msg.source_files && msg.source_files.length > 0" class="source-files">
              <text class="source-label">参考文件:</text>
              <text v-for="(file, idx) in msg.source_files" :key="idx" class="source-file-name">{{ file }}</text>
            </view>
            <view v-if="msg.role === 'ai' && msg.showActions" class="msg-actions">
              <text 
                class="action-link" 
                :class="{ 'action-link-disabled': !msg.file_records || msg.file_records.length === 0 }"
                @click="showSourceFiles(msg)"
              >查看源文件</text>
              <text class="action-divider">|</text>
              <text class="action-link">问题上报</text>
            </view>
          </view>
          <view v-if="msg.role === 'user'" class="avatar user-avatar">我</view>
        </view>
      </view>
      
      <view v-if="loading" class="msg-row ai-row">
        <view class="avatar ai-avatar">助</view>
        <view class="msg-box ai-msg">
          <view class="loading-dots">
            <view class="dot"></view>
            <view class="dot"></view>
            <view class="dot"></view>
          </view>
        </view>
      </view>
      
      <view id="scroll-bottom-anchor" class="scroll-bottom-anchor"></view>
    </scroll-view>

    <view class="input-panel">
      <input 
        class="chat-input" 
        placeholder="请输入业务问题..." 
        v-model="inputText"
        @confirm="onSend"
      />
      <view 
        :class="['send-btn', inputText.trim() ? '' : 'send-btn-disabled']"
        @click="onSend"
      >发送</view>
    </view>

    <view v-if="showFileModal" class="modal-overlay" @click="closeFileModal">
      <view class="modal-content" @click.stop>
        <view class="modal-header">
          <text class="modal-title">源文件列表</text>
          <text class="modal-close" @click="closeFileModal">×</text>
        </view>
        <scroll-view class="file-list" scroll-y>
          <view 
            v-for="file in currentFiles" 
            :key="file.id" 
            class="file-item"
            @click="openFile(file)"
          >
            <view class="file-icon">📄</view>
            <view class="file-info">
              <text class="file-name">{{ file.file_name }}</text>
              <text class="file-size">{{ formatFileSize(file.file_size) }}</text>
            </view>
            <view class="file-arrow">→</view>
          </view>
          <view v-if="currentFiles.length === 0" class="empty-state">
            <text>暂无匹配的源文件</text>
          </view>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'

const messages = ref([
  {
    role: 'ai',
    content: '您好，我是榕小助。您可以向我询问最新的资费政策、营销方案等业务问题。',
    showActions: false,
    source_files: [],
    file_records: [],
    timestamp: Date.now()
  }
])

const inputText = ref('')
const loading = ref(false)
const scrollToId = ref('')
const pageHeight = ref(0)
const showFileModal = ref(false)
const currentFiles = ref([])

onMounted(() => {
  const systemInfo = uni.getSystemInfoSync()
  pageHeight.value = systemInfo.windowHeight
})

watch(messages, () => {
  nextTick(() => {
    setTimeout(() => {
      scrollToBottom()
    }, 100)
  })
}, { deep: true })

function scrollToBottom() {
  scrollToId.value = 'scroll-bottom-anchor'
  setTimeout(() => {
    scrollToId.value = ''
  }, 300)
}

function shouldShowTime(index) {
  if (index === 0) return true
  
  const currentTime = messages.value[index].timestamp
  const prevTime = messages.value[index - 1].timestamp
  
  const diffMinutes = (currentTime - prevTime) / 1000 / 60
  
  if (diffMinutes >= 5) return true
  
  const currentDate = new Date(currentTime).toDateString()
  const prevDate = new Date(prevTime).toDateString()
  
  return currentDate !== prevDate
}

function formatMsgTime(timestamp) {
  const date = new Date(timestamp)
  const now = new Date()
  
  const todayStr = now.toDateString()
  const msgDateStr = date.toDateString()
  
  if (todayStr === msgDateStr) {
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    return `${hours}:${minutes}`
  } else {
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    return `${month}-${day} ${hours}:${minutes}`
  }
}

function onSend() {
  const text = inputText.value.trim()
  if (!text || loading.value) return
  
  inputText.value = ''
  loading.value = true
  
  messages.value.push({
    role: 'user',
    content: text,
    showActions: false,
    source_files: [],
    file_records: [],
    timestamp: Date.now()
  })
  
  nextTick(() => {
    setTimeout(() => {
      scrollToBottom()
    }, 100)
  })
  
  uni.request({
    url: '/api/knowledge',
    method: 'POST',
    data: {
      ques: text,
      'sys.files': [],
      'sys.user_id': '',
      'sys.app_id': '',
      'sys.workflow_id': '',
      'sys.workflow_run_id': '',
      stream: false
    },
    header: {
      'Content-Type': 'application/json'
    },
    success: (res) => {
      loading.value = false
      
      console.log('API响应:', res)
      
      if (res.statusCode !== 200) {
        messages.value.push({
          role: 'ai',
          content: `服务器返回错误 ${res.statusCode}，请稍后重试。`,
          showActions: false,
          source_files: [],
          file_records: [],
          timestamp: Date.now()
        })
        return
      }
      
      let replyContent = '抱歉，我暂时无法回答这个问题。'
      let sourceFiles = []
      let fileRecords = []
      
      if (res && res.data) {
        if (res.data.content) {
          replyContent = res.data.content
        } else if (res.data.msg) {
          replyContent = res.data.msg
        } else if (typeof res.data === 'string') {
          replyContent = res.data
        } else {
          replyContent = JSON.stringify(res.data)
        }
        
        if (res.data.source_files) {
          sourceFiles = res.data.source_files
        }
        if (res.data.file_records) {
          fileRecords = res.data.file_records
        }
      }
      
      messages.value.push({
        role: 'ai',
        content: replyContent,
        showActions: true,
        source_files: sourceFiles,
        file_records: fileRecords,
        timestamp: Date.now()
      })
    },
    fail: (err) => {
      loading.value = false
      messages.value.push({
        role: 'ai',
        content: '网络连接失败，请稍后重试。',
        showActions: false,
        source_files: [],
        file_records: [],
        timestamp: Date.now()
      })
    }
  })
}

function showSourceFiles(msg) {
  if (msg.file_records && msg.file_records.length > 0) {
    currentFiles.value = msg.file_records
    showFileModal.value = true
  }
}

function closeFileModal() {
  showFileModal.value = false
  currentFiles.value = []
}

function openFile(file) {
  uni.showLoading({ title: '下载中...' })
  
  // #ifdef H5
  // H5端：使用fetch下载并通过a标签实现正确文件名
  fetch(`/api/knowledge/download/${file.id}/`)
    .then(response => response.blob())
    .then(blob => {
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = file.file_name
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      uni.hideLoading()
    })
    .catch(() => {
      uni.hideLoading()
      uni.showToast({ title: '下载失败', icon: 'none' })
    })
  // #endif
  
  // #ifndef H5
  // 非H5端：使用uni.downloadFile
  uni.downloadFile({
    url: `/api/knowledge/download/${file.id}/`,
    success: (res) => {
      if (res.statusCode === 200) {
        // #ifdef MP-WEIXIN
        // 微信小程序：保存文件后再打开
        const fs = wx.getFileSystemManager()
        const savedPath = `${wx.env.USER_DATA_PATH}/${file.file_name}`
        try {
          fs.saveFileSync(res.tempFilePath, savedPath)
          uni.openDocument({
            filePath: savedPath,
            fileType: getFileType(file.file_type, file.file_name),
            showMenu: true,
            success: () => { uni.hideLoading() },
            fail: () => {
              uni.hideLoading()
              uni.showToast({ title: '无法打开文件', icon: 'none' })
            }
          })
        } catch (e) {
          uni.hideLoading()
          uni.openDocument({
            filePath: res.tempFilePath,
            fileType: getFileType(file.file_type, file.file_name),
            showMenu: true,
            success: () => {},
            fail: () => {
              uni.showToast({ title: '无法打开文件', icon: 'none' })
            }
          })
        }
        // #endif
        
        // #ifndef MP-WEIXIN
        // 其他平台：直接打开临时文件
        uni.hideLoading()
        uni.openDocument({
          filePath: res.tempFilePath,
          fileType: getFileType(file.file_type, file.file_name),
          showMenu: true,
          success: () => {},
          fail: () => {
            uni.showToast({ title: '无法打开文件', icon: 'none' })
          }
        })
        // #endif
      } else {
        uni.hideLoading()
        uni.showToast({ title: '下载失败', icon: 'none' })
      }
    },
    fail: () => {
      uni.hideLoading()
      uni.showToast({ title: '下载失败', icon: 'none' })
    }
  })
  // #endif
}

function getFileType(fileType, fileName) {
  if (fileType) {
    const ext = fileType.replace('.', '').toLowerCase()
    const typeMap = {
      'docx': 'doc',
      'doc': 'doc',
      'pdf': 'pdf',
      'txt': 'txt',
      'xlsx': 'xlsx',
      'xls': 'xls',
      'ppt': 'ppt',
      'pptx': 'pptx'
    }
    return typeMap[ext] || 'doc'
  }
  if (fileName) {
    const ext = fileName.split('.').pop().toLowerCase()
    const typeMap = {
      'docx': 'doc',
      'doc': 'doc',
      'pdf': 'pdf',
      'txt': 'txt',
      'xlsx': 'xlsx',
      'xls': 'xls',
      'ppt': 'ppt',
      'pptx': 'pptx'
    }
    return typeMap[ext] || 'doc'
  }
  return 'doc'
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  padding-top: var(--status-bar-height);
  box-sizing: border-box;
  background-color: #F5F6F8;
}
.navbar {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #ffffff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}
.navbar-title {
  font-size: 17px;
  font-weight: 600;
  color: #333333;
}
.chat-list {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  box-sizing: border-box;
}
.scroll-bottom-anchor {
  height: 0;
  width: 100%;
}
.chat-time {
  text-align: center;
  font-size: 12px;
  color: #999999;
  margin-bottom: 16px;
}
.msg-row {
  display: flex;
  margin-bottom: 20px;
  align-items: flex-start;
  width: 100%;
}
.ai-row {
  justify-content: flex-start;
}
.user-row {
  justify-content: flex-end;
}
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
  flex-shrink: 0;
}
.ai-avatar {
  background: linear-gradient(135deg, #006BB3 0%, #0085D0 100%);
  color: #ffffff;
  margin-right: 12px;
}
.user-avatar {
  background: linear-gradient(135deg, #5B8FF9 0%, #3B7EFF 100%);
  color: #ffffff;
  margin-left: 12px;
}
.msg-box {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  word-break: break-all;
  flex-shrink: 0;
}
.ai-msg {
  background-color: #ffffff;
  border-top-left-radius: 4px;
}
.user-msg {
  background: linear-gradient(135deg, #0085D0 0%, #006BB3 100%);
  border-top-right-radius: 4px;
}
.msg-text {
  font-size: 15px;
  line-height: 1.6;
}
.ai-msg .msg-text {
  color: #333333;
}
.user-msg .msg-text {
  color: #ffffff;
}
.msg-actions {
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px dashed #eeeeee;
  display: flex;
  align-items: center;
}
.action-link {
  font-size: 13px;
  color: #0085d0;
}
.action-divider {
  font-size: 12px;
  color: #dddddd;
  margin: 0 8px;
}
.input-panel {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background-color: #ffffff;
  border-top: 1px solid #eeeeee;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.03);
}
.chat-input {
  flex: 1;
  height: 36px;
  background-color: #f5f6f8;
  border-radius: 18px;
  padding: 0 16px;
  font-size: 14px;
}
.send-btn {
  margin-left: 12px;
  height: 36px;
  line-height: 36px;
  background: linear-gradient(135deg, #0085D0 0%, #006BB3 100%);
  color: #ffffff;
  font-size: 14px;
  padding: 0 16px;
  border-radius: 18px;
}
.send-btn-disabled {
  background: linear-gradient(135deg, #CCCCCC 0%, #BBBBBB 100%);
}
.loading-dots {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #0085D0;
  margin: 0 4px;
  animation: dotBounce 1.4s infinite ease-in-out both;
}
.dot:nth-child(1) {
  animation-delay: -0.32s;
}
.dot:nth-child(2) {
  animation-delay: -0.16s;
}
@keyframes dotBounce {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.source-files {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #f0f0f0;
}

.source-label {
  font-size: 12px;
  color: #999999;
}

.source-file-name {
  font-size: 12px;
  color: #0085d0;
  margin-left: 8px;
  margin-right: 8px;
}

.action-link-disabled {
  color: #cccccc;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  width: 80%;
  max-width: 320px;
  background-color: #ffffff;
  border-radius: 12px;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #eeeeee;
}

.modal-title {
  font-size: 16px;
  font-weight: 600;
  color: #333333;
}

.modal-close {
  font-size: 24px;
  color: #999999;
  line-height: 1;
}

.file-list {
  max-height: 400px;
  padding: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 4px;
}

.file-item:active {
  background-color: #f5f6f8;
}

.file-icon {
  font-size: 24px;
  margin-right: 12px;
}

.file-info {
  flex: 1;
  overflow: hidden;
}

.file-name {
  font-size: 14px;
  color: #333333;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 12px;
  color: #999999;
  margin-top: 4px;
}

.file-arrow {
  font-size: 16px;
  color: #cccccc;
}

.empty-state {
  text-align: center;
  padding: 40px 16px;
  color: #999999;
  font-size: 14px;
}
</style>
