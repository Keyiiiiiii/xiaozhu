import config from "./config.js";

function buildUrl(serverConfig) {
  const baseUrl = serverConfig.baseUrl.replace(/\/+$/, "");
  return `${baseUrl}${serverConfig.uploadPath}`;
}

function uploadFileH5(url, file, formData) {
  return new Promise((resolve, reject) => {
    const fd = new FormData();
    fd.append("file", file);
    if (formData) {
      Object.keys(formData).forEach(key => {
        fd.append(key, formData[key]);
      });
    }

    fetch(url, {
      method: "POST",
      body: fd
    })
      .then(response => response.json().then(data => ({ data, ok: response.ok })))
      .then(({ data, ok }) => {
        if (ok && data.status === "success") {
          resolve({
            file_url: data.file_url,
            record_id: data.record_id
          });
        } else {
          reject(new Error(data.message || "上传失败"));
        }
      })
      .catch(err => {
        reject(new Error(err.message || "上传失败"));
      });
  });
}

function uploadFileUni(url, filePath, formData) {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: url,
      filePath: filePath,
      name: 'file',
      formData: formData || {},
      success: (res) => {
        try {
          const data = JSON.parse(res.data);
          if (data.status === "success") {
            resolve({
              file_url: data.file_url,
              record_id: data.record_id
            });
          } else {
            reject(new Error(data.message || "上传失败"));
          }
        } catch (e) {
          console.error("响应解析失败，原始响应:", res);
          reject(new Error("响应解析失败: " + (res.data || res.errMsg || "未知错误")));
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || "上传失败"));
      }
    });
  });
}

export function uploadAudioFile(filePath, formData, fileObject) {
  const url = buildUrl(config.fileServer);
  console.log("上传音频文件:", url, filePath, formData);

  // #ifdef H5
  if (fileObject && fileObject instanceof File) {
    return uploadFileH5(url, fileObject, formData);
  }
  // #endif

  return uploadFileUni(url, filePath, formData);
}

export function submitSpeechToText(recordId, creatorId) {
  return new Promise((resolve, reject) => {
    const baseUrl = config.fileServer.baseUrl.replace(/\/+$/, "");
    const url = `${baseUrl}${config.fileServer.speechToTextPath}`;

    console.log("提交语音转文字任务:", url, { record_id: recordId, creator_id: creatorId });

    uni.request({
      url: url,
      method: 'POST',
      header: {
        'content-type': 'application/x-www-form-urlencoded'
      },
      data: {
        creator_id: creatorId || 1,
        id: recordId
      },
      success: (res) => {
        if (res.statusCode === 200 && res.data && res.data.status === "success") {
          resolve({
            job_id: res.data.job_id,
            record_id: res.data.record_id
          });
        } else {
          reject(new Error((res.data && res.data.message) || "提交转写任务失败"));
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || "请求失败"));
      }
    });
  });
}

export function connectAsrWebSocket(jobId, callbacks) {
  const wsBaseUrl = config.fileServer.wsBaseUrl.replace(/\/+$/, "");
  const wsPath = config.fileServer.wsPath.replace(/^\/|\/$/g, "");
  const wsUrl = `${wsBaseUrl}/${wsPath}/${jobId}/`;

  console.log("连接 ASR WebSocket:", wsUrl);

  const { onMessage, onError, onClose } = callbacks || {};

  let socketTask = null;

  // #ifdef H5
  try {
    const ws = new WebSocket(wsUrl);
    ws.onopen = () => {
      console.log("ASR WebSocket 连接已建立");
    };
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (onMessage) onMessage(data);
      } catch (e) {
        console.error("WebSocket 消息解析失败:", e);
      }
    };
    ws.onerror = (error) => {
      console.error("ASR WebSocket 错误:", error);
      if (onError) onError(error);
    };
    ws.onclose = (event) => {
      console.log("ASR WebSocket 连接关闭");
      if (onClose) onClose(event);
    };
    return {
      close: () => {
        if (ws) ws.close();
      }
    };
  } catch (e) {
    console.error("创建 WebSocket 失败:", e);
    if (onError) onError(e);
    return { close: () => {} };
  }
  // #endif

  // #ifndef H5
  socketTask = uni.connectSocket({
    url: wsUrl,
    success: () => {
      console.log("uni.connectSocket 调用成功");
    },
    fail: (err) => {
      console.error("uni.connectSocket 调用失败:", err);
      if (onError) onError(err);
    }
  });

  socketTask.onOpen(() => {
    console.log("ASR WebSocket 连接已建立");
  });

  socketTask.onMessage((res) => {
    try {
      const data = JSON.parse(res.data);
      if (onMessage) onMessage(data);
    } catch (e) {
      console.error("WebSocket 消息解析失败:", e);
    }
  });

  socketTask.onError((err) => {
    console.error("ASR WebSocket 错误:", err);
    if (onError) onError(err);
  });

  socketTask.onClose((event) => {
    console.log("ASR WebSocket 连接关闭");
    if (onClose) onClose(event);
  });

  return {
    close: () => {
      if (socketTask) {
        socketTask.close();
        socketTask = null;
      }
    }
  };
  // #endif
}
