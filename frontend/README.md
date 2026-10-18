# uni-app 前端（完整实现）

## 运行

1. 使用 **HBuilderX** 导入本目录（项目为 HBuilderX 标准结构，Vue 3）。
2. 先启动后端（见 `backend/README.md`），默认地址 `http://127.0.0.1:8000`。
3. HBuilderX 中选择「运行 → 运行到浏览器」调试 H5；
   或「运行 → 运行到小程序模拟器 → 微信开发者工具」调试小程序端。
4. 真机调试时，把 `common/config.js` 中的 `BASE_URL` 改为电脑的局域网 IP。

## 页面结构（10 页 + 5 个 tabBar）

| 页面 | 路径 | 说明 |
| --- | --- | --- |
| 登录 | pages/login/login | 已登录自动跳转首页 |
| 注册 | pages/register/register | 用户名 + 密码（≥6位）+ 昵称 |
| 首页 | pages/index/index | 月度收支总览、预算进度、最近账单、待办摘要、快捷入口 |
| 账单列表 | pages/bills/list | 月份切换、类型筛选、分页加载、AI 来源标记 |
| 记一笔 | pages/bills/edit | 支出/收入切换、分类宫格、日期选择、增改删 |
| AI 助手 | pages/ai/assistant | 一句话记账、便签整理、月度总结三种模式 |
| 便签列表 | pages/notes/list | 搜索、类型筛选、待办勾选完成 |
| 便签详情 | pages/notes/edit | 便签/待办切换、截止时间、增改删 |
| 统计分析 | pages/statistics/statistics | 汇总卡片、每日支出柱状图、分类占比条 |
| 我的 | pages/profile/profile | 昵称修改、月度预算设置、退出登录 |

## AI 交互状态设计（对应课程要求）

- 生成中 / 成功 / 失败 / 重试 四态完整；AI 内容统一带「AI 生成」标识
- 草稿可编辑：类型、金额、分类、日期、备注均可在确认前修改
- 缺失字段警示（金额/日期/分类待补充），模糊信息不会被自动猜测
- AI 未配置（503）或超时（504）时提供「手动记账」降级入口
- 月度总结基于后端真实统计数据生成，前端明确标注「仅供参考」
- 页面底部展示模型名、提示词版本与耗时（可解释性）

## 技术说明

- 状态管理：`store/user.js` 基于 Vue3 `reactive` 的轻量单例（token + 用户信息，
  同步 uni storage）；如需可平滑替换为 Pinia
- 网络层：`api/request.js` 统一封装 uni.request，自动携带 JWT，
  401 统一清登录态跳转，错误统一 toast
- tabBar 图标由 `tools/gen_tabbar_icons.py` 生成，位于 `static/tabbar/`
