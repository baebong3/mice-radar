"""메인 페이지(docs/index.html) 생성 - 헤드라인 · 주요 뉴스 · 주제별 동향

사용: python3 radar/build.py --days 7

같은 사안을 여러 매체가 보도한 경우 제목 유사도로 묶어 1건으로 보여주고(○○ 外 N개 매체),
주제 가중치 · 보도 매체 수 · 최신성으로 헤드라인과 주요 뉴스를 고른다. 외부 패키지·CDN 없음.
"""
import argparse
import base64
import html
import os
import re
import sys
from collections import Counter
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from common import CATEGORIES, DOCS, TRACKS, connect, list_briefings, now_kst  # noqa: E402

WD = "월화수목금토일"
WEIGHT = {"리스크·쟁점": 6, "정책·예산": 5, "발주처": 5, "유치·개최": 4, "통계·실적": 3.5,
          "지자체·시설": 3, "해외·경쟁국": 2.5, "산업 동향": 2.5, "전시회 개최·참가": 0.5, "기타": 0}
COLOR = {"리스크·쟁점": "#D9472B", "정책·예산": "#E3A51C", "발주처": "#E0457B", "유치·개최": "#1D3FA6",
         "통계·실적": "#1A8A4A", "해외·경쟁국": "#7A4BD6", "지자체·시설": "#0AA39A", "산업 동향": "#B07C00",
         "전시회 개최·참가": "#7B8197", "기타": "#9aa0b5"}
DESC = {"리스크·쟁점": "국정감사 · 적자 · 무산 · 예산 삭감 등", "정책·예산": "정부 · 국회 · 지자체 제도와 예산",
        "발주처": "한국관광공사 · 코리아MICE뷰로", "유치·개최": "국제회의 · 기업회의 유치와 개최",
        "통계·실적": "참가자 · 경제효과 · 순위 · 폐막 실적", "해외·경쟁국": "해외 MICE 시장과 경쟁 도시",
        "지자체·시설": "컨벤션센터 건립 · 확장 · 운영", "산업 동향": "MICE 산업 전반 · 비즈니스 관광",
        "전시회 개최·참가": "개별 전시회 개막 · 기업 참가 안내"}
TRACK_TAG = {"MICE 유치": "유치", "전시·컨벤션": "전시"}


# ---------------------------------------------------------------------------
# 디자인: 서던포스트 「The Gauge 기준」 손그림판을 한국관광공사 과업용으로 옮긴 것
#  - 제호: 네이비 띠 + 손글씨(Permanent Marker · Nanum Brush Script), 노란 밑줄 낙서
#  - 본문: Pretendard, 제목·라벨 Jua(작은 손글씨도 또렷하게), 숫자 tabular
#  - 상자 테두리·막대는 rough.js로 손으로 그린 선처럼 (docs/assets/rough.min.js)
#  - 둥근 그림자·그라데이션 없음. 흰 바탕 고정
# ---------------------------------------------------------------------------
FONT_LINKS = """<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jua&family=Nanum+Brush+Script&family=Permanent+Marker&display=swap">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">"""

