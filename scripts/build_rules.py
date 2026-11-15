import ast, collections, concurrent.futures, hashlib, ipaddress, json, os, re, time, urllib.request
from pathlib import Path
BASE='https://raw.githubusercontent.com/'
META=BASE+'MetaCubeX/meta-rules-dat/meta/geo/'
LOYAL=BASE+'Loyalsoldier/clash-rules/release/'
CATEGORIES={'Scholar':'category-scholar-!cn','MyTVSuper':'mytvsuper','Crypto':'category-cryptocurrency','AI':'category-ai-!cn','YouTube':'youtube','Google':'google','Netflix':'netflix','Telegram':'telegram','Steam':'steam','Epic':'epicgames','Xbox':'xbox','PlayStation':'playstation','HBO':'hbo','DisneyPlus':'disney','Bahamut':'bahamut','Bilibili':'bilibili','Microsoft':'microsoft','Apple':'apple','Tiktok':'tiktok','GitHub':'github'}
ORDER=['LAN','Bybit','AI','Scholar','MyTVSuper','Crypto','YouTube','Netflix','Telegram','HBO','DisneyPlus','Bahamut','Bilibili','GitHub','ServiceDirect','Steam','Epic','Xbox','PlayStation','Tiktok','Google','Microsoft','Apple','Overseas','China']
DIRECT={'LAN','ServiceDirect','China'}
DEFAULT_DIRECT={'Bilibili','Microsoft','Apple'}
OPENER=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def fetch(url):
 for n in range(3):
  try:
   with OPENER.open(urllib.request.Request(url,headers={'User-Agent':'Loon-rule-builder'}),timeout=45) as r: data=r.read(20000001)
   if len(data)>20000000:raise ValueError('Source too large')
   return data.decode('utf-8-sig')
  except Exception:
   if n==2:raise
   time.sleep(n+1)
def lines(text):return [s.strip() for s in text.splitlines() if s.strip() and not s.lstrip().startswith('#')]
def payload(text):
 result=[]
 for s in lines(text):
  if s=='payload:':continue
  if not s.startswith('- '):raise ValueError('Invalid YAML payload')
  s=s[2:].strip();result.append(ast.literal_eval(s) if s.startswith(('"',"'")) else s)
 return result
def domain(s):
 kind='DOMAIN-SUFFIX' if s.startswith('+.') else 'DOMAIN'; host=s[2:] if s.startswith('+.') else s
 if not re.fullmatch(r'[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*',host):raise ValueError('Unsupported domain: '+s)
 return kind+','+host.lower()
def cidr(s,no=False):
 n=ipaddress.ip_network(s,strict=False)
 return ('IP-CIDR6,' if n.version==6 else 'IP-CIDR,')+str(n)+(',no-resolve' if no else '')
def validate(s):
 p=s.split(',')
 if p[0] in {'DOMAIN','DOMAIN-SUFFIX','DOMAIN-KEYWORD'} and len(p)==2:
  if not p[1] or re.search(r'[\s,]',p[1]):raise ValueError(s)
 elif p[0] in {'IP-CIDR','IP-CIDR6'} and len(p) in {2,3}:
  if len(p)==3 and p[2]!='no-resolve':raise ValueError(s)
  if cidr(p[1],len(p)==3)!=s:raise ValueError('Noncanonical CIDR '+s)
 else:raise ValueError('Unsupported rule '+s)
 return s
class Coverage:
 def __init__(self):self.exact=set();self.suffix=set();self.literal=set()
 def covered(self,s):
  if s in self.literal:return True
  p=s.split(',')
  if p[0] in {'DOMAIN','DOMAIN-SUFFIX'}:
   if p[0]=='DOMAIN' and p[1] in self.exact:return True
   labels=p[1].split('.')
   return any('.'.join(labels[i:]) in self.suffix for i in range(len(labels)))
  return False
 def add(self,s):
  self.literal.add(s);p=s.split(',')
  if p[0]=='DOMAIN-SUFFIX':self.suffix.add(p[1])
  if p[0]=='DOMAIN':self.exact.add(p[1])
def compact(rules):
 # Broad suffix first only within the same policy; never broadens its coverage.
 ordered=sorted(set(rules),key=lambda s:(0 if s.startswith('DOMAIN-SUFFIX,') else 1,s.split(',')[1].count('.'),s))
 c=Coverage();out=[]
 for s in ordered:
  validate(s)
  if not c.covered(s):out.append(s);c.add(s)
 return out

