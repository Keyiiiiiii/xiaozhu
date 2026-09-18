import config from "./config.js";
import { request, getAuthHeader } from "./request.js";

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
      headers: getAuthHeader(),
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

function stringifyFormData(formData) {
  const result = {};
  if (!formData) {
    return result;
  }
  Object.keys(formData).forEach((key) => {
    const value = formData[key];
    result[key] = value === undefined || value === null ? "" : String(value);
  });
  return result;
}

function uploadFileUni(url, filePath, formData) {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: url,
      filePath: filePath,
      name: 'file',
      formData: stringifyFormData(formData),
      header: getAuthHeader(),
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

export function submitSpeechToText(recordId) {
  const baseUrl = config.fileServer.baseUrl.replace(/\/+$/, "");
  const url = `${baseUrl}${config.fileServer.speechToTextPath}`;

  return request({
    url,
    method: 'POST',
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    data: { id: recordId }
  }).then((res) => {
    if (res.data && res.data.status === "success") {
      return {
        job_id: res.data.job_id,
        record_id: res.data.record_id
      };
    }
    throw new Error((res.data && res.data.message) || "提交转写任务失败");
  });
}

export function summarizeRecording(recordId) {
  const baseUrl = config.fileServer.baseUrl.replace(/\/+$/, "");
  const url = `${baseUrl}${config.fileServer.summarizePath}`;

  return request({
    url,
    method: 'POST',
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    data: { id: recordId }
  }).then((res) => {
    if (res.data && res.data.status === "success") {
      return {
        aiSummary: res.data.ai_summary,
        recordId: res.data.record_id
      };
    }
    throw new Error((res.data && res.data.message) || "智能总结失败");
  });
}

export function getRecordIds() {
  const baseUrl = config.fileServer.baseUrl.replace(/\/+$/, "");
  const url = `${baseUrl}${config.fileServer.recordIdsPath}`;

  return request({
    url,
    method: 'POST',
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    data: {}
  }).then((res) => {
    if (res.data && res.data.status === "success") {
      const records = res.data.records || [];
      return records.map(record => ({
        id: record[0],
        status: record[1],
        customer_name: record[2],
        duration_seconds: record[3],
        visit_time: record[4]
      }));
    }
    throw new Error((res.data && res.data.message) || "获取记录列表失败");
  });
}

export function updateOriginalText(recordId, data) {
  const baseUrl = config.fileServer.baseUrl.replace(/\/+$/, "");
  const url = `${baseUrl}${config.fileServer.updateOriginalTextPath}`;

  const requestData = { id: recordId };

  if (data.original_text !== undefined) {
    requestData.original_text = data.original_text;
  }
  if (data.customer_name !== undefined) {
    requestData.customer_name = data.customer_name;
  }
  if (data.visit_time !== undefined) {
    requestData.visit_time = data.visit_time;
  }

  return request({
    url,
    method: 'POST',
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    data: requestData
  }).then((res) => {
    if (res.data && res.data.status === "success") {
      return {
        recordId: res.data.record_id,
        message: res.data.message
      };
    }
    throw new Error((res.data && res.data.message) || "更新走访记录失败");
  });
}

export function getRecordDetail(recordId) {
  const baseUrl = config.fileServer.baseUrl.replace(/\/+$/, "");
  const url = `${baseUrl}${config.fileServer.recordDetailPath}`;

  return request({
    url,
    method: 'POST',
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    data: { id: recordId }
  }).then((res) => {
    if (res.data && res.data.status === "success") {
      return res.data.data;
    }
    throw new Error((res.data && res.data.message) || "获取记录详情失败");
  });
}

export function fetchAudioData(recordId) {
  const baseUrl = config.fileServer.baseUrl.replace(/\/+$/, "");
  const url = `${baseUrl}${config.fileServer.getAudioFilePath}`;

  return request({
    url,
    method: 'POST',
    responseType: 'arraybuffer',
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    data: { id: recordId }
  }).then((res) => {
    if (res.data) {
      return res.data;
    }
    throw new Error('获取音频失败');
  });
}

export function deleteRecord(recordId) {
  const baseUrl = config.fileServer.baseUrl.replace(/\/+$/, "");
  const url = `${baseUrl}${config.fileServer.deleteRecordPath}`;

  return request({
    url,
    method: 'POST',
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    data: { id: recordId }
  }).then((res) => {
    if (res.data && res.data.status === "success") {
      return {
        recordId: res.data.record_id,
        message: res.data.message
      };
    }
    throw new Error((res.data && res.data.message) || "删除走访记录失败");
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
