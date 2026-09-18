<template>
  <view class="container">
    <view class="form-card">
      <view class="form-item">
        <text class="form-label">通知标题<text class="req">*</text></text>
        <input
          class="form-input"
          v-model="form.title"
          placeholder="请输入标题（最多60字）"
          maxlength="60"
        />
      </view>

      <view class="form-item">
        <text class="form-label">来源<text class="req">*</text></text>
        <view class="tag-picker">
          <view
            v-for="opt in sourceOptions"
            :key="opt.value"
            class="tag-option"
            :class="{ active: form.source === opt.value, disabled: opt.disabled }"
            @click="selectSource(opt)"
          >
            <text class="tag-option-text">{{ opt.label }}</text>
          </view>
        </view>
        <text class="form-hint" v-if="role === 'district'">区县专项仅可下发本区县来源通知</text>
      </view>

      <view class="form-item">
        <text class="form-label">紧急程度<text class="req">*</text></text>
        <view class="tag-picker">
          <view
            v-for="opt in urgencyOptions"
            :key="opt.value"
            class="tag-option"
            :class="{ active: form.urgency === opt.value }"
            @click="form.urgency = opt.value"
          >
            <text class="tag-option-text">{{ opt.label }}</text>
          </view>
        </view>
        <text class="form-hint">紧急通知用户开屏需倒计时 10 秒，重要通知倒计时 3 秒</text>
      </view>

      <view class="form-item">
        <text class="form-label">下发对象<text class="req">*</text></text>
        <view class="tag-picker">
          <view
            v-for="opt in audienceOptions"
            :key="opt.value"
            class="tag-option"
            :class="{ active: form.audience === opt.value, disabled: opt.disabled }"
            @click="selectAudience(opt)"
          >
            <text class="tag-option-text">{{ opt.label }}</text>
          </view>
        </view>
        <text class="form-hint" v-if="role === 'district'">区县专项仅可下发至本区县一线</text>
      </view>

      <view class="form-item">
        <view class="switch-row">
          <view class="switch-label">
            <text class="form-label">开屏强制展示</text>
            <text class="switch-desc">勾选后用户登录或切回前台时必须确认</text>
          </view>
          <switch :checked="form.force_display" @change="onForceChange" color="#0085D0" />
        </view>
      </view>

      <view class="form-item">
        <text class="form-label">通知正文<text class="req">*</text></text>
        <textarea
          class="form-textarea"
          v-model="form.content"
          placeholder="请输入通知正文（支持纯文本，将原样展示）"
          maxlength="-1"
          auto-height
        />
      </view>
    </view>

    <view class="submit-btn" :class="{ 'btn-disabled': submitting }" @click="handleSubmit">
      <text class="submit-text">{{ submitting ? '提交中...' : '下发通知' }}</text>
    </view>
  </view>
</template>

<script>
import notificationApi from '@/api/notification.js';
import { mapState } from 'vuex';

