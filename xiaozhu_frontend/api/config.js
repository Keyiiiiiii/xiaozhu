const config = {
  voiceServer: {
    baseUrl: "http://36.134.70.149:9005",
    wsPath: "/api/voice/auth/",
    apiToken: "OYECtTTccG1fOzsT6e8EKXR4sOBHJalv"
  },
  fileServer: {
    baseUrl: "http://101.33.219.170:20001/",
    uploadPath: "/api/file/upload/",
    speechToTextPath: "/api/file/speech-to-text/",
    summarizePath: "/api/file/summarize/",
    recordIdsPath: "/api/file/record-ids/",
    recordDetailPath: "/api/file/record-detail/",
    getAudioFilePath: "/api/file/get-audio-file/",
    updateOriginalTextPath: "/api/file/update-original-text/",
    deleteRecordPath: "/api/file/delete-record/",
    wsBaseUrl: "ws://101.33.219.170:20001/",
    wsPath: "/ws/asr/"
  },
  authServer: {
    baseUrl: "http://101.33.219.170:20001/",
    loginPath: "/api/auth/login/",
    logoutPath: "/api/auth/logout/",
    mePath: "/api/auth/me/",
    refreshPath: "/api/auth/refresh/"
  },
  versionServer: {
    baseUrl: "http://101.33.219.170:20001/",
    checkPath: "/api/version/check/"
  },
  notificationServer: {
    baseUrl: "http://101.33.219.170:20001/",
    listPath: "/api/notifications/",
    detailPath: "/api/notifications/", // 拼接 {id}/
    pendingForcePath: "/api/notifications/pending-force/",
    markDisplayedPath: "/api/notifications/", // 拼接 {id}/mark-displayed/
    publishPath: "/api/notifications/"
  },
  knowledgeServer: {
    // 所有平台统一绝对地址
    baseUrl: "http://101.33.219.170:20001/",
    queryPath: "/api/knowledge",
    downloadPath: "/api/knowledge/download/" // 拼接 {id}/
  }
};

export default config;
