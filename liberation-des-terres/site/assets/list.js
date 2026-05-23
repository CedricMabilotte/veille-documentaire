/* list.js — filtre, tri et recherche des catalogues.
   Fichier unique mis en cache, partagé par lieux/porteurs/usufruitiers/modeles
   (cf. cycle B — audit performance, B-2). Vanilla JS, aucune dépendance. */
(function(){
 var q=document.getElementById('q'),sort=document.getElementById('sort'),
   cnt=document.getElementById('cnt'),nores=document.getElementById('noresult'),
   grid=document.querySelector('.cards');
 if(!grid) return;
 var cards=[].slice.call(document.querySelectorAll('.card')),
   fbtns=[].slice.call(document.querySelectorAll('.fbtn'));
 var active={};
 fbtns.forEach(function(b){
  var k=b.dataset.fk;
  if(b.classList.contains('active')) active[k]=b.dataset.fv;
 });
 function apply(){
  var v=q?q.value.toLowerCase().trim():'',n=0;
  cards.forEach(function(c){
   var ok=c.dataset.nom.toLowerCase().indexOf(v)!==-1;
   for(var k in active){
    if(active[k]&&active[k]!=='all'&&c.dataset[k]!==active[k]) ok=false;
   }
   c.style.display=ok?'':'none';
   if(ok) n++;
  });
  if(cnt){
   cnt.innerHTML='<b>'+n+'</b> entrée'+(n>1?'s':'')+' affichée'+(n>1?'s':'');
  }
  if(nores) nores.hidden=n!==0;
 }
 function doSort(){
  var key=sort.value;
  var vis=cards.slice().sort(function(a,b){
   if(key==='nom') return a.dataset.nom.localeCompare(b.dataset.nom,'fr');
   return (parseFloat(b.dataset[key])||0)-(parseFloat(a.dataset[key])||0);
  });
  vis.forEach(function(c){grid.appendChild(c);});
 }
 if(q) q.addEventListener('input',apply);
 if(sort) sort.addEventListener('change',doSort);
 fbtns.forEach(function(b){
  b.addEventListener('click',function(){
   var k=b.dataset.fk;
   document.querySelectorAll('.fbtn[data-fk="'+k+'"]').forEach(function(x){
    x.classList.remove('active');
   });
   b.classList.add('active');active[k]=b.dataset.fv;apply();
  });
 });
})();

/* Classement — tri de colonnes + filtre par catégorie (page classement.html). */
(function(){
 var tbl=document.querySelector('.rank-tbl');
 if(!tbl||!tbl.tBodies.length||!tbl.tHead) return;
 var tb=tbl.tBodies[0],
   ths=[].slice.call(tbl.tHead.rows[0].cells),
   btns=[].slice.call(document.querySelectorAll('.fbtn[data-f]')),
   status=document.getElementById('sort-status');
 function reindex(){
  var i=0;
  [].slice.call(tb.rows).forEach(function(t){
   if(t.style.display!=='none'){i++;t.querySelector('.rank').textContent=i;}
  });
 }
 btns.forEach(function(b){
  b.addEventListener('click',function(){
   btns.forEach(function(x){x.classList.remove('active');});
   b.classList.add('active');
   var f=b.dataset.f;
   [].slice.call(tb.rows).forEach(function(t){
    t.style.display=(f==='all'||t.dataset.cat===f)?'':'none';
   });
   reindex();
  });
 });
 function cellVal(tr,i,type){
  var t=tr.cells[i].innerText.trim();
  if(type==='num') return t==='—'?-1:(parseFloat(t)||0);
  return t.toLowerCase();
 }
 function sortBy(th){
  var i=ths.indexOf(th),type=th.dataset.sort;
  var dir=th.getAttribute('aria-sort')==='ascending'?-1:1;
  ths.forEach(function(x){
   if(x.classList.contains('sortable')) x.setAttribute('aria-sort','none');
  });
  th.setAttribute('aria-sort',dir===1?'descending':'ascending');
  [].slice.call(tb.rows).sort(function(a,b){
   var va=cellVal(a,i,type),vb=cellVal(b,i,type);
   if(va<vb) return dir;
   if(va>vb) return -dir;
   return 0;
  }).forEach(function(r){tb.appendChild(r);});
  reindex();
  if(status){
   var lab=(th.querySelector('.th-sort')||th).innerText.trim();
   status.textContent='Tableau trié par '+lab+', ordre '
    +(dir===1?'décroissant':'croissant')+'.';
  }
 }
 ths.forEach(function(th){
  if(!th.classList.contains('sortable')) return;
  var btn=th.querySelector('.th-sort');
  (btn||th).addEventListener('click',function(){sortBy(th);});
 });
})();
