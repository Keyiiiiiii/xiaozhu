function getToken() {
  return uni.getStorageSync('token') || '';
}

function clearAuthStorage() {
  uni.removeStorageSync('token');
  uni.removeStorageSync('userInfo');
  uni.removeStorageSync('refreshToken');
}

function clearAuthAndRedirect() {
  clearAuthStorage();
  uni.reLaunch({
    url: '/pages/login/index'
  });
}

export function getAuthHeader(extra = {}) {
  const token = getToken();
  const headers = { ...extra };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

export function request(options = {}) {
  const {
    url,
    method = 'GET',
    data = {},
    header = {},
    needAuth = true,
    skipAuthRedirect = false,
    responseType
  } = options;

  const finalHeader = needAuth
    ? getAuthHeader(header)
    : { ...header };

  return new Promise((resolve, reject) => {
    uni.request({
      url,
      method,
      data,
      header: finalHeader,
      responseType,
      success: (res) => {
        if (res.statusCode === 401 && needAuth && !skipAuthRedirect) {
          clearAuthAndRedirect();
          reject(new Error('未登录或 token 已过期'));
          return;
        }

        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res);
        } else {
          const message = (res.data && res.data.message) || `请求失败，状态码: ${res.statusCode}`;
          reject(new Error(message));
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || '网络请求失败'));
      }
    });
  });
}

export { clearAuthAndRedirect, clearAuthStorage, getToken };
