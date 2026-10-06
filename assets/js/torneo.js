'use strict';
const $=id=>document.getElementById(id);
let token=sessionStorage.getItem('torneo-token')||'',state, busy=false;
const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
const error=message=>{$('error').textContent=message;$('error').hidden=!message;};
async function api(path,data){
 const response=await fetch((window.TORNEO_API_URL||'').replace(/\/$/,'')+'/api/'+path,{method:data?'POST':'GET',headers:{...(data?{'Content-Type':'application/json'}:{}),...(token?{Authorization:'Bearer '+token}:{})},...(data?{body:JSON.stringify(data)}:{})});
 let result;try{result=await response.json();}catch{throw Error('Il servizio torneo non è disponibile.');}
 if(!response.ok)throw Error(result.error||'Operazione non riuscita');return result;
}
async function run(task){if(busy)return;busy=true;error('');try{await task();}catch(e){error(e.message);}finally{busy=false;}}
const teamName=id=>state.teams.find(t=>t.id===id)?.name||'Squadra';
function resultForm(m){
 const f=el('form');f.className='t-match';f.append(el('strong',teamName(m.a)+' — '+teamName(m.b)+' · Set '+m.leg));
 const row=el('div');row.className='t-score';const inputs=[];
 for(const [id,name,value] of [['a',teamName(m.a),m.p_a],['b',teamName(m.b),m.p_b]]){
  const label=el('label',name);const input=el('input');input.type='number';input.min=0;input.max=50;input.required=true;input.name=id;input.value=value??'';label.append(input);row.append(label);inputs.push(input);
 }
 const submit=el('button',m.status==='done'?'Correggi risultato':'Registra risultato');f.append(row,submit);
 f.onsubmit=e=>{e.preventDefault();run(async()=>{state=await api('result',{match:m.id,a:Number(inputs[0].value),b:Number(inputs[1].value)});render();});};return f;
}
function render(){
 const admin=state.team==='admin', me=state.teams.find(t=>t.id===state.team);
 $('status').textContent=(state.settings.closed?'Nuove assegnazioni chiuse':state.settings.paused?'Torneo in pausa':'Torneo attivo')+' · Aggiornamento '+new Date().toLocaleTimeString('it-IT');
 $('login').hidden=!!state.team;$('account').hidden=!state.team;$('admin').hidden=!admin;$('team-controls').hidden=!me;
 $('identity').textContent=admin?'Accesso organizzatore':me?me.name+' · Girone '+me.group_id+' · '+(me.available?'Disponibile':'In pausa'):'';
 $('my-match').replaceChildren();
 if(me){const m=state.matches.find(m=>['waiting','playing'].includes(m.status)&&[m.a,m.b].includes(me.id));
 $('available').disabled=!!m||!!state.settings.paused||!!state.settings.closed;$('unavailable').disabled=!!m;
 if(m){const box=el('div');box.className='t-match';box.append(el('strong','Campo '+m.court+' · '+teamName(m.a)+' contro '+teamName(m.b)));
 if(m.status==='waiting'){const ready=me.id===m.a?m.ready_a:m.ready_b;box.append(el('p',ready?'Hai confermato. Aspettiamo l’altra squadra.':'Conferma entro '+new Date(m.deadline*1000).toLocaleTimeString('it-IT')));for(const [text,value] of [['Siamo pronti',true],['Non possiamo giocare',false]]){const b=el('button',text);b.disabled=ready&&value;b.onclick=()=>run(async()=>{state=await api('ready',{match:m.id,ready:value});render();});box.append(b);}}
 else{box.append(el('p','Set '+m.leg+' di 2'),resultForm(m));} $('my-match').append(box);
 }else $('my-match').append(el('p',me.available?'In attesa di un campo e di un avversario disponibili.':'Segnala quando la squadra è pronta a giocare.'));}
 $('courts').replaceChildren();if(!state.courts.length)$('courts').append(el('p','Il torneo non è ancora configurato.'));
 for(const c of state.courts){const m=state.matches.find(m=>m.court===c.id&&['waiting','playing'].includes(m.status));const d=el('div');d.className='t-court';d.append(el('strong','Campo '+c.id+' · Girone '+c.group_id),el('div',m?teamName(m.a)+' — '+teamName(m.b)+' · '+(m.status==='waiting'?'In attesa di conferma':'Set '+m.leg):'Libero'));$('courts').append(d);}
 $('ranking').replaceChildren();
 for(const g of [...new Set(state.teams.map(t=>t.group_id))]){const wrap=el('div');wrap.className='t-table-wrap';const table=el('table');table.append(el('caption','Girone '+g));const head=el('thead'),hr=el('tr');for(const title of ['Pos.','Squadra','Set','Vittorie','Punti']){const th=el('th',title);th.scope='col';hr.append(th);}head.append(hr);table.append(head);const body=el('tbody');state.teams.filter(t=>t.group_id===g).forEach((t,i)=>{const tr=el('tr');if(t.id===state.team)tr.className='mine';[i+1,t.name,t.played,t.wins,t.points].forEach(v=>tr.append(el('td',v)));body.append(tr);});table.append(body);wrap.append(table);$('ranking').append(wrap);}
 $('setup').hidden=state.teams.length>0;$('admin-controls').hidden=!state.teams.length;$('corrections').replaceChildren();if(admin)state.matches.filter(m=>m.status==='done').forEach(m=>$('corrections').append(resultForm(m)));
}
async function refresh(){state=await api('state');render();}
$('refresh').onclick=()=>run(refresh);
$('login').onsubmit=e=>{e.preventDefault();run(async()=>{const r=await api('login',{code:$('code').value,admin:$('admin-login').checked});token=r.token;sessionStorage.setItem('torneo-token',token);$('code').value='';await refresh();});};
$('logout').onclick=()=>{token='';sessionStorage.removeItem('torneo-token');$('codes').replaceChildren();run(refresh);};
for(const [id,value]of[['available',true],['unavailable',false]])$(id).onclick=()=>run(async()=>{state=await api('availability',{available:value});render();});
$('setup').onsubmit=e=>{e.preventDefault();run(async()=>{const r=await api('setup',{names:$('names').value,groups:Number($('groups').value),courts:Number($('court-count').value)});$('codes').replaceChildren(el('h3','Codici squadra: copiali ora'),el('p','Consegna ogni codice soltanto alla squadra corrispondente. Non saranno più visualizzati dopo la chiusura della pagina.'));for(const t of r.codes){const p=el('p',t.name+' · Girone '+t.group+' · ');p.append(el('code',t.code));$('codes').append(p);}await refresh();});};
document.querySelectorAll('[data-control]').forEach(b=>b.onclick=()=>run(async()=>{state=await api('control',{action:b.dataset.control});render();}));
run(refresh);setInterval(()=>{if(!document.hidden&&!busy)run(refresh);},5000);
