# 一、先在公众号后台把“钥匙”和权限找齐

1. 进入后台路径
   **mp.weixin.qq.com →（左侧）设置与开发 → 开发 → 基本配置**
   在这个页面你能看到并操作：

* **AppID / AppSecret（开发者ID/密码）**：若从未启用，需要管理员扫码启用或重置；启用后请妥善保存。([极光文档][1], [CSDN博客][2])
* **IP 白名单**：把你将要调用接口的服务器出口公网 IP 加入白名单，否则获取 `access_token` 常见报错 40164（IP 不在白名单）。([华为云帮助中心][3], [博客园][4])

2. 快速自测 `access_token`

* 官方获取口：`GET https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=APPID&secret=APPSECRET`
* 有效期通常 \~7200 秒，建议做统一中控刷新。([腾讯云][5])

3. 查看接口配额与权限
   后台“开发者中心/接口权限模板”里可看到各接口**日调用上限**与**实时调用量**；若触发限频会报 `45009 api freq out of limit`。必要时可按官方流程清零配额。([CSDN博客][6], [W3C学校][7])

---

# 二、你真正要用来“备份内容”的三大数据面

> 目标是把**已发布内容**、**草稿**、**永久素材**都能拉取出来，便于备份到 GitHub。

## A. 已发布文章（“发布能力”）

* **接口：** `POST https://api.weixin.qq.com/cgi-bin/freepublish/batchget?access_token=ACCESS_TOKEN`
  请求体：`{"offset":0,"count":20,"no_content":0}`（一次最多 20 条；`no_content=1` 可只拿概要）
* 说明：这是官方“发布能力-获取成功发布列表”接口，返回里包含 `article_id`、`url`（公众号图文链接）等关键字段。([CSDN博客][8], [GitHub][9])
* 补充：拿到 `article_id` 后，还可**按篇获取详情**（`freepublish/getarticle`），各家 SDK 均已实现该能力。([GitHub][10], [binary.ac.cn][11])

## B. 草稿箱（未发布/已发布后会从草稿移除）

* **列表接口：** `POST https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=ACCESS_TOKEN`
  请求体：`{"offset":0,"count":20,"no_content":0}`
* **其它常用：** 新建 `draft/add`、获取 `draft/get`、修改 `draft/update`、删除 `draft/delete`、统计 `draft/count`。
* 这些接口与参数在各官方/权威 SDK 文档中均有明确列出（含文档地址），可对照实现。([Javadoc][12], [CSDN博客][13])

## C. 永久素材库（图片/语音/视频/图文等）

* **列表接口：** `POST https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token=ACCESS_TOKEN`
  请求体：`{"type":"news|image|video|voice","offset":0,"count":20}`
* 注意：这里的“图文（news）”是**永久图文素材**，与“草稿箱/发布能力”是两条线；调用需 HTTPS。([DBA][14], [腾讯云][15])

---

# 三、在后台哪里能“看文档/做调试”

1. **在线接口调试工具**（官方网页）
   打开 `https://mp.weixin.qq.com/debug/`，可直接选接口、填参数、在线调试（含获取 `access_token` 等）。这是最省事的“先通一遍”。([腾讯云][16], [CSDN博客][17])

2. **官方文档定位**（若需要一手描述/字段解释）

* “发布能力-获取成功发布列表”等官方文档链接常见于 SDK 说明与社区问答中（可跳转到 developers.weixin.qq.com 对应页）。([GitHub][9])
* “草稿箱”各接口的**文档地址**在 WxJava Javadoc 里也有直链（同样指向官方开发文档各章节）。([Javadoc][12])

---

# 四、最小化“通路测试”清单（建议按此顺序）

1. **拿 token**

```bash
curl "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=你的APPID&secret=你的APPSECRET"
```

确认返回包含 `access_token`；如报 40164，回到**基本配置**加 IP 白名单。([腾讯云][5], [华为云帮助中心][3])

2. **测“已发布列表”**

```bash
curl -X POST \
  "https://api.weixin.qq.com/cgi-bin/freepublish/batchget?access_token=ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"offset":0,"count":20,"no_content":0}'
```

应看到 `item[].content.news_item[].url` 等字段，即每篇图文的访问链接。([CSDN博客][8])

3. **测“草稿箱列表”**

```bash
curl -X POST \
  "https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"offset":0,"count":20,"no_content":0}'
```

用于备份未发布内容，或作为发布流程的源。([CSDN博客][13])

4. **测“永久素材列表”**

```bash
curl -X POST \
  "https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token=ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"news","offset":0,"count":20}'
```

可批量拿到永久图文、图片等素材信息。([腾讯云][15])

