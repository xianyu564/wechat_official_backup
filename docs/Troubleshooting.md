# 常见错误与排查指南 · WeChat OA 备份

本文指导如何定位和修复运行备份时的常见错误。所有接口原始返回会保存在 `data/snapshots/`，出现异常时请优先查看最新快照（文件名形如 `published-0-YYYYMMDD-HHMMSS.json`），定位 `errcode` 与 `errmsg`。

## 一、快速定位：48001（api unauthorized）

48001 表示“接口未授权/无权限”。建议按以下步骤定位与修复：

- 第 1 步：先判明到底是哪个接口在报 48001。
  本脚本会触发 3 类接口：
  - 发布能力：`freepublish/batchget`（已发布列表）与 `freepublish/getarticle`（取正文）
  - 草稿箱：`draft/batchget`
  - 永久素材：`material/batchget_material`（`type=news` 为图文）

- 使用下面 3 条 curl 逐个测试（把 ACCESS_TOKEN 换成你刚拿到的 token）：

```bash
# A. 已发布列表（发布能力）
curl -sX POST "https://api.weixin.qq.com/cgi-bin/freepublish/batchget?access_token=ACCESS_TOKEN" \
  -H "Content-Type: application/json" -d '{"offset":0,"count":1,"no_content":1}'

# B. 草稿列表
curl -sX POST "https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=ACCESS_TOKEN" \
  -H "Content-Type: application/json" -d '{"offset":0,"count":1,"no_content":1}'

# C. 永久素材（图文）
curl -sX POST "https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token=ACCESS_TOKEN" \
  -H "Content-Type: application/json" -d '{"type":"news","offset":0,"count":1}'
```

- 哪个返回 `{ "errcode": 48001, ... }`，就说明哪个能力没开通/没资格。
- 如果三者都 OK，再运行脚本；否则继续第 2 步。

提示：上述接口在第三方 SDK（如 WxJava）Javadoc 可查到与微信官方开发文档的一一对应关系，便于进一步核对字段与权限条件。

- 第 2 步：在公众号后台把“接口权限”开通/补齐。
  进入：`mp.weixin.qq.com → 设置与开发 → 开发 → 接口权限`（英文：Developer Center → Interface permissions）。
  按第 1 步测出来的缺口处理：
  - freepublish（发布能力）报 48001：多数是“发布能力”未开通、或账号类型/认证不满足。页面会显示“未获得/可申请/需认证”等状态，按提示开通或先完成认证。
  - draft（草稿箱）报 48001：同理，在接口权限里找到“草稿箱”相关项，若标注“未获得/申请”，按提示开通。
  - material（永久素材）报 48001：在接口权限里找到“素材管理”相关项，若受限，同样需满足主体类型/认证状态。

常见误区：
- 用错主体/类型的 AppID（将小程序/开放平台或其他公众号的 AppID/Secret 用在当前号上）。
- 账号未认证或权限过期（很多接口要求“已认证服务号”）。

## 六、常见误区与限制（权限）

- 权限与账号类型强相关：不同主体（个人/企业/媒体等）、不同认证状态（未认证/已认证）可用接口不同，请以公众号后台“接口权限”页为准。
- 重要政策提示（freepublish）：自 2025-07 起，个人主体账号、企业主体未认证账号及不支持认证的账号将被回收以下发布能力接口权限：
  - `freepublish/batchget`、`freepublish/delete`、`freepublish/get`、`freepublish/getarticle`、`freepublish/submit`
  - 影响：上述账号将无法通过官方 API 获取“已发布图文”。本仓库在该场景下仅提供合规与能力边界提示。
- AppID/Secret 必须与当前公众号主体一致；同名/相似主体或历史项目的凭据常被误用。
- 若页面显示可申请/需认证，请按提示完成认证或提交申请；不少接口仅“认证服务号”可用。

公众号后台入口路径（界面标签可能随版本微调）：
- 开发接口管理 → 基本配置
- 开发接口管理 → 开发者工具
- 开发接口管理 → 运维中心
- 开发接口管理 → 接口权限（检查/申请 `freepublish`、`draft`、`material` 等能力）

## 二、其他常见错误码与处理

- 40164（不在 IP 白名单）
  - 现象：返回 `errcode: 40164`。通常是服务器/本机出口 IP 不在白名单。
  - 处理：在公众号平台“IP 白名单”中添加运行环境的公网 IP。若经代理/公司网络，需确认最终出口 IP。

- 40001 / 42001（access_token 无效/过期）
  - 现象：`invalid credential`、`access_token expired`。
  - 处理：重新获取 `access_token`；确保系统时间正确（严重偏差会影响签名和 token）。

- 45009（调用频率受限）
  - 现象：`api freq out of limit`。
  - 处理：降低频率；本脚本已内置简单限速（0.2s/次），可适当增大间隔或加入重试。

- 40013（AppID 不合法）/ 40125（invalid appsecret）
  - 处理：核对 `APPID/AppSecret` 是否来自当前公众号主体，是否填错或混用。

## 三、如何获取 ACCESS_TOKEN（用于 curl 自测）

你可以用以下方式获取一次性 `access_token`（替换 APPID/APPSECRET）：
```bash
curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=APPID&secret=APPSECRET"
```
将返回 JSON 中的 `access_token` 带入前述 3 条 curl 测试。

## 四、在仓库中定位快照与问题

- 快照位置：`data/snapshots/`，文件名包含接口类别与时间戳，如：
  - `published-0-YYYYMMDD-HHMMSS.json`
  - `drafts-0-YYYYMMDD-HHMMSS.json`
  - `materials-0-YYYYMMDD-HHMMSS.json`
- 打开最新快照，查看 `errcode/errmsg`，据此对照上文处理。

## 五、运行建议

- 若 curl 自测均正常，再运行脚本。
- 建议分支隔离：为不同时间段/尝试新参数的备份创建独立特性分支，合并前先审阅增量变更。
- 若问题仍未解决：请附上相关快照文件与精简的报错上下文提交到 Issues。
