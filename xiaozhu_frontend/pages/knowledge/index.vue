<template>
  <view class="container">
    <scroll-view class="chat-list" scroll-y>
      <view class="chat-time">2026-06-02 09:12</view>

      <!-- AI 消息 -->
      <view class="msg-row ai-row">
        <view class="avatar ai-avatar">助</view>
        <view class="msg-box ai-msg">
          <text class="msg-text"
            >您好，我是榕小助。您可以向我询问最新的资费政策、营销方案等业务问题。</text
          >
        </view>
      </view>

      <!-- 用户 消息 -->
      <view class="msg-row user-row">
        <view class="msg-box user-msg">
          <text class="msg-text">目前企宽专线的最新优惠政策是什么？</text>
        </view>
        <view class="avatar user-avatar">我</view>
      </view>

      <!-- AI 复杂回复 -->
      <view class="msg-row ai-row">
        <view class="avatar ai-avatar">助</view>
        <view class="msg-box ai-msg">
          <text class="msg-text">根据2026年6月最新政策：</text>
          <view class="bullet-list">
            <text class="bullet-item">1. 企业宽带百兆新装享8折优惠；</text>
            <text class="bullet-item"
              >2. 专线客户叠加云主机业务，可免首月专线月租。</text
            >
          </view>
          <view class="msg-actions">
            <text class="action-link">查看源文件</text>
            <text class="action-divider">|</text>
            <text class="action-link">问题上报</text>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 底部输入栏 -->
    <view class="input-panel">
      <view class="voice-btn">语音</view>
      <input class="chat-input" placeholder="请输入业务问题..." />
      <view class="send-btn">发送</view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {};
  },
};
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  /* 增加 padding-top 适配状态栏，并给 padding-bottom 留出 tabbar 的高度 */
  padding-top: var(--status-bar-height);
  padding-bottom: 50px;
  box-sizing: border-box;
  background-color: #F5F6F8;
}
.chat-list {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
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
  border-radius: 2px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
  flex-shrink: 0;
}
.ai-avatar {
  background-color: #0085d0;
  color: #ffffff;
  margin-right: 12px;
}
.user-avatar {
  background-color: #cccccc;
  color: #ffffff;
  margin-left: 12px;
}
.msg-box {
  max-width: 70%;
  padding: 12px;
  border-radius: 2px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}
.ai-msg {
  background-color: #ffffff;
  border: 1px solid #eeeeee;
}
.user-msg {
  background-color: #e6f7ff;
  border: 1px solid #91d5ff;
}
.msg-text {
  font-size: 15px;
  color: #333333;
  line-height: 1.5;
}
.bullet-list {
  margin-top: 8px;
  background-color: #f9f9f9;
  padding: 8px;
  border-radius: 2px;
}
.bullet-item {
  font-size: 14px;
  color: #666666;
  display: block;
  margin-bottom: 4px;
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
}
.voice-btn {
  font-size: 14px;
  color: #666666;
  border: 1px solid #dddddd;
  padding: 6px 12px;
  border-radius: 2px;
  margin-right: 12px;
}
.chat-input {
  flex: 1;
  height: 36px;
  background-color: #f5f6f8;
  border-radius: 2px;
  padding: 0 12px;
  font-size: 14px;
  border: 1px solid #eeeeee;
}
.send-btn {
  margin-left: 12px;
  height: 36px;
  line-height: 36px;
  background-color: #0085d0;
  color: #ffffff;
  font-size: 14px;
  padding: 0 16px;
  border-radius: 2px;
}
</style>