#!/usr/bin/env python3
"""Build the external-annotator package: label-annotator.html + annotator_key_mapping.json.

Sources (never shipped to the annotator):
  - Set A: kit validation_set_answers.json (54, canonical) + 5 catch cases
  - Set B: label.html  DATA.our_disputed      (57, control-slice adjudication pool)
  - Set C: label2.html DATA.engine_disputed   (64, engine-side adjudication pool)

The annotator sees ONLY masked ids (a01.., b01.., c01..) and neutral set names.
Catch cases (3 obvious-CORRECT from Mem0 published answers not overlapping Set A,
2 obvious-WRONG built by cross-swapping answers) are recorded only in the mapping file.
"""
import json, os, re, random, html, sys, io
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The session labeling tools (label*.html) carry the author's set titles and
# are not part of this repository. Rebuilding the shipped artifacts
# (label-annotator.html + annotator_key_mapping.json) is a maintainer operation:
# point BENCH_LABELING_DIR at the directory holding label.html / label2.html /
# label3.html. Without it the script stops with a message.
LAB = Path(os.environ.get("BENCH_LABELING_DIR", ""))
if not os.environ.get("BENCH_LABELING_DIR"):
    raise SystemExit(
        "BENCH_LABELING_DIR is not set: the session labeling tools this builder reads are "
        "not part of the public repository; the shipped label-annotator.html and "
        "annotator_key_mapping.json are the artifacts of record."
    )
KIT = HERE.parents[1]

def extract_data(fname):
    s = (LAB / fname).read_text(encoding="utf-8")
    m = re.search(r"const DATA = (\{.*?\});\n", s, re.S)
    return json.loads(m.group(1))

validation = json.loads((KIT / "experiments/golden_judge/validation_set_answers.json").read_text(encoding="utf-8"))
lab1 = extract_data("label.html")
lab2 = extract_data("label2.html")
lab3 = extract_data("label3.html")

set_b_src = lab1["our_disputed"]["cases"]      # 57 control-slice disputed
set_c_src = lab2["engine_disputed"]["cases"]   # 64 engine-side disputed
audit_pool = lab3["mem0_audit"]["cases"]       # 90 Mem0 published (catch source)

assert len(validation) == 54 and len(set_b_src) == 57 and len(set_c_src) == 64

# ---- catch cases -------------------------------------------------------------
val_questions = {c["question"].strip().lower() for c in validation}

def norm(s): return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

# obvious-CORRECT: answer == gold (near-exact), question not in Set A
correct_pool = [c for c in audit_pool
                if c["question"].strip().lower() not in val_questions
                and norm(c["answer"]) == norm(c["gold"])
                and len(c["gold"]) >= 4]
random.seed(42)
random.shuffle(correct_pool)
catch_correct = correct_pool[:3]
if len(catch_correct) < 3:
    sys.exit(f"FATAL: only {len(catch_correct)} exact-match catch candidates")

# obvious-WRONG: take a question, swap in the gold of an unrelated case
swap_pool = [c for c in audit_pool
             if c["question"].strip().lower() not in val_questions
             and c not in catch_correct and len(c["gold"]) >= 4]
random.shuffle(swap_pool)

def looks_date(s):
    return bool(re.search(r"\b(19|20)\d\d\b|january|february|march|april|may|june|july|august|"
                          r"september|october|november|december", s.lower()))

# no swapped-in answer may collide with ANY text already visible in Set A
# (review finding: 'CS:GO' appeared in two catches at once -> links them)
seen_text = {norm(c["gold"]) for c in validation} | {norm(c["answer"]) for c in validation} \
          | {norm(c["gold"]) for c in catch_correct} | {norm(c["answer"]) for c in catch_correct}

catch_wrong, used = [], set()
for q_case in swap_pool:
    if len(catch_wrong) == 2:
        break
    if norm(q_case["gold"]) in seen_text:
        continue
    for a_case in swap_pool:
        if a_case is q_case or id(a_case) in used:
            continue
        # the swapped-in answer must be an obviously different KIND of fact
        if norm(a_case["gold"]) == norm(q_case["gold"]) or norm(a_case["gold"]) in seen_text:
            continue
        if looks_date(q_case["gold"]) or looks_date(a_case["gold"]):
            continue
        catch_wrong.append({
            "qid": f"catch_wrong_{len(catch_wrong)+1}(q:{q_case['qid']}|a-from:{a_case['qid']})",
            "category": q_case["category"],
            "question": q_case["question"],
            "gold": q_case["gold"],
            "answer": a_case["gold"],
        })
        used.add(id(q_case)); used.add(id(a_case))
        seen_text.add(norm(q_case["gold"])); seen_text.add(norm(a_case["gold"]))
        break
