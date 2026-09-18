import config from "./config.js";

/**
 * 拼接知识库 URL（所有平台统一使用绝对地址）
 * @param {string} path 例如 "/api/knowledge" 或 "/api/knowledge/download/123/"
 */
export function buildKnowledgeUrl(path) {
  const base = config.knowledgeServer.baseUrl.replace(/\/+$/, "");
  return `${base}${path}`;
}

/**
 * 知识库问答查询 URL（不带 streaming 参数）
 */
export function getKnowledgeQueryUrl() {
  return buildKnowledgeUrl(config.knowledgeServer.queryPath);
}

/**
 * 知识库文件下载 URL
 * @param {string|number} fileId
 */
export function getKnowledgeDownloadUrl(fileId) {
  return buildKnowledgeUrl(`${config.knowledgeServer.downloadPath}${fileId}/`);
}

export function sendKnowledgeQuery(question) {
  const userInfo = uni.getStorageSync('userInfo') || {};
  const userId = userInfo.empId || String(userInfo.id || '');

  return new Promise((resolve, reject) => {
    const url = getKnowledgeQueryUrl();

    const requestData = {
      ques: question,
      'sys.files': [],
      'sys.user_id': userId,
      'sys.app_id': '',
      'sys.workflow_id': '',
      'sys.workflow_run_id': '',
      stream: false
    };

    uni.request({
      url: url,
      method: 'POST',
      data: requestData,
      header: {
        'Content-Type': 'application/json'
      },
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data);
        } else {
          reject(new Error(`请求失败，状态码: ${res.statusCode}`));
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || '网络请求失败'));
      }
    });
  });
}
