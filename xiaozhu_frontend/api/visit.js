import config from "./config.js";

export function uploadVisitRecord(filePath, formData) {
  return new Promise((resolve, reject) => {
    const baseUrl = config.fileServer.baseUrl.replace(/\/+$/, "");
    const url = `${baseUrl}${config.fileServer.uploadPath}`;

    console.log("上传走访记录:", url, formData);

    uni.uploadFile({
      url: url,
      filePath: filePath,
      name: 'file',
      formData: formData,
      success: (res) => {
        try {
          const data = JSON.parse(res.data);
          if (data.status === "success") {
            resolve(data);
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
