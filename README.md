# Bybit Loon 分流规则

基于 [MetaCubeX 的 Bybit 域名列表](https://github.com/MetaCubeX/meta-rules-dat/blob/meta/geo/geosite/classical/bybit.list) 整理，供 Loon 作为远程规则订阅。

## 在 Loon 中使用

将以下一行加入配置文件的 `[Remote Rule]` 段，或在 Loon 的远程规则页面添加规则 URL 并选择代理策略：

```ini
https://raw.githubusercontent.com/wuleaves/bybit-loon-rules/main/Bybit.list,policy=PROXY,enabled=true
```

将 `PROXY` 替换成你在 Loon 中实际使用的节点或策略组名称。让这条远程规则排在通用规则和 `FINAL` 规则之前。

规则文件：[Bybit.list](Bybit.list) · [原始订阅地址](https://raw.githubusercontent.com/wuleaves/bybit-loon-rules/main/Bybit.list)


## 登录域名补充与排查

2026-10-14：在上游列表基础上补充 `DOMAIN-SUFFIX,bybit.global`。
公开的 [Bybit 登录页面](https://www.bybit.global/en/login) 使用 `www.bybit.global`，
它不属于原先已有的 `bybitglobal.com` 或 `bybit-global.com`，因此需要独立规则。
此项依据公开网页登录页面补充；尚未通过手机 App 请求记录确认其实际使用情况，不能视为手机登录故障已经修复。

`DOMAIN-SUFFIX,bybit.com` 已覆盖 `api.bybit.com`、`www.bybit.com` 等子域名，
无需为 `/login` 或 `/app/login` 等 URL 路径添加域名规则。

更新后请在 Loon 中手动刷新远程规则，确认订阅包含 `bybit.global`，并检查所选策略。
如果手机 App 仍无法登录，请在 Loon 请求记录开启时重新尝试登录，查看失败请求的主机名、命中规则和实际策略。
只需提供这些信息，不要公开密码、验证码、Cookie、Authorization 或含令牌的完整 URL。
第三方登录、验证码、DNS、规则优先级和节点连通性也可能影响登录；没有请求证据时，不把 Google、Apple 或验证码服务的整个域名加入此专用规则。


## 扩展域名与来源（2026-10-14）

本轮新增 8 条，规则总数为 25 条。所有条目使用订阅所选策略。

- 区域站点：`bybit.eu`、`bybit.tr`、`bybit.kz`、`bybitgeorgia.ge`、`bybit.ae`、`bybit.id`。依据 [Bybit 官方 API 文档](https://bybit-exchange.github.io/docs/v5/guide#authentication) 中列出的区域 API 地址，以域名后缀规则覆盖对应站点及子域名。官方 API 地址不等于手机 App 登录地址；这些条目仅补充区域站点覆盖。
- 备用域名候选：`byffbb.com`。依据 [社区规则原始列表](https://gist.github.com/toimc/00cd37e1cccd4dde12af96ba4b60e638) 补充；[公开 DNS 观测](https://dnsrepo.noc.org/?ip=163.171.146.25) 中也出现过 `api3.byffbb.com`。尚未通过本机手机 App 请求记录确认登录用途，也未取得官方登录接口说明。
- 监控主机：`monitor-frontend-collector.a.bybit-aws.com`。依据 [社区抓包报告](https://github.com/blackmatrix7/ios_rule_script/issues/1476) 精确匹配该主机，不扩大到整个 `bybit-aws.com`。这是辅助监控流量，未确认是登录必需依赖。

本轮更新用于补齐已发现的域名覆盖，不代表已经定位或修复手机登录故障。未纳入社区列表中的通用统计域名，也未新增 Google、Apple 或验证码服务的全域规则。
