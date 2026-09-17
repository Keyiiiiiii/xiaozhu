import config from './config.js';
import { request } from './request.js';

// ============================================================
// 临时静态测试数据开关
// 后端 Django 接口 /api/notifications/* 联调完成后，将 USE_MOCK 置为 false 即可
// ============================================================
const USE_MOCK = true;

// 静态测试数据（模拟后端返回结构，字段与 Django 模型对齐）
// 字段说明：
//   source:  来源（city=市级, district=区县）
//   urgency: 紧急程度（important=重要, urgent=紧急）
//   tag:     兼容旧字段（= source），便于老逻辑过渡
const MOCK_NOTIFICATIONS = [
  {
    id: 1,
    title: '关于下发2026年6月政企宽带最新营销方案的通知',
    content: '各区县公司、市公司各部室：\n\n为深入贯彻省公司"宽融合、云赋能"战略部署，现将2026年6月政企宽带最新营销方案下发如下，请认真组织执行。\n\n一、目标客户群\n1. 园区企业：软件园、自贸区、保税区入驻企业\n2. 楼宇企业：5A 级写字楼内中小企业\n3. 连锁商户：餐饮、零售、便利店连锁总部\n\n二、营销政策\n1. 包年套餐：300M 包年 9 折优惠，新装免初装费\n2. 融合套餐：宽带+固话+云盘三合一，月费 159 元起\n3. 专线升级：原 50M 专线客户可免费升级至 100M\n\n三、执行时间\n2026 年 6 月 1 日至 6 月 30 日，逾期政策收回。\n\n四、考核要求\n各区县公司需在 6 月 30 日前完成本月新增 30 单宽带任务，未完成单位将纳入月度绩效考核。\n\n请各单位高度重视，按方案推进落实。',
    source: 'city',
    urgency: 'urgent',
    tag: 'city',
    audience: 'frontline',
    publisher: '市公司·政企客户部',
    publish_time: '2026-06-01 09:30:00',
    created_at: '2026-06-01 09:30:00',
    force_display: true
  },
  {
    id: 2,
    title: '关于规范走访录音上传要求的说明',
    content: '各区县走访人员：\n\n近期发现部分走访录音存在未上传、上传格式不规范、转写内容缺失等问题，影响后端数据归档与商机挖掘。现就走访录音上传要求再次明确如下：\n\n1. 录音时长：单次走访录音不得低于 3 分钟，低于 3 分钟的视为无效录音。\n2. 上传时效：走访结束后 2 小时内必须完成上传，超时未传系统将自动预警。\n3. 文件命名：客户名称_走访日期_工号，例如"福州某某科技_20260602_E00123"。\n4. 转写校对：上传后请于 24 小时内完成转写内容校对，校对未完成不可结案。\n\n市公司将对 6 月起所有走访录音进行抽检，违规者将通报批评并扣除当月走访绩效。\n\n如有疑问，请联系政企部张工（分机 8866）。',
    source: 'city',
    urgency: 'important',
    tag: 'city',
    audience: 'frontline',
    publisher: '市公司·综合部',
    publish_time: '2026-05-28 14:20:00',
    created_at: '2026-05-28 14:20:00',
    force_display: false
  },
  {
    id: 3,
    title: '仓山区6月园区企业专项走访行动启动通知',
    content: '本区县一线走访人员：\n\n根据市公司6月营销方案部署，仓山区公司定于 6 月启动"园区企业专项走访行动"，覆盖仓山科技园、橘园洲工业区、福湾工业园三个核心园区。\n\n一、走访对象\n三个园区内在册企业共 326 家，每人分配 25-30 家，名单已通过企微下发。\n\n二、走访内容\n1. 宽带使用现状摸排（现有速率、套餐到期日、满意度）\n2. 融合套餐推荐介绍（含云盘、固话）\n3. 客户意向登记（高意向/中意向/无意向）\n\n三、走访要求\n- 每日走访不少于 4 家\n- 每家走访时长不少于 15 分钟\n- 当日 18:00 前完成录音上传\n\n走访结果将作为本月绩效加分项，请按时按质完成。',
    source: 'district',
    urgency: 'important',
    tag: 'district',
    audience: 'frontline',
    publisher: '仓山区公司·政企部',
    publish_time: '2026-05-30 10:00:00',
    created_at: '2026-05-30 10:00:00',
    force_display: true
  },
  {
    id: 4,
    title: '关于走访神器App v2.3.0版本升级公告',
    content: '各位一线走访人员：\n\n走访神器 App 将于 2026 年 6 月 5 日 22:00-24:00 进行 v2.3.0 版本升级，期间 App 暂停服务 2 小时。\n\n本次版本主要更新：\n1. 录音模块：新增实时转写功能，可在录音过程中同步显示转写文本\n2. 走访详情：新增音频播放进度条与片段定位\n3. 待办模块：AI 提取的待办支持批量编辑与截止时间修改\n4. 通知模块：新增开屏强制通知展示机制\n\n升级后请重新登录账号以同步最新用户权限。如遇登录异常，请先清理 App 缓存后重试。\n\n如有问题，请联系 IT 支持组（分机 8000）。',
    source: 'city',
    urgency: 'important',
    tag: 'city',
    audience: 'all',
    publisher: '市公司·IT 支持组',
    publish_time: '2026-05-25 16:45:00',
    created_at: '2026-05-25 16:45:00',
    force_display: false
  },
  {
    id: 5,
    title: '2026年Q2走访数据通报与7月任务部署',
    content: '各区县公司：\n\n现将 2026 年 Q2（4-6月）走访数据通报如下，并部署 7 月任务。\n\n一、Q2 数据汇总\n- 全市累计走访 8642 次，完成率 96%\n- 转写完成率 91%，仍有 9% 走访未上传录音\n- 商机挖掘 326 条，已成交 87 单\n\n二、问题通报\n1. 鼓楼区公司上传及时率仅 78%，需重点关注\n2. 部分走访录音存在客户名称缺失，影响数据归档\n3. 多家单位未按规范使用统一走访话术\n\n三、7 月任务部署\n- 全市走访目标 9500 次\n- 商机挖掘目标 380 条\n- 转写上传及时率 ≥ 95%\n\n请各区县公司于 6 月 28 日前完成 7 月走访计划上报。',
    source: 'city',
    urgency: 'important',
    tag: 'city',
    audience: 'district',
    publisher: '市公司·政企部',
    publish_time: '2026-05-20 09:00:00',
    created_at: '2026-05-20 09:00:00',
    force_display: false
  },
  {
    id: 6,
    title: '紧急：即日起所有园区企业走访录音必须含客户经理签字确认',
    content: '全体一线走访人员：\n\n接省公司通知，自 2026 年 6 月 3 日起，所有园区企业走访录音必须包含客户经理（或对方接待人）口头签字确认环节，确认内容包括：\n1. 走访时间属实\n2. 客户基本信息核对无误\n3. 后续跟进意向确认\n\n未包含签字确认环节的录音将视为无效走访，不计入绩效。\n\n请在走访结束前留出至少 30 秒进行确认环节录音，话术参考：\n"以上为本期走访内容，请问客户经理您是否确认走访时间及内容无误？"\n\n如有疑问请联系政企部。',
    source: 'city',
    urgency: 'urgent',
    tag: 'city',
    audience: 'frontline',
    publisher: '市公司·政企客户部',
    publish_time: '2026-06-03 18:30:00',
    created_at: '2026-06-03 18:30:00',
    force_display: true
  }
];

