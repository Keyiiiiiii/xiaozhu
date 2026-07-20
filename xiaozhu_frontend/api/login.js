import config from './config.js';

// TODO: 连接后端登录接口
// 替换硬编码验证为后端API调用
const loginApi = {
  login(username, password) {
    return new Promise((resolve, reject) => {
      // TODO: 替换为真实后端接口请求
      // uni.request({
      //   url: config.authServer.baseUrl + '/api/auth/login',
      //   method: 'POST',
      //   data: { username, password },
      //   success: (res) => {
      //     if (res.data.code === 0) {
      //       resolve(res.data.data);
      //     } else {
      //       reject(new Error(res.data.message || '登录失败'));
      //     }
      //   },
      //   fail: (err) => {
      //     reject(err);
      //   }
      // });

      // 临时硬编码验证
      setTimeout(() => {
        if (username === 'admin' && password === '123456') {
          resolve({
            token: 'mock-token-' + Date.now(),
            userInfo: {
              id: 1,
              username: 'admin',
              name: '张三',
              role: '客户经理',
              dept: '市公司 / 政企客户部 / 第一网格',
              empId: 'FZ10086'
            }
          });
        } else {
          reject(new Error('账号或密码错误'));
        }
      }, 500);
    });
  },

  logout() {
    return new Promise((resolve) => {
      // TODO: 调用后端登出接口
      // uni.request({
      //   url: config.authServer.baseUrl + '/api/auth/logout',
      //   method: 'POST',
      //   success: () => resolve(),
      //   fail: () => resolve()
      // });
      setTimeout(() => {
        resolve();
      }, 200);
    });
  }
};

export default loginApi;