if len(catch_wrong) < 2:
    sys.exit("FATAL: could not build 2 obvious-wrong catch cases")

catch_cases = (
    [{**c, "qid": f"catch_correct_{i+1}({c['qid']})"} for i, c in enumerate(catch_correct)]
    + catch_wrong
)
print("=== CATCH CASES (eyeball these) ===")
for c in catch_cases:
    print(f"- {c['qid']}\n    Q: {c['question']}\n    gold: {c['gold']}\n    answer: {c['answer']}")

# ---- assemble ONE masked stream ----------------------------------------------
# Review BLOCKER: separate sets sized 59/57/64 let a paper-aware annotator map
# each set to its provenance (the paper prints 54/57/64). One shuffled stream of
# 180 with neutral ids kills that, interleaves B/C (anti-anchoring), and removes
# the fatigue-confound of C always coming last.
# Also: one category spelling everywhere ('single-hop' vs 'single_hop'
# fingerprinted provenance).
def unify_cat(c):
    return c.replace("_", "-")

stream_src = ([("set_a", c) for c in validation + catch_cases]
              + [("set_b", c) for c in set_b_src]
              + [("set_c", c) for c in set_c_src])
random.shuffle(stream_src)

cases_out, mapping = [], []
for disp_i, (src_set, c) in enumerate(stream_src, 1):
    mid = f"q{disp_i:03d}"
    cases_out.append({"qid": mid, "category": unify_cat(c["category"]),
                      "question": c["question"], "gold": c["gold"], "answer": c["answer"]})
    sqid = str(c["qid"])
    mapping.append({"masked_id": mid, "source_set": src_set, "source_qid": sqid,
                    "is_catch": sqid.startswith("catch_"),
                    "catch_expected": ("CORRECT" if sqid.startswith("catch_correct")
                                       else "WRONG" if sqid.startswith("catch_wrong") else None)})

DATA = {"cases": {"label": "All cases (180)", "cases": cases_out}}
mapping_doc = {
    "_note": "PRIVATE key for label-annotator.html. NEVER send to the annotator. "
             "One shuffled stream of 180 (random.seed(42)): set_a = OOS validation set "
             "(54) + 5 catch cases; set_b = control-slice adjudication pool (57); "
             "set_c = engine-side adjudication pool (64). Reconstruct sets at analysis "
             "time via source_set.",
    "cases": mapping,
}

# ---- HTML --------------------------------------------------------------------
CSS = (LAB / "label2.html").read_text(encoding="utf-8")
CSS = CSS[CSS.index("<style>") + 7: CSS.index("</style>")]

RUBRIC = ("Read <b>question &middot; gold &middot; answer</b>. Mark <b>CORRECT</b> if the answer conveys "
          "the right fact (paraphrase / partial / reordered is fine), <b>WRONG</b> if it's a "
          "different/incorrect/missing fact, <b>AMBIGUOUS</b> if genuinely unclear. Judge like a fair "
          "human &mdash; not a string matcher. Keys: <kbd>C</kbd> <kbd>W</kbd> <kbd>A</kbd>, "
          "<kbd>&larr;</kbd> <kbd>&rarr;</kbd>. Your work autosaves in this browser &mdash; use a "
          "normal window (not private/incognito) and the same browser throughout. You can download "
          "and send a partial JSON any time; send the final one when it shows 180 / 180.")

# One-click submission endpoint (submit-worker/). Empty = button hidden, annotators
# download JSON and send it back manually. After deploying the worker (gated), set
# to "https://<worker-host>/?k=<SUBMIT_KEY>" and rebuild.
SUBMIT_URL = ""

