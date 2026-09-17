const STORAGE_KEY = 'notification_settings';

const defaultSettings = {
  notificationEnabled: true,
  soundEnabled: true,
  vibrateEnabled: true
};

// 应用是否处于前台（用户可见）
let isAppActive = true;
// 是否已注册全局前后台监听
let appStateListenerInitialized = false;
// 推送点击监听是否已注册
let pushClickListenerInitialized = false;

function ensureAppStateListener() {
  if (appStateListenerInitialized) return;
  appStateListenerInitialized = true;

  // #ifdef APP-PLUS || H5
  if (typeof uni !== 'undefined' && uni.onAppShow) {
    uni.onAppShow(() => {
      isAppActive = true;
    });
  }
  if (typeof uni !== 'undefined' && uni.onAppHide) {
    uni.onAppHide(() => {
      isAppActive = false;
    });
  }
  // #endif

  // #ifdef H5
  if (typeof document !== 'undefined' && typeof document.addEventListener === 'function') {
    document.addEventListener('visibilitychange', () => {
      isAppActive = !document.hidden;
    });
    // 初始化时同步一次
    isAppActive = !document.hidden;
  }
  // #endif
}

/**
 * 获取应用是否处于前台
 */
export function getAppActiveState() {
  return isAppActive;
}

export function getNotificationSettings() {
  try {
    const saved = uni.getStorageSync(STORAGE_KEY);
    if (saved) {
      return {
        notificationEnabled: saved.notificationEnabled !== undefined ? saved.notificationEnabled : defaultSettings.notificationEnabled,
        soundEnabled: saved.soundEnabled !== undefined ? saved.soundEnabled : defaultSettings.soundEnabled,
        vibrateEnabled: saved.vibrateEnabled !== undefined ? saved.vibrateEnabled : defaultSettings.vibrateEnabled
      };
    }
  } catch (e) {
    console.error("获取通知设置失败:", e);
  }
  return { ...defaultSettings };
}

export function saveNotificationSettings(settings) {
  try {
    uni.setStorageSync(STORAGE_KEY, {
      notificationEnabled: settings.notificationEnabled,
      soundEnabled: settings.soundEnabled,
      vibrateEnabled: settings.vibrateEnabled
    });
  } catch (e) {
    console.error("保存通知设置失败:", e);
  }
}

/**
 * 统一的通知入口：在应用内外都向用户推送消息
 * @param {string} title 通知标题
 * @param {string} content 通知正文
 * @param {object} options 可选参数：
 *   - showModal: 应用内是否使用 modal 弹窗（默认 false 使用 toast）
 *   - payload: 应用外通知点击后传递的负载数据
 *   - targetType: 点击通知后的跳转目标，可选 'visit' / 'visitDetail' / 'notificationList'
 *   - targetId: 跳转目标所需的 ID（如 recordId / jobId）
 *   - forceSystem: 即使应用在前台也发送系统通知（默认 false）
 */
export function showNotification(title, content, options = {}) {
  ensureAppStateListener();

  const settings = getNotificationSettings();
  if (!settings.notificationEnabled) {
    return;
  }

  // 提示音与震动在应用内外均触发
  if (settings.soundEnabled) {
    playNotificationSound();
  }
  if (settings.vibrateEnabled) {
    triggerVibration();
  }

  const isForceSystem = options && options.forceSystem === true;
  const shouldSendSystem = !isAppActive || isForceSystem;

  // 应用内：始终显示 toast（如配置则附加 modal）
  if (isAppActive && !shouldSendSystem) {
    uni.showToast({
      title: title,
      icon: 'none',
      duration: 3000
    });

    if (options && options.showModal) {
      uni.showModal({
        title: title,
        content: content,
        showCancel: false,
        confirmText: '我知道了'
      });
    }
  }

  // 应用外（后台 / 锁屏 / 应用未在前台）或强制系统通知：发送系统本地通知
  if (shouldSendSystem) {
    sendSystemNotification(title, content, options);
  }
}

/**
 * 发送系统级本地通知（应用外可见）
 */
