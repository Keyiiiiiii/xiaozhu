const config = {
  voiceServer: {
    baseUrl: "http://36.134.70.149:9005",
    wsPath: "/api/voice/auth/",
    apiToken: "OYECtTTccG1fOzsT6e8EKXR4sOBHJalv"
  },
  fileServer: {
    baseUrl: "http://localhost:8000",
    uploadPath: "/api/file/upload/",
    speechToTextPath: "/api/file/speech-to-text/",
    summarizePath: "/api/file/summarize/",
    recordIdsPath: "/api/file/record-ids/",
    recordDetailPath: "/api/file/record-detail/",
    getAudioFilePath: "/api/file/get-audio-file/",
    updateOriginalTextPath: "/api/file/update-original-text/",
    deleteRecordPath: "/api/file/delete-record/",
    wsBaseUrl: "ws://localhost:8000",
    wsPath: "/ws/asr/"
  },
  authServer: {
    baseUrl: "http://localhost:8000",
    loginPath: "/api/auth/login/",
    logoutPath: "/api/auth/logout/",
    mePath: "/api/auth/me/",
    refreshPath: "/api/auth/refresh/"
  },
  versionServer: {
    baseUrl: "http://localhost:8000",
    checkPath: "/api/version/check/"
  }
};

export default config;