INTRO = """
  <div class="intro-card">
    <h2>Before you start <span style="font-weight:400;color:var(--muted);font-size:15px">(2 minutes, read once)</span></h2>
    <p>You are helping a research study on how well automated systems answer questions about long,
    multi-month text conversations between friends. The answer you grade will be consumed by an
    <b>assistant acting on it</b>: a good answer lets it interpret the situation correctly; a wrong or
    misleading one sends it the wrong way. Grade with that reader in mind.</p>
    <p><b>All conversations took place in 2023.</b> Relative time expressions (&ldquo;last summer&rdquo;,
    &ldquo;next month&rdquo;) count from the moment of the conversation, in 2023.</p>
    <p>Each case shows a <b>question</b>, a <b>gold answer</b> (our reference), and a <b>system answer</b>.
    Your job: does the system answer convey the fact named in the gold answer?</p>
    <ul>
      <li>The gold answer is your <b>only measure of truth</b>. You never need outside knowledge and
      cannot check the real world &mdash; don't try.</li>
      <li>More or less detail than the gold is fine: if the gold fact is conveyed and nothing
      contradicts it, it's <b>CORRECT</b>. Paraphrase, partial recall of a list, reordering &mdash; fine.
      You are not asked to verify details the gold doesn't mention.</li>
      <li>A different fact, a contradiction, or a missing fact &mdash; <b>WRONG</b>.</li>
      <li>Genuinely can't tell whether the gold fact is there? <b>AMBIGUOUS</b> &mdash; a full verdict,
      not a failure. Use it freely.</li>
      <li>Judge like a fair human reader, not a string matcher. There is no &ldquo;right&rdquo; share of
      CORRECT/WRONG &mdash; we don't know it ourselves.</li>
    </ul>
    <button id="ackbtn">I've read this and I'm ready &mdash; start grading</button>
    <div class="hint" style="margin-top:10px">You can reopen these instructions any time via the
    &ldquo;instructions&rdquo; link in the header.</div>
  </div>
"""

page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Answer Grading &mdash; human labeling</title>
<style>__CSS__
  #intro { position:fixed; inset:0; background:rgba(28,33,40,.55); z-index:100; overflow:auto; padding:30px 16px; }
  .intro-card { max-width:680px; margin:0 auto; background:var(--card); border-radius:14px; padding:26px 30px; box-shadow:0 8px 40px rgba(0,0,0,.25); }
  .intro-card h2 { margin:0 0 12px; }
  .intro-card p, .intro-card li { font-size:15px; line-height:1.55; }
  .intro-card ul { padding-left:20px; }
  #ackbtn { margin-top:14px; padding:12px 22px; font:inherit; font-weight:700; color:#fff; background:var(--green); border:none; border-radius:10px; cursor:pointer; }
</style>
</head>
<body>
<div id="intro" style="display:none">__INTRO__</div>
<header>
  <h1>Answer Grading &mdash; human labeling</h1>
  <div class="sub">__RUBRIC__ <a href="#" id="showintro">instructions</a></div>
  <div class="controls">
    <label>Annotator code: <input id="annid" style="width:110px;padding:6px 8px;border:1px solid var(--line);border-radius:8px;font:inherit" placeholder="e.g. R1"></label>
    <label>Set: <select id="dataset"></select></label>
    <div class="progress"><div class="bar"><div id="barfill"></div></div><div class="txt" id="progtxt"></div></div>
  </div>
</header>
<main id="main"></main>
<div class="footer">
  <button class="dl" id="dljson">Download JSON (this set)</button>
  <button id="dlcsv">Download CSV (this set)</button>
  <button id="subbtn" style="display:none;background:#1a5fb4;color:#fff;border-color:#1a5fb4">Submit results online</button>
  <span class="hint" id="savestate"></span>
  <button id="reset" style="margin-left:auto;color:#a00">Reset this set</button>
</div>
<script>
const DATA = __DATA__;
const VERDICTS = {C:"CORRECT", W:"WRONG", A:"AMBIGUOUS"};
let dsKey = Object.keys(DATA)[0];
let idx = 0;

/* storage helpers survive private-mode Safari (setItem throws there) */
let MEM = {};  /* in-memory fallback so the tool still works, just without persistence */
function lsGet(k){ try { const v = localStorage.getItem(k); return v!==null?v:(k in MEM?MEM[k]:null); } catch(e){ return k in MEM?MEM[k]:null; } }
function lsSet(k,v){ MEM[k]=v; try { localStorage.setItem(k,v); return true; } catch(e){ return false; } }
function lsDel(k){ delete MEM[k]; try { localStorage.removeItem(k); } catch(e){} }
let STORAGE_OK = lsSet('ext1_probe','1');
function storeKey(k){ return "ext1_labels_" + k; }
function loadLabels(k){ try { return JSON.parse(lsGet(storeKey(k))) || {}; } catch(e){ return {}; } }
function saveLabels(k, obj){ lsSet(storeKey(k), JSON.stringify(obj)); }
/* intro / instructions acknowledgment (v2: agent-frame + 2023 + gold-only standard) */
const INSTR_VERSION = 'v2-2026-07-05';
function ackGet(){ try { return JSON.parse(lsGet('ext1_ack')) || null; } catch(e){ return null; } }
function introShow(){ document.getElementById('intro').style.display='block'; }
function introHide(){ document.getElementById('intro').style.display='none'; }
if(!ackGet()) introShow();
document.getElementById('ackbtn').onclick = ()=>{
  if(!ackGet()) lsSet('ext1_ack', JSON.stringify({version:INSTR_VERSION, ts:Date.now()}));
  introHide();
  if(!STORAGE_OK) alert("Heads up: this browser blocks saving (private/incognito mode?). The tool works, but progress will be LOST if you close the tab. Please switch to a normal window, or finish and download the JSON in one sitting.");
};
document.getElementById('showintro').onclick = (e)=>{ e.preventDefault(); introShow(); };

