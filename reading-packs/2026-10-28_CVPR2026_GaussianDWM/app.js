(()=>{"use strict";
const main=document.querySelector(".layout main"),tabs=[...document.querySelectorAll("[data-tab]")],panels=[...document.querySelectorAll(".panel")],toc=document.getElementById("toc");
if(!main||!toc||!panels.length)return;
const key="paper-reader:"+(document.body.dataset.paper||"GaussianDWM");
const memory={};const get=k=>{try{return window.localStorage.getItem(k)}catch(_){return memory[k]??null}},set=(k,v)=>{memory[k]=String(v);try{window.localStorage.setItem(k,String(v))}catch(_){}};
let current="original",started=false;
const allowed=["original","translation","explanation"];
function save(){set(key+":"+current,String(main.scrollTop))}
function makeToc(){toc.textContent="";const panel=document.getElementById(current);
const nodes=current==="original"?[...panel.querySelectorAll(".paper-page")]:[...panel.querySelectorAll("h1,h2,h3")];
nodes.forEach((el,n)=>{if(!el.id)el.id=current+"-section-"+n;const a=document.createElement("a");a.href="#"+el.id;a.className=el.tagName==="H3"?"level-3":"";a.textContent=current==="original"?"第 "+(n+1)+" 页":(el.textContent||"").replace(/\s+/g," ").trim().slice(0,88);a.addEventListener("click",e=>{e.preventDefault();el.scrollIntoView({block:"start",behavior:"smooth"})});toc.appendChild(a)})}
function show(name){if(!allowed.includes(name)||!document.getElementById(name))name="original";
if(started)save();current=name;
tabs.forEach(b=>{const on=b.dataset.tab===name;b.classList.toggle("active",on);b.setAttribute("aria-selected",String(on))});
panels.forEach(p=>p.classList.toggle("active",p.id===name));
set(key+":tab",name);makeToc();const previous=Number(get(key+":"+name));void main.offsetHeight;main.scrollTop=Number.isFinite(previous)?Math.max(0,previous):0;started=true}
tabs.forEach(b=>b.addEventListener("click",()=>show(b.dataset.tab)));
// Persist positions on tab switches and pagehide; avoid delayed scroll callbacks racing with a newly activated tab.
window.addEventListener("pagehide",save);show(get(key+":tab")||"original");

function renderFormulae(){
  if(typeof window.katex==="undefined")return;
  document.querySelectorAll(".formula[data-latex]").forEach(el=>{
    const target=el.querySelector(".formula-rendered");
    if(!target)return;
    try{window.katex.render(el.getAttribute("data-latex"),target,{displayMode:true,throwOnError:false,strict:"ignore"});}
    catch(err){el.dataset.mathError=String(err).slice(0,160);}
  });
}
renderFormulae();

})();