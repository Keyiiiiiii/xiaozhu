<template>
  <view class="ticket-page">
    <!-- 角色标签 -->
    <view class="role-banner" v-if="currentRole !== 'gm'">
      <text class="role-icon">{{ currentRole === 'pm' ? '产' : '保' }}</text>
      <text class="role-text">{{ currentRole === 'pm' ? '产品经理视图' : '保障人视图' }}</text>
    </view>

    <!-- 状态筛选 -->
    <view class="filter-bar">
      <view
        v-for="tab in statusTabs"
        :key="tab.value"
        :class="['filter-tab', activeStatus === tab.value ? 'filter-tab-active' : '']"
        @click="switchStatus(tab.value)"
      >
        {{ tab.label }}
      </view>
    </view>

    <!-- 列表 -->
    <scroll-view class="ticket-list" scroll-y refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view
        v-for="t in tickets"
        :key="t.id"
        class="ticket-card"
        @click="goDetail(t.id)"
      >
        <view class="ticket-header">
          <text class="ticket-id">#{{ t.id }}</text>
          <text class="ticket-status" :style="{ color: statusMap[t.status].color }">
            {{ statusMap[t.status].text }}
          </text>
        </view>
        <text class="ticket-question">{{ t.question }}</text>
        <text v-if="t.manager_answer" class="ticket-answer-preview">
          经理答复：{{ truncate(t.manager_answer, 80) }}
        </text>
        <view class="ticket-meta">
          <text class="ticket-reporter">{{ t.reporter_name || t.reporter_work_id || '—' }}</text>
          <text class="ticket-time">{{ formatTime(t.created_at) }}</text>
        </view>
      </view>

      <view v-if="tickets.length === 0 && !loading" class="empty">
        <text>暂无工单</text>
      </view>
      <view v-if="loading" class="loading">
        <text>加载中...</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { listTickets, STATUS_MAP } from '@/api/ticket.js'

const tickets = ref([])
const loading = ref(false)
const refreshing = ref(false)
const activeStatus = ref('')
const statusMap = STATUS_MAP

const userInfo = uni.getStorageSync('userInfo') || {}
const currentRole = computed(() => {
  const r = (userInfo.role || '').trim()
  const map = { '客户经理': 'gm', '产品经理': 'pm', '保障人': 'guard', 'gm': 'gm', 'pm': 'pm', 'guard': 'guard' }
  return map[r] || 'gm'
})

const statusTabs = computed(() => {
  if (currentRole.value === 'gm') {
    return [
      { label: '全部', value: '' },
      { label: '待处理', value: 'pending' },
      { label: '已解决', value: 'resolved' },
      { label: '已闭环', value: 'closed' }
    ]
  }
  return [
    { label: '全部', value: '' },
    { label: '待处理', value: 'pending' },
    { label: '处理中', value: 'processing' },
    { label: '已解决', value: 'resolved' }
  ]
})

onMounted(() => loadList())

function loadList() {
  loading.value = true
  const params = {}
  if (activeStatus.value) params.status = activeStatus.value

  listTickets(params).then(res => {
    tickets.value = res.data || []
  }).catch(err => {
    uni.showToast({ title: err.message || '加载失败', icon: 'none' })
  }).finally(() => {
    loading.value = false
    refreshing.value = false
  })
}

function switchStatus(val) {
  if (activeStatus.value === val) return
  activeStatus.value = val
  loadList()
}

function onRefresh() {
  refreshing.value = true
  loadList()
}

function goDetail(id) {
  uni.navigateTo({ url: `/pages/ticket/detail?id=${id}` })
}

function truncate(str, n) {
  if (!str) return ''
  return str.length > n ? str.slice(0, n) + '...' : str
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  if (isToday) return `${hh}:${mm}`
  const mo = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${mo}-${dd} ${hh}:${mm}`
}
</script>

<style scoped>
.ticket-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #F5F6F8;
}
.role-banner {
  display: flex;
  align-items: center;
  background-color: #fff7e6;
  padding: 10px 16px;
}
.role-icon {
  width: 22px;
  height: 22px;
  background-color: #fa8c16;
  color: #fff;
  border-radius: 50%;
  font-size: 12px;
  text-align: center;
  line-height: 22px;
  margin-right: 8px;
}
.role-text {
  font-size: 13px;
  color: #fa8c16;
}
.filter-bar {
  display: flex;
  background-color: #ffffff;
  padding: 10px 12px;
  border-bottom: 1px solid #eeeeee;
  gap: 8px;
}
.filter-tab {
  padding: 6px 14px;
  font-size: 13px;
  color: #666666;
  border-radius: 16px;
  background-color: #f5f6f8;
}
.filter-tab-active {
  background: linear-gradient(135deg, #0085D0 0%, #006BB3 100%);
  color: #ffffff;
}
.ticket-list {
  flex: 1;
  padding: 12px;
}
.ticket-card {
  background-color: #ffffff;
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.ticket-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.ticket-id {
  font-size: 12px;
  color: #999999;
}
.ticket-status {
  font-size: 12px;
  font-weight: 500;
}
.ticket-question {
  font-size: 15px;
  color: #333333;
  line-height: 1.5;
  display: block;
  margin-bottom: 6px;
}
.ticket-answer-preview {
  font-size: 13px;
  color: #0085d0;
  background-color: #f0f7ff;
  padding: 8px 10px;
  border-radius: 6px;
  display: block;
  margin-bottom: 8px;
}
.ticket-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #bbbbbb;
}
.empty, .loading {
  text-align: center;
  padding: 40px;
  color: #999999;
  font-size: 14px;
}
</style>