def main():
 urls={k:META+'geosite/'+v+'.list' for k,v in CATEGORIES.items()}
 urls.update({'cn':META+'geosite/cn.list','cnip':META+'geoip/cn.list','telegramip':META+'geoip/telegram.list','netflixip':META+'geoip/netflix.list','private':LOYAL+'private.txt','privateip':LOYAL+'lancidr.txt','proxy':LOYAL+'proxy.txt','applecn':META+'geosite/apple-cn.list','mscn':META+'geosite/microsoft@cn.list','steamcn':META+'geosite/steam@cn.list'})
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:data=dict(zip(urls,pool.map(fetch,urls.values())))
 raw={k:[domain(x) for x in lines(data[k])] for k in CATEGORIES}
 raw['Telegram'] += [cidr(x,True) for x in lines(data['telegramip'])]
 raw['Netflix'] += [cidr(x,True) for x in lines(data['netflixip'])]
 raw['LAN']=[domain(x) for x in payload(data['private'])]+[cidr(x,True) for x in payload(data['privateip'])]+['DOMAIN-SUFFIX,lan']
 raw['Bybit']=[validate(x) for x in lines(Path('Bybit.list').read_text(encoding='utf-8-sig'))]
 raw['ServiceDirect']=[domain(x) for k in ['applecn','mscn','steamcn'] for x in lines(data[k])]
 raw['Overseas']=[domain(x) for x in payload(data['proxy'])]
 raw['China']=[domain(x) for x in lines(data['cn'])]+[cidr(x) for x in lines(data['cnip'])]+['DOMAIN-SUFFIX,cn']
 for k,r in raw.items():
  if not r:raise ValueError('Empty category '+k)
 for k,n in {'China':50000,'Overseas':10000,'LAN':50}.items():
  if len(raw[k])<n:raise ValueError('Source too small '+k)
 # Each category remains useful on its own; ordered/ removes rules shadowed by earlier policies.
 independent={};effective={};stats={};prior=Coverage();report_old={}
 if Path('sources-and-stats.json').exists():report_old=json.loads(Path('sources-and-stats.json').read_text())
 for k in ORDER:
  custom=Path('custom')/(k+'.list')
  if custom.exists():raw[k]+=[validate(x) for x in lines(custom.read_text(encoding='utf-8-sig'))]
  independent[k]=compact(raw[k])
  old=report_old.get('categories',{}).get(k,{}).get('source_count',0)
  if old and len(raw[k])<old*0.8:raise ValueError('Source count dropped >20%: '+k)
  effective[k]=[s for s in independent[k] if not prior.covered(s)]
  for s in effective[k]:prior.add(s)
  stats[k]={'source_count':len(raw[k]),'independent_count':len(independent[k]),'effective_count':len(effective[k]),'within_removed':len(raw[k])-len(independent[k]),'earlier_shadowed':len(independent[k])-len(effective[k])}
 outputs={}
 def render(k,r):return '# Loon rules; assign policy on import.\n# Category: '+k+'\n# Sources and counts: sources-and-stats.json\n# Generated; edit custom/'+k+'.list for additions.\n'+'\n'.join(r)+'\n'
 for k in ORDER:
  outputs['rules/'+k+'.list']=render(k,independent[k]);outputs['ordered/'+k+'.list']=render(k,effective[k])
 # Preserve previously published subscription paths and the hand-maintained Bybit.list.
 outputs['ChinaDirect.list']=render('China',independent['China']);outputs['LANDirect.list']=render('LAN',independent['LAN'])
 root='https://raw.githubusercontent.com/wuleaves/bybit-loon-rules/main/'
 groups=['[Proxy Group]','NX-Proxies = select,PROXY','NX-Direct = select,DIRECT,NX-Proxies']
 for k in ORDER:
  if k in DIRECT or k=='Overseas':continue
  choices='NX-Direct,NX-Proxies' if k in DEFAULT_DIRECT else 'NX-Proxies,NX-Direct'
  groups.append('NX-'+k+' = select,'+choices)
 groups.append('NX-Final = select,NX-Proxies,NX-Direct')
 policy=lambda k:'NX-Direct' if k in DIRECT else 'NX-Proxies' if k=='Overseas' else 'NX-'+k
 remote=['[Remote Rule]']+[root+'ordered/'+k+'.list,policy='+policy(k)+',tag='+k+',enabled=true' for k in ORDER if effective[k]]
 warning='# Routing template: add your own node/subscription before use. PROXY must point to a working node.\n# No node credentials included. Merge existing sections; do not duplicate FINAL.\n'
 outputs['Loon-Full.conf']=warning+'[General]\ndns-server = system,223.5.5.5,119.29.29.29\n\n'+'\n'.join(groups)+'\n\n[Rule]\nFINAL,NX-Final\n\n'+'\n'.join(remote)+'\n'
 local=[]
 for k in ORDER:
  local.append('# '+k)
  for s in effective[k]:
   p=s.split(',');local.append(','.join(p[:2]+[policy(k)]+p[2:]))
 local.append('FINAL,NX-Final')
 outputs['Loon-Local-Routing.conf']=warning+'\n'.join(groups)+'\n\n[Rule]\n'+'\n'.join(local)+'\n'
 report={'order':ORDER,'sources':urls,'source_sha256':{k:hashlib.sha256(t.encode()).hexdigest() for k,t in data.items()},'categories':stats,'notes':['Nexitally classification reference only; source domains come from public upstream.','Bybit.list is preserved, then incorporated with highest service priority.','Only exact and proven DOMAIN/DOMAIN-SUFFIX coverage removed; overlapping IP ranges and keywords are preserved.','No attempt to widen or subtract a later broad suffix around earlier exceptions.']}
 outputs['sources-and-stats.json']=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
 outputs['FULL-GUIDE.txt']='''Loon 完整分流：Nexitally 分类 + 公开上游自动更新

Loon-Full.conf 是远程规则模板；须先保留/添加自己的节点订阅，再让 PROXY 指向有效节点。
建议将策略组与远程规则合并进现有配置，不要直接覆盖已有节点、DNS 或证书设置。
NX- 前缀用于避免同名冲突；Apple、Microsoft、Bilibili 默认直连，其他服务默认代理，可自行切换。
完整优先级及数量见 sources-and-stats.json。Bybit 优先于 Crypto；AI、YouTube 优先于 Google；GitHub 优先于 Microsoft；国内服务例外先于宽泛服务分类。
Loon-Local-Routing.conf 是严格按顺序展开的离线规则片段，与远程模板二选一，只有远程订阅会随仓库更新。
不把 Nexitally 的私有节点、进程规则、随机直连域名或 DNS 覆写上传。分类参考不等于一比一复刻原规则。

rules/：每类独立去重版本，可单独使用。
ordered/：用于完整模板，删除被前面类别完全覆盖的规则；请按模板顺序使用，不建议单独抽取。
相同策略的域名后缀覆盖可安全合并；跨策略仅删除已被早先规则完全覆盖的项。宽泛的后置规则仍保留，以免丢失未被覆盖的子域名。
IP 只去除精确重复；未声称解决所有网段交集。规则优先级仍决定结果。

自动更新：每天北京时间 06:47；Actions 可手动运行。所有源通过格式、数量检查后才发布，失败保留旧版。Loon 也需要刷新远程规则。
custom/分类名.list 可添加兼容规则，下次构建会合并。此处只支持新增，不是优先强制覆盖；改变策略请调整源清单及顺序。
Bybit.list 保留手工维护；其变更会触发完整构建。国内旧订阅地址保持有效。

来源：MetaCubeX/meta-rules-dat（国内/服务分类）、Loyalsoldier/clash-rules（通用海外/局域网）。每个精确 URL 与内容校验值记录在 sources-and-stats.json。
采用 MetaCubeX 提供的 domain list 版本；它与 classical 含正则版本不完全等价。不支持的格式会令更新失败，不会静默丢弃。
Apple/Microsoft/Steam 的国内服务例外采用同源 @cn/apple-cn 集合，避免再叠加不同体系的 CDN 总表。
保留上游归属，来源项目的许可证仍适用；本仓库转换不改变原始规则的许可。
已做构建与去重验证；未在 iPhone Loon 上实机验证。规则不能保证节点解锁、地区或服务可用性。
'''
 outputs['使用说明.txt']=outputs['FULL-GUIDE.txt']
 for name,text in outputs.items():
  p=Path(name);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8',newline='\n')
 summary='\n'.join(f"{k}: {stats[k]['source_count']} -> {stats[k]['effective_count']}" for k in ORDER)
 print(summary)
 if os.environ.get('GITHUB_STEP_SUMMARY'):Path(os.environ['GITHUB_STEP_SUMMARY']).write_text('## Loon rule validation\n\n```\n'+summary+'\n```\n',encoding='utf-8')
if __name__=='__main__':main()

