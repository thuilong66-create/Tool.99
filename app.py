import os, time, requests
from flask import Flask, jsonify, render_template_string
from algorithms import du_doan_huy

app = Flask(__name__)
API_URL = os.environ.get("LC79_API_URL", "https://wtx.tele68.com/v1/tx/lite-sessions")
POLL_SECONDS = max(3, int(os.environ.get("POLL_SECONDS", "5")))
CACHE = {"at": 0, "rows": [], "error": None}

HTML = """<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hưng Đẹp Zai | LC79 Hũ</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#080d18;color:#eaf2ff;font:15px Arial,sans-serif;background-image:radial-gradient(circle at 20% 0,#12315b 0,transparent 40%)}
main{max-width:900px;margin:auto;padding:22px}.brand{color:#5bd6ff;font-weight:900;letter-spacing:2px;font-size:25px}.sub{color:#91a8c5}
.card{background:#101c30;border:1px solid #24476b;border-radius:16px;padding:18px;margin:14px 0;box-shadow:0 10px 30px #0005}
.hero{display:flex;gap:12px;flex-wrap:wrap}.pill{padding:8px 12px;border-radius:30px;background:#172d49;color:#9ddfff}
.pred{font-size:54px;font-weight:900;text-align:center;padding:15px;color:#5bd6ff}.tai{color:#ff637c}.xiu{color:#53e6ad}
button{background:#1377b9;color:white;border:0;border-radius:9px;padding:11px 16px;font-weight:bold}
table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:9px;border-bottom:1px solid #263b55}small{color:#8ea6c5}
</style></head><body><main><div class="brand">HƯNG ĐẸP ZAI</div><div class="sub">LC79 HŨ · AI HISTORY ANALYZER</div>
<div class="card hero"><span class="pill">API: <b id="api">Đang tải</b></span><span class="pill">Số phiên: <b id="count">0</b></span><span class="pill">Cập nhật: <b id="updated">—</b></span></div>
<div class="card"><small>DỰ ĐOÁN THAM KHẢO · THUẬT TOÁN HŨ</small><div id="pred" class="pred">—</div><div id="confidence" style="text-align:center">Chờ dữ liệu lịch sử</div><p id="engine" class="sub"></p></div>
<div class="card"><h3>Lịch sử LC79 Hũ</h3><div id="history">Đang lấy dữ liệu...</div></div>
<p><small>Phân tích mẫu lịch sử không thể biết trước kết quả ngẫu nhiên và không đảm bảo thắng. Không có chức năng đặt cược tự động.</small></p></main>
<script>
async function load(){try{let r=await fetch('/api/status',{cache:'no-store'}),d=await r.json();document.getElementById('api').textContent=d.error?'Lỗi API':'Đã kết nối';document.getElementById('count').textContent=d.count;document.getElementById('updated').textContent=d.updated||'—';
if(d.prediction){let p=d.prediction;let el=document.getElementById('pred');el.textContent=p.du_doan==='T'?'TÀI':'XỈU';el.className='pred '+(p.du_doan==='T'?'tai':'xiu');document.getElementById('confidence').textContent='Độ tin cậy mô hình: '+p.do_tin_cay+'% · '+(p.tong_mau||0)+' tín hiệu';document.getElementById('engine').textContent=p.engine||'Unified engine';}
document.getElementById('history').innerHTML='<table><tr><th>Phiên</th><th>Kết quả</th></tr>'+d.history.slice(-25).reverse().map(x=>'<tr><td>'+esc(x.ma_phien||'—')+'</td><td class="'+(x.ket_qua==='T'?'tai':'xiu')+'">'+(x.ket_qua==='T'?'TÀI':'XỈU')+'</td></tr>').join('')+'</table>'+(d.error?'<p class="tai">'+esc(d.error)+'</p>':'');
}catch(e){document.getElementById('api').textContent='Mất kết nối';}}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
load();setInterval(load,5000);
</script></body></html>"""

def get_history():
    now=time.time()
    if now-CACHE["at"] < POLL_SECONDS and CACHE["rows"]: return CACHE["rows"]
    try:
        r=requests.get(API_URL,timeout=15,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
        r.raise_for_status(); raw=r.json()
        arr=raw if isinstance(raw,list) else next((raw[k] for k in ("sessions","data","list","history") if isinstance(raw,dict) and isinstance(raw.get(k),list)),[])
        rows=[]
        for item in arr:
            if not isinstance(item,dict): continue
            val=next((item.get(k) for k in ("result","big_small","tai_xiu","outcome","value","type","resultTruyenThong") if item.get(k) is not None),"")
            if not val and item.get("total") is not None:
                try: val="TAI" if int(item["total"])>10 else "XIU"
                except (TypeError,ValueError): pass
            if not val and isinstance(item.get("dices"),list) and len(item["dices"])>=3:
                try: val="TAI" if sum(map(int,item["dices"][:3]))>10 else "XIU"
                except (TypeError,ValueError): pass
            v=str(val).upper()
            side="T" if v in ("T","TAI","BIG","1","P") else "X" if v in ("X","XIU","SMALL","2","B") else ""
            if side:
                rows.append({"ma_phien":str(next((item.get(k) for k in ("id","session","session_id","round","code","number") if item.get(k) is not None),"")), "ket_qua":side})
        rows.reverse()
        CACHE.update(at=now,rows=rows,error=None)
    except Exception as e:
        CACHE["error"]=str(e)
        if not CACHE["rows"]: raise
    return CACHE["rows"]

@app.get("/")
def home(): return render_template_string(HTML)
@app.get("/health")
def health(): return jsonify(ok=True,app="lc79_hu")
@app.get("/api/status")
def status():
    try:
        rows=get_history()
        if len(rows)>=5:
            pred,_=du_doan_huy([x["ket_qua"] for x in rows])
        else: pred=None
        return jsonify(count=len(rows),history=rows[-100:],prediction=pred,updated=time.strftime("%H:%M:%S"),error=CACHE["error"])
    except Exception as e:
        return jsonify(count=0,history=[],prediction=None,error="Không lấy được API lịch sử: "+str(e)),200

if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT","10000")))