function sendSystemNotification(title, content, options) {
  const payload = buildPayload(options);

  // #ifdef APP-PLUS
  try {
    if (typeof plus === 'undefined' || !plus.push) {
      console.warn("App-PLUS 环境下 plus.push 不可用");
      return;
    }
    // 创建本地推送消息（即使在应用内也会出现在系统通知栏，但通常用于应用外场景）
    plus.push.createMessage(content, JSON.stringify(payload), {
      title: title,
      sound: 'system',
      cover: false
    });
  } catch (e) {
    console.error("App-PLUS 系统通知发送失败:", e);
  }
  // #endif

  // #ifdef H5
  try {
    if (typeof window === 'undefined' || !('Notification' in window)) {
      console.warn("浏览器不支持系统通知");
      return;
    }

    const fireNotification = () => {
      try {
        const n = new Notification(title, {
          body: content,
          tag: payload && payload.targetId ? payload.targetId : 'visit-asr',
          // icon: '/static/logo.png'
        });
        n.onclick = () => {
          try {
            window.focus();
            handleNotificationClick(payload);
            n.close();
          } catch (e) {
            console.error("H5 通知点击处理失败:", e);
          }
        };
      } catch (e) {
        console.error("H5 系统通知创建失败:", e);
      }
    };

    if (Notification.permission === 'granted') {
      fireNotification();
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then((permission) => {
        if (permission === 'granted') {
          fireNotification();
        }
      });
    }
  } catch (e) {
    console.error("H5 系统通知失败:", e);
  }
  // #endif

  // #ifdef MP-WEIXIN
  // 小程序订阅消息需要服务端模板和用户授权，本地无法主动创建系统通知，
  // 这里仅静默处理，已通过 toast / 声音 / 震动提示用户。
  // #endif
}

function buildPayload(options) {
  const o = options || {};
  return {
    type: 'visit_asr',
    targetType: o.targetType || 'visit',
    targetId: o.targetId || null,
    extra: o.payload || null,
    timestamp: Date.now()
  };
}

/**
 * 初始化全局推送点击监听（建议在 App.vue onLaunch 中调用一次）
 */
export function initPushClickListener() {
  // #ifdef APP-PLUS
  if (pushClickListenerInitialized) return;
  pushClickListenerInitialized = true;

  try {
    if (typeof plus === 'undefined' || !plus.push) {
      return;
    }

    // 点击系统通知栏消息时触发
    plus.push.addEventListener('click', (msg) => {
      let payload = null;
      try {
        payload = typeof msg.payload === 'string' ? JSON.parse(msg.payload) : msg.payload;
      } catch (e) {
        payload = msg && msg.payload;
      }
      handleNotificationClick(payload);
    }, false);

    // 应用前台运行时收到透传消息触发 receive（用于在应用内提示）
    plus.push.addEventListener('receive', (msg) => {
      let payload = null;
      try {
        payload = typeof msg.payload === 'string' ? JSON.parse(msg.payload) : msg.payload;
      } catch (e) {
        payload = msg && msg.payload;
      }
      // 应用前台收到透传消息时，以应用内通知呈现
      const title = (msg && (msg.title || (payload && payload.title))) || '走访通知';
      const content = (msg && (msg.content || (payload && payload.content))) || '您有一条新消息';
      showNotification(title, content, { payload: payload });
    }, false);
  } catch (e) {
    console.error("初始化推送点击监听失败:", e);
  }
  // #endif
}

/**
 * 处理通知点击：根据 payload 跳转到对应页面
 */
function handleNotificationClick(payload) {
  if (!payload) {
    return;
  }

  const targetType = payload.targetType || 'visit';
  const targetId = payload.targetId;

  try {
    if (targetType === 'visitDetail' && targetId) {
      uni.navigateTo({
        url: `/pages/visit/detail?id=${encodeURIComponent(targetId)}`
      });
    } else if (targetType === 'notificationList') {
      uni.switchTab({
        url: '/pages/tabBar/template/template'
      });
    } else {
      // 默认跳转到走访页（tabBar 页面，使用 switchTab）
      uni.switchTab({
        url: '/pages/visit/index'
      });
    }
  } catch (e) {
    console.error("处理通知点击跳转失败:", e);
  }
}

function playNotificationSound() {
  // #ifdef APP-PLUS
  try {
    plus.device.beep(1);
  } catch (e) {
    console.error("播放提示音失败:", e);
  }
  // #endif

  // #ifdef MP-WEIXIN
  // 小程序环境暂不支持自定义提示音
  // #endif

  // #ifdef H5
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);

    oscillator.frequency.value = 800;
    oscillator.type = 'sine';
    gainNode.gain.setValueAtTime(0.3, audioCtx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);

    oscillator.start(audioCtx.currentTime);
    oscillator.stop(audioCtx.currentTime + 0.3);
  } catch (e) {
    console.error("H5 播放提示音失败:", e);
  }
  // #endif
}

function triggerVibration() {
  // #ifdef APP-PLUS
  try {
    plus.device.vibrate(500);
  } catch (e) {
    console.error("震动失败:", e);
  }
  // #endif

  // #ifndef APP-PLUS
  try {
    uni.vibrateLong({
      success: () => {},
      fail: () => {}
    });
  } catch (e) {
    console.error("震动失败:", e);
  }
  // #endif
}
