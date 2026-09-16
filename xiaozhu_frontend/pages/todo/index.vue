<template>
  <view class="container">
    <view class="tab-header">
      <view
        class="tab-item"
        :class="{ active: currentTab === 0 }"
        @click="switchTab(0)"
      >
        <text class="tab-text">未办 ({{ countByStatus.pending }})</text>
      </view>
      <view
        class="tab-item"
        :class="{ active: currentTab === 1 }"
        @click="switchTab(1)"
      >
        <text class="tab-text">进行中 ({{ countByStatus.doing }})</text>
      </view>
      <view
        class="tab-item"
        :class="{ active: currentTab === 2 }"
        @click="switchTab(2)"
      >
        <text class="tab-text">已闭环 ({{ countByStatus.done }})</text>
      </view>
    </view>

    <view class="todo-list" v-if="currentList.length > 0">
      <view
        class="swipe-card"
        v-for="item in currentList"
        :key="item.id"
      >
        <view class="swipe-delete-btn" @click="confirmDelete(item)">
          <text class="swipe-delete-text">删除</text>
        </view>
        <view
          class="swipe-content"
          :style="{ transform: `translateX(${swipeOffsets[item.id] || 0}px)` }"
          @touchstart="onTouchStart($event, item.id)"
          @touchmove="onTouchMove($event, item.id)"
          @touchend="onTouchEnd($event, item.id)"
        >
          <view class="todo-card">
            <view class="todo-head">
              <view class="todo-tags">
                <text class="tag" :class="item.priority === 'high' ? 'tag-high' : 'tag-normal'">
                  {{ item.priority === 'high' ? '高优' : '常规' }}
                </text>
                <text class="tag tag-source">
                  {{ item.source === 'ai' ? 'AI提取' : '手动创建' }}
                </text>
              </view>
              <text class="todo-deadline" v-if="item.deadline">截止: {{ item.deadline }}</text>
            </view>
            <view class="todo-title">{{ item.title }}</view>
            <view class="todo-foot">
              <text class="todo-meta">
                来源：{{ item.sourceText || (item.source === 'ai' ? 'AI走访提取' : '手动创建') }}
              </text>
              <view
                v-if="item.status === 'pending'"
                class="todo-btn"
                @click.stop="handleStart(item)"
              >
                开始办理
              </view>
              <view
                v-else-if="item.status === 'doing'"
                class="todo-btn todo-btn-done"
                @click.stop="handleComplete(item)"
              >
                完成闭环
              </view>
              <view
                v-else
                class="todo-btn todo-btn-disabled"
              >
                已闭环
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 空状态 -->
    <view class="todo-list" v-else>
      <view class="empty-state">
        <text class="empty-text">{{ emptyText }}</text>
      </view>
    </view>

    <!-- 底部悬浮按钮 -->
    <view class="fab-wrapper">
      <view class="fab-btn" @click="openCreateModal">新增待办</view>
    </view>

    <!-- 新增待办弹窗 -->
    <view class="modal-mask" v-if="showCreateModal" @click="closeCreateModal">
      <view class="modal-content" @click.stop>
        <view class="modal-header">
          <text class="modal-title">新增待办</text>
        </view>
        <view class="modal-body">
          <view class="form-row">
            <text class="form-label">事项标题</text>
            <input
              class="form-input"
              v-model="form.title"
              placeholder="请输入待办事项"
              :maxlength="100"
              focus
            />
          </view>
          <view class="form-row">
            <text class="form-label">截止日期</text>
            <picker mode="date" :value="form.deadlineDate" @change="onDateChange">
              <view class="form-picker">{{ form.deadlineDate || '请选择日期' }}</view>
            </picker>
          </view>
          <view class="form-row">
            <text class="form-label">截止时间</text>
            <picker mode="time" :value="form.deadlineTime" @change="onTimeChange">
              <view class="form-picker">{{ form.deadlineTime || '请选择时间' }}</view>
            </picker>
          </view>
          <view class="form-row">
            <text class="form-label">优先级</text>
            <view class="priority-group">
              <view
                class="priority-option"
                :class="{ 'priority-active': form.priority === 'high' }"
                @click="form.priority = 'high'"
              >
                <text>高优</text>
              </view>
              <view
                class="priority-option"
                :class="{ 'priority-active': form.priority === 'normal' }"
                @click="form.priority = 'normal'"
              >
                <text>常规</text>
              </view>
            </view>
          </view>
        </view>
        <view class="modal-footer">
          <view class="modal-btn modal-btn-cancel" @click="closeCreateModal">
            <text class="modal-btn-text">取消</text>
          </view>
          <view class="modal-btn modal-btn-confirm" @click="handleCreate">
            <text class="modal-btn-text">确定</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import {
  getTodoList,
  addTodo,
  updateTodoStatus,
  deleteTodo,
  seedTodoListIfEmpty,
  TODO_STATUS
} from '@/api/todo.js';

