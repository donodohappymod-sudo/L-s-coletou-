import requests, pandas as pd
def check_entries(entries,timeout=8):
    rows=[]
    for e in entries:
        status="erro"; detail=""
        try:
            r=requests.get(e["url"],stream=True,timeout=timeout,allow_redirects=True,
                           headers={"User-Agent":"LosCollector/1.0"})
            status="online" if r.status_code<400 else "erro"
            detail=f"HTTP {r.status_code}"
        except requests.Timeout: status="timeout"; detail="Tempo excedido"
        except Exception as ex: detail=str(ex)[:150]
        rows.append({"nome":e["name"],"categoria":e.get("category",""),
                     "status":status,"detalhe":detail,"url":e["url"]})
    return pd.DataFrame(rows)
