import config from './config.js';
import { request } from './request.js';

function buildUrl(path) {
  const baseUrl = config.versionServer.baseUrl.replace(/\/+$/, '');
  return `${baseUrl}${path}`;
}

// 获取当前应用版本信息
export function getAppVersionInfo() {
  // #ifdef APP-PLUS
  try {
    const info = uni.getSystemInfoSync();
    return {
      version: plus.runtime.version || info.appVersion || '1.0.0',
      versionCode: parseInt(plus.runtime.versionCode || info.appVersionCode || '100', 10),
      platform: info.platform === 'ios' ? 'iOS' : 'Android'
    };
  } catch (e) {
    console.error('获取 App 版本信息失败:', e);
    return { version: '1.0.0', versionCode: 100, platform: 'Android' };
  }
  // #endif

  // #ifndef APP-PLUS
  return { version: '1.0.0', versionCode: 100, platform: 'H5' };
  // #endif
}

const versionApi = {
  /**
   * 检查更新
   * 请求参数：platform、version、versionCode
   * 返回字段：update_type (0:提示热更 1:强制热更 2:提示整包 3:强制整包)、download_url、update_log、version、version_code、is_silent
   */
  checkUpdate(params) {
    const info = getAppVersionInfo();
    const data = {
      platform: info.platform,
      version: info.version,
      versionCode: info.versionCode,
      ...(params || {})
    };

    return request({
      url: buildUrl(config.versionServer.checkPath),
      method: 'POST',
      data,
      header: { 'Content-Type': 'application/json' },
      needAuth: false
    }).then((res) => {
      if (res.data && res.data.status === 'success') {
        return res.data.data || null;
      }
      throw new Error((res.data && res.data.message) || '版本检查失败');
    });
  }
};

export default versionApi;