const annBox = document.getElementById('annid');
annBox.value = lsGet('ext1_annid') || '';
annBox.addEventListener('input', ()=>lsSet('ext1_annid', annBox.value.trim()));
function annId(){
  let v = annBox.value.trim();
  if(!v){
    v = (prompt("Please enter your annotator code (it was in the email you received):") || "").trim();
    if(v){ annBox.value = v; lsSet('ext1_annid', v); }
  }
  return v || 'unknown';
}

function esc(s){ const d=document.createElement('div'); d.textContent=(s==null?'':String(s)); return d.innerHTML; }

function render(){
  const ds = DATA[dsKey], cases = ds.cases, labels = loadLabels(dsKey);
  const done = cases.filter(c => labels[c.qid] && labels[c.qid].verdict).length;
  document.getElementById('barfill').style.width = (100*done/cases.length).toFixed(1)+'%';
  document.getElementById('progtxt').textContent = done+" / "+cases.length+" labeled";
  document.getElementById('savestate').textContent = (STORAGE_OK?"Autosaved in this browser. ":"NOT SAVED (private mode?) - finish in one sitting. ")+done+"/"+cases.length+" done in this set.";
  const main = document.getElementById('main');
  if(idx<0) idx=0; if(idx>=cases.length) idx=cases.length-1;
  const c = cases[idx];
  const cur = labels[c.qid] || {};
  main.innerHTML = `
    <div class="card">
      <span class="badge">${esc(c.category)}</span>
      <div class="field question"><div class="k">Question</div><div class="v">${esc(c.question)}</div></div>
      <div class="field gold"><div class="k">Gold answer</div><div class="v">${esc(c.gold)}</div></div>
      <div class="field answer"><div class="k">System answer (judge this)</div><div class="v">${esc(c.answer)}</div></div>
      <div class="verdict">
        <button class="v-correct ${cur.verdict==='CORRECT'?'on':''}" data-v="C">CORRECT</button>
        <button class="v-wrong ${cur.verdict==='WRONG'?'on':''}" data-v="W">WRONG</button>
        <button class="v-amb ${cur.verdict==='AMBIGUOUS'?'on':''}" data-v="A">AMBIGUOUS</button>
      </div>
      <input class="note" id="note" placeholder="optional note" value="${esc(cur.note||'')}">
      <div class="nav">
        <button id="prev">&larr; Prev</button>
        <span class="idx">case ${idx+1} of ${cases.length} &middot; id ${esc(c.qid)}</span>
        <button id="next">Next &rarr;</button>
      </div>
    </div>`;
  main.querySelectorAll('.verdict button').forEach(b=>b.onclick=()=>setVerdict(b.dataset.v));
  document.getElementById('prev').onclick=()=>{ idx--; render(); };
  document.getElementById('next').onclick=()=>{ idx++; render(); };
  document.getElementById('note').onblur=(e)=>{ const l=loadLabels(dsKey); l[c.qid]=Object.assign({},l[c.qid],{note:e.target.value}); saveLabels(dsKey,l); };
}

function setVerdict(vk){
  const ds=DATA[dsKey], c=ds.cases[idx], l=loadLabels(dsKey);
  const note=document.getElementById('note'); const noteVal=note?note.value:'';
  const firstTs=(l[c.qid]&&l[c.qid].first_ts)||Date.now();
  l[c.qid]=Object.assign({},l[c.qid],{verdict:VERDICTS[vk], note:noteVal, ts:Date.now(), first_ts:firstTs});
  saveLabels(dsKey,l);
  if(idx < ds.cases.length-1){ idx++; }
  render();
}

