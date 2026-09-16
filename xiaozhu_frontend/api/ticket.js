/**
 * 工单系统 API 封装
 * 对应后端 /api/knowledge/tickets/ 系列接口
 */
const BASE = '/api/knowledge/tickets';

function _authHeaders() {
  const token = uni.getStorageSync('token');
  const h = { 'Content-Type': 'application/json' };
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

function _getRole() {
  const userInfo = uni.getStorageSync('userInfo') || {};
  // 前端 role 字段可能是中文"客户经理/产品经理/保障人"或英文 gm/pm/guard
  const roleMap = {
    '客户经理': 'gm',
    '产品经理': 'pm',
    '保障人': 'guard',
    'gm': 'gm',
    'pm': 'pm',
    'guard': 'guard'
  };
  return roleMap[(userInfo.role || '').trim()] || 'gm';
}

function _getWorkId() {
  const userInfo = uni.getStorageSync('userInfo') || {};
  return userInfo.empId || userInfo.workId || '';
}

function _request(url, options = {}) {
  const { method = 'GET', data, params } = options;
  let fullUrl = url;
  if (params) {
    const qs = Object.keys(params)
      .filter(k => params[k] !== undefined && params[k] !== null && params[k] !== '')
      .map(k => `${encodeURIComponent(k)}=${encodeURIComponent(params[k])}`)
      .join('&');
    if (qs) fullUrl += (url.includes('?') ? '&' : '?') + qs;
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: fullUrl,
      method,
      data,
      header: _authHeaders(),
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          const msg = (res.data && res.data.message) || `请求失败(${res.statusCode})`;
          reject(new Error(msg));
        }
      },
      fail: (err) => reject(new Error(err.errMsg || '网络错误'))
    });
  });
}

// ===== 1. 创建工单 =====
export function createTicket(payload) {
  // payload: { question, agent_answer?, reason? }
  return _request(`${BASE}/create/`, {
    method: 'POST',
    data: payload
  });
}

// ===== 2. 工单列表 =====
export function listTickets(params = {}) {
  // params: { status?, role?, work_id? }
  const query = {
    role: _getRole(),
    work_id: _getWorkId(),
    ...params
  };
  return _request(`${BASE}/`, { params: query });
}

// ===== 3. 工单详情 =====
export function getTicketDetail(ticketId) {
  return _request(`${BASE}/${ticketId}/`, {
    params: { work_id: _getWorkId() }
  });
}

// ===== 4. 产品经理：解答工单 =====
export function answerTicket(ticketId, payload) {
  // payload: { manager_answer, manager_note?, status? }
  return _request(`${BASE}/${ticketId}/answer/`, {
    method: 'POST',
    data: payload,
    params: { work_id: _getWorkId() }
  });
}

// ===== 5. 产品经理：闭环 =====
export function closeTicket(ticketId, payload) {
  // payload: { related_file_id }
  return _request(`${BASE}/${ticketId}/close/`, {
    method: 'POST',
    data: payload,
    params: { work_id: _getWorkId() }
  });
}

// ===== 6. 上传附件（multipart） =====
export function uploadAttachment(ticketId, filePath, fileName) {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync('token');
    const header = {};
    if (token) header.Authorization = `Bearer ${token}`;

    uni.uploadFile({
      url: `${BASE}/${ticketId}/upload/?work_id=${encodeURIComponent(_getWorkId())}`,
      filePath,
      name: 'file',
      header,
      success: (res) => {
        try {
          const data = JSON.parse(res.data);
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(data);
          } else {
            reject(new Error(data.message || `上传失败(${res.statusCode})`));
          }
        } catch (e) {
          reject(new Error('响应解析失败'));
        }
      },
      fail: (err) => reject(new Error(err.errMsg || '上传失败'))
    });
  });
}

// ===== 状态标签工具 =====
export const STATUS_MAP = {
  pending: { text: '待处理', color: '#fa8c16' },
  processing: { text: '处理中', color: '#1890ff' },
  resolved: { text: '已解决', color: '#52c41a' },
  closed: { text: '已闭环', color: '#999999' },
  rejected: { text: '已驳回', color: '#f5222d' }
};
