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
      :style="{ paddingBottom: listPaddingBottom + 'px' }"
    >
      <view v-for="(msg, index) in messages" :key="index">
        <view v-if="shouldShowTime(index)" class="chat-time">
          {{ formatMsgTime(msg.timestamp) }}
        </view>
        
        <view :class="['msg-row', msg.role === 'ai' ? 'ai-row' : 'user-row']">
          <view v-if="msg.role === 'ai'" class="avatar ai-avatar">助</view>
          <view :class="['msg-box', msg.role === 'ai' ? 'ai-msg' : 'user-msg']">
            <rich-text 
              v-if="msg.role === 'ai'" 
              class="msg-text" 
              :nodes="msg.htmlContent || msg.content"
            ></rich-text>
            <text v-else class="msg-text">{{ msg.content }}</text>
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

    <view class="input-panel" :style="{ bottom: inputBottom + 'px' }">
      <input 
        class="chat-input" 
        placeholder="请输入业务问题..." 
        v-model="inputText"
        :adjust-position="false"
        @confirm="onSend"
        @focus="onInputFocus"
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
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'

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
const keyboardHeight = ref(0)
const tabbarHeight = ref(0) // 原生 tabbar 高度 + 底部安全区
const showFileModal = ref(false)
const currentFiles = ref([])

// 输入栏底部偏移：键盘弹起时贴键盘顶部（需减去 tabbar 高度，因 .chat-page 底部在 tabbar 上方），否则贴页面底部
const inputBottom = computed(() => {
  if (keyboardHeight.value > 0) {
    return Math.max(0, keyboardHeight.value - tabbarHeight.value)
  }
  return 0
})

// 聊天列表底部留白：键盘弹起时留键盘高度，否则留输入栏高度
const listPaddingBottom = computed(() => {
  return inputBottom.value + 76
})

onMounted(() => {
  const systemInfo = uni.getSystemInfoSync()
  // App端使用 screenHeight（物理屏幕高度，不随键盘变化）
  // H5端使用 windowHeight（不包含浏览器地址栏）
  // #ifdef APP-PLUS
  // 原生 tabbar 高度约 50px + 底部安全区
  const safeBottom = systemInfo.safeAreaInsets?.bottom || 0
  tabbarHeight.value = 50 + safeBottom
  // 页面高度 = 屏幕高度 - tabbar 高度（只占 tabbar 上方区域，避免页面可滚动）
  pageHeight.value = systemInfo.screenHeight - tabbarHeight.value
  // #endif
  // #ifndef APP-PLUS
  pageHeight.value = systemInfo.windowHeight
  // H5 端 tabbar 是页面内渲染的，不需要额外偏移
  tabbarHeight.value = 0
  // #endif

  // 监听键盘高度变化 - 仅用于控制输入栏 bottom 偏移，不改变列表高度
  uni.onKeyboardHeightChange((res) => {
    keyboardHeight.value = res.height
    if (res.height > 0) {
      nextTick(() => {
        setTimeout(() => {
          scrollToBottom()
        }, 100)
      })
    }
  })
})

onUnmounted(() => {
  uni.offKeyboardHeightChange()
})