function buildSelect(){
  const sel=document.getElementById('dataset'); sel.innerHTML='';
  for(const k in DATA){ const o=document.createElement('option'); o.value=k; o.textContent=DATA[k].label; sel.appendChild(o); }
  sel.value=dsKey;
  sel.onchange=()=>{ dsKey=sel.value; idx=0; render(); };
}

function download(filename, text, type){
  const b=new Blob([text],{type}); const u=URL.createObjectURL(b); const a=document.createElement('a');
  a.href=u; a.download=filename; a.click(); URL.revokeObjectURL(u);
}
const SUBMIT_URL = "__SUBMIT_URL__";
function exportObj(){
  const l=loadLabels(dsKey);
  return {annotator:annId(), set:dsKey, exported:new Date().toISOString(), instructions_ack:ackGet(),
    labels: DATA[dsKey].cases.map(c=>({id:c.qid,category:c.category,verdict:(l[c.qid]||{}).verdict||'',note:(l[c.qid]||{}).note||'',ts:(l[c.qid]||{}).ts||null,first_ts:(l[c.qid]||{}).first_ts||null}))};
}
document.getElementById('dljson').onclick=()=>{
  download(dsKey+"_"+annId()+"_labels.json", JSON.stringify(exportObj(),null,2), "application/json");
};
if(SUBMIT_URL){
  const b=document.getElementById('subbtn');
  b.style.display='inline-block';
  b.onclick=async()=>{
    b.disabled=true; b.textContent='Submitting…';
    try{
      const r=await fetch(SUBMIT_URL,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(exportObj())});
      const j=await r.json();
      b.textContent=j.ok?('Submitted ✓ ('+j.received+' verdicts)'):'Failed — use Download JSON';
    }catch(e){ b.textContent='Failed — use Download JSON and send it back'; }
    setTimeout(()=>{ b.disabled=false; }, 4000);
  };
}
document.getElementById('dlcsv').onclick=()=>{
  const l=loadLabels(dsKey);
  const rows=[["id","category","verdict","note","ts","annotator"]];
  DATA[dsKey].cases.forEach(c=>{ const x=l[c.qid]||{}; rows.push([c.qid,c.category,x.verdict||'',(x.note||'').replace(/"/g,'""'),x.ts||'',annId()]); });
  const csv=rows.map(r=>r.map(v=>/[",\\n]/.test(String(v))?'"'+v+'"':v).join(",")).join("\\n");
  download(dsKey+"_"+annId()+"_labels.csv", "\\ufeff"+csv, "text/csv");
};
document.getElementById('reset').onclick=()=>{ if(confirm("Clear your labels for this set?")){ lsDel(storeKey(dsKey)); idx=0; render(); } };

document.addEventListener('keydown',(e)=>{
  if(e.target.tagName==='INPUT'||e.target.tagName==='SELECT') return;
  if(e.ctrlKey||e.metaKey||e.altKey) return; /* Ctrl+C = copy, never a verdict */
  const k=e.key.toUpperCase();
  if(k==='C')setVerdict('C'); else if(k==='W')setVerdict('W'); else if(k==='A')setVerdict('A');
  else if(e.key==='ArrowLeft'){ idx--; render(); } else if(e.key==='ArrowRight'){ idx++; render(); }
});

buildSelect(); render();
</script>
</body>
</html>
"""
page = page.replace("__CSS__", CSS).replace("__RUBRIC__", RUBRIC).replace("__INTRO__", INTRO).replace("__SUBMIT_URL__", SUBMIT_URL).replace("__DATA__", json.dumps(DATA, ensure_ascii=False))

# leak self-check BEFORE writing; word-bounded patterns to avoid 'catch the eye' noise
leaks = [bad for bad in [r"mnemoverse", r"\bmem0\b", r"\blocomo\b", r"\bgolden\b", r"\bdisputed\b",
                         r"judge the judge", r"\bvalidation\b", r"catch_", r"\bjtj"]
         if re.search(bad, page, re.I)]
if leaks:
    sys.exit(f"FATAL: leak markers in shipped HTML: {leaks} — NOT writing files")

(HERE / "label-annotator.html").write_text(page, encoding="utf-8", newline="\n")
(HERE / "annotator_key_mapping.json").write_text(json.dumps(mapping_doc, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

total = len(cases_out)
by_set = {s: sum(1 for m in mapping if m["source_set"] == s) for s in ("set_a", "set_b", "set_c")}
print(f"\nOK: label-annotator.html (ONE stream, {total} cases; composition {by_set}) + annotator_key_mapping.json; leak check clean")
