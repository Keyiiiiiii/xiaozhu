const baseUrl = '/api/knowledge';
const apiPath = '/api';

export function sendKnowledgeQuery(question) {
  return new Promise((resolve, reject) => {
    const url = `${baseUrl}${apiPath}?streaming=true`;
    
    const requestData = {
      ques: question,
      'sys.files': [],
      'sys.user_id': '',
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
