import config from "./config.js";

export function uploadAudioFile(filePath) {
  return new Promise((resolve, reject) => {
    const baseUrl = config.fileServer.baseUrl.replace(/\/+$/, "");
    const url = `${baseUrl}${config.fileServer.uploadPath}`;

    console.log("上传音频文件:", url, filePath);

    uni.uploadFile({
      url: url,
      filePath: filePath,
      name: 'file',
      header: {
        'content-type': 'multipart/form-data'
      },
      success: (res) => {
        try {
          const data = JSON.parse(res.data);
          if (data.status === "success") {
            resolve(data.file_url);
          } else {
            reject(new Error(data.message || "上传失败"));
          }
        } catch (e) {
          reject(new Error("响应解析失败"));
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || "上传失败"));
      }
    });
  });
}

export function speechToText(fileUrl) {
  return new Promise((resolve, reject) => {
    const baseUrl = config.fileServer.baseUrl.replace(/\/+$/, "");
    const url = `${baseUrl}${config.fileServer.speechToTextPath}`;

    console.log("语音转文字:", url, fileUrl);

    uni.request({
      url: url,
      method: 'POST',
      header: {
        'content-type': 'application/x-www-form-urlencoded'
      },
      data: {
        file_url: fileUrl
      },
      success: (res) => {
        if (res.statusCode === 200 && res.data && res.data.status === "success") {
          resolve(res.data.data.text || "");
        } else {
          reject(new Error((res.data && res.data.message) || "转写失败"));
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || "请求失败"));
      }
    });
  });
}
