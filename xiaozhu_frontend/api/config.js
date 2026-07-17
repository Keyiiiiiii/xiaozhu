const config = {
  voiceServer: {
    baseUrl: "http://36.134.70.149:9005",
    wsPath: "/api/voice/auth/",
    //TODO：从后端获取 API Token
    apiToken: "OYECtTTccG1fOzsT6e8EKXR4sOBHJalv"
  },
  visitServer: {
    baseUrl: "http://localhost:8001",
    uploadPath: "/api/file/upload/"
  },
  fileServer: {
    //改为后端运行端口
    baseUrl: "http://localhost:8001",
    uploadPath: "/api/file/upload/",
    speechToTextPath: "/api/file/speech-to-text/"
  }
};

export default config;
