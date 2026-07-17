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

export function uploadVisitRecordApi(filePath, formData, fileObject) {
  const url = buildUrl(config.visitServer);
  console.log("上传走访记录:", url, formData);

  // #ifdef H5
  if (fileObject && fileObject instanceof File) {
    return uploadFileH5(url, fileObject, formData);
  }
  // #endif

  return uploadFileUni(url, filePath, formData);
}

export function speechToText(recordId, creatorId) {
  return new Promise((resolve, reject) => {
    const baseUrl = config.fileServer.baseUrl.replace(/\/+$/, "");
    const url = `${baseUrl}${config.fileServer.speechToTextPath}`;

    console.log("语音转文字:", url, { record_id: recordId, creator_id: creatorId });

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
          const segments = res.data.data.segments || [];
          const text = segments.map(s => s.text || "").join("");
          resolve(text);
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
