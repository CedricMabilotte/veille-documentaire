/* compare.js — comparateur de deux montages, page comparer.html.
   Rendu côté client depuis data.json. Vanilla JS, aucune dépendance.
   N'est chargé que par comparer.html ; list.js n'est pas touché. */
(function(){
 var selA=document.getElementById('cmp-a'),selB=document.getElementById('cmp-b'),
   grid=document.getElementById('cmp-grid'),warn=document.getElementById('cmp-warn');
 if(!selA||!selB||!grid) return;
 var byUid={};
 function esc(s){
  return String(s==null?'':s).replace(/[&<>"]/g,function(c){
   return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];
  });
 }
 var AXES=[['A','Intérêt général','#4a7a3a'],
           ['B','Libération des terres','#bc5d3a'],
           ['C','Gouvernance participative','#36748a']];
 var CATLAB={lieu:'Lieu',porteur:'Porteur',usufruitier:'Usufruitier',
   modele:'Modèle voisin'};
 var SLUG={lieu:'l',porteur:'p',usufruitier:'u',modele:'m'};
 function bar(label,col,val){
  var w=(val==null?0:Math.max(0,Math.min(100,val)));
  var txt=(val==null?'n.r.':val);
  return '<div class="axis-row"><span class="axis-label">'+esc(label)
   +'</span><span class="axis-track"><span class="axis-fill'
   +(val==null?' axis-na':'')+'" style="width:'+w+'%;background:'+col
   +'"></span></span><span class="axis-val">'+esc(txt)+'</span></div>';
 }
 function col(d){
  if(!d) return '<div class="cmp-col cmp-empty"><p class="note">'
   +'Choisissez une entrée.</p></div>';
  var bars='';
  for(var i=0;i<AXES.length;i++){
   bars+=bar(AXES[i][0]+' · '+AXES[i][1],AXES[i][2],
     d.axes?d.axes[AXES[i][0]]:null);
  }
  var estime=d.score_type==='estime';
  var idl=(d.idl==null?'n.r.':d.idl)+(estime?' · estimé':'');
  var pal=d.palier_label?esc(d.palier_label):'—';
  var palCol=d.palier_couleur||'#999';
  var rows='';
  function row(k,v){
   if(!v) return '';
   return '<dt>'+esc(k)+'</dt><dd>'+esc(v)+'</dd>';
  }
  rows+=row('Catégorie',CATLAB[d.categorie]||d.categorie);
  rows+=row('Forme juridique',d.forme_juridique);
  rows+=row('Type de montage',d.montage_label);
  rows+=row('Nature juridique',d.nature_juridique);
  if(d.completude!=null){
   rows+=row('Complétude',Math.round(d.completude*100)+' %');
  }
  var href=SLUG[d.categorie]+'/'+d.uid+'.html';
  return '<div class="cmp-col"><div class="cmp-col-head">'
   +'<span class="tag tag-'+esc(d.categorie)+'">'
   +esc(CATLAB[d.categorie]||d.categorie)+'</span>'
   +'<span class="cmp-idl" style="--pal:'+esc(palCol)+'">'
   +'<b>'+esc(idl)+'</b><span class="idl-pal">'+pal+'</span></span></div>'
   +'<h2 class="cmp-name">'+esc(d.nom)+'</h2>'
   +'<p class="cmp-sub">'+esc(d.sous_titre||'')+'</p>'
   +'<div class="axis-block">'+bars+'</div>'
   +'<dl class="cmp-dl">'+rows+'</dl>'
   +'<p class="cmp-link"><a href="'+esc(href)+'">Fiche complète →</a></p>'
   +'</div>';
 }
 function render(){
  var a=byUid[selA.value],b=byUid[selB.value];
  grid.innerHTML=col(a)+col(b);
  if(a&&b&&a.categorie!==b.categorie){
   warn.textContent='Ces deux entrées relèvent de catégories différentes, '
    +'notées par des grilles distinctes : la comparaison est indicative.';
   warn.hidden=false;
  }else{ warn.hidden=true; }
  var p=new URLSearchParams();
  if(selA.value) p.set('a',selA.value);
  if(selB.value) p.set('b',selB.value);
  var qs=p.toString();
  history.replaceState(null,'',qs?('?'+qs):location.pathname);
 }
 fetch('data.json').then(function(r){return r.json();}).then(function(list){
  list.forEach(function(d){byUid[d.uid]=d;});
  var q=new URLSearchParams(location.search);
  if(q.get('a')&&byUid[q.get('a')]) selA.value=q.get('a');
  if(q.get('b')&&byUid[q.get('b')]) selB.value=q.get('b');
  render();
 }).catch(function(){
  grid.innerHTML='<p class="no-result">Données indisponibles. '
   +'Consultez le <a href="classement.html">classement</a>.</p>';
 });
 selA.addEventListener('change',render);
 selB.addEventListener('change',render);
})();