---

# 五、常见坑与后台位置对照

* **IP 白名单忘配** → `40164 invalid ip`：回“设置与开发 → 开发 → 基本配置 → IP 白名单”，加入服务器出口 IP。([华为云帮助中心][3])
* **限频 `45009`**：到“开发者中心/接口权限模板”看本日用量、必要时清零或降并发。([CSDN博客][6])
* **接口字段/能力找不到**：优先查“发布能力/草稿箱/素材管理”章节，或参考成熟 SDK（WxJava / wechatpy）的对应模块与方法签名，能快速定位官方接口与参数。([Javadoc][18], [微信 Python SDK 文档][19])

---

# 六、把返回结果“落地到 GitHub”的提示

你的上一环节已经能拉到数据；要备份到 GitHub，通常做法是：

* **格式化保存**：把 `freepublish`、`draft`、`material` 各自按日期/篇目落成 `JSON/Markdown` 文件；
* **自动化**：写一个脚本（Python/Node/Go 均可）每日拉取差量并提交到仓库，再用 **GitHub Actions** 定时运行。

---


[1]: https://docs.jiguang.cn/jums/senderguide/jums-to-wechatoa?utm_source=chatgpt.com "微信公众号对接指南 - 开发文档- 极光推送"
[2]: https://blog.csdn.net/weixin_44098853/article/details/101208495?utm_source=chatgpt.com "微信公众号如何设置开发者密码（APPSecret）？ 原创"
[3]: https://support.huaweicloud.com/adaptive-cloudsite/adaptive_7020.html?utm_source=chatgpt.com "步骤二设置公众号IP白名单 - 华为云- Huawei Cloud"
[4]: https://www.cnblogs.com/wlovet/p/15908344.html?utm_source=chatgpt.com "我的小程序之旅七：微信公众号设置IP白名单- sum墨"
[5]: https://cloud.tencent.com/developer/article/1424863?utm_source=chatgpt.com "TNW-获取微信公众号的access_token"
[6]: https://blog.csdn.net/minihuabei/article/details/111312218?utm_source=chatgpt.com "微信公众号接口调用频次限制说明原创"
[7]: https://www.w3cschool.cn/weixinkaifawendang/2yqt1q8e.html?utm_source=chatgpt.com "微信公众号接口调用频次限制说明"
[8]: https://blog.csdn.net/weixin_48927623/article/details/127571432 "获取微信公众号成功发布的列表_获取成功发布列表-CSDN博客"
[9]: https://github.com/w7corp/easywechat/discussions/2630?utm_source=chatgpt.com "微信新增发布能力接口，有更新计划吗？或是自己开发如何做 ..."
[10]: https://github.com/binarywang/weixin-java-mp-demo/issues/126?utm_source=chatgpt.com "weixin-java-mp:4.2.1.B 微信发布能力接口文章信息缺少 ..."
[11]: https://binary.ac.cn/weixin-java-mp-javadoc/me/chanjar/weixin/mp/api/WxMpFreePublishService.html?utm_source=chatgpt.com "WxMpFreePublishService (WxJava - MP Java SDK 4.7.0 API)"
[12]: https://javadoc.io/static/com.github.binarywang/weixin-java-mp/4.7.7-20250724.154939/me/chanjar/weixin/mp/api/WxMpDraftService.html?utm_source=chatgpt.com "WxMpDraftService (WxJava - MP Java SDK 4.7.7- ..."
[13]: https://blog.csdn.net/m0_58095675/article/details/128308773?utm_source=chatgpt.com "公众号草稿箱接口"
[14]: https://www.dba.cn/book/weixinmp/SuCaiGuanLi/HuoQuSuCaiLieBiao.html?utm_source=chatgpt.com "获取素材列表- 微信公众号开发手册"
[15]: https://cloud.tencent.com/developer/article/2060502?utm_source=chatgpt.com "微信公众平台-微信服务号开发"
[16]: https://cloud.tencent.com/developer/article/2102290?utm_source=chatgpt.com "微信公众平台接口调试工具"
[17]: https://blog.csdn.net/u012432468/article/details/76762634?utm_source=chatgpt.com "微信在线接口调试工具的使用原创"
[18]: https://javadoc.io/static/com.github.binarywang/weixin-java-mp/4.7.6-20250712.165956/me/chanjar/weixin/mp/bean/freepublish/package-summary.html?utm_source=chatgpt.com "程序包me.chanjar.weixin.mp.bean.freepublish"
[19]: https://docs.wechatpy.org/zh-cn/v1/?utm_source=chatgpt.com "wechatpy 使用文档"
