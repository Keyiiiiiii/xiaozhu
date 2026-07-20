<template>
  <view class="login-container">
    <view class="login-header">
      <view class="logo-area">
        <view class="logo-icon">榕</view>
        <text class="app-name">榕小助</text>
        <text class="app-slogan">走访神器 · 高效办公</text>
      </view>
    </view>

    <view class="login-form">
      <view class="form-title">账号登录</view>

      <view class="form-item">
        <view class="input-wrapper">
          <text class="input-icon">账</text>
          <input
            class="form-input"
            type="text"
            v-model="username"
            placeholder="请输入账号"
            placeholder-class="input-placeholder"
            @confirm="handleLogin"
          />
        </view>
      </view>

      <view class="form-item">
        <view class="input-wrapper">
          <text class="input-icon">密</text>
          <input
            class="form-input"
            :type="passwordVisible ? 'text' : 'password'"
            v-model="password"
            placeholder="请输入密码"
            placeholder-class="input-placeholder"
            @confirm="handleLogin"
          />
          <text class="eye-icon" @click="togglePassword">
            {{ passwordVisible ? '隐' : '显' }}
          </text>
        </view>
      </view>

      <view class="form-tips">
        <text class="error-msg" v-if="errorMsg">{{ errorMsg }}</text>
      </view>

      <view class="login-btn" :class="{ 'btn-loading': loading }" @click="handleLogin">
        <text v-if="!loading">登 录</text>
        <text v-else>登录中...</text>
      </view>

      <view class="login-footer">
        <text class="footer-text">测试账号：admin / 123456</text>
      </view>
    </view>
  </view>
</template>

<script>
import loginApi from '@/api/login.js';
import { mapMutations } from 'vuex';

export default {
  data() {
    return {
      username: '',
      password: '',
      passwordVisible: false,
      loading: false,
      errorMsg: ''
    };
  },
  onLoad() {
    const token = uni.getStorageSync('token');
    if (token) {
      this.goToHome();
    }
  },
  methods: {
    ...mapMutations(['login', 'logout', 'setUserInfo']),

    togglePassword() {
      this.passwordVisible = !this.passwordVisible;
    },

    handleLogin() {
      if (this.loading) return;

      this.errorMsg = '';

      if (!this.username.trim()) {
        this.errorMsg = '请输入账号';
        return;
      }
      if (!this.password.trim()) {
        this.errorMsg = '请输入密码';
        return;
      }

      this.loading = true;

      loginApi.login(this.username.trim(), this.password.trim())
        .then((res) => {
          uni.setStorageSync('token', res.token);
          uni.setStorageSync('userInfo', res.userInfo);
          this.setUserInfo(res.userInfo);
          this.login('password');
          this.goToHome();
        })
        .catch((err) => {
          this.errorMsg = err.message || '登录失败，请重试';
        })
        .finally(() => {
          this.loading = false;
        });
    },

    goToHome() {
      uni.switchTab({
        url: '/pages/workbench/index'
      });
    }
  }
};
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background: linear-gradient(180deg, #0085D0 0%, #006BB3 40%, #F5F6F8 40%, #F5F6F8 100%);
  display: flex;
  flex-direction: column;
}

.login-header {
  flex: 0 0 auto;
  padding-top: calc(80px + var(--status-bar-height));
  padding-bottom: 60px;
  display: flex;
  justify-content: center;
}

.logo-area {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.logo-icon {
  width: 80px;
  height: 80px;
  background-color: #ffffff;
  color: #0085D0;
  font-size: 36px;
  font-weight: bold;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 16px;
  margin-bottom: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.app-name {
  font-size: 28px;
  color: #ffffff;
  font-weight: bold;
  letter-spacing: 2px;
  margin-bottom: 8px;
}

.app-slogan {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
}

.login-form {
  flex: 1;
  margin: 0 24px;
  background-color: #ffffff;
  border-radius: 12px;
  padding: 32px 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.form-title {
  font-size: 20px;
  font-weight: 600;
  color: #222222;
  margin-bottom: 28px;
  text-align: center;
}

.form-item {
  margin-bottom: 20px;
}

.input-wrapper {
  display: flex;
  align-items: center;
  background-color: #F7F8FA;
  border-radius: 8px;
  padding: 0 16px;
  height: 48px;
  border: 1px solid transparent;
  transition: border-color 0.2s;
}

.input-wrapper:focus-within {
  border-color: #0085D0;
  background-color: #ffffff;
}

.input-icon {
  width: 28px;
  height: 28px;
  background-color: #E6F4FF;
  color: #0085D0;
  font-size: 14px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 6px;
  margin-right: 12px;
  flex-shrink: 0;
}

.form-input {
  flex: 1;
  height: 48px;
  font-size: 15px;
  color: #333333;
}

.input-placeholder {
  color: #AAAAAA;
  font-size: 15px;
}

.eye-icon {
  font-size: 13px;
  color: #999999;
  padding: 4px 8px;
  margin-left: 8px;
}

.form-tips {
  height: 20px;
  margin-bottom: 8px;
}

.error-msg {
  font-size: 12px;
  color: #F5222D;
}

.login-btn {
  width: 100%;
  height: 48px;
  background: linear-gradient(135deg, #0085D0 0%, #006BB3 100%);
  color: #ffffff;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 8px;
  letter-spacing: 2px;
}

.login-btn.btn-loading {
  opacity: 0.7;
}

.login-footer {
  margin-top: 20px;
  text-align: center;
}

.footer-text {
  font-size: 12px;
  color: #BBBBBB;
}
</style>
