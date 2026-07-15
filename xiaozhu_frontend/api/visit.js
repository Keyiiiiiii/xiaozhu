import config from "./config.js";

export function uploadVisitRecord(filePath, formData) {
  return new Promise((resolve, reject) => {
    const baseUrl = config.visitServer.baseUrl.replace(/\/+$/, "");
    const url = `${baseUrl}${config.visitServer.uploadPath}`;
    
    console.log("上传走访记录:", url, formData);
    
    uni.uploadFile({
      url: url,
      filePath: filePath,
      name: 'audio',
      formData: formData,
      success: (res) => {
        try {
          const data = JSON.parse(res.data);
          if (data.code === 0) {
            resolve(data);
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
