
const tabs=[...document.querySelectorAll('.tab')],panels=[...document.querySelectorAll('.panel')],main=document.querySelector('.main'),toc=document.querySelector('.toc');
const pos={original:0,translation:0,algorithms:0};let current='original';
function buildToc(id){toc.innerHTML='';if(id==='original'){document.querySelectorAll('#original .paper-page').forEach((el,i)=>add(el,`第 ${i+1} 页`));}else{document.querySelectorAll(`#${id} section[id]`).forEach(el=>add(el,el.querySelector('h2')?.textContent||el.id));}}
function add(el,label){const a=document.createElement('a');a.href='#'+el.id;a.textContent=label;a.onclick=e=>{e.preventDefault();el.scrollIntoView({block:'start'});};toc.appendChild(a)}
function show(id){pos[current]=main.scrollTop;current=id;tabs.forEach(x=>x.classList.toggle('active',x.dataset.panel===id));panels.forEach(x=>x.classList.toggle('active',x.id===id));buildToc(id);requestAnimationFrame(()=>main.scrollTop=pos[id]||0)}
tabs.forEach(x=>x.onclick=()=>show(x.dataset.panel));show('original');