function onInputFocus() {
  nextTick(() => {
    setTimeout(() => {
      scrollToBottom()
    }, 100)
  })
}

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
  
  const userInfo = uni.getStorageSync('userInfo') || {};
  const userId = userInfo.empId || String(userInfo.id || '');

  uni.request({
    url: '/api/knowledge',
    method: 'POST',
    data: {
      ques: text,
      'sys.files': [],
      'sys.user_id': userId,
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
        htmlContent: markdownToHtml(replyContent),
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

function markdownToHtml(text) {
  if (!text) return ''
  
  let html = text
  
  // 先处理双重转义的格式 $\\rightarrow$
  html = html.replace(/\\rightarrow/g, '→')
  html = html.replace(/\\leftarrow/g, '←')
  html = html.replace(/\\Rightarrow/g, '⇒')
  html = html.replace(/\\Leftarrow/g, '⇐')
  html = html.replace(/\\leftrightarrow/g, '↔')
  html = html.replace(/\\Leftrightarrow/g, '⇔')
  html = html.replace(/\\uparrow/g, '↑')
  html = html.replace(/\\downarrow/g, '↓')
  html = html.replace(/\\times/g, '×')
  html = html.replace(/\\div/g, '÷')
  html = html.replace(/\\leq/g, '≤')
  html = html.replace(/\\geq/g, '≥')
  html = html.replace(/\\neq/g, '≠')
  html = html.replace(/\\infty/g, '∞')
  html = html.replace(/\\alpha/g, 'α')
  html = html.replace(/\\beta/g, 'β')
  html = html.replace(/\\gamma/g, 'γ')
  html = html.replace(/\\delta/g, 'δ')
  html = html.replace(/\\theta/g, 'θ')
  html = html.replace(/\\pi/g, 'π')
  html = html.replace(/\\sigma/g, 'σ')
  html = html.replace(/\\omega/g, 'ω')
  
  // 再处理 LaTeX 公式中的 $...$ 格式
  html = html.replace(/\$→\$/g, '→')
  html = html.replace(/\$←\$/g, '←')
  html = html.replace(/\$⇒\$/g, '⇒')
  html = html.replace(/\$⇐\$/g, '⇐')
  html = html.replace(/\$↔\$/g, '↔')
  html = html.replace(/\$⇔\$/g, '⇔')
  html = html.replace(/\$↑\$/g, '↑')
  html = html.replace(/\$↓\$/g, '↓')
  html = html.replace(/\$×\$/g, '×')
  html = html.replace(/\$÷\$/g, '÷')
  html = html.replace(/\$≤\$/g, '≤')
  html = html.replace(/\$≥\$/g, '≥')
  html = html.replace(/\$≠\$/g, '≠')
  html = html.replace(/\$∞\$/g, '∞')
  html = html.replace(/\$α\$/g, 'α')
  html = html.replace(/\$β\$/g, 'β')
  html = html.replace(/\$γ\$/g, 'γ')
  html = html.replace(/\$δ\$/g, 'δ')
  html = html.replace(/\$θ\$/g, 'θ')
  html = html.replace(/\$π\$/g, 'π')
  html = html.replace(/\$σ\$/g, 'σ')
  html = html.replace(/\$ω\$/g, 'ω')
  
  // 处理剩余的 $...$（移除美元符号）
  html = html.replace(/\$/g, '')
  
  // 处理行内代码 `code`
  html = html.replace(/`([^`]+)`/g, '<code style="background:#f0f0f0;padding:2px 4px;border-radius:3px;font-family:monospace;">$1</code>')
  
  // 处理 **粗体**
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong style="font-weight:bold;">$1</strong>')
  
  // 处理 *斜体*
  html = html.replace(/\*([^*]+)\*/g, '<em style="font-style:italic;">$1</em>')
  
  // 处理 __粗体__
  html = html.replace(/__([^_]+)__/g, '<strong style="font-weight:bold;">$1</strong>')
  
  // 处理 _斜体_
  html = html.replace(/_([^_]+)_/g, '<em style="font-style:italic;">$1</em>')
  
  // 处理换行符（实际的换行符）
  html = html.replace(/\n/g, '<br/>')
  html = html.replace(/\\n/g, '<br/>')
  
  // 处理列表 - 数字列表
  html = html.replace(/^(\d+)\.\s+(.+)$/gm, '<li>$2</li>')
  
  // 处理列表 - 无序列表
  html = html.replace(/^\*\s+(.+)$/gm, '<li style="list-style-type:disc;">$1</li>')
  html = html.replace(/^-\s+(.+)$/gm, '<li style="list-style-type:disc;">$1</li>')
  
  // 处理标题
  html = html.replace(/^###\s+(.+)$/gm, '<h3 style="font-size:14px;font-weight:bold;margin:10px 0;">$1</h3>')
  html = html.replace(/^##\s+(.+)$/gm, '<h2 style="font-size:16px;font-weight:bold;margin:10px 0;">$1</h2>')
  html = html.replace(/^#\s+(.+)$/gm, '<h1 style="font-size:18px;font-weight:bold;margin:10px 0;">$1</h1>')
  
  return html
}
</script>

<style scoped>
.chat-page {
  position: relative;
  display: flex;
  flex-direction: column;
  padding-top: var(--status-bar-height);
  box-sizing: border-box;
  background-color: #F5F6F8;
  overflow: hidden;
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
  padding: 16px 16px 0 16px;
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
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  padding: 12px 16px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  background-color: #ffffff;
  border-top: 1px solid #eeeeee;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.03);
  z-index: 10;
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
