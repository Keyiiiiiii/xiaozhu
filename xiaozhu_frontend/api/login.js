import config from './config.js';
import { request, clearAuthStorage } from './request.js';

function buildAuthUrl(path) {
  const baseUrl = config.authServer.baseUrl.replace(/\/+$/, '');
  return `${baseUrl}${path}`;
}

const loginApi = {
  login(username, password) {
    return request({
      url: buildAuthUrl(config.authServer.loginPath),
      method: 'POST',
      data: { username, password },
      header: { 'Content-Type': 'application/json' },
      needAuth: false
    }).then((res) => {
      if (res.data && res.data.status === 'success') {
        const data = res.data.data || {};
        if (data.refresh) {
          uni.setStorageSync('refreshToken', data.refresh);
        }
        return {
          token: data.token,
          userInfo: data.userInfo
        };
      }
      throw new Error((res.data && res.data.message) || '登录失败');
    });
  },

  logout() {
    const token = uni.getStorageSync('token');
    const promise = token
      ? request({
          url: buildAuthUrl(config.authServer.logoutPath),
          method: 'POST',
          header: { 'Content-Type': 'application/json' },
          skipAuthRedirect: true
        }).catch(() => {})
      : Promise.resolve();

    return promise.finally(() => {
      clearAuthStorage();
    });
  },

  getCurrentUser() {
    return request({
      url: buildAuthUrl(config.authServer.mePath),
      method: 'GET'
    }).then((res) => {
      if (res.data && res.data.status === 'success') {
        return res.data.data.userInfo;
      }
      throw new Error((res.data && res.data.message) || '获取用户信息失败');
    });
  },

  refreshToken() {
    const refresh = uni.getStorageSync('refreshToken');
    if (!refresh) {
      return Promise.reject(new Error('无 refresh token'));
    }

    return request({
      url: buildAuthUrl(config.authServer.refreshPath),
      method: 'POST',
      data: { refresh },
      header: { 'Content-Type': 'application/json' },
      needAuth: false,
      skipAuthRedirect: true
    }).then((res) => {
      if (res.data && res.data.status === 'success') {
        const token = res.data.data.token;
        uni.setStorageSync('token', token);
        return token;
      }
      throw new Error((res.data && res.data.message) || '刷新 token 失败');
    });
  }
};

export default loginApi;