CSS = """
:root{color-scheme:light;--paper:#fff;--ink:#2b2f45;--navy:#16193A;--sub:#3f455c;--mute:#646a80;--rule:#d9dbe6;--wash:#f5f6fa;--cream:#FFF6E5;--yel:#FFC845;--red:#D9472B;
--f-body:"Pretendard","Noto Sans KR","Apple SD Gothic Neo","Malgun Gothic",sans-serif;--f-title:"Jua","Noto Sans KR",sans-serif;--f-hand:"Jua","Noto Sans KR",sans-serif;--f-mark:"Permanent Marker","Jua",cursive;--f-brush:"Nanum Brush Script","Jua",cursive}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--f-body);font-size:15px;line-height:1.6;word-break:keep-all;overflow-wrap:break-word;-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
a{color:inherit;text-decoration:none}a:hover .tt,a.tt:hover{text-decoration:underline;text-underline-offset:3px;text-decoration-thickness:2px;text-decoration-color:var(--yel)}
.wrap{max-width:1120px;margin:0 auto;padding:14px 20px 40px}
.sk{position:relative}.sk-frame{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;overflow:visible;z-index:0}.sk>*:not(.sk-frame){position:relative;z-index:1}
.sk-rule{display:block;width:100%;height:14px}
/* 상단 기관 띠 */
.org{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;padding:4px 2px 10px}
.org .l{display:flex;align-items:center;gap:14px}.kto{display:block;width:118px;height:40px;background:url(KTO_URI) left center/contain no-repeat}
.org .vl{width:1px;height:30px;background:var(--rule)}.org .cap{font-family:var(--f-hand);font-size:18px;color:var(--sub);line-height:1.25}.org .cap small{display:block;font-family:var(--f-body);font-size:13.5px;font-weight:500;color:var(--mute);margin-top:2px}
.org .r{display:flex;align-items:center;gap:10px;font-family:var(--f-hand);font-size:15.5px;color:var(--sub)}.sp{display:block;width:104px;height:24px;background:url(SP_URI) right center/contain no-repeat}
/* 손글씨 제호 */
.mast{position:relative;background:var(--navy);color:var(--cream);border-radius:22px 30px 20px 28px/28px 20px 30px 22px;padding:16px 26px 32px;overflow:hidden}
.mast::after{content:"";position:absolute;left:0;right:0;bottom:0;height:16px;background:repeating-linear-gradient(90deg,rgba(255,246,229,.55) 0 2px,transparent 2px 12px),repeating-linear-gradient(90deg,rgba(255,200,69,.95) 0 3px,transparent 3px 60px);background-size:auto 9px,auto 16px;background-repeat:repeat-x;background-position:0 100%,0 100%;filter:url(#rough-f)}
.m-top{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;font-family:var(--f-hand);font-size:17px;color:rgba(255,246,229,.82);border-bottom:2px dashed rgba(255,246,229,.3);padding-bottom:8px}
.m-kick{font-family:var(--f-mark);font-weight:400;font-size:16px;letter-spacing:.08em;color:var(--yel);transform:rotate(-1.5deg);display:inline-block}
.m-top b{color:var(--cream)}
.m-main{display:flex;align-items:center;justify-content:center;gap:26px;margin:14px 0 4px;flex-wrap:wrap}
.m-radar{width:clamp(96px,12vw,140px);height:auto;flex:none;filter:url(#rough-f);transform:rotate(-3deg)}
.m-word{display:flex;align-items:center;gap:20px}
.m-en{position:relative;margin:0;font-family:var(--f-mark);font-weight:400;font-size:clamp(54px,9vw,104px);line-height:.95;letter-spacing:.01em;color:var(--cream);transform:rotate(-2.5deg);padding-bottom:.12em}
.m-en small{font-size:.24em;letter-spacing:.06em;margin:.3em .25em 0 0;color:var(--yel);writing-mode:vertical-rl;transform:rotate(180deg);display:inline-block;vertical-align:top}
.m-scribble{position:absolute;left:4%;bottom:-.04em;width:96%;height:.16em;overflow:visible}
.m-ko{position:relative;transform:rotate(2deg);padding-left:16px}
.m-ko::before{content:"";position:absolute;left:0;top:6%;bottom:6%;width:4px;border-radius:3px;background:var(--yel);transform:rotate(-3deg);filter:url(#rough-f)}
.m-ko b{display:block;font-family:var(--f-brush);font-weight:400;font-size:clamp(56px,8vw,92px);line-height:.9;color:var(--cream)}
.m-ko span{display:block;font-family:var(--f-hand);font-size:clamp(17px,2vw,21px);letter-spacing:.06em;color:var(--yel);margin-top:4px}
.m-tag{text-align:center;margin:8px 0 14px;font-family:var(--f-title);font-size:17px;line-height:1.45;color:rgba(255,246,229,.9)}
.chips{position:relative;z-index:1;display:flex;flex-wrap:wrap;gap:8px;justify-content:center}
.chips a,.chips button{font:inherit;font-family:var(--f-title);font-size:15.5px;line-height:1.3;color:#fff;padding:6px 14px;border:0;cursor:pointer;border-radius:255px 15px 225px 15px/15px 225px 15px 255px;box-shadow:0 0 0 2px rgba(255,246,229,.18)}
.chips>*:nth-child(odd){transform:rotate(-1.5deg)}.chips>*:nth-child(even){transform:rotate(1.2deg)}
.chips button{background:transparent;color:var(--cream);box-shadow:0 0 0 2px rgba(255,246,229,.55)}.chips button.on{background:var(--yel);color:var(--navy);box-shadow:none}
.chips .sep{width:1px;background:rgba(255,246,229,.3);margin:0 4px;transform:none}
/* 숫자 띠 */
.numbers{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin:22px 0 6px}
.nb{padding:14px 14px 12px;display:flex;flex-direction:column;gap:4px;min-width:0}
.nb .desk{font-family:var(--f-title);font-size:17px;color:var(--sub)}.nb .big{font-weight:800;font-size:clamp(24px,2.6vw,32px);line-height:1.1;letter-spacing:-.02em}.nb .big small{font-size:.5em;font-weight:700;margin-left:2px}
.nb .what{font-size:14.5px;color:var(--ink)}.nb .src{font-size:13px;color:var(--mute);margin-top:auto}
.numbers-cap{color:var(--sub);margin:0 0 22px;font-family:var(--f-hand);font-size:15.5px}
/* 1면 톱 */
.top{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);gap:28px;padding-bottom:22px}
.kicker{display:inline-block;font-family:var(--f-title);font-size:15px;padding:3px 10px;border-radius:4px;color:#fff;margin-right:6px;vertical-align:2px}
.kicker.o{background:transparent;color:var(--sub);box-shadow:inset 0 0 0 1.5px var(--rule)}
.top h2{font-family:var(--f-title);font-weight:400;font-size:clamp(30px,4.6vw,50px);line-height:1.2;margin:12px 0 10px;text-wrap:balance}
.top .src{font-size:14px;color:var(--mute)}.top .src b{color:var(--sub)}
ul.pts{margin:14px 0 0;padding:0;list-style:none;display:grid;gap:7px}
ul.pts li{padding-left:18px;position:relative;font-size:14.5px;display:flex;gap:8px;min-width:0}
ul.pts li::before{content:"";position:absolute;left:2px;top:.6em;width:7px;height:7px;border-radius:2px;background:var(--dot,var(--ink))}
ul.pts li span{color:var(--mute);white-space:nowrap;font-size:13px;flex:none}ul.pts li a{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.side h3{font-family:var(--f-title);font-weight:400;font-size:19px;margin:0 0 10px}
.chart{display:grid;gap:9px}.bar-row{display:grid;grid-template-columns:136px minmax(0,1fr);align-items:center;gap:10px}
.bar-row .lab{font-family:var(--f-hand);font-size:16.5px;white-space:nowrap;text-align:right}.bar-row .lab i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:6px;vertical-align:0}
.bar-track{position:relative;height:28px}.bar{height:100%;display:flex;align-items:center;justify-content:flex-end;padding-right:6px;font-weight:800;font-size:14px;min-width:44px;position:relative}
.sk-lbl{position:relative;z-index:1;background:rgba(255,255,255,.92);border-radius:3px;padding:0 5px;line-height:1.3}
.bar svg.sk-bar{position:absolute;left:0;top:0;width:100%;height:100%;overflow:visible;pointer-events:none}
.chart-note{font-size:13.5px;color:var(--mute);margin-top:10px;line-height:1.55}
/* 섹션 */
.sec{padding:26px 0 0}.sec-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.sec-head h2{font-family:var(--f-title);font-weight:400;font-size:32px;margin:0;line-height:1}.sec-head .meta{font-family:var(--f-hand);font-size:17px;color:var(--sub)}
.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.card{padding:16px 16px 14px;display:flex;flex-direction:column;gap:8px;min-width:0}
.card .tt{font-family:var(--f-title);font-weight:400;font-size:19px;line-height:1.35;flex:1}.card .src{font-size:13.5px;color:var(--mute)}.card .src b{color:var(--sub)}
.tag{display:inline-block;font-family:var(--f-title);font-size:14px;padding:2px 8px;border-radius:4px;color:#fff;margin-right:5px;vertical-align:1px}
.tag.o{background:transparent;color:var(--sub);box-shadow:inset 0 0 0 1.5px var(--rule)}
/* 데스크(주제) 구획 */
.desk-sec{padding:26px 0 8px;scroll-margin-top:12px}
.desk-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.desk-head h2{font-family:var(--f-title);font-weight:400;font-size:30px;margin:0;line-height:1}.desk-head .meta{font-family:var(--f-hand);font-size:17px;color:var(--sub)}.desk-head .meta b{color:var(--ink)}
.grid{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:22px;align-items:start}
.lead-card{padding:20px 22px;border-radius:12px}
.lead-card h3{font-family:var(--f-title);font-weight:400;font-size:24px;line-height:1.35;margin:10px 0 8px;text-wrap:balance}
.lead-card .src{font-size:14px;color:var(--mute)}.lead-card .src b{color:var(--sub)}
.lead-card ul.pts{margin-top:12px}
.briefs{display:grid;align-content:start}
.brief{padding:11px 0;border-top:2px dashed var(--rule)}.brief:first-child{border-top:0;padding-top:2px}
.brief h4{font-family:var(--f-title);font-weight:400;font-size:17.5px;line-height:1.4;margin:0 0 3px}
.brief .src{font-size:13.5px;color:var(--mute)}.brief .src b{color:var(--sub)}.brief .src .many{color:var(--red);font-weight:700}
.two .briefs{grid-template-columns:repeat(2,minmax(0,1fr));column-gap:28px}.two .brief:nth-child(2){border-top:0;padding-top:2px}
details.more{margin-top:6px}details.more summary{cursor:pointer;font-family:var(--f-hand);font-size:16.5px;color:var(--sub);list-style:none;padding:6px 0}
details.more summary::before{content:"+ ";color:var(--red)}details.more[open] summary::before{content:"- "}
.empty{font-family:var(--f-hand);font-size:16.5px;color:var(--mute);padding:8px 0}
.etc{margin-top:22px;padding:14px 18px;background:var(--wash);border-radius:10px}.etc summary{cursor:pointer;font-family:var(--f-hand);font-size:16.5px;color:var(--sub);list-style:none}.etc summary::before{content:"+ ";color:var(--red)}.etc[open] summary::before{content:"- "}
.etc ul{list-style:none;margin:10px 0 0;padding:0;columns:2;column-gap:28px}.etc li{font-size:13px;padding:3px 0;break-inside:avoid;color:var(--sub)}.etc li span{color:var(--mute)}
/* 푸터 */
.foot{margin-top:26px;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:20px;align-items:end;font-size:13.5px;color:var(--mute);line-height:1.7}
.foot b{color:var(--ink)}.foot .r{display:flex;align-items:center;gap:10px;font-family:var(--f-hand);font-size:15.5px;color:var(--sub)}
body.f-유치 [data-tr]:not([data-tr~="유치"]),body.f-전시 [data-tr]:not([data-tr~="전시"]){display:none}
@media (max-width:900px){.numbers{grid-template-columns:repeat(2,minmax(0,1fr))}.nb:first-child{grid-column:1/-1}.top,.grid{grid-template-columns:minmax(0,1fr)}.cards{grid-template-columns:repeat(2,minmax(0,1fr))}.two .briefs{grid-template-columns:minmax(0,1fr)}.two .brief:nth-child(2){border-top:2px dashed var(--rule);padding-top:11px}}
@media (max-width:640px){.wrap{padding:10px 14px 34px}.mast{padding:12px 14px 28px;border-radius:20px}.m-top{font-size:14px;justify-content:center;text-align:center}.m-main{flex-direction:column;gap:4px;margin-top:10px}.m-radar{width:96px}.m-word{flex-direction:column;gap:6px}.m-en{font-size:clamp(50px,15vw,72px)}.m-ko{transform:rotate(-1deg);padding-left:0;text-align:center}.m-ko::before{display:none}.m-ko b{font-size:56px}.m-tag{font-size:15px}.chips a,.chips button{font-size:14px;padding:5px 11px}.cards{grid-template-columns:minmax(0,1fr)}.org .cap{display:none}.kto{width:100px;height:34px}.foot{grid-template-columns:minmax(0,1fr)}.etc ul{columns:1}.top h2{font-size:28px}.desk-head h2,.sec-head h2{font-size:27px}}
"""

