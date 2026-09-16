<template>
  <view class="detail-page">
    <scroll-view class="detail-scroll" scroll-y>
      <!-- 工单头部 -->
      <view class="section">
        <view class="section-head">
          <text class="section-title">工单 #{{ ticket.id }}</text>
          <text class="status-tag" :style="{ background: statusColor }">{{ statusText }}</text>
        </view>
        <text class="meta-line">
          上报人：{{ ticket.reporter_name || ticket.reporter_work_id || '—' }}
          ｜ {{ formatTime(ticket.created_at) }}
        </text>
      </view>

      <!-- 用户问题 -->
      <view class="section">
        <text class="section-title">用户问题</text>
        <view class="content-box">
          <text class="content-text">{{ ticket.question || '—' }}</text>
        </view>
      </view>

      <!-- 智能体回答 -->
      <view class="section" v-if="ticket.agent_answer">
        <text class="section-title">智能体回答</text>
        <view class="content-box content-box-ai">
          <text class="content-text">{{ ticket.agent_answer }}</text>
        </view>
      </view>

      <!-- 用户补充 -->
      <view class="section" v-if="ticket.reason">
        <text class="section-title">没解决的原因</text>
        <view class="content-box content-box-reason">
          <text class="content-text">{{ ticket.reason }}</text>
        </view>
      </view>

      <!-- 经理解答 -->
      <view class="section" v-if="ticket.manager_answer || isManager">
        <text class="section-title">产品经理解答</text>
        <view v-if="!isManager && ticket.manager_answer" class="content-box content-box-pm">
          <text class="content-text">{{ ticket.manager_answer }}</text>
          <text class="content-meta">— {{ ticket.handler_name || '产品经理' }}  {{ formatTime(ticket.resolved_at) }}</text>
        </view>
        <view v-if="isManager" class="pm-editor">
          <textarea
            class="pm-textarea"
            v-model="answerText"
            placeholder="请填写正式答复..."
            maxlength="2000"
          />
          <textarea
            class="pm-textarea pm-textarea-note"
            v-model="noteText"
            placeholder="内部备注（不对用户可见，可选）"
            maxlength="500"
          />
          <view class="pm-actions">
            <view class="pm-btn pm-btn-submit" @click="saveAnswer" :class="{ disabled: submitting }">
              {{ submitting ? '保存中...' : '保存解答' }}
            </view>
          </view>
        </view>
      </view>

      <!-- 关联知识库（经理闭环） -->
      <view class="section" v-if="isManager">
        <text class="section-title">关联知识库条目</text>
        <view v-if="!ticket.related_file_id" class="kb-picker">
          <picker mode="selector" :range="kbOptions" range-key="file_name" @change="onKbSelect">
            <view class="kb-picker-btn">
              <text>{{ selectedKbName || '选择知识库文件（可选）' }}</text>
              <text class="kb-arrow">▾</text>
            </view>
          </picker>
          <view class="pm-btn pm-btn-close" @click="closeTicket" :class="{ disabled: !canClose || submitting }">
            {{ submitting ? '闭环中...' : '闭环工单' }}
          </view>
        </view>
        <view v-else class="linked-kb">
          <text class="kb-icon">📎</text>
          <view class="kb-info">
            <text class="kb-name">{{ ticket.related_file_name }}</text>
            <text class="kb-time">闭环于 {{ formatTime(ticket.closed_at) }}</text>
          </view>
        </view>
      </view>

      <!-- 关联知识库（客户经理查看） -->
      <view class="section" v-if="!isManager && ticket.related_file_name">
        <text class="section-title">已关联知识库</text>
        <view class="linked-kb">
          <text class="kb-icon">📎</text>
          <view class="kb-info">
            <text class="kb-name">{{ ticket.related_file_name }}</text>
          </view>
        </view>
      </view>

      <!-- 经理内部备注（仅经理/保障人可见） -->
      <view class="section" v-if="isManager && ticket.manager_note">
        <text class="section-title">内部备注</text>
        <view class="content-box content-box-note">
          <text class="content-text">{{ ticket.manager_note }}</text>
        </view>
      </view>

      <view style="height: 40px;"></view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getTicketDetail, answerTicket, closeTicket, STATUS_MAP } from '@/api/ticket.js'
import { KnowledgeFile } from '@/api/knowledge.js'

const ticket = ref({})
const answerText = ref('')
const noteText = ref('')
const submitting = ref(false)
const kbOptions = ref([])
const selectedKbId = ref(null)
const selectedKbName = ref('')

const pages = getCurrentPages()
const currentPage = pages[pages.length - 1]
const ticketId = currentPage.options?.id || 1

const userInfo = uni.getStorageSync('userInfo') || {}
const currentRole = computed(() => {
  const r = (userInfo.role || '').trim()
  const map = { '客户经理': 'gm', '产品经理': 'pm', '保障人': 'guard', 'gm': 'gm', 'pm': 'pm', 'guard': 'guard' }
  return map[r] || 'gm'
})
const isManager = computed(() => currentRole.value === 'pm' || currentRole.value === 'guard')
const statusText = computed(() => ticket.value.status ? STATUS_MAP[ticket.value.status]?.text || ticket.value.status : '')
const statusColor = computed(() => ticket.value.status ? STATUS_MAP[ticket.value.status]?.color || '#999' : '#999')
const canClose = computed(() => !!ticket.value.manager_answer)

