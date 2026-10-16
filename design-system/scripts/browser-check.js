/* Run only in the temporary verification page created by prepare_check.py. */
(() => {
  const results = [];
  const check = (name, fn) => { try { fn(); results.push({name,ok:true}); } catch(error) { results.push({name,ok:false,error:String(error)}); } };
  const q = s => {const e=document.querySelector(s);if(!e) throw Error(s);return e;};
  const assert = (ok,msg='Assertion failed') => {if(!ok)throw Error(msg);};
  const input = (s,value) => {const e=q(s);e.value=value;e.dispatchEvent(new Event('input',{bubbles:true}));return e;};
  const click = s => q(s).click();
  const choice = (s,value) => [...document.querySelectorAll(s+' [role=radio]')].find(b=>b.dataset.value===value);
  check('Offline runtime initializes ranges and export default',()=>{assert(q('#stroke-number').value==='4');assert(choice('[data-export-size]','100 %').getAttribute('aria-checked')==='true');});
  check('Range → exact value; exact value → range; bounds',()=>{input('#stroke','90');assert(q('#stroke-number').value==='90');input('#stroke-number','25');assert(q('#stroke').value==='25');input('#stroke-number','600');assert(q('#stroke').value==='500');assert(q('#stroke-number').value==='500');});
  check('Stepper and minimum boundary',()=>{input('#stroke-number','1');q('#stroke-number').closest('.spin').querySelector('[data-step="-1"]').click();assert(q('#stroke').value==='1');q('#stroke-number').closest('.spin').querySelector('[data-step="1"]').click();assert(q('#stroke').value==='2');});
  check('Exclusive tool selection and keyboard arrows',()=>{choice('.tool-choices','brush').click();assert(document.querySelectorAll('.tool-choices [aria-checked=true]').length===1);assert(q('#tool-description').textContent.includes('Pinsel'));choice('.tool-choices','brush').dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));assert(choice('.tool-choices','line').getAttribute('aria-checked')==='true');assert(document.activeElement===choice('.tool-choices','line'));});
  check('Switch and indeterminate checkbox',()=>{const s=q('#toggles [role=switch]');const before=s.getAttribute('aria-checked');s.click();assert(s.getAttribute('aria-checked')!==before);assert(q('#mixed-check').indeterminate);});
  check('Invalid filename becomes valid after correction',()=>{input('#invalid-name','good.jpg');assert(q('#invalid-name').getAttribute('aria-invalid')==='false');input('#invalid-name','bad/name.jpg');assert(q('#invalid-name').getAttribute('aria-invalid')==='true');});
  check('Thumbnail filter handles matches and empty state',()=>{input('#search-demo','duenen');assert([...document.querySelectorAll('.thumb')].filter(b=>!b.hidden).length===1);input('#search-demo','missing');assert(q('#thumb-status').textContent.includes('Keine Bilder'));input('#search-demo','');});
  check('Effect preview, compare, apply and cancel',()=>{input('#intensity','80');assert(q('#effect-image').style.filter==='sepia(0.8)');click('#compare');assert(q('#effect-image').style.filter==='none');click('#compare');click('#apply-effect');input('#intensity','20');click('#cancel-effect');assert(q('#intensity').value==='80');click('#reset-effect');assert(q('#intensity').value==='65');});
  check('PNG disables lossy quality; custom size calculates height',()=>{choice('[data-export-format]','PNG').click();assert(q('#export-quality').disabled);assert(!q('[data-quality-note]').hidden);choice('[data-export-format]','JPG').click();choice('[data-export-size]','Eigene').click();assert(!q('[data-custom-size]').hidden);input('#custom-width','900');assert(q('[data-custom-height]').textContent.includes('600'));choice('[data-export-size]','100 %').click();});
  check('Export modal isolates IDs and range synchronization',()=>{const trigger=q('#export [data-open=export]');trigger.focus();trigger.click();assert(q('#demo-dialog').open);const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);assert(new Set(ids).size===ids.length);input('#modal-export-quality','40');assert(q('output[for=modal-export-quality]').value==='40');assert(q('#export-quality').value==='85');click('#demo-dialog [data-close-dialog]');assert(!q('#demo-dialog').open);assert(document.activeElement===trigger);});
  check('Resize dialog preserves ratio and blocks invalid input',()=>{click('#export [data-open=resize]');input('#modal-width','900');assert(q('#modal-height').value==='600');input('#modal-width','0');assert(q('#demo-dialog [data-demo-submit]').disabled);input('#modal-width','1200');assert(!q('#demo-dialog [data-demo-submit]').disabled);click('#demo-dialog [data-close-dialog]');});
  check('Information and confirmation dialogs open and close',()=>{click('#export [data-open=info]');assert(q('#demo-dialog .data-list'));click('#demo-dialog [data-close-dialog]');click('#feedback [data-open=confirm]');assert(document.activeElement.hasAttribute('data-close-dialog'));click('#demo-dialog [data-demo-submit]');assert(!q('#demo-dialog').open);});
  check('Every modal shares the export footprint and visible footer',()=>{
    for(const kind of ['export','resize','info','confirm']) {
      q(`[data-open=${kind}]`).click(); const d=q('#demo-dialog');
      const rect=d.getBoundingClientRect();
      assert(Math.abs(rect.width-Math.min(520,innerWidth-32))<2,kind+' width '+rect.width);
      if(kind==='confirm') { assert(rect.height<380, 'Confirmation must stay compact'); assert([...d.querySelectorAll('.dialog-footer button')].map(b=>b.textContent.trim()).join(',')==='Abbrechen,Verwerfen,Speichern'); }
      else assert(Math.abs(rect.height-Math.min(760,innerHeight-32))<2,kind+' height '+rect.height);
      const body=q('#modal-content .modal-body'); body.scrollTop=body.scrollHeight;
      const footer=q('#modal-content > .dialog-footer').getBoundingClientRect();
      assert(footer.bottom<=rect.bottom && footer.top>=rect.top,kind+' footer');
      click('#demo-dialog [data-close-dialog]');
    }
  });
  check('No horizontal document overflow at current viewport',()=>{assert(document.documentElement.scrollWidth<=innerWidth+1,`${document.documentElement.scrollWidth}px exceeds ${innerWidth}px`);});
  const failures = results.filter(r=>!r.ok);
  window.BILDBLICK_CHECK = {passed:results.length-failures.length,total:results.length,failures};
  document.title = `${failures.length?'FAIL':'PASS'} — ${results.length} Bildblick browser checks`;
  const report=document.createElement('div');report.id='verification-report';report.style.cssText='position:relative;min-height:100vh;background:#f5f5f3;padding:24px;font:14px/1.5 system-ui;overflow:auto;color:#242424';
  const heading=document.createElement('h1');heading.style.cssText='font-size:28px;letter-spacing:-1px;margin:0 0 10px';heading.textContent=`${failures.length?'FAIL':'PASS'} · ${results.length-failures.length}/${results.length} browser checks`;report.append(heading);
  const viewport=document.createElement('p');viewport.textContent=`Firefox · ${innerWidth} × ${innerHeight} · local file:// · no external dependencies`;report.append(viewport);
  for(const result of results){const row=document.createElement('p');row.style.cssText=`padding:8px 0;border-bottom:1px solid #dededb;margin:0;color:${result.ok?'#242424':'#a02020'}`;row.textContent=`${result.ok?'✓':'✗'} ${result.name}${result.error?' — '+result.error:''}`;report.append(row);}
  document.documentElement.style.scrollBehavior='auto';document.body.replaceChildren(report);window.scrollTo(0,0);
})();