export default {
  data() {
    return {
      currentTab: 0,
      todoList: [],
      swipeOffsets: {},
      touchStartX: {},
      touchStartY: {},
      showCreateModal: false,
      form: {
        title: '',
        deadlineDate: '',
        deadlineTime: '',
        priority: 'normal'
      }
    };
  },
  computed: {
    countByStatus() {
      return {
        pending: this.todoList.filter(i => i.status === TODO_STATUS.PENDING).length,
        doing: this.todoList.filter(i => i.status === TODO_STATUS.DOING).length,
        done: this.todoList.filter(i => i.status === TODO_STATUS.DONE).length
      };
    },
    currentList() {
      const statusMap = [TODO_STATUS.PENDING, TODO_STATUS.DOING, TODO_STATUS.DONE];
      const target = statusMap[this.currentTab];
      return this.todoList
        .filter(i => i.status === target)
        .slice()
        .sort((a, b) => (b.createTime || 0) - (a.createTime || 0));
    },
    emptyText() {
      if (this.currentTab === 0) return '暂未有待办事项';
      if (this.currentTab === 1) return '暂无进行中的待办';
      return '暂无已闭环的待办';
    }
  },
  methods: {
    switchTab(index) {
      this.currentTab = index;
      this.closeAllSwipes();
    },
    loadTodoList() {
      seedTodoListIfEmpty();
      this.todoList = getTodoList();
    },
    handleStart(item) {
      uni.showModal({
        title: '开始办理',
        content: `确认将「${item.title}」标记为进行中？`,
        confirmText: '确认',
        success: (res) => {
          if (res.confirm) {
            updateTodoStatus(item.id, TODO_STATUS.DOING);
            this.todoList = getTodoList();
            uni.showToast({ title: '已开始办理', icon: 'success' });
          }
        }
      });
    },
    handleComplete(item) {
      uni.showModal({
        title: '完成闭环',
        content: `确认完成「${item.title}」？`,
        confirmText: '完成',
        success: (res) => {
          if (res.confirm) {
            updateTodoStatus(item.id, TODO_STATUS.DONE);
            this.todoList = getTodoList();
            uni.showToast({ title: '已完成', icon: 'success' });
          }
        }
      });
    },
    confirmDelete(item) {
      uni.showModal({
        title: '删除待办',
        content: `确定删除「${item.title}」？`,
        confirmText: '删除',
        confirmColor: '#FF4D4F',
        cancelText: '取消',
        success: (res) => {
          if (res.confirm) {
            deleteTodo(item.id);
            this.todoList = getTodoList();
            this.$set(this.swipeOffsets, item.id, 0);
            uni.showToast({ title: '已删除', icon: 'success' });
          }
        }
      });
    },
    onTouchStart(e, id) {
      this.touchStartX[id] = e.touches[0].clientX;
      this.touchStartY[id] = e.touches[0].clientY;
    },
    onTouchMove(e, id) {
      const deltaX = e.touches[0].clientX - this.touchStartX[id];
      const deltaY = e.touches[0].clientY - this.touchStartY[id];
      if (Math.abs(deltaY) > Math.abs(deltaX)) return;
      let offset = Math.max(-80, Math.min(0, deltaX));
      if (this.swipeOffsets[id] === -80 && deltaX < 0) {
        offset = -80 + deltaX * 0.3;
      }
      this.$set(this.swipeOffsets, id, offset);
    },
    onTouchEnd(e, id) {
      const deltaX = e.changedTouches[0].clientX - this.touchStartX[id];
      this.$set(this.swipeOffsets, id, deltaX < -40 ? -80 : 0);
    },
    closeSwipe(id) {
      this.$set(this.swipeOffsets, id, 0);
    },
    closeAllSwipes() {
      Object.keys(this.swipeOffsets).forEach(id => {
        this.$set(this.swipeOffsets, id, 0);
      });
    },
    openCreateModal() {
      this.form = {
        title: '',
        deadlineDate: this.today(),
        deadlineTime: '18:00',
        priority: 'normal'
      };
      this.showCreateModal = true;
    },
    closeCreateModal() {
      this.showCreateModal = false;
    },
    onDateChange(e) {
      this.form.deadlineDate = e.detail.value;
    },
    onTimeChange(e) {
      this.form.deadlineTime = e.detail.value;
    },
    handleCreate() {
      const title = (this.form.title || '').trim();
      if (!title) {
        uni.showToast({ title: '请输入待办事项', icon: 'none' });
        return;
      }
      const deadline = this.form.deadlineDate
        ? `${this.form.deadlineDate}${this.form.deadlineTime ? ' ' + this.form.deadlineTime : ''}`
        : '';
      addTodo({
        title,
        deadline,
        priority: this.form.priority,
        source: 'manual',
        sourceText: '手动创建'
      });
      this.todoList = getTodoList();
      this.showCreateModal = false;
      this.currentTab = 0;
      uni.showToast({ title: '已添加', icon: 'success' });
    },
    today() {
      const d = new Date();
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${y}-${m}-${day}`;
    }
  },
  onShow() {
    this.loadTodoList();
  }
};
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #F5F6F8;
  display: flex;
  flex-direction: column;
  padding-top: var(--status-bar-height);
  padding-bottom: calc(72px + var(--window-bottom));
  box-sizing: border-box;
}
.tab-header {
  display: flex;
  background-color: #ffffff;
  border-bottom: 1px solid #eeeeee;
  position: sticky;
  top: var(--status-bar-height);
  z-index: 10;
}
.tab-item {
  flex: 1;
  text-align: center;
  padding: 14px 0;
}
.tab-item.active {
  border-bottom: 2px solid #0085d0;
}
.tab-item.active .tab-text {
  color: #0085d0;
  font-weight: bold;
}
.tab-text {
  font-size: 15px;
  color: #666666;
}
.todo-list {
  padding: 16px;
  flex: 1;
}
.swipe-card {
  position: relative;
  overflow: hidden;
  margin-bottom: 16px;
  border-radius: 2px;
}
.swipe-delete-btn {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 80px;
  background-color: #ff4d4f;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  border-radius: 0 2px 2px 0;
}
.swipe-delete-text {
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
}
.swipe-content {
  position: relative;
  z-index: 2;
  transition: transform 0.2s ease;
}
.todo-card {
  background-color: #ffffff;
  padding: 16px;
  border-radius: 2px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
  border: 1px solid #eeeeee;
}
.todo-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.todo-tags {
  display: flex;
}
.tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 2px;
  margin-right: 8px;
}
.tag-high {
  background-color: #fff1f0;
  color: #f5222d;
  border: 1px solid #ffa39e;
}
.tag-normal {
  background-color: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}
.tag-source {
  background-color: #f5f5f5;
  color: #666666;
  border: 1px solid #d9d9d9;
}
.todo-deadline {
  font-size: 12px;
  color: #fa8c16;
}
.todo-title {
  font-size: 16px;
  color: #333333;
  font-weight: bold;
  line-height: 1.4;
  margin-bottom: 16px;
}
.todo-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px dashed #eeeeee;
  padding-top: 12px;
}
.todo-meta {
  font-size: 12px;
  color: #999999;
  flex: 1;
  margin-right: 12px;
}
.todo-btn {
  background-color: #0085d0;
  color: #ffffff;
  font-size: 13px;
  padding: 6px 16px;
  border-radius: 2px;
  flex-shrink: 0;
}
.todo-btn-done {
  background-color: #52c41a;
}
.todo-btn-disabled {
  background-color: #d9d9d9;
  color: #999999;
}
.fab-wrapper {
  position: fixed;
  left: 0;
  right: 0;
  bottom: var(--window-bottom);
  padding: 12px 16px;
  background-color: #ffffff;
  border-top: 1px solid #eeeeee;
  z-index: 20;
}
.fab-btn {
  background-color: #0085d0;
  color: #ffffff;
  text-align: center;
  padding: 12px 0;
  font-size: 16px;
  border-radius: 2px;
  font-weight: bold;
}
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 240px;
}
.empty-text {
  color: #999999;
  font-size: 14px;
}

/* 弹窗 */
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
  width: 86%;
  max-width: 360px;
  background-color: #ffffff;
  border-radius: 8px;
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
  padding: 8px 20px 16px;
}
.form-row {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f5f5f5;
}
.form-row:last-child {
  border-bottom: none;
}
.form-label {
  width: 80px;
  font-size: 14px;
  color: #666666;
  flex-shrink: 0;
}
.form-input {
  flex: 1;
  height: 40px;
  font-size: 15px;
  color: #333333;
  background-color: transparent;
}
.form-picker {
  flex: 1;
  font-size: 15px;
  color: #333333;
  padding: 10px 0;
}
.priority-group {
  flex: 1;
  display: flex;
  gap: 12px;
}
.priority-option {
  flex: 1;
  text-align: center;
  padding: 8px 0;
  font-size: 14px;
  color: #666666;
  border: 1px solid #d9d9d9;
  border-radius: 2px;
}
.priority-option.priority-active {
  color: #0085d0;
  border-color: #0085d0;
  background-color: #e6f4ff;
  font-weight: 600;
}
.modal-footer {
  display: flex;
  border-top: 1px solid #f0f0f0;
}
.modal-btn {
  flex: 1;
  padding: 14px 0;
  display: flex;
  justify-content: center;
  align-items: center;
}
.modal-btn:active {
  background-color: #f5f7fa;
}
.modal-btn-cancel {
  border-right: 1px solid #f0f0f0;
}
.modal-btn-cancel .modal-btn-text {
  color: #666666;
}
.modal-btn-confirm .modal-btn-text {
  color: #0085d0;
  font-weight: 600;
}
.modal-btn-text {
  font-size: 16px;
}
</style>
