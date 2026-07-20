const config = {
  voiceServer: {
    baseUrl: "http://36.134.70.149:9005",
    wsPath: "/api/voice/auth/",
    //TODO：从后端获取 API Token
    apiToken: "OYECtTTccG1fOzsT6e8EKXR4sOBHJalv"
  },
  fileServer: {
    baseUrl: "http://localhost:8001",
    uploadPath: "/api/file/upload/",
    speechToTextPath: "/api/file/speech-to-text/",
    wsBaseUrl: "ws://localhost:8001",
    wsPath: "/ws/asr/"
  },
  // TODO: 后端登录认证服务配置
  authServer: {
    baseUrl: "http://localhost:8001",
    loginPath: "/api/auth/login/",
    logoutPath: "/api/auth/logout/"
  }
};

export default config;