RADAR_SVG = """<svg class="m-radar" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 120" aria-hidden="true">
<path d="M14 108 A86 86 0 0 1 186 108" stroke="#FFC845" stroke-width="3" fill="none" stroke-linecap="round"/>
<path d="M42 108 A58 58 0 0 1 158 108" stroke="#FFF6E5" stroke-width="2.2" fill="none" opacity=".75" stroke-linecap="round"/>
<path d="M70 108 A30 30 0 0 1 130 108" stroke="#FFF6E5" stroke-width="2" fill="none" opacity=".6" stroke-linecap="round"/>
<line x1="100" y1="108" x2="100" y2="22" stroke="#FFF6E5" stroke-width="1.4" opacity=".4"/><line x1="100" y1="108" x2="39" y2="47" stroke="#FFF6E5" stroke-width="1.4" opacity=".4"/><line x1="100" y1="108" x2="161" y2="47" stroke="#FFF6E5" stroke-width="1.4" opacity=".4"/>
<line x1="100" y1="108" x2="154" y2="36" stroke="#FFC845" stroke-width="5" stroke-linecap="round"/>
<circle cx="100" cy="108" r="7" fill="#FFC845"/>
<circle cx="66" cy="60" r="6" fill="#D9472B"/><circle cx="128" cy="78" r="5.5" fill="#E478A8"/><circle cx="118" cy="40" r="5" fill="#2FB7A0"/><circle cx="48" cy="92" r="4.5" fill="#FFF6E5"/>
</svg>"""