onMounted(() => {
  loadDetail()
  if (isManager.value) loadKbOptions()
})

function loadDetail() {
  getTicketDetail(ticketId).then(res => {
    ticket.value = res.data || {}
    answerText.value = ticket.value.manager_answer || ''
    noteText.value = ticket.value.manager_note || ''
  }).catch(err => {
    uni.showToast({ title: err.message || '加载失败', icon: 'none' })
  })
}

async function loadKbOptions() {
  try {
    // 复用现有知识库文件列表（从 Django 接口取）
    const resp = await new Promise((resolve, reject) => {
      const token = uni.getStorageSync('token')
      uni.request({
        url: '/api/knowledge/upload/',
        method: 'GET',
        header: token ? { Authorization: `Bearer ${token}` } : {},
        success: (r) => resolve(r.data),
        fail: reject
      })
    })
    kbOptions.value = resp.data || []
  } catch (e) {
    kbOptions.value = []
  }
}

function onKbSelect(e) {
  const idx = e.detail.value
  const item = kbOptions.value[idx]
  if (item) {
    selectedKbId.value = item.id
    selectedKbName.value = item.file_name + (item.file_type ? '.' + item.file_type : '')
  }
}

function saveAnswer() {
  if (submitting.value) return
  if (!answerText.value.trim()) {
    uni.showToast({ title: '请填写解答内容', icon: 'none' })
    return
  }
  submitting.value = true
  answerTicket(ticketId, {
    manager_answer: answerText.value.trim(),
    manager_note: noteText.value.trim()
  }).then(() => {
    uni.showToast({ title: '解答已保存', icon: 'success' })
    loadDetail()
  }).catch(err => {
    uni.showToast({ title: err.message || '保存失败', icon: 'none' })
  }).finally(() => {
    submitting.value = false
  })
}

function closeTicket() {
  if (submitting.value) return
  const payload = {}
  if (selectedKbId.value) payload.related_file_id = selectedKbId.value

  uni.showModal({
    title: '确认闭环',
    content: payload.related_file_id ? `将关联知识库文件"${selectedKbName.value}"？闭环后不可撤销。` : '闭环后不可撤销，确定继续？',
    confirmColor: '#0085D0',
    success: (r) => {
      if (!r.confirm) return
      submitting.value = true
      closeTicket(ticketId, payload).then(() => {
        uni.showToast({ title: '已闭环', icon: 'success' })
        loadDetail()
      }).catch(err => {
        uni.showToast({ title: err.message || '闭环失败', icon: 'none' })
      }).finally(() => {
        submitting.value = false
      })
    }
  })
}

function formatTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  const y = d.getFullYear()
  const mo = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${mo}-${dd} ${hh}:${mm}`
}
</script>

<style scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #F5F6F8;
}
.detail-scroll {
  flex: 1;
}
.section {
  background-color: #ffffff;
  margin: 12px;
  padding: 14px 16px;
  border-radius: 10px;
}
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.section-title {
  font-size: 13px;
  color: #999999;
  display: block;
  margin-bottom: 8px;
}
.status-tag {
  font-size: 12px;
  color: #ffffff;
  padding: 2px 10px;
  border-radius: 10px;
}
.meta-line {
  font-size: 12px;
  color: #bbbbbb;
}
.content-box {
  background-color: #f5f6f8;
  padding: 12px;
  border-radius: 8px;
}
.content-box-ai {
  background-color: #fff7e6;
}
.content-box-reason {
  background-color: #fff1f0;
}
.content-box-pm {
  background-color: #f0f7ff;
}
.content-box-note {
  background-color: #f6ffed;
}
.content-text {
  font-size: 14px;
  color: #333333;
  line-height: 1.6;
  word-break: break-all;
}
.content-meta {
  display: block;
  font-size: 12px;
  color: #999999;
  margin-top: 8px;
}
/* 经理编辑器 */
.pm-editor {
  margin-top: 8px;
}
.pm-textarea {
  width: 100%;
  min-height: 100px;
  background-color: #f0f7ff;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
  margin-bottom: 10px;
}
.pm-textarea-note {
  min-height: 60px;
  background-color: #f6ffed;
}
.pm-actions {
  display: flex;
  justify-content: flex-end;
}
.pm-btn {
  padding: 8px 20px;
  border-radius: 16px;
  font-size: 14px;
  text-align: center;
}
.pm-btn-submit {
  background: linear-gradient(135deg, #0085D0 0%, #006BB3 100%);
  color: #ffffff;
}
.pm-btn-close {
  background-color: #52c41a;
  color: #ffffff;
  margin-top: 10px;
  width: 100%;
}
.pm-btn.disabled {
  opacity: 0.5;
}
/* 知识库选择 */
.kb-picker-btn {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f5f6f8;
  padding: 12px 14px;
  border-radius: 8px;
  font-size: 14px;
  color: #333333;
  margin-bottom: 10px;
}
.kb-arrow {
  color: #999999;
}
.linked-kb {
  display: flex;
  align-items: center;
  background-color: #f6ffed;
  padding: 12px 14px;
  border-radius: 8px;
}
.kb-icon {
  font-size: 20px;
  margin-right: 10px;
}
.kb-info {
  flex: 1;
}
.kb-name {
  font-size: 14px;
  color: #333333;
  display: block;
}
.kb-time {
  font-size: 12px;
  color: #999999;
  margin-top: 4px;
  display: block;
}
</style>
