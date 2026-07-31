const baseUrl = '/api/knowledge';

export function sendKnowledgeQuery(question) {
  const userInfo = uni.getStorageSync('userInfo') || {};
  const userId = userInfo.empId || String(userInfo.id || '');

  return new Promise((resolve, reject) => {
    const url = `${baseUrl}?streaming=true`;
    
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