SCRIBBLE = """<svg class="m-scribble" viewBox="0 0 300 14" preserveAspectRatio="none" aria-hidden="true"><path d="M3 9 C60 3 120 12 180 6 S270 4 297 8" stroke="#FFC845" stroke-width="4.5" fill="none" stroke-linecap="round"/><path d="M40 12 C110 8 190 13 262 9" stroke="#FFC845" stroke-width="2.2" fill="none" stroke-linecap="round" opacity=".7"/></svg>"""

ROUGH_DEFS = """<svg width="0" height="0" aria-hidden="true" style="position:absolute"><filter id="rough-f"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="7"/><feDisplacementMap in="SourceGraphic" scale="3.2"/></filter></svg>"""

JS = """
document.querySelectorAll('.chips button').forEach(function(b){b.addEventListener('click',function(){
document.querySelectorAll('.chips button').forEach(function(x){x.classList.toggle('on',x===b)});
document.body.className=b.dataset.f?'f-'+b.dataset.f:'';if(window.skRerun)window.skRerun();});});
(function(){
  if(!window.rough) return;
  var SEED=11, INK='#3a3f55';
  function sketchBar(el,i){
    var old=el.querySelector('svg.sk-bar'); if(old) old.remove();
    var w=el.clientWidth, h=el.clientHeight; if(!w||!h) return;
    var bg=el.dataset.skColor;
    if(!bg){ bg=getComputedStyle(el).backgroundColor; if(!bg||bg==='rgba(0, 0, 0, 0)'||bg==='transparent') bg='#888'; el.dataset.skColor=bg; el.style.setProperty('background','transparent','important');
      Array.prototype.slice.call(el.childNodes).forEach(function(nd){ if(nd.nodeType===3 && nd.textContent.trim()){ var sp=document.createElement('span'); sp.className='sk-lbl'; sp.textContent=nd.textContent.trim(); el.replaceChild(sp,nd); } }); }
    var svg=document.createElementNS('http://www.w3.org/2000/svg','svg'); svg.setAttribute('class','sk-bar'); svg.setAttribute('viewBox','0 0 '+w+' '+h);
    var rc=rough.svg(svg);
    svg.appendChild(rc.rectangle(1.5,1.5,w-3,h-3,{fill:bg,fillStyle:'hachure',hachureAngle:-45+(i%6)*6,hachureGap:Math.max(5,h/4.2),fillWeight:Math.max(1,h/14),stroke:INK,strokeWidth:1.3,roughness:1.7,bowing:1,seed:SEED+i}));
    el.insertBefore(svg,el.firstChild);
  }
  function frame(el,i){
    var old=el.querySelector(':scope > svg.sk-frame'); if(old) old.remove();
    var w=el.offsetWidth, h=el.offsetHeight; if(!w||!h) return;
    var svg=document.createElementNS('http://www.w3.org/2000/svg','svg'); svg.setAttribute('class','sk-frame'); svg.setAttribute('viewBox','0 0 '+w+' '+h);
    var rc=rough.svg(svg);
    svg.appendChild(rc.rectangle(2,2,w-4,h-4,{stroke:el.dataset.skStroke||INK,strokeWidth:1.2,roughness:1.3,bowing:1.4,fill:'none',seed:SEED+i}));
    el.insertBefore(svg,el.firstChild);
  }
  function rule(el,i){
    var old=el.querySelector(':scope > svg.sk-rule'); if(old) old.remove();
    var w=el.clientWidth; var svg=document.createElementNS('http://www.w3.org/2000/svg','svg'); svg.setAttribute('class','sk-rule'); svg.setAttribute('viewBox','0 0 '+w+' 14');
    var rc=rough.svg(svg); svg.appendChild(rc.line(2,7,w-2,7,{stroke:INK,strokeWidth:2.2,roughness:1.6,bowing:1,seed:SEED+i}));
    el.appendChild(svg);
  }
  function run(){
    document.querySelectorAll('.bar').forEach(sketchBar);
    document.querySelectorAll('.sk').forEach(frame);
    document.querySelectorAll('.rule-after').forEach(rule);
  }
  var t; window.skRerun=function(){ clearTimeout(t); t=setTimeout(run,150); };
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',run); else run();
  if(document.fonts && document.fonts.ready) document.fonts.ready.then(window.skRerun);
  window.addEventListener('resize',window.skRerun);
})();
"""


