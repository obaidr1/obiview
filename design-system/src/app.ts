/** Bildblick reference interactions. Demo state only; never edits or uploads files. */
(() => {
  type QueryRoot = Document | Element;
  const one = <T extends Element = HTMLElement>(selector: string, root: QueryRoot = document): T => {
    const element = root.querySelector<T>(selector);
    if (!element) throw new Error(`Missing reference element: ${selector}`);
    return element;
  };
  const all = <T extends Element = HTMLElement>(selector: string, root: QueryRoot = document): T[] => Array.from(root.querySelectorAll<T>(selector));
  let toastTimer: ReturnType<typeof setTimeout>;
  function notify(message: string): void {
    const toast = one('#toast');
    toast.textContent = message; toast.hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(() => { toast.hidden = true; }, 4000);
  }
  function syncRange(range: HTMLInputElement): void {
    const value = Number(range.value);
    all<HTMLOutputElement>('output').filter(output => output.htmlFor.value === range.id).forEach(output => { output.value = String(value); });
    all<HTMLInputElement>('input[data-sync]').filter(input => input.dataset.sync === range.id).forEach(input => { input.value = String(value); });
  }
  function clampInput(input: HTMLInputElement): void {
    if (input.value === '') return;
    const n = Number(input.value);
    if (!Number.isFinite(n)) return;
    input.value = String(Math.max(Number(input.min || -Infinity), Math.min(Number(input.max || Infinity), n)));
  }
  function selectChoice(button: HTMLButtonElement): void {
    const group = button.closest<HTMLElement>('[role=radiogroup]');
    if (!group) return;
    all<HTMLButtonElement>('[role=radio]', group).forEach(other => {
      const active = other === button;
      other.setAttribute('aria-checked', String(active)); other.tabIndex = active ? 0 : -1;
    });
    if (group.classList.contains('tool-choices')) {
      const descriptions: Record<string, string> = {pen: 'Stift · präziser Strich mit harter Kante.', brush: 'Pinsel · weich auslaufende Striche.', line: 'Linie · gerade Verbindung zwischen zwei Punkten.', arrow: 'Pfeil · Richtung oder Detail hervorheben.', rectangle: 'Rechteck · rechteckige Kontur zeichnen.', ellipse: 'Ellipse · ovale oder kreisförmige Kontur zeichnen.'};
      one('#tool-description').textContent = descriptions[button.dataset.value || 'pen'];
    }
    if (group.id === 'effect-choices') renderEffect();
    if (group.hasAttribute('data-export-format')) {
      const scope = group.closest('.export-scope') || one('#export-example');
      const isPng = button.dataset.value === 'PNG';
      const panel = one('[data-quality-panel]', scope);
      one<HTMLInputElement>('input[type=range]', panel).disabled = isPng;
      one('[data-quality-note]', panel).hidden = !isPng;
    }
    if (group.hasAttribute('data-export-size')) {
      const scope = group.closest('.export-scope') || one('#export-example');
      one('[data-custom-size]', scope).hidden = button.dataset.value !== 'Eigene';
    }
  }
  function renderEffect(): void {
    const selected = one<HTMLButtonElement>('#effect-choices [aria-checked=true]').dataset.value || 'Sepia';
    const value = Number(one<HTMLInputElement>('#intensity').value) / 100;
    const compare = one('#compare').getAttribute('aria-pressed') === 'true';
    const simulations: Record<string, string> = {Sepia: `sepia(${value})`, Weichzeichnen: `blur(${value * 5}px)`, Kanten: `grayscale(1) contrast(${1 + value * 5})`};
    one<SVGElement>('#effect-image').style.filter = compare ? 'none' : simulations[selected] || 'none';
    one('#effect-note').textContent = compare ? 'Unverändertes Original · Vergleich aktiv' : `${selected} · ${simulations[selected] ? 'Vorschau mit CSS simuliert' : 'Auswahlbeispiel; Pixelvorschau in der nativen App'}`;
  }
  const initialIntensity = 65;
  let appliedIntensity = initialIntensity;
  let appliedEffect = 'Sepia';
  function restoreEffect(value: number, effect: string): void {
    const range = one<HTMLInputElement>('#intensity'); range.value = String(value); syncRange(range);
    const button = all<HTMLButtonElement>('#effect-choices [role=radio]').find(b => b.dataset.value === effect);
    if (button) selectChoice(button);
    one('#compare').setAttribute('aria-pressed', 'false'); renderEffect();
  }
  document.addEventListener('click', event => {
    const target = event.target instanceof Element ? event.target.closest<HTMLButtonElement>('button') : null;
    if (!target || target.disabled) return;
    if (target.dataset.toast) notify(target.dataset.toast);
    if (target.getAttribute('role') === 'radio') selectChoice(target);
    if (target.getAttribute('role') === 'switch') target.setAttribute('aria-checked', String(target.getAttribute('aria-checked') !== 'true'));
    if (target.dataset.step) {
      const input = one<HTMLInputElement>('input', target.closest('.spin')!);
      if (input.disabled) return;
      if (Number(target.dataset.step) > 0) input.stepUp(); else input.stepDown();
      input.dispatchEvent(new Event('input', {bubbles: true}));
    }
    if (target.dataset.zoom) {
      const output = one<HTMLOutputElement>('#zoom-value');
      const value = Math.max(25, Math.min(800, parseInt(output.value) + Number(target.dataset.zoom)));
      output.value = `${value} %`;
    }
    if (target.matches('.thumb')) {
      all('.thumb').forEach(thumb => thumb.setAttribute('aria-pressed', String(thumb === target)));
      one('#thumb-status').textContent = `${target.dataset.name} ausgewählt`;
    }
    if (target.hasAttribute('data-native-open')) one<HTMLInputElement>('#file-demo').click();
    if (target.id === 'compare') { target.setAttribute('aria-pressed', String(target.getAttribute('aria-pressed') !== 'true')); renderEffect(); }
    if (target.id === 'reset-effect') restoreEffect(initialIntensity, 'Sepia');
    if (target.id === 'cancel-effect') { restoreEffect(appliedIntensity, appliedEffect); notify('Demo: Nicht angewendete Änderungen verworfen.'); }
    if (target.id === 'apply-effect') {
      appliedIntensity = Number(one<HTMLInputElement>('#intensity').value);
      appliedEffect = one<HTMLButtonElement>('#effect-choices [aria-checked=true]').dataset.value || 'Sepia';
      notify(`Demo: ${appliedEffect} mit ${appliedIntensity} % übernommen. Keine Datei verändert.`);
    }
    if (target.id === 'play-demo') {
      const active = target.getAttribute('aria-pressed') !== 'true';
      target.setAttribute('aria-pressed', String(active)); target.setAttribute('aria-label', active ? 'Wiedergabe-Beispiel pausieren' : 'Wiedergabe-Beispiel starten');
      one('use', target).setAttribute('href', active ? '#i-pause' : '#i-play');
      one('#play-state').textContent = active ? 'Wiedergabe · Zustandsdemo' : 'Pausiert · Demo';
    }
    if (target.dataset.open) openDialog(target.dataset.open);
    if (target.hasAttribute('data-close-dialog')) one<HTMLDialogElement>('#demo-dialog').close();
    if (target.hasAttribute('data-demo-submit')) { one<HTMLDialogElement>('#demo-dialog').close(); notify('Design-Demo bestätigt. Keine Datei wurde verändert.'); }
  });
  document.addEventListener('keydown', event => {
    const target = event.target instanceof Element ? event.target.closest<HTMLButtonElement>('[role=radio]') : null;
    if (!target || !['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End'].includes(event.key)) return;
    const buttons = all<HTMLButtonElement>('[role=radio]:not(:disabled)', target.closest('[role=radiogroup]')!);
    const index = buttons.indexOf(target);
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1 : (index + (['ArrowLeft','ArrowUp'].includes(event.key) ? -1 : 1) + buttons.length) % buttons.length;
    event.preventDefault(); selectChoice(buttons[next]); buttons[next].focus();
  });
  document.addEventListener('input', event => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement || input instanceof HTMLTextAreaElement)) return;
    if (input instanceof HTMLInputElement) {
      if (input.type === 'range') { syncRange(input); if (input.id === 'intensity') renderEffect(); }
      if (input.dataset.sync) {
        clampInput(input);
        const range = document.getElementById(input.dataset.sync) as HTMLInputElement | null;
        if (range && input.value !== '') { range.value = input.value; syncRange(range); if (range.id === 'intensity') renderEffect(); }
      }
      if (input.id === 'color-demo') one<HTMLOutputElement>('output[for=color-demo]').value = input.value;
      if (input.id === 'invalid-name') {
        const invalid = !input.value.trim() || /[\/\\]/.test(input.value);
        input.setAttribute('aria-invalid', String(invalid));
        one('#invalid-help').textContent = invalid ? 'Bitte einen Dateinamen ohne / oder \\ eingeben.' : 'Der Dateiname ist gültig.';
        one('#invalid-help').classList.toggle('error-text', invalid);
      }
      if (input.id === 'search-demo') {
        let count = 0;
        all<HTMLButtonElement>('.thumb').forEach(thumb => { thumb.hidden = !thumb.dataset.name!.includes(input.value.toLowerCase()); if (!thumb.hidden) count++; });
        one('#search-result').textContent = `${count} Vorschaubilder gefunden.`;
        one('#thumb-reset').hidden = count > 0;
        one('#thumb-status').textContent = count ? 'Treffer nach Dateinamen gefiltert.' : 'Keine Bilder gefunden. Suchbegriff ändern.';
      }
      if (input.id.endsWith('custom-width')) {
        const scope = input.closest('.export-scope') || one('#export-example');
        const width = Number(input.value);
        one('[data-custom-height]', scope).textContent = input.validity.valid && width ? `Höhe: ${Math.round(width * 2/3)} px` : 'Breite zwischen 1 und 10 000 px eingeben.';
      }
    }
    if (input.id === 'shortcut-reference-search') all<HTMLTableRowElement>('#shortcut-reference-table tr').forEach(row => { row.hidden = !row.textContent!.toLowerCase().includes(input.value.toLowerCase()); });
    if (input.id === 'text-demo') one('#font-preview').textContent = input.value || 'Textvorschau';
  });
  document.addEventListener('change', event => {
    const input = event.target;
    if (input instanceof HTMLInputElement && input.type === 'number') { clampInput(input); input.dispatchEvent(new Event('input', {bubbles: true})); }
  });
  one<HTMLSelectElement>('#font-demo').addEventListener('change', event => { one('#font-preview').style.fontFamily = (event.target as HTMLSelectElement).value; });
  one<HTMLInputElement>('#file-demo').addEventListener('change', event => {
    const file = (event.target as HTMLInputElement).files?.[0];
    one('#file-demo-result').textContent = file ? `Lokal ausgewählt: ${file.name}. Keine Übertragung oder Bearbeitung.` : 'Keine Datei gewählt.';
  });
  one<HTMLInputElement>('#mixed-check').indeterminate = true;
  function openDialog(kind: string): void {
    const dialog = one<HTMLDialogElement>('#demo-dialog');
    const content = one('#modal-content'); content.replaceChildren();
    dialog.classList.toggle('compact-dialog', kind === 'confirm');
    const titles: Record<string,string> = {export: 'Bild exportieren', resize: 'Größe ändern', info: 'Bildinformationen', confirm: 'Änderungen speichern?'};
    one('#modal-title').textContent = titles[kind] || 'Beispieldialog';
    if (kind === 'export') {
      const clone = one('#export-example').cloneNode(true) as HTMLElement;
      clone.id = 'modal-export'; clone.classList.add('export-scope');
      all<HTMLElement>('[id]', clone).forEach(element => { element.id = `modal-${element.id}`; });
      all<HTMLElement>('[for],[aria-labelledby],[data-sync]', clone).forEach(element => {
        for (const attr of ['for','aria-labelledby','data-sync']) {
          const value = element.getAttribute(attr); if (value) element.setAttribute(attr, value.split(' ').map(id => 'modal-'+id).join(' '));
        }
      });
      content.append(clone);
    } else if (kind === 'resize') {
      content.innerHTML = '<p class="muted small">Exakte Abmessungen · Beispielwerte, kein Bild wird verändert.</p><div class="card stack"><div class="field"><label for="modal-width">Breite (px)</label><input id="modal-width" type="number" min="1" max="10000" value="1920"></div><div class="field"><label for="modal-height">Höhe (px)</label><input id="modal-height" type="number" min="1" max="10000" value="1280"></div><label class="check"><input id="modal-ratio" type="checkbox" checked>Seitenverhältnis erhalten</label></div>';
      const width = one<HTMLInputElement>('#modal-width'); const height = one<HTMLInputElement>('#modal-height');
      width.addEventListener('input', () => { if (one<HTMLInputElement>('#modal-ratio').checked && width.validity.valid && width.value) height.value = String(Math.max(1,Math.round(Number(width.value)*2/3))); });
      height.addEventListener('input', () => { if (one<HTMLInputElement>('#modal-ratio').checked && height.validity.valid && height.value) width.value = String(Math.min(10000,Math.round(Number(height.value)*3/2))); });
    } else if (kind === 'info') {
      const source = one('#data [data-info-groups]').cloneNode(true); content.append(source);
      const note = document.createElement('p'); note.className = 'small muted spaced'; note.textContent = 'Beispielwerte. Die native App zeigt zusätzlich vollständige Pfade, Original-/aktuelle Farben, Datei-/Pixel-Speicher, Ordnerposition, Datum, Ladezeit sowie EXIF/IPTC/Kommentar.'; content.append(note);
    } else {
      content.innerHTML = '<p>Das Bild enthält ungespeicherte Änderungen. Vor dem Fortfahren speichern?</p><p class="small muted">Bestätigungsbeispiel. Es werden keine Dateien verändert.</p>';
    }
    const scrollBody = document.createElement('div'); scrollBody.className = 'modal-body';
    scrollBody.append(...Array.from(content.childNodes)); content.append(scrollBody);
    const footer = document.createElement('div'); footer.className = 'dialog-footer';
    footer.innerHTML = `<button type="button" class="btn secondary" data-close-dialog>${kind === 'info' ? 'Schließen' : 'Abbrechen'}</button>`;
    if (kind === 'confirm') footer.innerHTML += '<button type="button" class="btn secondary" data-demo-submit>Verwerfen</button>';
    if (kind !== 'info') footer.innerHTML += `<button type="button" class="btn primary" data-demo-submit>${kind === 'confirm' ? 'Speichern' : kind === 'export' ? 'Bild speichern' : 'Größe ändern'}</button>`;
    content.append(footer);
    const controls = content.querySelectorAll('.modal-body button,.modal-body input,.modal-body select,.modal-body textarea,.modal-body [role="switch"],.modal-body label,.modal-body p,.modal-body .data-list > div,.modal-body .info-groups > section');
    const tokens = getComputedStyle(document.documentElement);
    const base = parseFloat(tokens.getPropertyValue('--dialog-width-base')) || 480;
    const step = parseFloat(tokens.getPropertyValue('--dialog-width-per-element')) || 24;
    const maximum = parseFloat(tokens.getPropertyValue('--dialog-width-maximum')) || 960;
    const targetWidth = Math.min(maximum, base + Math.max(0, controls.length - 4) * step);
    dialog.style.width = `min(${targetWidth}px, calc(100vw - 32px))`;
    dialog.style.height = kind === 'confirm' ? 'fit-content' : 'auto';
    content.oninput = () => {
      const submit = content.querySelector<HTMLButtonElement>('[data-demo-submit]');
      if (submit) submit.disabled = all<HTMLInputElement>('input[type=number]',content).some(input => !input.closest('[hidden]') && (!input.value || !input.validity.valid));
    };
    dialog.showModal();
    // Safe focus for destructive confirmation. Native dialog traps and restores focus.
    one<HTMLButtonElement>('[data-close-dialog]', dialog).focus();
  }
  all<HTMLInputElement>('input[type=range]').forEach(syncRange);
  one('#thumb-reset').addEventListener('click', () => { const search = one<HTMLInputElement>('#search-demo'); search.value = ''; search.dispatchEvent(new Event('input', {bubbles:true})); search.focus(); });
  const defaultExport = all<HTMLButtonElement>('[data-export-size] [role=radio]').find(button => button.dataset.value === '100 %');
  if (defaultExport) selectChoice(defaultExport);
  renderEffect();
  const observer = new IntersectionObserver(entries => {
    const visible = entries.filter(entry => entry.isIntersecting).sort((a,b) => a.boundingClientRect.top - b.boundingClientRect.top);
    if (!visible.length) return;
    all<HTMLAnchorElement>('.sidebar nav a').forEach(link => {
      if (link.hash === `#${visible[0].target.id}`) link.setAttribute('aria-current','page'); else link.removeAttribute('aria-current');
    });
  }, {rootMargin: '-5% 0px -65% 0px'});
  all<HTMLElement>('main section').forEach(section => observer.observe(section));
})();
