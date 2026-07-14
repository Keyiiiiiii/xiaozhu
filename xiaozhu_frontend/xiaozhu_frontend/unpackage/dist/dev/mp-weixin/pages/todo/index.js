"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  data() {
    return {
      currentTab: 0
    };
  },
  methods: {
    switchTab(index) {
      this.currentTab = index;
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: $data.currentTab === 0 ? 1 : "",
    b: common_vendor.o(($event) => $options.switchTab(0), "52"),
    c: $data.currentTab === 1 ? 1 : "",
    d: common_vendor.o(($event) => $options.switchTab(1), "86"),
    e: $data.currentTab === 2 ? 1 : "",
    f: common_vendor.o(($event) => $options.switchTab(2), "79"),
    g: $data.currentTab === 0
  }, $data.currentTab === 0 ? {} : {}, {
    h: $data.currentTab === 1
  }, $data.currentTab === 1 ? {} : {}, {
    i: $data.currentTab === 2
  }, $data.currentTab === 2 ? {} : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-7167769e"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/todo/index.js.map