// 模拟已展示过的强制通知 ID 列表（本地维护，模拟后端状态）
const MOCK_DISPLAYED_IDS_KEY = 'mock_force_displayed_ids';
// 模拟已读通知 ID 列表（普通通知进入详情后自动标记，对应后端 NotificationRead 表）
const MOCK_READ_IDS_KEY = 'mock_notification_read_ids';

function getMockDisplayedIds() {
  try {
    const stored = uni.getStorageSync(MOCK_DISPLAYED_IDS_KEY);
    return Array.isArray(stored) ? stored : [];
  } catch (e) {
    return [];
  }
}

function setMockDisplayedIds(ids) {
  try {
    uni.setStorageSync(MOCK_DISPLAYED_IDS_KEY, Array.isArray(ids) ? ids : []);
  } catch (e) {}
}

function getMockReadIds() {
  try {
    const stored = uni.getStorageSync(MOCK_READ_IDS_KEY);
    return Array.isArray(stored) ? stored : [];
  } catch (e) {
    return [];
  }
}

function setMockReadIds(ids) {
  try {
    uni.setStorageSync(MOCK_READ_IDS_KEY, Array.isArray(ids) ? ids : []);
  } catch (e) {}
}

// 给 mock 通知附加 is_read 字段，便于前端展示样式区分
function decorateWithReadState(list) {
  const readIds = getMockReadIds();
  return list.map((n) => Object.assign({}, n, { is_read: readIds.includes(n.id) }));
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// 模拟分页
function mockPaginate(list, page, pageSize) {
  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  const slice = list.slice(start, end);
  return {
    results: slice,
    count: list.length,
    next: end < list.length ? `mock?page=${page + 1}` : null
  };
}

function buildUrl(path) {
  const baseUrl = config.notificationServer.baseUrl.replace(/\/+$/, '');
  return `${baseUrl}${path}`;
}

function unwrap(res) {
  // 204 No Content
  if (!res.data || (typeof res.data === 'object' && Object.keys(res.data).length === 0)) {
    return null;
  }
  // 1) 自定义后端包装：{ status: 'success', data: ... }
  if (res.data.status === 'success') {
    return res.data.data;
  }
  // 2) 自定义后端包装失败：{ status: 'error', message: '...' }
  if (res.data.status === 'error' && res.data.message) {
    throw new Error(res.data.message);
  }
  // 3) DRF 错误体：{ detail: '...' }
  if (typeof res.data.detail === 'string' && res.data.detail.length > 0 && !res.data.id) {
    throw new Error(res.data.detail);
  }
  // 4) 数组或分页结构 { count, next, results } / { list }
  if (Array.isArray(res.data)) return res.data;
  if (res.data.results || typeof res.data.count === 'number' || Array.isArray(res.data.list)) {
    return res.data;
  }
  // 5) 其余 2xx 响应：视为单对象（DRF 默认行为）原样返回
  return res.data;
}

const notificationApi = {
  /**
   * 获取通知列表（分页）
   * @param {Object} params { page, page_size, tag, audience, keyword }
   */
  getList(params = {}) {
    const query = Object.assign({ page: 1, page_size: 10 }, params);

    // === Mock 分支 ===
    if (USE_MOCK) {
      let filtered = MOCK_NOTIFICATIONS.slice();
      // 来源筛选：city / district
      if (query.source && query.source !== 'all') {
        filtered = filtered.filter((n) => (n.source || n.tag) === query.source);
      }
      // 紧急程度筛选：important / urgent
      if (query.urgency && query.urgency !== 'all') {
        filtered = filtered.filter((n) => (n.urgency || n.level) === query.urgency);
      }
      // 兼容旧 tag 参数：若传 tag 则按 source 匹配
      if (query.tag && query.tag !== 'all' && !query.source) {
        filtered = filtered.filter((n) => (n.source || n.tag) === query.tag);
      }
      if (query.keyword) {
        const kw = String(query.keyword).toLowerCase();
        filtered = filtered.filter((n) =>
          (n.title || '').toLowerCase().includes(kw) ||
          (n.content || '').toLowerCase().includes(kw)
        );
      }
      // 按发布时间倒序（mock 数据本身不是严格排序）
      filtered.sort((a, b) => (String(b.publish_time || '').localeCompare(String(a.publish_time || ''))));
      const decorated = decorateWithReadState(filtered);
      return delay(200).then(() => mockPaginate(decorated, query.page, query.page_size));
    }

    return request({
      url: buildUrl(config.notificationServer.listPath),
      method: 'GET',
      data: query
    }).then((res) => {
      const data = unwrap(res) || {};
      // 兼容两种返回：数组 或 { results: [], count, next }
      if (Array.isArray(data)) {
        return { results: data, count: data.length, next: null };
      }
      return {
        results: data.results || data.list || [],
        count: data.count != null ? data.count : (data.results || []).length,
        next: data.next || null
      };
    });
  },

  /**
   * 获取通知详情
   */
  getDetail(id) {
    // === Mock 分支 ===
    if (USE_MOCK) {
      const found = MOCK_NOTIFICATIONS.find((n) => String(n.id) === String(id));
      const decorated = found ? decorateWithReadState([found])[0] : null;
      return delay(150).then(() => decorated || null);
    }

    return request({
      url: buildUrl(`${config.notificationServer.detailPath}${id}/`),
      method: 'GET'
    }).then((res) => unwrap(res) || {});
  },

  /**
   * 获取未展示的强制通知（开屏触发）
   * 返回数组：[{ id, title, content, tag, level, publisher, publish_time, ... }]
   */
  getPendingForce() {
    // === Mock 分支 ===
    if (USE_MOCK) {
      const displayed = getMockDisplayedIds();
      const pending = MOCK_NOTIFICATIONS.filter(
        (n) => n.force_display && !displayed.includes(n.id)
      );
      return delay(200).then(() => pending);
    }

    return request({
      url: buildUrl(config.notificationServer.pendingForcePath),
      method: 'GET'
    }).then((res) => {
      const data = unwrap(res) || [];
      if (Array.isArray(data)) return data;
      if (Array.isArray(data.results)) return data.results;
      if (Array.isArray(data.list)) return data.list;
      return [];
    });
  },

  /**
   * 标记强制通知为已展示
   */
  markDisplayed(id) {
    // === Mock 分支 ===
    if (USE_MOCK) {
      const displayed = getMockDisplayedIds();
      if (!displayed.includes(id)) {
        displayed.push(id);
        setMockDisplayedIds(displayed);
      }
      return delay(100).then(() => ({ id, marked: true }));
    }

    return request({
      url: buildUrl(`${config.notificationServer.markDisplayedPath}${id}/mark-displayed/`),
      method: 'POST',
      header: { 'Content-Type': 'application/json' }
    }).then((res) => {
      // 容错：204 No Content 或空 body
      if (!res.data || Object.keys(res.data).length === 0) return { id, marked: true };
      try {
        return unwrap(res);
      } catch (e) {
        return { id, marked: true };
      }
    });
  },

  /**
   * 标记通知为已读（进入详情页自动调用，无需用户手动点击）
   */
  markRead(id) {
    // === Mock 分支 ===
    if (USE_MOCK) {
      const readIds = getMockReadIds();
      if (!readIds.includes(id)) {
        readIds.push(id);
        setMockReadIds(readIds);
      }
      return delay(80).then(() => ({ id, read: true }));
    }

    return request({
      url: buildUrl(`${config.notificationServer.markReadPath || '/api/notifications/'}${id}/mark-read/`),
      method: 'POST',
      header: { 'Content-Type': 'application/json' }
    }).then((res) => {
      if (!res.data || Object.keys(res.data).length === 0) return { id, read: true };
      try {
        return unwrap(res);
      } catch (e) {
        return { id, read: true };
      }
    });
  },

  /**
   * 获取未读通知数量（用于首页红点提示）
   * 返回数字
   */
  getUnreadCount() {
    // === Mock 分支 ===
    if (USE_MOCK) {
      const readIds = getMockReadIds();
      const unread = MOCK_NOTIFICATIONS.filter((n) => !readIds.includes(n.id));
      return delay(150).then(() => ({ count: unread.length }));
    }

    return request({
      url: buildUrl(config.notificationServer.unreadCountPath || '/api/notifications/unread-count/'),
      method: 'GET'
    }).then((res) => {
      const data = unwrap(res);
      // 兼容多种返回：{ count: N } / { unread_count: N } / N
      if (typeof data === 'number') return { count: data };
      if (data && typeof data.count === 'number') return { count: data.count };
      if (data && typeof data.unread_count === 'number') return { count: data.unread_count };
      return { count: 0 };
    });
  },

  /**
   * 下发通知（仅 city/district 角色可用）
   * @param {Object} payload { title, content, tag, audience, force_display, expire_at }
   */
  publish(payload = {}) {
    // === Mock 分支 ===
    if (USE_MOCK) {
      const newId = (MOCK_NOTIFICATIONS[0]?.id || 0) + 1;
      const now = new Date();
      const pad = (n) => (n < 10 ? '0' + n : '' + n);
      const newRecord = Object.assign({
        id: newId,
        publisher: '当前用户',
        publish_time: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`,
        created_at: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
      }, payload);
      MOCK_NOTIFICATIONS.unshift(newRecord);
      return delay(300).then(() => newRecord);
    }

    return request({
      url: buildUrl(config.notificationServer.publishPath),
      method: 'POST',
      data: payload,
      header: { 'Content-Type': 'application/json' }
    }).then((res) => unwrap(res));
  }
};

export default notificationApi;
