"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  data() {
    return {
      // 是否正在录音
      isRecording: false,
      // 录音时长（秒）
      recordDuration: 0,
      // 录音计时器引用
      timer: null,
      // 是否正在长按（用于触发结束录音的进度条）
      isLongPressing: false,
      // 长按进度（0~1）
      longPressProgress: 0,
      // 长按进度定时器引用
      longPressTimer: null,
      // 长按开始时间戳
      longPressStartTime: 0,
      // 长按时长阈值（毫秒），达到后触发结束录音
      longPressDuration: 1e3,
      // 圆形进度条的周长（2 * π * 半径）
      circumference: 2 * Math.PI * 55
    };
  },
  computed: {
    // 计算进度条的 dashoffset，控制圆弧显示长度
    // 原理：stroke-dasharray = 周长，stroke-dashoffset 从周长递减到0
    progressDashOffset() {
      return this.circumference * (1 - this.longPressProgress);
    }
  },
  methods: {
    // 将秒数格式化为 mm:ss 格式
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
    },
    // 点击录音按钮处理
    handleRecordClick() {
      if (!this.isRecording) {
        this.startRecording();
      }
    },
    // 开始录音
    startRecording() {
      this.isRecording = true;
      this.recordDuration = 0;
      this.longPressProgress = 0;
      this.timer = setInterval(() => {
        this.recordDuration++;
      }, 1e3);
    },
    // 触摸开始（按下按钮）
    handleTouchStart() {
      if (!this.isRecording)
        return;
      this.isLongPressing = true;
      this.longPressStartTime = Date.now();
      this.longPressProgress = 0;
      if (this.longPressTimer) {
        clearInterval(this.longPressTimer);
      }
      this.longPressTimer = setInterval(() => {
        const elapsed = Date.now() - this.longPressStartTime;
        this.longPressProgress = Math.min(elapsed / this.longPressDuration, 1);
        if (this.longPressProgress >= 1) {
          this.stopRecording();
          this.resetLongPress();
        }
      }, 16);
    },
    // 触摸结束（松开按钮）
    handleTouchEnd() {
      if (!this.isRecording)
        return;
      if (this.longPressProgress < 1) {
        this.resetLongPress();
      }
    },
    // 重置长按状态
    resetLongPress() {
      this.isLongPressing = false;
      this.longPressProgress = 0;
      if (this.longPressTimer) {
        clearInterval(this.longPressTimer);
        this.longPressTimer = null;
      }
    },
    // 停止录音
    stopRecording() {
      this.isRecording = false;
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }
      this.resetLongPress();
    }
  },
  // 组件销毁前清理定时器，防止内存泄漏
  beforeDestroy() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    if (this.longPressTimer) {
      clearInterval(this.longPressTimer);
      this.longPressTimer = null;
    }
  }
};
if (!Array) {
  const _component_circle = common_vendor.resolveComponent("circle");
  const _component_svg = common_vendor.resolveComponent("svg");
  (_component_circle + _component_svg)();
}
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: $data.isRecording
  }, $data.isRecording ? {
    b: common_vendor.p({
      cx: "60",
      cy: "60",
      r: "55",
      fill: "none",
      ["stroke-width"]: "3"
    }),
    c: common_vendor.p({
      cx: "60",
      cy: "60",
      r: "55",
      fill: "none",
      ["stroke-width"]: "3",
      ["stroke-dasharray"]: $data.circumference,
      ["stroke-dashoffset"]: $options.progressDashOffset,
      ["stroke-linecap"]: "round"
    }),
    d: common_vendor.p({
      viewBox: "0 0 120 120"
    })
  } : {}, {
    e: !$data.isRecording
  }, !$data.isRecording ? {} : {
    f: common_vendor.t($options.formatTime($data.recordDuration))
  }, {
    g: $data.isRecording ? 1 : "",
    h: common_vendor.o((...args) => $options.handleRecordClick && $options.handleRecordClick(...args), "f2"),
    i: common_vendor.o((...args) => $options.handleTouchStart && $options.handleTouchStart(...args), "2c"),
    j: common_vendor.o((...args) => $options.handleTouchEnd && $options.handleTouchEnd(...args), "a9"),
    k: common_vendor.o((...args) => $options.handleTouchEnd && $options.handleTouchEnd(...args), "01"),
    l: !$data.isRecording ? 1 : "",
    m: $data.isRecording && !$data.isLongPressing ? 1 : "",
    n: $data.isRecording ? 1 : "",
    o: common_vendor.t($data.isRecording ? "长按按钮结束录音" : "点击上方按钮开始录音")
  });
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-72a20504"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/visit/index.js.map
