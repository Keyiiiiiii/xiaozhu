const API_CONFIG = {
  // #ifdef H5
  baseUrl: '/api/knowledge',
  // #endif
  // #ifndef H5
  baseUrl: 'http://36.212.132.154:30086/berry-apps/server/apps/GtjGSJ2V4rrQP-rg457sbi3BDJM7vyDv',
  // #endif
  apiPath: '/api'
};

export function sendKnowledgeQuery(question) {
  return new Promise((resolve, reject) => {
    const baseUrl = API_CONFIG.baseUrl.replace(/\/+$/, '');
    const url = `${baseUrl}${API_CONFIG.apiPath}?streaming=true`;
    
    const requestData = {
      ques: question,
      'sys.files': [],
      'sys.user_id': '',
      'sys.app_id': '',
      'sys.workflow_id': '',
      'sys.workflow_run_id': '',
      stream: false
    };
    
    console.log('发送知识库查询:', url, requestData);
    
    uni.request({
      url: url,
      method: 'POST',
      data: requestData,
      header: {
        'Content-Type': 'application/json'
      },
      success: (res) => {
        console.log('知识库查询结果:', res);
        if (res.statusCode === 200) {
          resolve(res.data);
        } else {
          reject(new Error(`请求失败，状态码: ${res.statusCode}`));
        }
      },
      fail: (err) => {
        console.error('知识库查询失败:', err);
        reject(new Error(err.errMsg || '网络请求失败'));
      }
    });
  });
}