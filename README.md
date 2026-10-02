# Bybit Loon 分流规则

基于 [MetaCubeX 的 Bybit 域名列表](https://github.com/MetaCubeX/meta-rules-dat/blob/meta/geo/geosite/classical/bybit.list) 整理，供 Loon 作为远程规则订阅。

## 在 Loon 中使用

将以下一行加入配置文件的 `[Remote Rule]` 段，或在 Loon 的远程规则页面添加规则 URL 并选择代理策略：

```ini
https://raw.githubusercontent.com/wuleaves/bybit-loon-rules/main/Bybit.list,policy=PROXY,enabled=true
```

将 `PROXY` 替换成你在 Loon 中实际使用的节点或策略组名称。让这条远程规则排在通用规则和 `FINAL` 规则之前。

规则文件：[Bybit.list](Bybit.list) · [原始订阅地址](https://raw.githubusercontent.com/wuleaves/bybit-loon-rules/main/Bybit.list)