def data_uri(name):
    """docs/assets/<name>을 base64 data URI로 (없으면 빈 문자열)"""
    p = os.path.join(DOCS, "assets", name)
    if not os.path.exists(p):
        return ""
    with open(p, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def esc(s):
    return html.escape(s or "", quote=True)


def clean_title(t, media):
    t = (t or "").strip()
    while media and t.endswith(" - " + media):
        t = t[: -len(" - " + media)].strip()
    return re.sub(r"\s+", " ", t)


MAJOR = ["연합뉴스", "뉴스1", "뉴시스", "KBS", "MBC", "SBS", "YTN", "한국경제", "매일경제", "서울경제", "머니투데이",
         "조선일보", "중앙일보", "동아일보", "한겨레", "경향신문", "한국일보", "아시아경제", "파이낸셜뉴스", "이데일리", "헤럴드경제", "아주경제", "국민일보", "세계일보"]


def grams(t):
    s = re.sub(r"[\s\W_]+", "", t.lower())
    return {s[i:i + 2] for i in range(len(s) - 1)}


def toks(t):
    t = re.sub(r"\[[^\]]*\]", " ", t)
    return {w for w in re.findall(r"[가-힣A-Za-z0-9]+", t) if len(w) >= 2}


def same_story(a, b):
    """bigram 겹침 계수 0.45 이상 또는 2글자 이상 단어 4개 이상 공유"""
    inter = len(a["g"] & b["g"])
    if inter / (min(len(a["g"]), len(b["g"])) or 1) >= 0.45:
        return True
    return len(a["t"] & b["t"]) >= 4


def cluster(rows):
    """같은 사안 묶기: 보도일 2일 이내 + 그룹 안 아무 기사와 same_story (최대 12건과 비교)"""
    groups = []
    for r in rows:
        r["g"], r["t"] = grams(r["title"]), toks(r["title"])
        d = date.fromisoformat(r["date"])
        hit = None
        for c in groups:
            if abs((c["d"] - d).days) > 2:
                continue
            if any(same_story(r, m) for m in c["items"][:12]):
                hit = c
                break
        if hit:
            hit["items"].append(r)
        else:
            groups.append({"items": [r], "d": d})
    out = []
    for c in groups:
        its = c["items"]
        cats = Counter(i["category"] for i in its if i["category"] != "기타")
        if cats:
            top = max(cats.values())
            cat = min((k for k, v in cats.items() if v == top), key=lambda k: CATEGORIES.index(k))
        else:
            cat = "기타"
        medias = []
        for i in its:
            if i["media"] and i["media"] not in medias:
                medias.append(i["media"])
        rep = sorted(its, key=lambda i: (i["media"] not in MAJOR, len(i["title"]) < 14, abs(len(i["title"]) - 34)))[0]
        out.append({
            "title": rep["title"], "url": rep["url"], "media": rep["media"] or (medias[0] if medias else ""),
            "n": max(len(medias), 1), "date": max(i["date"] for i in its), "cat": cat,
            "tracks": sorted({TRACK_TAG.get(i["track"], "") for i in its} - {""}),
            "items": its,
        })
    return out


def score(c, latest):
    age = (latest - date.fromisoformat(c["date"])).days
    return WEIGHT.get(c["cat"], 0) * 2 + min(c["n"], 10) * 1.2 - age * 2


def mdate(d):
    return f"{int(d[5:7])}.{int(d[8:10])}"


def src_line(c, cls="src"):
    more = f" 外 {c['n'] - 1}개 매체" if c["n"] > 1 else ""
    return f'<span class="{cls}"><b>{esc(c["media"])}</b>{more} · {mdate(c["date"])}</span>'


def tags(c):
    return "".join(f'<span class="tg">{t}</span>' for t in c["tracks"])


def chip(cat):
    return f'<span class="chip" style="background:{COLOR.get(cat, "#A6A3A1")}">{esc(cat)}</span>'


def dtr(c):
    return f' data-tr="{" ".join(c["tracks"])}"'


def item_li(c):
    more = f'<span class="many">外 {c["n"] - 1}개 매체</span>' if c["n"] > 1 else ""
    return (f'<li{dtr(c)}><a class="tt" href="{esc(c["url"])}" target="_blank" rel="noopener">{esc(c["title"])}</a>'
            f'<div class="m"><span>{esc(c["media"])}</span>{more}<span>· {mdate(c["date"])}</span>{tags(c)}</div></li>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    a = ap.parse_args()

    con = connect()
    now = now_kst()
    since = (now - timedelta(days=a.days - 1)).strftime("%Y-%m-%d")
    raw = con.execute(
        "select url,track,title,media,date,category from news where date>=? and date<=? "
        "order by date desc, collected_at desc", (since, now.strftime("%Y-%m-%d"))).fetchall()
    total, last = con.execute("select count(*), max(collected_at) from news").fetchone()
    today_new = con.execute("select count(*) from news where substr(collected_at,1,10)=?",
                            (now.strftime("%Y-%m-%d"),)).fetchone()[0]
    briefs = list_briefings()

    rows = [{"url": u, "track": t, "title": clean_title(ti, m), "media": m or "", "date": d, "category": c or "기타"}
            for u, t, ti, m, d, c in raw if d]
    clusters = cluster(rows)
    latest = max((date.fromisoformat(c["date"]) for c in clusters), default=now.date())
    for c in clusters:
        c["score"] = score(c, latest)
    clusters.sort(key=lambda c: -c["score"])

    # 1면 톱 1건 + 주요 뉴스 4건 (전시회 안내·기타 제외, 같은 주제 최대 2건)
    pool = [c for c in clusters if c["cat"] not in ("기타", "전시회 개최·참가")]
    head = pool[0] if pool else None
    feats, per = [], Counter()
    for c in pool[1:]:
        if per[c["cat"]] >= 2:
            continue
        feats.append(c)
        per[c["cat"]] += 1
        if len(feats) == 4:
            break
    shown = {id(c) for c in ([head] if head else []) + feats}
    cat_cnt = Counter(c["cat"] for c in clusters if c["cat"] != "기타")
    by_tr = {t: sum(1 for r in rows if r["track"] == t) for t in TRACKS}

    def kicker(cat, cls="kicker"):
        return f'<span class="{cls}" style="background:{COLOR[cat]}">{esc(cat)}</span>'

    def tracks(c, cls="kicker"):
        return "".join(f'<span class="{cls} o">{t}</span>' for t in c["tracks"])

    def src(c):
        more = f" 外 {c['n'] - 1}개 매체" if c["n"] > 1 else ""
        return f'<div class="src"><b>{esc(c["media"])}</b>{more} · {mdate(c["date"])}</div>'

    def related(c, k=4):
        rel = [i for i in c["items"] if i["url"] != c["url"]][:k]
        if not rel:
            return ""
        lis = "".join(f'<li><span>{esc(i["media"])}</span><a href="{esc(i["url"])}" target="_blank" rel="noopener">{esc(i["title"])}</a></li>' for i in rel)
        return f'<ul class="pts" style="--dot:{COLOR[c["cat"]]}">{lis}</ul>'

    # ---- 제호
    kto, sp = data_uri("kto_signature.png"), data_uri("southernpost.png")
    css = CSS.replace("KTO_URI", kto).replace("SP_URI", sp)
    org_l = (f'<span class="kto" role="img" aria-label="한국관광공사"></span><span class="vl"></span>' if kto else "") + \
        '<div class="cap">MICE 산업 일일 이슈 모니터링<small>국제회의 유치 · 전시·컨벤션 뉴스, 매일 08:30 자동수집</small></div>'
    sp_logo = '<span class="sp" role="img" aria-label="서던포스트"></span>' if sp else "<b>(주)서던포스트</b>"
    topic_chips = "".join(f'<a href="#t{CATEGORIES.index(k)}" style="background:{COLOR[k]}">{esc(k)} {cat_cnt[k]}</a>'
                          for k in CATEGORIES if cat_cnt[k])
    mast = f"""<header class="mast">
<div class="m-top"><span class="m-kick">KTO · MICE ISSUE RADAR</span><span>{now:%Y.%m.%d}({WD[now.weekday()]}) · 보도일 <b>{since[5:].replace('-', '.')}-{now:%m.%d}</b> · 매일 08:30 자동수집</span></div>
<div class="m-main">{RADAR_SVG}<div class="m-word"><h1 class="m-en"><small>KTO</small>MICE{SCRIBBLE}</h1><div class="m-ko"><b>이슈 레이더</b><span>국제회의 · 전시 · 컨벤션</span></div></div></div>
<p class="m-tag">국제회의 유치와 전시·컨벤션 뉴스를 매일 모아 같은 사안끼리 묶고 중요도순으로 정리한 일일 이슈 모니터링</p>
<div class="chips"><button class="on" data-f="">전체</button><button data-f="유치">MICE 유치 {by_tr.get("MICE 유치", 0)}</button><button data-f="전시">전시·컨벤션 {by_tr.get("전시·컨벤션", 0)}</button><span class="sep"></span>{topic_chips}<a href="briefings/" style="background:#FFC845;color:#16193A">일일 브리핑 PDF {len(briefs)}건 →</a></div>
</header>"""

    # ---- 숫자 띠
    top_cat = max(cat_cnt.items(), key=lambda kv: kv[1]) if cat_cnt else ("-", 0)
    nbs = [
        ("오늘 신규 수집", f"{today_new:,}<small>건</small>", "08:30 KST 자동수집 회차 기준", f"최종 {esc((last or '-')[5:16])}"),
        (f"최근 {a.days}일 사안", f"{len(clusters):,}<small>건</small>", f"기사 {len(rows):,}건을 같은 사안끼리 묶음", "제목 유사도 기준 자동 묶음"),
        ("누적 수집", f"{total:,}<small>건</small>", " · ".join(f"{t} {n:,}" for t, n in by_tr.items()), "수집 시작 이후"),
        ("가장 많은 주제", f"{top_cat[1]:,}<small>건</small>", esc(top_cat[0]), f"전체 {sum(cat_cnt.values()):,}건 중"),
        ("일일 브리핑", f"{len(briefs):,}<small>호</small>", "A4 1쪽 PDF, 날짜별 모음", '<a href="briefings/" style="text-decoration:underline">브리핑 모음 열기</a>'),
    ]
    numbers = '<div class="numbers">' + "".join(
        f'<div class="nb sk"><div class="desk">{d}</div><div class="big">{b}</div><div class="what">{w}</div><div class="src">{s}</div></div>'
        for d, b, w, s in nbs) + "</div>"
    numbers += '<p class="numbers-cap">숫자는 수집 데이터베이스(mice-radar)에서 그대로 집계한 값, 주제 분류와 묶음은 규칙 기반 자동 처리</p>'

    # ---- 1면 톱 + 주제별 기사 수
    if head:
        top_l = (f'<div>{kicker(head["cat"])}{tracks(head)}<span class="kicker o">보도 {head["n"]}개 매체</span>'
                 f'<h2><a class="tt" href="{esc(head["url"])}" target="_blank" rel="noopener">{esc(head["title"])}</a></h2>{src(head)}{related(head)}</div>')
    else:
        top_l = '<div><span class="kicker o">1면 톱</span><h2>최근 수집된 MICE 관련 기사가 없음</h2></div>'
    mx = max(cat_cnt.values(), default=1)
    bars = "".join(
        f'<div class="bar-row"><span class="lab"><i style="background:{COLOR[k]}"></i>{esc(k)}</span><div class="bar-track"><div class="bar" style="width:{max(14, cat_cnt[k] / mx * 100):.1f}%;background:{COLOR[k]}">{cat_cnt[k]:,}</div></div></div>'
        for k in CATEGORIES if cat_cnt[k])
    top_r = (f'<aside class="side"><h3>최근 {a.days}일 주제별 사안 수</h3><div class="chart">{bars}</div>'
             f'<p class="chart-note">같은 사안을 여러 매체가 보도해도 1건으로 셈 · 분류 외(기타) {sum(1 for c in clusters if c["cat"] == "기타"):,}건은 제외</p></aside>')
    top = f'<section class="top rule-after">{top_l}{top_r}</section>'

    # ---- 주요 뉴스
    cards = "".join(
        f'<a class="card sk" data-sk-stroke="{COLOR[c["cat"]]}" href="{esc(c["url"])}" target="_blank" rel="noopener"{dtr(c)}>'
        f'<div>{kicker(c["cat"], "tag")}{tracks(c, "tag")}</div><span class="tt">{esc(c["title"])}</span>{src(c)}</a>' for c in feats)
    feat_sec = (f'<section class="sec rule-after"><div class="sec-head"><h2>주요 뉴스</h2><span class="meta">주제 중요도 · 보도 매체 수 · 최신성으로 자동 선정</span></div>'
                f'<div class="cards">{cards or "<p class=empty>해당 없음</p>"}</div></section>')

    # ---- 주제별 데스크
    desks = []
    for k in CATEGORIES:
        cs = [c for c in clusters if c["cat"] == k and id(c) not in shown]
        if not cs and k == "전시회 개최·참가":
            continue
        slug = f"t{CATEGORIES.index(k)}"
        col = COLOR[k]
        head_html = f'<div class="desk-head"><h2 style="color:{col}">{esc(k)}</h2><span class="meta">{DESC.get(k, "")} · <b>{len(cs)}</b>건</span></div>'
        if not cs:
            desks.append(f'<section class="desk-sec rule-after" id="{slug}">{head_html}<p class="empty">최근 {a.days}일 보도 없음</p></section>')
            continue
        compact = k == "전시회 개최·참가"
        if compact:
            lead_html, rest = "", cs
        else:
            ld = cs[0]
            lead_html = (f'<article class="lead-card sk" data-sk-stroke="{col}" style="background:{col}12"{dtr(ld)}>{kicker(ld["cat"])}{tracks(ld)}'
                         f'<h3><a class="tt" href="{esc(ld["url"])}" target="_blank" rel="noopener">{esc(ld["title"])}</a></h3>{src(ld)}{related(ld, 3)}</article>')
            rest = cs[1:]
        limit = 12 if compact else 6

        def brief(c):
            more = f' <span class="many">外 {c["n"] - 1}개 매체</span>' if c["n"] > 1 else ""
            return (f'<div class="brief"{dtr(c)}><h4><a class="tt" href="{esc(c["url"])}" target="_blank" rel="noopener">{esc(c["title"])}</a></h4>'
                    f'<div class="src"><b>{esc(c["media"])}</b>{more} · {mdate(c["date"])} {tracks(c, "tag")}</div></div>')
        briefs_html = "".join(brief(c) for c in rest[:limit])
        more_html = ""
        if len(rest) > limit:
            more_html = f'<details class="more"><summary>{len(rest) - limit}건 더 보기</summary><div class="briefs">{"".join(brief(c) for c in rest[limit:])}</div></details>'
        if compact:
            body = f'<div class="two"><div class="briefs">{briefs_html}</div>{more_html}</div>'
        else:
            body = f'<div class="grid">{lead_html}<div><div class="briefs">{briefs_html or "<p class=empty>이 사안 1건</p>"}</div>{more_html}</div></div>'
        desks.append(f'<section class="desk-sec rule-after" id="{slug}">{head_html}{body}</section>')

    etc = [c for c in clusters if c["cat"] == "기타"]
    etc_html = ""
    if etc:
        etc_li = "".join(f'<li{dtr(c)}><a href="{esc(c["url"])}" target="_blank" rel="noopener">{esc(c["title"])}</a> <span>{esc(c["media"])} · {mdate(c["date"])}</span></li>' for c in etc)
        etc_html = f'<details class="etc"><summary>분류 외 기사 {len(etc)}건 (자동 수집 잡음 포함)</summary><ul>{etc_li}</ul></details>'

    foot = (f'<footer class="foot"><div>자료원 : <b>https://baebong3.github.io/mice-radar/</b> · Google News RSS 자동수집 (MICE 유치·전시·컨벤션 2개 트랙)<br>'
            f'주제 분류 · 같은 사안 묶음 · 주요 뉴스 선정은 규칙 기반 자동 처리 · 생성 {now:%Y-%m-%d %H:%M} KST</div>'
            f'<div class="r"><span>발주 한국관광공사 · 수행</span>{sp_logo}</div></footer>')

    out = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MICE 이슈 레이더</title><meta name="description" content="한국관광공사 MICE 산업 일일 이슈 모니터링">{FONT_LINKS}<style>{css}</style></head><body>
{ROUGH_DEFS}<div class="wrap">
<div class="org"><div class="l">{org_l}</div><div class="r"><span>발주 한국관광공사 · 수행</span>{sp_logo}</div></div>
{mast}{numbers}{top}{feat_sec}{''.join(desks)}{etc_html}{foot}
</div><script src="assets/rough.min.js"></script><script>{JS}</script>
</body></html>"""
    os.makedirs(DOCS, exist_ok=True)
    with open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8") as f:
        f.write(out)
    print(f"docs/index.html 생성: 최근 {a.days}일 기사 {len(rows)}건 → 사안 {len(clusters)}건, 브리핑 {len(briefs)}건")


if __name__ == "__main__":
    main()