export default {
  data() {
    return {
      role: '',
      form: {
        title: '',
        source: 'city',
        urgency: 'important',
        audience: 'frontline',
        force_display: false,
        content: ''
      },
      submitting: false
    };
  },
  computed: {
    ...mapState(['userInfo']),
    sourceOptions() {
      // city 可选市级 / 区县；district 仅可选本区县
      if (this.role === 'city') {
        return [
          { value: 'city', label: '市级' },
          { value: 'district', label: '区县' }
        ];
      }
      if (this.role === 'district') {
        return [
          { value: 'district', label: '本区县', disabled: false },
          { value: 'city', label: '市级', disabled: true }
        ];
      }
      return [];
    },
    urgencyOptions() {
      return [
        { value: 'important', label: '重要' },
        { value: 'urgent', label: '紧急' }
      ];
    },
    audienceOptions() {
      // city 可下发至一线 / 区县 / 全部；district 仅可下发至本区县一线
      if (this.role === 'city') {
        return [
          { value: 'frontline', label: '一线人员' },
          { value: 'district', label: '区县专项' },
          { value: 'all', label: '全部人员' }
        ];
      }
      if (this.role === 'district') {
        return [
          { value: 'frontline', label: '本区县一线', disabled: false },
          { value: 'district', label: '区县专项', disabled: true },
          { value: 'all', label: '全部人员', disabled: true }
        ];
      }
      return [];
    }
  },
  onLoad() {
    const role = this.userInfo && this.userInfo.role;
    this.role = role || '';
    if (this.role !== 'city' && this.role !== 'district') {
      uni.showToast({ title: '无权下发通知', icon: 'none' });
      setTimeout(() => uni.navigateBack(), 800);
      return;
    }
    // 区县角色默认来源为 district
    if (this.role === 'district') {
      this.form.source = 'district';
      this.form.audience = 'frontline';
    }
  },
  methods: {
    onForceChange(e) {
      this.form.force_display = e.detail.value;
    },
    selectSource(opt) {
      if (opt.disabled) return;
      this.form.source = opt.value;
    },
    selectAudience(opt) {
      if (opt.disabled) return;
      this.form.audience = opt.value;
    },
    handleSubmit() {
      if (this.submitting) return;

      const { title, content, source, urgency, audience, force_display } = this.form;
      if (!title.trim()) {
        uni.showToast({ title: '请输入标题', icon: 'none' });
        return;
      }
      if (!source) {
        uni.showToast({ title: '请选择来源', icon: 'none' });
        return;
      }
      if (!urgency) {
        uni.showToast({ title: '请选择紧急程度', icon: 'none' });
        return;
      }
      if (!audience) {
        uni.showToast({ title: '请选择下发对象', icon: 'none' });
        return;
      }
      if (!content.trim()) {
        uni.showToast({ title: '请输入正文', icon: 'none' });
        return;
      }

      this.submitting = true;
      notificationApi.publish({
        title: title.trim(),
        content: content.trim(),
        source,
        urgency,
        // 兼容旧字段：tag = source
        tag: source,
        audience,
        force_display: !!force_display
      })
        .then(() => {
          uni.showToast({ title: '下发成功', icon: 'success' });
          setTimeout(() => {
            uni.redirectTo({ url: '/pages/notification/list' });
          }, 600);
        })
        .catch((err) => {
          uni.showToast({ title: err.message || '下发失败', icon: 'none' });
        })
        .finally(() => {
          this.submitting = false;
        });
    }
  }
};
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #F4F6F9;
  padding: 16px 16px 40px;
}
.form-card {
  background-color: #FFFFFF;
  border-radius: 8px;
  padding: 8px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}
.form-item {
  padding: 14px 0;
  border-bottom: 1px solid #F5F5F5;
}
.form-item:last-child {
  border-bottom: none;
}
.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333333;
  margin-bottom: 10px;
}
.req {
  color: #F5222D;
  margin-left: 2px;
}
.form-input {
  height: 44px;
  background-color: #F7F8FA;
  border-radius: 6px;
  padding: 0 12px;
  font-size: 15px;
  color: #333333;
}
.form-textarea {
  width: 100%;
  min-height: 160px;
  background-color: #F7F8FA;
  border-radius: 6px;
  padding: 12px;
  font-size: 15px;
  color: #333333;
  line-height: 1.6;
  box-sizing: border-box;
}
.tag-picker {
  display: flex;
  flex-wrap: wrap;
}
.tag-option {
  padding: 8px 14px;
  background-color: #F5F5F5;
  border-radius: 4px;
  margin-right: 10px;
  margin-bottom: 8px;
  border: 1px solid transparent;
}
.tag-option.active {
  background-color: #E6F4FF;
  border-color: #0085D0;
}
.tag-option.disabled {
  opacity: 0.4;
}
.tag-option-text {
  font-size: 13px;
  color: #666666;
}
.tag-option.active .tag-option-text {
  color: #0085D0;
  font-weight: 500;
}
.form-hint {
  display: block;
  font-size: 12px;
  color: #AAAAAA;
  margin-top: 4px;
}
.switch-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.switch-label {
  display: flex;
  flex-direction: column;
}
.switch-label .form-label {
  margin-bottom: 4px;
}
.switch-desc {
  font-size: 12px;
  color: #AAAAAA;
}
.submit-btn {
  margin-top: 24px;
  height: 46px;
  background: linear-gradient(135deg, #0085D0 0%, #006BB3 100%);
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
}
.submit-btn.btn-disabled {
  opacity: 0.6;
}
.submit-text {
  color: #ffffff;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 2px;
}
</style>
