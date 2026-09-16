// 缓存管理工具：清理录音临时文件及非关键缓存，保留登录态、走访历史与通知设置

// 受保护的本地存储键，清理时保留
const PRESERVED_KEYS = [
  'token',
  'userInfo',
  'refreshToken',
  'visit_history',
  'notification_settings'
];

// 录音临时文件前缀（与 visit/index.vue 中保存路径一致）
const RECORD_FILE_PREFIX = 'record_';
const RECORD_FILE_EXTENSIONS = ['.wav', '.m4a', '.mp3', '.ogg', '.flac'];

/**
 * 将字节数格式化为可读字符串
 */
export function formatSize(bytes) {
  if (!bytes || bytes <= 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(k)), sizes.length - 1);
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
}

/**
 * 获取本地缓存占用大小（字节）
 * - 包含 uni.storage 占用
 * - App 平台额外统计 USER_DATA_PATH 下的录音临时文件
 */
export function getCacheSize() {
  let total = 0;

  try {
    const info = uni.getStorageInfoSync();
    // currentSize 单位为 KB
    total += (info.currentSize || 0) * 1024;
  } catch (e) {
    console.error('获取 storage 信息失败:', e);
  }

  // #ifdef APP-PLUS
  total += getRecordFilesSize();
  // #endif

  return total;
}

// #ifdef APP-PLUS
/**
 * 统计 USER_DATA_PATH 下录音临时文件总大小（字节）
 */
function getRecordFilesSize() {
  try {
    const fs = uni.getFileSystemManager();
    const userDataPath = uni.env.USER_DATA_PATH;
    const files = fs.readdirSync(userDataPath);
    let size = 0;
    files.forEach((name) => {
      if (isRecordFile(name)) {
        try {
          const stat = fs.statSync(`${userDataPath}/${name}`);
          if (stat && typeof stat.size === 'number') {
            size += stat.size;
          }
        } catch (e) {
          // 忽略单个文件 stat 失败
        }
      }
    });
    return size;
  } catch (e) {
    console.error('统计录音临时文件失败:', e);
    return 0;
  }
}

function isRecordFile(name) {
  if (!name || !name.startsWith(RECORD_FILE_PREFIX)) return false;
  return RECORD_FILE_EXTENSIONS.some((ext) => name.toLowerCase().endsWith(ext));
}
// #endif

/**
 * 清理本地缓存
 * - 删除 USER_DATA_PATH 下的录音临时文件
 * - 删除非受保护键的本地存储
 * 返回清理后剩余大小（字节）
 */
export function clearCache() {
  return new Promise((resolve) => {
    // 1. 清理录音临时文件
    // #ifdef APP-PLUS
    clearRecordFiles();
    // #endif

    // 2. 清理非受保护的本地存储
    try {
      const info = uni.getStorageInfoSync();
      const keys = info.keys || [];
      keys.forEach((key) => {
        if (!PRESERVED_KEYS.includes(key)) {
          try {
            uni.removeStorageSync(key);
          } catch (e) {
            // 忽略单个 key 删除失败
          }
        }
      });
    } catch (e) {
      console.error('清理本地存储失败:', e);
    }

    // 统计清理后剩余大小（异步：等待文件操作完成）
    setTimeout(() => {
      resolve(getCacheSize());
    }, 100);
  });
}

// #ifdef APP-PLUS
function clearRecordFiles() {
  try {
    const fs = uni.getFileSystemManager();
    const userDataPath = uni.env.USER_DATA_PATH;
    let files = [];
    try {
      files = fs.readdirSync(userDataPath) || [];
    } catch (e) {
      console.error('读取 USER_DATA_PATH 失败:', e);
      return;
    }

    files.forEach((name) => {
      if (!isRecordFile(name)) return;
      try {
        fs.unlinkSync(`${userDataPath}/${name}`);
      } catch (e) {
        // 忽略单个文件删除失败
      }
    });
  } catch (e) {
    console.error('清理录音临时文件失败:', e);
  }
}
// #endif

export default {
  formatSize,
  getCacheSize,
  clearCache
};
