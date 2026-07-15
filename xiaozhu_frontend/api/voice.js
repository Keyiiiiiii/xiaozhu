import config from "./config.js";

export function getVoiceWsUrl() {
  return new Promise((resolve, reject) => {
    const baseUrl = config.voiceServer.baseUrl.replace(/\/+$/, "");
    const url = `${baseUrl}${config.voiceServer.wsPath}`;
    console.log("获取语音 WebSocket URL:", url);
    uni.request({
      url: url,
      method: "GET",
      success: (res) => {
        if (res.statusCode === 200 && res.data && res.data.code === 0 && res.data.data && res.data.data.url) {
          resolve(res.data.data.url);
        } else {
          reject(new Error(`获取 WebSocket URL 失败: ${JSON.stringify(res.data)}`));
        }
      },
      fail: (err) => {
        reject(new Error(`请求失败: ${err.errMsg}`));
      }
    });
  });
}
