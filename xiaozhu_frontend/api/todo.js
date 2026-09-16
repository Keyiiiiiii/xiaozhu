// 待办模块本地存储管理 (MVP 阶段使用本地存储，与 visit_history 约定保持一致)

const STORAGE_KEY = 'todo_list';

// 待办状态枚举
export const TODO_STATUS = {
  PENDING: 'pending', // 未办
  DOING: 'doing',     // 进行中
  DONE: 'done'        // 已闭环
};

// 优先级枚举
export const TODO_PRIORITY = {
  HIGH: 'high',     // 高优
  NORMAL: 'normal'  // 常规
};

// 来源枚举
export const TODO_SOURCE = {
  MANUAL: 'manual', // 手动创建
  AI: 'ai'          // AI 走访提取
};

// 读取待办列表
export function getTodoList() {
  try {
    const list = uni.getStorageSync(STORAGE_KEY);
    return Array.isArray(list) ? list : [];
  } catch (e) {
    console.error('读取待办列表失败:', e);
    return [];
  }
}

// 保存整张待办列表
export function saveTodoList(list) {
  try {
    uni.setStorageSync(STORAGE_KEY, Array.isArray(list) ? list : []);
  } catch (e) {
    console.error('保存待办列表失败:', e);
  }
}

// 新增一条待办 (手动 / AI 推入通用入口)
export function addTodo(todo = {}) {
  const list = getTodoList();
  const now = Date.now();
  const item = {
    id: `todo_${now}_${Math.floor(Math.random() * 1000)}`,
    title: (todo.title || '').trim(),
    deadline: todo.deadline || '',
    priority: todo.priority || TODO_PRIORITY.NORMAL,
    source: todo.source || TODO_SOURCE.MANUAL,
    sourceText: todo.sourceText || '',
    status: todo.status || TODO_STATUS.PENDING,
    createTime: now
  };
  list.unshift(item);
  saveTodoList(list);
  return item;
}

// 批量推入 AI 提取的待办 (走访模块可调用)
export function pushAiTodos(todos = []) {
  if (!Array.isArray(todos) || todos.length === 0) return [];
  const list = getTodoList();
  const now = Date.now();
  const items = todos.map((t, idx) => ({
    id: `todo_${now + idx}_${Math.floor(Math.random() * 1000)}`,
    title: (t.title || '').trim(),
    deadline: t.deadline || '',
    priority: t.priority || TODO_PRIORITY.NORMAL,
    source: TODO_SOURCE.AI,
    sourceText: t.sourceText || '',
    status: TODO_STATUS.PENDING,
    createTime: now + idx
  }));
  const merged = [...items, ...list];
  saveTodoList(merged);
  return items;
}

// 更新待办状态 (状态流转核心)
export function updateTodoStatus(id, status) {
  const list = getTodoList();
  const index = list.findIndex(item => item.id === id);
  if (index === -1) return null;
  list[index].status = status;
  if (status === TODO_STATUS.DONE) {
    list[index].completeTime = Date.now();
  }
  saveTodoList(list);
  return list[index];
}

// 删除一条待办
export function deleteTodo(id) {
  const list = getTodoList();
  const filtered = list.filter(item => item.id !== id);
  saveTodoList(filtered);
  return filtered;
}

// 首次进入若无数据，写入种子数据用于演示
export function seedTodoListIfEmpty() {
  const list = getTodoList();
  if (list.length > 0) return list;

  const now = Date.now();
  const seeds = [
    {
      id: 'todo_seed_1',
      title: '核实软件园二期A区装机地址的宽带资源情况',
      deadline: '06-03 18:00',
      priority: TODO_PRIORITY.HIGH,
      source: TODO_SOURCE.AI,
      sourceText: '福州某某科技走访',
      status: TODO_STATUS.PENDING,
      createTime: now - 86400000
    },
    {
      id: 'todo_seed_2',
      title: '联系福建某某实业集团财务确认开票信息及款项进度',
      deadline: '06-05 12:00',
      priority: TODO_PRIORITY.NORMAL,
      source: TODO_SOURCE.MANUAL,
      sourceText: '张三',
      status: TODO_STATUS.PENDING,
      createTime: now - 43200000
    },
    {
      id: 'todo_seed_3',
      title: '整理本月客户走访数据并提交至区县公司',
      deadline: '06-08 18:00',
      priority: TODO_PRIORITY.NORMAL,
      source: TODO_SOURCE.AI,
      sourceText: '市公司周会走访纪要',
      status: TODO_STATUS.DOING,
      createTime: now - 3600000
    }
  ];
  saveTodoList(seeds);
  return seeds;
}
