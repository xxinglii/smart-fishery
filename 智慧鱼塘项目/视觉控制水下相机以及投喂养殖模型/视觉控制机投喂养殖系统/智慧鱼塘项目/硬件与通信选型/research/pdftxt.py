import sys, fitz
p=sys.argv[1]
d=fitz.open(p)
out=[]
for i,pg in enumerate(d):
    out.append(f"\n===== PAGE {i+1} =====\n"+pg.get_text())
t="".join(out)
open(p+".txt","w",encoding="utf-8").write(t)
print(t[:200])
print("TOTAL PAGES",len(d))
