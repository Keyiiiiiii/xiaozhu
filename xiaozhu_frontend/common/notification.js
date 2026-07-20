const STORAGE_KEY = 'notification_settings';

const defaultSettings = {
  notificationEnabled: true,
  soundEnabled: true,
  vibrateEnabled: true
};

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

export function showNotification(title, content, options) {
  const settings = getNotificationSettings();
  if (!settings.notificationEnabled) {
    return;
  }

  if (settings.soundEnabled) {
    playNotificationSound();
  }

  if (settings.vibrateEnabled) {
    triggerVibration();
  }

  uni.showToast({
    title: title,
    icon: 'none',
    duration: 3000
  });
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
