import sys,re,subprocess,html
url=sys.argv[1]
r=subprocess.run(["curl","-sL","--max-time","60","-A","Mozilla/5.0",url],capture_output=True)
t=r.stdout.decode("utf-8","ignore")
# strip scripts/styles
t=re.sub(r'(?is)<(script|style|nav|svg)[^>]*>.*?</\1>',' ',t)
m=re.search(r'(?is)<article[^>]*>(.*?)</article>',t)
if m: t=m.group(1)
else:
    m=re.search(r'(?is)<main[^>]*>(.*?)</main>',t)
    if m: t=m.group(1)
t=re.sub(r'(?is)<br\s*/?>','\n',t)
t=re.sub(r'(?is)</(p|div|li|tr|h1|h2|h3|h4|td|th)>','\n',t)
t=re.sub(r'(?is)<td[^>]*>',' | ',t)
t=re.sub(r'(?is)<[^>]+>',' ',t)
t=html.unescape(t)
t=re.sub(r'[ \t]+',' ',t)
t=re.sub(r'\n\s*\n+','\n',t)
print(t.strip())
