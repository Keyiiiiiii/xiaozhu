<template>
  <view class="container">
    <view class="navbar">
      <text class="navbar-title">知识库</text>
    </view>
    
    <scroll-view 
      class="chat-list" 
      scroll-y 
      :scroll-top="scrollTop"
      :scroll-with-animation="true"
      :style="{ height: chatListHeight + 'px' }"
      :scroll-into-view="scrollToId"
    >
      <view 
        v-for="(msg, index) in messages" 
        :key="index"
        :id="'msg-' + index"
      >
        <view v-if="shouldShowTime(index)" class="chat-time">
          {{ formatMsgTime(msg.timestamp) }}
        </view>
        
        <view :class="['msg-row', msg.role === 'ai' ? 'ai-row' : 'user-row']">
          <view v-if="msg.role === 'ai'" class="avatar ai-avatar">助</view>
          <view :class="['msg-box', msg.role === 'ai' ? 'ai-msg' : 'user-msg']">
            <text class="msg-text">{{ msg.content }}</text>
            <view v-if="msg.role === 'ai' && msg.showActions" class="msg-actions">
              <text class="action-link">查看源文件</text>
              <text class="action-divider">|</text>
              <text class="action-link">问题上报</text>
            </view>
          </view>
          <view v-if="msg.role === 'user'" class="avatar user-avatar">我</view>
        </view>
      </view>

      <view v-if="loading" id="loading-row" class="msg-row ai-row">
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
      <view class="voice-btn">🎤</view>
      <input 
        class="chat-input" 
        placeholder="请输入业务问题..." 
        v-model="inputText"
        @confirm="onSend"
        @focus="onInputFocus"
        :adjust-position="false"
      />
      <view 
        :class="['send-btn', inputText.trim() ? '' : 'send-btn-disabled']"
        @click="onSend"
      >发送</view>
    </view>
  </view>
</template>

<script>
import { sendKnowledgeQuery } from '@/api/knowledge.js';

export default {
  data() {
    return {
      messages: [
        {
          role: 'ai',
          content: '您好，我是榕小助。您可以向我询问最新的资费政策、营销方案等业务问题。',
          showActions: false,
          timestamp: Date.now()
        }
      ],
      inputText: '',
      scrollTop: 0,
      scrollToId: '',
      loading: false,
      chatListHeight: 0,
      windowHeight: 0,
      keyboardHeight: 0,
      navbarHeight: 44,
      inputPanelHeight: 52,
      scrollTimer: null
    };
  },
  
  onLoad() {
    this.initChatHeight();
    setTimeout(() => {
      this.scrollToBottom();
    }, 500);
  },
  
  onShow() {
    this.initChatHeight();
    setTimeout(() => {
      this.scrollToBottom();
    }, 300);
  },
  
  onUnload() {
    uni.offKeyboardHeightChange(this.onKeyboardHeightChange);
    if (this.scrollTimer) {
      clearTimeout(this.scrollTimer);
    }
  },
  
  watch: {
    messages() {
      this.$nextTick(() => {
        setTimeout(() => {
          this.scrollToBottom();
        }, 100);
      });
    }
  },
  
  methods: {
    initChatHeight() {
      const systemInfo = uni.getSystemInfoSync();
      this.windowHeight = systemInfo.windowHeight;
      const statusBarHeight = systemInfo.statusBarHeight || 0;
      this.chatListHeight = this.windowHeight - statusBarHeight - this.navbarHeight - this.inputPanelHeight;
      
      uni.onKeyboardHeightChange(this.onKeyboardHeightChange);
    },
    
    onKeyboardHeightChange(e) {
      const systemInfo = uni.getSystemInfoSync();
      const statusBarHeight = systemInfo.statusBarHeight || 0;
      this.keyboardHeight = e.height;
      
      if (e.height > 0) {
        this.chatListHeight = this.windowHeight - statusBarHeight - this.navbarHeight - this.inputPanelHeight - e.height;
        this.safeScrollToBottom();
      } else {
        this.chatListHeight = this.windowHeight - statusBarHeight - this.navbarHeight - this.inputPanelHeight;
        this.safeScrollToBottom();
      }
    },
    
    safeScrollToBottom() {
      if (this.scrollTimer) {
        clearTimeout(this.scrollTimer);
      }
      this.scrollTimer = setTimeout(() => {
        this.scrollToBottom();
      }, 300);
    },
    
    onInputFocus() {
      this.safeScrollToBottom();
    },
    
    scrollToBottom() {
      this.scrollToId = 'scroll-bottom-anchor';
      setTimeout(() => {
        this.scrollToId = '';
      }, 300);
    },
    
    shouldShowTime(index) {
      if (index === 0) return true;
      
      const currentTime = this.messages[index].timestamp;
      const prevTime = this.messages[index - 1].timestamp;
      
      const diffMinutes = (currentTime - prevTime) / 1000 / 60;
      
      if (diffMinutes >= 5) return true;
      
      const currentDate = new Date(currentTime).toDateString();
      const prevDate = new Date(prevTime).toDateString();
      
      return currentDate !== prevDate;
    },
    
    formatMsgTime(timestamp) {
      const date = new Date(timestamp);
      const now = new Date();
      
      const todayStr = now.toDateString();
      const msgDateStr = date.toDateString();
      
      if (todayStr === msgDateStr) {
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${hours}:${minutes}`;
      } else {
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${month}-${day} ${hours}:${minutes}`;
      }
    },
    
    onSend() {
      const text = this.inputText.trim();
      if (!text || this.loading) return;
      
      this.inputText = '';
      this.loading = true;
      
      this.messages.push({
        role: 'user',
        content: text,
        showActions: false,
        timestamp: Date.now()
      });
      
      this.$nextTick(() => {
        this.safeScrollToBottom();
      });
      
      sendKnowledgeQuery(text)
        .then((res) => {
          this.loading = false;
          let replyContent = '抱歉，我暂时无法回答这个问题。';
          
          if (res && typeof res === 'object') {
            if (res.content) {
              replyContent = res.content;
            } else if (res.data && res.data.content) {
              replyContent = res.data.content;
            } else if (res.msg) {
              replyContent = res.msg;
            } else {
              replyContent = JSON.stringify(res);
            }
          } else if (typeof res === 'string') {
            replyContent = res;
          }
          
          this.messages.push({
            role: 'ai',
            content: replyContent,
            showActions: true,
            timestamp: Date.now()
          });
          
          this.$nextTick(() => {
            this.safeScrollToBottom();
          });
        })
        .catch((err) => {
          this.loading = false;
          console.error('发送消息失败:', err);
          this.messages.push({
            role: 'ai',
            content: '网络连接失败，请稍后重试。',
            showActions: false,
            timestamp: Date.now()
          });
          
          this.$nextTick(() => {
            this.safeScrollToBottom();
          });
        });
    }
  }
};
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
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
  padding: 16px;
  overflow-y: auto;
  box-sizing: border-box;
}
.scroll-bottom-anchor {
  height: 0px;
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
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  background-color: #ffffff;
  border-top: 1px solid #eeeeee;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.03);
}
.voice-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: #f5f6f8;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: 12px;
  font-size: 18px;
}
.chat-input {
  flex: 1;
  height: 36px;
  background-color: #f5f6f8;
  border-radius: 18px;
  padding: 0 16px;
  font-size: 14px;
  border: none;
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
</style>