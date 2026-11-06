# GaussianDWM：补充材料源图逐项核对（2026-11-07）

原始制作：2026-10-28；本次修订：2026-11-07；状态：repairing（**未完成全篇验收**）。

## 附录 B 问答与轨迹

已检查保存在本仓库的完整原文合并 [第14页](pages/page-14.jpg)，直接按左右栏的印刷版核验，而不是将双栏 PDF 的乱序文本拼接为数据。

* 左栏的 QA 标注：`token` 为 `fd8420396768425eabec9bdddf7e64b6`，`scene_token` 为 `e7ef871f77f44331aefdebc24ec034b7`，均为32位；scene_idx=2，frame_idx=0，category=2D_perception_infos，task=rdp；用户指定前视框 (14,219)–(37,248)，模型回答 38.7 米。原相机文件路径和 Gaussian 场景路径均已经恢复到 translation.md/html。
* 右栏的 4 帧历史轨迹位置依次为 (-7.45,3.05,0.16)、(-5.75,1.97,0.11)、(-4.04,0.92,0.09)、(-2.15,0.26,0.04)；6 帧目标位置为 (0,0,0)、(2.47,0.65,-0.06)、(4.24,2.32,-0.11)、(5.5,4.08,-0.15)、(7.03,6.45,-0.15)、(8.66,8.91,-0.17)。所有逐帧四元数保存在完整 JSON 里；仅规范断行、小数显示，保留数值语义。
* 作者原文英文问题保存在 JSON；与译者中文解释分离。不是实际模型运行轨迹。

## 定性补充图

[合并第17页](pages/page-17.jpg) 对应补充图1，翻译六相机 CAM_FRONT_LEFT/FRONT/FRONT_RIGHT/BACK_RIGHT/BACK/BACK_LEFT、3D Gaussians、Temporal Generation、GT/Generated、Turn Left。对应未来三个时间步 t1/t2/t3。

[合并第18页](pages/page-18.jpg) 对应补充图2，翻译雨天相机、车辆边界框、Go Straight、Parked car、It will remain stationary、It will be close to the ego car、Spatial Generation、Ref. GT、+1m、+2m。两页原始页图完整嵌入译文，避免任何裁图丢失原始信息。

## 尚缺及验收边界

这次完成的是附录两段 JSON 和两张定性图的**局部页面视觉核对**，未逐段审完主论文12页和附录其他内容。浏览器位置恢复的代码已修正 CSS smooth scroll 的潜在时序问题，尚需对实际完整 `file://` 页面、窄屏布局及 KaTeX 公式执行独立浏览器验收；此前离线检查曾失败，不能据此标记通过。独立中文简报 PDF 和可选 ZIP 备份均需在最终文本审校后重新核验一致性。不得将本修复项改为 completed。
