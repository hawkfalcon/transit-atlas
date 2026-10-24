'use strict';
(() => {
 const D=JSON.parse(document.getElementById('atlasData').textContent);
 const $=id=>document.getElementById(id);
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const fmt=n=>new Intl.NumberFormat('en-US',{maximumFractionDigits:2}).format(n);
 const rowById=new Map(D.routes.map(r=>[r.id,r]));
 const state={tab:'network',mode:'historic',selected:null,focus:[],plan:'protect',performanceSort:'review',query:'',filter:'all',lost:true,amtrak:true,extras:false,stops:false};
 const params=new URLSearchParams(location.hash.slice(1));
 if(['historic','current'].includes(params.get('view')))state.mode=params.get('view');
 if(params.get('tab')==='saving'||params.get('view')==='cut')state.tab='saving';
 if(params.get('view')==='cut')state.mode='current';
 if(['protect','merge','target','fund'].includes(params.get('plan')))state.plan=params.get('plan');
 if(params.get('focus'))state.focus=[...new Set(params.get('focus').split(','))].filter(id=>rowById.has(id));
 if(rowById.has(params.get('line'))){state.selected=params.get('line');state.focus=[];}
 const colors={frequent:'#007e78',moderate:'#3d80a6',halfHourly:'#cc8b29',hourly:'#cf6252',infrequent:'#914858',limited:'#6554a4',ghost:'#474a43'};
 const modeKey=m=>m==='historic'?'historic':'current';
 function metric(r,mode=state.mode){
  const rec=r[modeKey(mode)];
  return {rec,active:!!rec?.active,h:rec?.active&&rec.headway!=null?rec.headway:null,min:rec?.gapMin??null,max:rec?.gapMax??null,mid:rec?.middayTrips??0,day:rec?.dayTrips??0};
 }
 function color(m){return !m.active?colors.ghost:m.h==null?colors.limited:m.h<=15?colors.frequent:m.h<=30?colors.moderate:m.h<=45?colors.halfHourly:m.h<=60?colors.hourly:colors.infrequent;}
 function variable(m){return m.h!=null&&m.min!==m.max;}
 function value(m,units=true){if(!m.active)return 'No trips';if(m.h==null)return 'Limited';return `${variable(m)?'~':''}${fmt(m.h)}${units?' min':''}`;}
 function range(m){return m.min==null?'No regular midday interval':m.min===m.max?`${fmt(m.min)} min`:`${fmt(m.min)}–${fmt(m.max)} min`;}
 function clock(s){if(s==null)return '—';const day=Math.floor(s/86400),h=Math.floor(s/3600)%24,m=Math.floor(s/60)%60;return `${h%12||12}:${String(m).padStart(2,'0')} ${h>=12?'pm':'am'}${day?' +1 day':''}`;}
 function updateHash(){try{const p=new URLSearchParams({tab:state.tab,view:state.mode});if(state.selected)p.set('line',state.selected);if(state.focus.length)p.set('focus',state.focus.join(','));if(state.tab==='saving')p.set('plan',state.plan);history.replaceState(null,'','#'+p.toString());}catch(e){/* Sandboxed file viewers can have an opaque origin. */}}
 const map=L.map('map',{zoomControl:false,attributionControl:false,minZoom:10,maxZoom:16,zoomSnap:.25,zoomDelta:.75,scrollWheelZoom:true,preferCanvas:false,fadeAnimation:false,zoomAnimation:true,maxBounds:[[34.22,-120.08],[34.62,-119.32]],maxBoundsViscosity:.5});
 map.createPane('atlasBase');map.getPane('atlasBase').style.zIndex=100;
 L.imageOverlay(ATLAS_BASEMAP,ATLAS_BOUNDS,{pane:'atlasBase',interactive:false,opacity:1}).addTo(map);
 map.createPane('places');map.getPane('places').style.zIndex=360;map.getPane('places').style.pointerEvents='none';
 map.createPane('routeCasing');map.getPane('routeCasing').style.zIndex=390;map.getPane('routeCasing').style.pointerEvents='none';
 map.createPane('routeLines');map.getPane('routeLines').style.zIndex=400;
 map.createPane('referenceCasing');map.getPane('referenceCasing').style.zIndex=415;map.getPane('referenceCasing').style.pointerEvents='none';
 map.createPane('routeReferences');map.getPane('routeReferences').style.zIndex=420;
 map.createPane('routeBadges');map.getPane('routeBadges').style.zIndex=440;
 L.control.zoom({position:'bottomright'}).addTo(map);
 L.control.scale({position:'bottomleft',imperial:false,maxWidth:90}).addTo(map);
 L.control.attribution({prefix:'<a href="https://leafletjs.com" target="_blank" rel="noopener noreferrer">Leaflet</a>'}).addAttribution('Esri, HERE, Garmin, © OpenStreetMap contributors, GIS user community').addTo(map);
 let routesGroup=L.layerGroup().addTo(map),badgesGroup=L.layerGroup().addTo(map),stopsGroup=L.layerGroup().addTo(map),placesGroup=L.layerGroup().addTo(map);
 let drawn=[];
 const regions={all:[[34.356,-119.929],[34.479,-119.47]],sb:[[34.39,-119.755],[34.461,-119.64]],goleta:[[34.405,-119.927],[34.476,-119.778]],carp:[[34.367,-119.556],[34.421,-119.465]]};
 const places=[['GOLETA',34.466,-119.836,''],['SANTA BARBARA',34.456,-119.712,''],['CARPINTERIA',34.405,-119.505,''],['MONTECITO',34.439,-119.642,'small'],['SUMMERLAND',34.428,-119.595,'small'],['ISLA VISTA',34.396,-119.861,'small'],['UCSB',34.407,-119.844,'campus'],['SBCC',34.397,-119.699,'campus'],['TRANSIT CENTER',34.4255,-119.7003,'campus'],['SANTA BARBARA CHANNEL',34.358,-119.715,'ocean']];
 function renderPlaces(){placesGroup.clearLayers();const z=map.getZoom();for(const [name,lat,lon,cls]of places){if(z<11.5&&['SUMMERLAND','MONTECITO','TRANSIT CENTER','SBCC'].includes(name))continue;L.marker([lat,lon],{pane:'places',interactive:false,keyboard:false,icon:L.divIcon({className:'place-icon',iconSize:[190,20],iconAnchor:[95,10],html:`<div class="atlas-place ${cls}">${name}</div>`})}).addTo(placesGroup);}}
 function permitted(r){return r.kind==='regular'||r.kind==='amtrak'&&state.amtrak||(r.kind==='booster'||r.kind==='standby')&&state.extras;}
 function routePaths(r){const rec=r[modeKey(state.mode)];return rec?.paths?.length?rec.paths:(r.historic?.paths?.length?r.historic.paths:r.current?.paths)||[];}
 function width(m){return m.h==null?3.2:Math.max(2.8,6.8-Math.log2(Math.max(m.h,8)/10)*.9);}
 function referenceLabel(r){return state.mode==='historic'?'Not in the 2019 timetable · 2026 path':r.historic?.active?'2019 route · no trips today':'No trips on this date';}
 function renderMap(){
  routesGroup.clearLayers();badgesGroup.clearLayers();drawn=[];
  let candidates=[];
  for(const r of D.routes){
   if(!permitted(r)&&r.id!==state.selected&&!state.focus.includes(r.id))continue;
   const m=metric(r);let ghost=false,paths=[];
   if(m.active)paths=m.rec.paths;
   else if(state.mode!=='historic'&&state.lost&&r.historic?.active){ghost=true;paths=r.historic.paths;}
   else if(r.id===state.selected){ghost=true;paths=routePaths(r);}
   if(!paths.length)continue;
   candidates.push({r,m,ghost,paths});
  }
  candidates.sort((a,b)=>(a.ghost?-1:0)-(b.ghost?-1:0)||(b.m.h??999)-(a.m.h??999));
  for(const x of candidates){
   const {r,m,ghost,paths}=x,c=ghost?colors.ghost:color(m),selected=r.id===state.selected||state.focus.includes(r.id);
   const faded=(state.selected||state.focus.length>0)&&!selected,opacity=faded?0.13:ghost?0.97:m.h==null?0.98:0.91,w=ghost?(selected?5.8:4.2):selected?width(m)+2.1:width(m);
   L.polyline(paths,{pane:ghost?'referenceCasing':'routeCasing',interactive:false,color:'#fffef8',weight:w+2.4,opacity:faded?0.08:ghost?0.98:0.87,dashArray:ghost?'10 7':null,smoothFactor:.65,lineCap:'round',lineJoin:'round'}).addTo(routesGroup);
   const layer=L.polyline(paths,{pane:ghost?'routeReferences':'routeLines',color:c,weight:w,opacity,className:ghost?'route-reference':m.h==null?'route-limited':'route-regular',dashArray:ghost?'10 7':null,smoothFactor:.65,lineCap:'round',lineJoin:'round',bubblingMouseEvents:false});
   layer.bindTooltip(`<span class="tooltip-line">Line ${esc(r.id)} · ${esc(m.rec?.name||r.historic?.name||r.name)}</span><span class="tooltip-frequency">${ghost?esc(referenceLabel(r)):esc(m.h==null?'Limited / timed service':value(m))+(variable(m)?` typical · gaps ${esc(range(m))}`:'')}<br>Click to compare 2019 and today</span>`,{sticky:true,direction:'top',opacity:1});
   layer.on('click',()=>selectRoute(r.id,false));
   layer.on('mouseover',()=>{if(!state.selected&&!state.focus.length)layer.setStyle({weight:w+1.5,opacity:1});});
   layer.on('mouseout',()=>{if(!state.selected&&!state.focus.length)layer.setStyle({weight:w,opacity});});
   layer.addTo(routesGroup);if(layer.getElement())layer.getElement().dataset.line=r.id;drawn.push({...x,layer,color:c});
  }
  if(state.selected){const s=drawn.find(x=>x.r.id===state.selected);if(s)s.layer.bringToFront();}
  renderBadges();renderStops();renderPlaces();renderFocus();
  const references=drawn.filter(x=>x.ghost);
  $('ghostLegend').hidden=!references.length;
  $('ghostLabel').textContent=state.mode==='historic'?'Not in 2019 · 2026 route shown':references.every(x=>x.r.historic?.active)?'2019 routes missing today':'No trips on this date';
  $('lostToggle').disabled=state.mode==='historic';
  $('map').closest('.map-area').classList.toggle('has-selection',!!state.selected);
 }
 // Label placement uses original route points and a screen-space collision test.
 function renderBadges(){
  badgesGroup.clearLayers();const used=[],size=map.getSize();
  const focused=state.selected?[state.selected]:state.focus;
  const priority=[...drawn].sort((a,b)=>focused.includes(b.r.id)-focused.includes(a.r.id)||(a.ghost?0:1)-(b.ghost?0:1)||(a.r.kind==='regular'?0:1)-(b.r.kind==='regular'?0:1)||(a.m.h??999)-(b.m.h??999));
  for(const x of priority){
   if(focused.length&&!focused.includes(x.r.id))continue;
   if(x.r.kind!=='regular'&&x.r.id!==state.selected&&map.getZoom()<12.5)continue;
   const paths=x.paths.map(p=>({p,len:p.reduce((n,a,i)=>i?n+Math.hypot((a[0]-p[i-1][0])*1.2,a[1]-p[i-1][1]):0,0)})).sort((a,b)=>b.len-a.len);
   let choice=null;
   for(const {p}of paths.slice(0,22)){
    for(const frac of [.5,.28,.72,.12,.88]){
     const ll=p[Math.floor((p.length-1)*frac)],pt=map.latLngToContainerPoint(ll);
     if(pt.x<35||pt.x>size.x-40||pt.y<130||pt.y>size.y-158)continue;
     if(used.some(a=>Math.abs(a.x-pt.x)<38&&Math.abs(a.y-pt.y)<30))continue;
     choice={ll,pt};break;
    }if(choice)break;
   }
   if(!choice)continue;
   used.push(choice.pt);
   const wide=x.r.id.length>3;
   const marker=L.marker(choice.ll,{pane:'routeBadges',keyboard:true,title:`Line ${x.r.id}: ${x.r.name}${x.ghost?' · '+referenceLabel(x.r):x.m.h==null?' · Limited / timed service':''}`,icon:L.divIcon({className:'route-map-icon',iconSize:[wide?36:29,22],iconAnchor:[wide?18:14.5,11],html:`<span class="map-route-badge ${wide?'wide':''} ${x.ghost?'ghost':x.m.h==null?'limited':''}" style="--route:${x.color}">${esc(x.r.id)}${!x.ghost&&x.m.h==null?'<span class="badge-clock" aria-hidden="true"><svg viewBox="0 0 12 12"><circle cx="6" cy="6" r="4"/><path d="M6 3.3V6l1.8 1.1"/></svg></span>':''}</span>`})});
   marker.on('click',()=>selectRoute(x.r.id,false));marker.addTo(badgesGroup);
  }
 }
 function renderStops(){
  stopsGroup.clearLayers();if(!state.stops||map.getZoom()<13)return;
  const bounds=map.getBounds().pad(.1),period=modeKey(state.mode);
  for(const s of D.stops[period]){
   const rr=s.routes.filter(id=>{const r=rowById.get(id);return r&&permitted(r)&&(state.selected?state.selected===id:!state.focus.length||state.focus.includes(id));});
   if(!rr.length||!bounds.contains([s.lat,s.lon]))continue;
   L.circleMarker([s.lat,s.lon],{radius:3,color:'#607d67',weight:1,fillColor:'#fffef8',fillOpacity:.95}).bindTooltip(`<b>${esc(s.name)}</b><br>Lines ${rr.map(esc).join(', ')}`,{direction:'top'}).addTo(stopsGroup);
  }
 }
 function renderStats(){
  const core=D.routes.filter(r=>r.kind==='regular');
  const active=core.filter(r=>metric(r).active),base=core.reduce((a,r)=>a+(r.historic?.middayTrips||0),0),trips=active.reduce((a,r)=>a+metric(r).mid,0),frequent=active.filter(r=>metric(r).h!=null&&metric(r).h<=15).length;
  $('statLines').textContent=active.length;$('statTrips').textContent=fmt(trips);$('statFrequent').textContent=frequent;$('statTripsLabel').textContent='midday departures';
  $('changeStrip').className='change-strip '+state.mode;
  $('changeText').textContent=state.mode==='historic'?'Before the pandemic · Weekday midday':`${Math.round((1-trips/base)*100)}% fewer midday departures than 2019`;
 }
 function renderTitles(){
  const data={historic:{date:'TUESDAY · OCTOBER 15, 2019',title:'2019 network',sub:'Weekday service before the pandemic.',note:'<b>Fall 2019.</b> Four routes offered a typical 15-minute interval or better.'},current:{date:'THURSDAY · OCTOBER 15, 2026',title:'2026 network',sub:'October weekday service, after August’s cuts.',note:'<b>Six routes from 2019 are missing.</b> Dark dashes show where they ran.'}}[state.mode];
  $('mapDate').textContent=data.date;$('mapTitle').textContent=data.title;$('mapSubtitle').textContent=data.sub;$('scenarioNote').innerHTML=data.note;$('scenarioNote').className='scenario-note';
  document.querySelectorAll('.scenario').forEach(b=>{const on=b.dataset.mode===state.mode;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});
 }
 function renderFocus(){
  const el=$('focusBanner');el.hidden=!state.focus.length;
  if(!state.focus.length){el.innerHTML='';return;}
  el.innerHTML=`<div><b>${state.mode==='historic'?'2019':'CURRENT'} ROUTES · ${state.focus.map(esc).join(' + ')}</b><span>${state.mode==='historic'?'October 2019 timetable.':'Existing routes · October 2026 timetable.'}</span></div><div class="focus-actions"><button data-return-saving>Back to Saving MTD ↗</button><button data-clear-focus aria-label="Clear group focus">×</button></div>`;
  el.querySelector('[data-return-saving]').onclick=()=>setTab('saving');el.querySelector('[data-clear-focus]').onclick=clearSelection;
 }
 function renderList(){
  let list=D.routes.filter(r=>state.filter==='extras'||r.kind==='regular'||r.kind==='amtrak'&&state.amtrak||r.kind==='booster'&&state.extras);
  if(state.query)list=list.filter(r=>[r.id,r.name,r.historicName||''].join(' ').toLowerCase().includes(state.query.toLowerCase()));
  if(state.filter==='changed')list=list.filter(r=>r.historic?.active&&(!r.current?.active||r.current.headway!=null&&r.historic.headway!=null&&r.current.headway>r.historic.headway));
  if(state.filter==='absent')list=list.filter(r=>r.historic?.active&&!r.current?.active);
  if(state.filter==='frequent')list=list.filter(r=>{const m=metric(r);return m.active&&m.h!=null&&m.h<=15;});
  $('lineCount').textContent=String(list.length);
  $('routeList').innerHTML=list.length?list.map(r=>{
   const m=metric(r),h=r.historic,c=r.current,currName=m.rec?.name||r.name;
   let sub=r.kind==='regular'?'':r.kind==='amtrak'?'Timed Amtrak connection':'School & special trips';
   if(m.active&&m.h==null)sub=r.kind==='amtrak'?'Runs · timed Amtrak connection':'Runs · limited / timed departures';
   if(!m.active)sub=!m.rec?(state.mode==='historic'?'Not in the 2019 timetable':'2019 route · missing today'):'No trips on this date';
   if(r.id==='33')sub='Seasonal · No October weekday trips';
   let trend='';
   if(h?.headway!=null&&c?.headway!=null&&h.active&&c.active){const change=c.headway-h.headway;trend=change===0?'Same interval':change>0?`${fmt(h.headway)} → ${fmt(c.headway)} min`:`${fmt(h.headway)} → ${fmt(c.headway)} min`;}
   return `<button class="route-row ${!m.active?'ghost':m.h==null?'limited':''} ${r.id===state.selected||state.focus.includes(r.id)?'selected':''}" data-line="${esc(r.id)}" aria-pressed="${r.id===state.selected||state.focus.includes(r.id)}"><span class="route-chip" style="--route:${color(m)}">${esc(r.id)}</span><span class="route-name"><strong>${esc(currName)}</strong><small>${esc(sub|| (variable(m)?'Uneven midday gaps':'Weekday daytime'))}</small></span><span class="route-frequency" style="color:${color(m)}">${esc(value(m))}<small class="${h?.headway&&c?.headway<h.headway?'improved':''}">${esc(trend)}</small></span></button>`;
  }).join(''):'<div class="empty-list">No lines match this filter.<br>Try another search or network.</div>';
  document.querySelectorAll('#routeList [data-line]').forEach(b=>b.addEventListener('click',()=>selectRoute(b.dataset.line,false,true)));
  $('clearSelectionTop').hidden=!state.selected&&!state.focus.length;
 }
 function renderCard(){
  const el=$('selectedCard');if(!state.selected){el.hidden=true;el.innerHTML='';return;}
  const r=rowById.get(state.selected),m=metric(r),rec=m.rec,kind=r.kind==='regular'?'Regular bus route':r.kind==='amtrak'?'Timed Amtrak connection':'School & special trips';
  el.hidden=false;el.classList.toggle('is-limited',m.active&&m.h==null);el.classList.toggle('is-inactive',!m.active);
  const cards=['historic','current'].map((mode,i)=>{const a=metric(r,mode),num=a.h!=null;return `<div class="mini ${!a.active?'inactive':a.h==null?'limited':''} ${state.mode===mode?'active':''}"><span>${['2019','TODAY'][i]}</span><strong class="${num?'':'word'}">${esc(num?`${variable(a)?'~':''}${fmt(a.h)}`:value(a))}</strong><small>${num?'min between buses':a.active?'Trips run · limited/timed':'No departures'}</small></div>`;}).join('');
  const directions=(rec?.directions||[]).map(dir=>`<div class="direction-row"><strong>${esc(dir.headsign||`Direction ${dir.id}`)}</strong><small>${dir.headway==null||dir.middayTrips<2?`${fmt(dir.dayTrips)} ${dir.dayTrips===1?'departure':'departures'} that day · ${fmt(dir.middayTrips)} at midday`:`Typical ${fmt(dir.headway)} min · gaps ${fmt(dir.gapMin)}–${fmt(dir.gapMax)} min<br>${fmt(dir.middayTrips)} midday departures`}</small></div>`).join('');
  el.innerHTML=`<div class="card-top"><span class="route-chip" style="--route:${color(m)}">${esc(r.id)}</span><div><h3>${esc(rec?.name||r.historic?.name||r.name)}</h3><div class="card-kicker">${kind}</div>${m.active&&m.h==null?'<span class="service-status limited">Runs · limited/timed trips</span>':!m.active?'<span class="service-status inactive">No trips in this timetable</span>':''}</div><button class="card-close" aria-label="Close line details">×</button></div><div class="card-comparison">${cards}</div><p class="gap-note">${m.active&&m.h!=null?`<b>${esc(range(m))}</b> between departures. ~ means the gaps vary.`:m.active?'Scheduled trips, with no regular midday interval.':state.mode==='current'&&r.historic?.active?'This route ran in 2019. The dark dashes follow its old path.':state.mode==='historic'?'This route wasn’t in the 2019 timetable. The dashes show its 2026 path.':'No departures on this date.'}</p>${r.note?`<p class="card-note">${esc(r.note)}</p>`:''}<div class="card-detail-row"><span>Midday departures</span><b>${fmt(m.mid)}<br><small>10 am–2 pm · both directions</small></b></div><div class="card-detail-row"><span>Trips that day</span><b>${fmt(m.day)}</b></div>${rec?.active?`<div class="card-detail-row"><span>First → last bus</span><b>${clock(rec.first)} → ${clock(rec.last)}</b></div>`:''}${directions}<div class="card-actions"><button class="zoom-line">Zoom to line ↗</button><button class="clear-line">Show all lines</button></div>`;
  el.querySelector('.card-close').onclick=clearSelection;el.querySelector('.clear-line').onclick=clearSelection;el.querySelector('.zoom-line').onclick=()=>fitRoute(r);
 }
 function fitRoute(r){const paths=routePaths(r);if(!paths.length)return;const bb=L.latLngBounds(paths.flat());const mobile=innerWidth<=760;map.fitBounds(bb,{paddingTopLeft:[35,mobile?115:120],paddingBottomRight:[mobile?35:Math.min(340,map.getSize().x*.4),mobile?150:175],maxZoom:14.5,animate:!matchMedia('(prefers-reduced-motion: reduce)').matches});}
 function selectRoute(id,zoom=false,fromList=false){if(!rowById.has(id))return;state.selected=id;state.focus=[];if(state.tab!=='network')setTab('network');renderList();renderCard();renderMap();updateHash();if(zoom)fitRoute(rowById.get(id));if(fromList&&innerWidth<=760)$('map').closest('.map-area').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});}
 function clearSelection(){state.selected=null;state.focus=[];renderList();renderCard();renderMap();updateHash();}
 function setMode(mode){if(!['historic','current'].includes(mode))return false;state.mode=mode;renderTitles();renderStats();renderList();renderCard();renderMap();updateHash();return true;}
 function setTab(tab){if(!['network','saving'].includes(tab))return;state.tab=tab;$('comparisonView').hidden=tab!=='network';$('savingView').hidden=tab!=='saving';document.querySelectorAll('[role="tab"][data-tab]').forEach(b=>{const on=b.dataset.tab===tab;b.classList.toggle('active',on);b.setAttribute('aria-selected',String(on));b.tabIndex=on?0:-1;});if(tab==='network'){map.invalidateSize({pan:false});renderMap();}else window.ATLAS_SAVING?.render();updateHash();}
 function focusRoutes(ids){const valid=[...new Set(ids)].filter(id=>rowById.has(id)&&rowById.get(id).current?.active);if(!valid.length)return;state.mode='current';state.selected=null;state.focus=valid;setTab('network');renderTitles();renderStats();renderList();renderCard();renderMap();const paths=valid.flatMap(id=>rowById.get(id).current.paths);map.fitBounds(L.latLngBounds(paths.flat()),{paddingTopLeft:[35,190],paddingBottomRight:[35,165],maxZoom:13.5,animate:false});updateHash();if(innerWidth<=760)$('map').closest('.map-area').scrollIntoView({behavior:'auto',block:'start'});}
 function restoreFromHash(){
  const p=new URLSearchParams(location.hash.slice(1)),view=p.get('view');
  if(['historic','current'].includes(view))state.mode=view;else if(view==='cut')state.mode='current';
  state.plan=['protect','merge','target','fund'].includes(p.get('plan'))?p.get('plan'):state.plan;
  state.selected=rowById.has(p.get('line'))?p.get('line'):null;
  state.focus=state.selected?[]:[...new Set((p.get('focus')||'').split(','))].filter(id=>rowById.has(id));
  const tab=p.get('tab')==='saving'||view==='cut'?'saving':'network';
  renderTitles();renderStats();renderList();renderCard();setTab(tab);updateHash();
 }
 window.addEventListener('hashchange',restoreFromHash);
 function gotoRegion(key){map.fitBounds(regions[key]||regions.all,{paddingTopLeft:[25,125],paddingBottomRight:[32,165],animate:false});}
 function openDialog(id){$(id).showModal();$('layersPanel').hidden=true;$('layersBtn').setAttribute('aria-expanded','false');}
 function tableCell(r,mode){const m=metric(r,mode);return `<td><span class="table-value ${!m.active?'inactive-status':m.h==null?'limited-status':''}">${esc(value(m))}</span>${m.active&&m.h==null?'<small class="limited-explainer">Trips run · no regular midday interval</small>':m.h!=null&&variable(m)?`<small>gaps ${esc(range(m))}</small>`:''}</td>`;}
 function renderTable(){const list=D.routes.filter(r=>$('tableExtras').checked||r.kind==='regular');$('compareBody').innerHTML=list.map(r=>`<tr data-line="${esc(r.id)}" tabindex="0" aria-label="Show line ${esc(r.id)} on map" class="${r.kind==='regular'?'':'row-extra'}"><td><span class="route-chip ${!metric(r).active?'inactive-status':metric(r).h==null?'limited-status':''}" style="--route:${color(metric(r))}">${esc(r.id)}</span><div><strong>${esc(r.name)}</strong><small>${esc(r.historicName&&r.historicName!==r.name?`2019: ${r.historicName}`:r.kind==='regular'?'Regular line':r.kind==='amtrak'?'Amtrak shuttle':'School & special trips')}</small></div></td>${tableCell(r,'historic')}${tableCell(r,'current')}</tr>`).join('');$('compareBody').querySelectorAll('tr[data-line]').forEach(el=>{const go=()=>{$('compareDialog').close();selectRoute(el.dataset.line,true);};el.onclick=go;el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go();}};});}
 function downloadCSV(){const s=atob('/*CSV_B64*/'),bytes=Uint8Array.from(s,c=>c.charCodeAt(0)),blob=new Blob([new Uint8Array([239,187,191]),bytes],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='SBMTD-line-comparison.csv';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 document.querySelectorAll('[role="tab"][data-tab]').forEach(b=>{b.onclick=()=>setTab(b.dataset.tab);b.onkeydown=e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();const tab=e.key==='Home'?'network':e.key==='End'?'saving':b.dataset.tab==='network'?'saving':'network';setTab(tab);$(tab==='network'?'networkTab':'savingTab').focus();}};});
 document.querySelectorAll('.scenario').forEach(b=>b.onclick=()=>setMode(b.dataset.mode));
 $('routeSearch').addEventListener('input',e=>{state.query=e.target.value;renderList();});
 $('routeFilter').onchange=e=>{state.filter=e.target.value;renderList();};
 $('clearSelectionTop').onclick=clearSelection;
 $('layersBtn').onclick=()=>{const open=$('layersPanel').hidden;$('layersPanel').hidden=!open;$('layersBtn').setAttribute('aria-expanded',String(open));};
 for(const [id,key]of [['lostToggle','lost'],['amtrakToggle','amtrak'],['extrasToggle','extras'],['stopsToggle','stops']])$(id).onchange=e=>{state[key]=e.target.checked;renderMap();renderList();};
 $('areaSelect').onchange=e=>gotoRegion(e.target.value);
 $('resetView').onclick=()=>{$('areaSelect').value='all';gotoRegion('all');};
 $('sourcesBtn').onclick=()=>openDialog('sourcesDialog');$('metricInfo').onclick=()=>openDialog('sourcesDialog');
 $('compareBtn').onclick=()=>{renderTable();openDialog('compareDialog');};$('tableExtras').onchange=renderTable;
 ['csvBtn','sourceCsvBtn','tableCsvBtn'].forEach(id=>$(id).onclick=downloadCSV);
 document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>$(b.dataset.close).close());
 document.querySelectorAll('dialog').forEach(d=>d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}}));
 document.addEventListener('click',e=>{if(!e.target.closest('.map-tools')){$('layersPanel').hidden=true;$('layersBtn').setAttribute('aria-expanded','false');}});
 document.addEventListener('keydown',e=>{if(document.querySelector('dialog[open]'))return;if(state.tab==='network'&&e.key==='/'&&!['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName)){e.preventDefault();$('routeSearch').focus();}if(e.key==='Escape'){if(!$('layersPanel').hidden){$('layersPanel').hidden=true;$('layersBtn').setAttribute('aria-expanded','false');}else if(state.selected||state.focus.length)clearSelection();}});
 document.querySelector('.brand').onclick=e=>{e.preventDefault();state.selected=null;state.focus=[];setTab('network');setMode('historic');gotoRegion('all');};
 map.on('moveend',()=>{renderBadges();renderStops();renderPlaces();});
 let resizeTimer;window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{if(state.tab==='network'){map.invalidateSize();renderBadges();}},150);});
 gotoRegion('all');renderTitles();renderStats();renderList();renderCard();renderMap();setTab(state.tab);updateHash();
 window.ATLAS={data:D,state,map,setMode,setTab,focusRoutes,updateHash,selectRoute,clearSelection,metric,renderTable,get drawnRoutes(){return drawn.map(x=>x.r.id);}};
})();
