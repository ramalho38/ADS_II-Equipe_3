/* ============================================================
   Minhas pendências
   - sem atraso: abre um popup simples com a mensagem
   - com atraso: as linhas atrasadas saem do painel, voam até o
     centro da tela e se empilham num novo painel
   ============================================================ */
(() => {
  'use strict';

  /* ---------- configuração (ajuste aqui se mudar o HTML) ---------- */
  const SEL_BOTAO  = '#btn-pendencias';
  const SEL_LINHAS = '.emp-tabela tbody tr'; // linhas do painel de empréstimos
  const SEL_ATRASO = '.prazo-atraso';        // a linha que contém isso está em atraso
  const VOO        = 650;                    // ms que cada linha leva para chegar
  const INTERVALO  = 90;                     // ms entre uma linha e a seguinte
  const CURVA      = 'cubic-bezier(.22, .9, .3, 1)';
  const TEXTOS     = '.pend__topo, .pend__cab, .pend__rodape';

  const botao    = document.querySelector(SEL_BOTAO);
  const dlgVazio = document.getElementById('pend-vazio');
  const dlgLista = document.getElementById('pend-lista');
  if (!botao || !dlgVazio || !dlgLista) return;

  const html = document.documentElement;
  let ocupado = false; // true enquanto algo está animando
  let aberto = null;   // popup que está na tela: { dlg, itens }

  /* ---------- utilidades ---------- */
  const animavel = () =>
    typeof Element.prototype.animate === 'function' &&
    !matchMedia('(prefers-reduced-motion: reduce)').matches;

  // espera as animações terminarem (mesmo que alguma seja cancelada)
  const fim = (anims) => Promise.all(anims.map((a) => a.finished.catch(() => {})));

  const fade = (el, de, ate, opcoes) =>
    el.animate([{ opacity: de }, { opacity: ate }], { easing: 'ease-out', ...opcoes });

  const todos = (dlg, sel) => [...dlg.querySelectorAll(sel)];

  function travarScroll() {
    html.style.setProperty('--pend-barra', window.innerWidth - html.clientWidth + 'px');
    html.classList.add('pend-aberto');
  }

  // se o painel estiver fora da tela, rola até ele e espera a rolagem assentar
  function garantirVisivel(el) {
    return new Promise((resolve) => {
      const r = el.getBoundingClientRect();
      if (r.top >= 0 && r.bottom <= window.innerHeight) return resolve();

      el.scrollIntoView({ block: 'center', behavior: animavel() ? 'smooth' : 'auto' });

      let ultimo = null;
      let parado = 0;
      const inicio = performance.now();
      (function checar() {
        const y = el.getBoundingClientRect().top;
        parado = y === ultimo ? parado + 1 : 0;
        ultimo = y;
        if (parado >= 8 || performance.now() - inicio > 1500) resolve();
        else requestAnimationFrame(checar);
      })();
    });
  }

  /* ---------- aparência (ponto de partida e de chegada do voo) ---------- */
  const transparente = (c) => c === 'transparent' || /^rgba\(.*,\s*0\)$/.test(c);

  function fundoDe(el) {
    for (let n = el; n; n = n.parentElement) {
      const cor = getComputedStyle(n).backgroundColor;
      if (!transparente(cor)) return cor;
    }
    return '#fff';
  }

  // como a <tr> da tabela original se parece
  const aparenciaTr = (tr) => ({
    gridTemplateColumns: [...tr.cells].map((td) => td.getBoundingClientRect().width + 'px').join(' '),
    backgroundColor: fundoDe(tr.cells[0] || tr),
    borderRadius: '0px',
    boxShadow: 'none',
  });

  // como a linha do popup se parece
  function aparenciaCard(el) {
    const cs = getComputedStyle(el);
    return {
      gridTemplateColumns: cs.gridTemplateColumns,
      backgroundColor: cs.backgroundColor,
      borderRadius: cs.borderRadius,
      boxShadow: cs.boxShadow,
    };
  }

  /* ---------- linhas ---------- */
  // monta a linha do popup copiando o conteúdo de uma <tr> da tabela
  function criarLinha(tr) {
    const linha = document.createElement('div');
    linha.className = 'pend__linha';
    linha.setAttribute('role', 'row');
    for (const td of tr.cells) {
      const cel = document.createElement('span');
      cel.className = `pend__cel ${td.className}`.trim();
      cel.setAttribute('role', 'cell');
      td.childNodes.forEach((n) => cel.append(n.cloneNode(true)));
      linha.append(cel);
    }
    return linha;
  }

  // cria uma cópia da linha e a faz viajar do retângulo A (aparência a) ao B (aparência b)
  function voar(dlg, tr, A, a, B, b, atraso) {
    const copia = criarLinha(tr);
    copia.classList.add('pend__voo');
    copia.setAttribute('aria-hidden', 'true');
    dlg.append(copia);

    // número de colunas diferente (tela estreita): não dá para animar as colunas
    if (a.gridTemplateColumns.split(' ').length !== b.gridTemplateColumns.split(' ').length) {
      delete a.gridTemplateColumns;
      delete b.gridTemplateColumns;
    }
    const quadro = (r, estilo) => ({
      transform: `translate(${r.left}px, ${r.top}px)`,
      width: r.width + 'px',
      height: r.height + 'px',
      ...estilo,
    });
    return copia.animate([quadro(A, a), quadro(B, b)], {
      duration: VOO,
      delay: atraso,
      easing: CURVA,
      fill: 'both',
    });
  }

  /* ---------- abrir ---------- */
  async function abrirVazio() {
    travarScroll();
    dlgVazio.showModal();
    aberto = { dlg: dlgVazio };
    if (!animavel()) return;
    await fim([
      fade(dlgVazio.querySelector('.pend__fundo'), 0, 1, { duration: 250, fill: 'backwards' }),
      dlgVazio.querySelector('.pend__caixa').animate(
        [{ opacity: 0, transform: 'translateY(14px) scale(.96)' }, { opacity: 1, transform: 'none' }],
        { duration: 300, easing: CURVA, fill: 'backwards' }
      ),
    ]);
  }

  async function abrirLista(trs) {
    await garantirVisivel(trs[0].closest('.emp') || trs[0].closest('table'));
    travarScroll();

    // 1) linhas "de verdade" do popup (invisíveis até as cópias chegarem)
    const lista = dlgLista.querySelector('.pend__linhas');
    lista.replaceChildren();
    const itens = trs.map((tr) => {
      const real = criarLinha(tr);
      real.classList.add('pend__linha--oculta');
      lista.append(real);
      return { tr, real };
    });
    const n = itens.length;
    dlgLista.querySelector('#pend-lista-sub').textContent =
      n === 1
        ? '1 empréstimo passou do prazo de devolução.'
        : `${n} empréstimos passaram do prazo de devolução.`;
    dlgLista.style.setProperty('--pend-fonte', getComputedStyle(trs[0].cells[0]).fontSize);

    // 2) abre o popup
    dlgLista.showModal();
    aberto = { dlg: dlgLista, itens };
    if (!animavel()) {
      itens.forEach(({ real }) => real.classList.remove('pend__linha--oculta'));
      return;
    }

    // 3) mede de onde cada linha sai e para onde ela vai
    const voos = itens.map(({ tr, real }) => ({
      tr,
      A: tr.getBoundingClientRect(),
      a: aparenciaTr(tr),
      B: real.getBoundingClientRect(),
      b: aparenciaCard(real),
    }));
    trs.forEach((tr) => { tr.style.visibility = 'hidden'; }); // a linha "sai" do painel

    // 4) a tela escurece, o painel aparece e as linhas voam
    const anims = [
      fade(dlgLista.querySelector('.pend__fundo'), 0, 1, { duration: 350, fill: 'backwards' }),
      dlgLista.querySelector('.pend__papel').animate(
        [{ opacity: 0, transform: 'scale(.92)' }, { opacity: 1, transform: 'scale(1)' }],
        { duration: 450, delay: 150, easing: CURVA, fill: 'backwards' }
      ),
      ...todos(dlgLista, TEXTOS).map((t) => fade(t, 0, 1, { duration: 300, delay: 350, fill: 'backwards' })),
      ...voos.map((v, i) => voar(dlgLista, v.tr, v.A, v.a, v.B, v.b, i * INTERVALO)),
    ];
    await fim(anims);

    // 5) chegou: as cópias saem de cena e as linhas reais aparecem no mesmo lugar
    if (!dlgLista.open) return;
    todos(dlgLista, '.pend__voo').forEach((c) => c.remove());
    itens.forEach(({ real }) => real.classList.remove('pend__linha--oculta'));
  }

  async function abrir() {
    if (ocupado || aberto) return;
    ocupado = true;
    try {
      const atrasadas = [...document.querySelectorAll(SEL_LINHAS)].filter((tr) =>
        tr.querySelector(SEL_ATRASO)
      );
      await (atrasadas.length ? abrirLista(atrasadas) : abrirVazio());
    } catch (erro) {
      console.error('[pendencias]', erro);
      encerrar(); // não deixa a tela "quebrada" se algo falhar
    } finally {
      ocupado = false;
    }
  }

  /* ---------- fechar ---------- */
  async function fecharVazio() {
    if (animavel()) {
      await fim([
        fade(dlgVazio.querySelector('.pend__fundo'), 1, 0, { duration: 220, fill: 'forwards' }),
        dlgVazio.querySelector('.pend__caixa').animate(
          [{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateY(10px) scale(.97)' }],
          { duration: 220, easing: 'ease-in', fill: 'forwards' }
        ),
      ]);
    }
    encerrar();
  }

  // as linhas fazem o caminho inverso: do painel de volta para o lugar delas na tabela
  async function fecharLista() {
    const { itens } = aberto;
    if (animavel()) {
      const n = itens.length;
      const anims = itens.map(({ tr, real }, i) => {
        const A = real.getBoundingClientRect();
        const a = aparenciaCard(real);
        real.classList.add('pend__linha--oculta');
        return voar(dlgLista, tr, A, a, tr.getBoundingClientRect(), aparenciaTr(tr), (n - 1 - i) * INTERVALO);
      });
      anims.push(
        fade(dlgLista.querySelector('.pend__fundo'), 1, 0, {
          duration: VOO + (n - 1) * INTERVALO,
          easing: 'ease-in',
          fill: 'forwards',
        }),
        fade(dlgLista.querySelector('.pend__papel'), 1, 0, { duration: 300, fill: 'forwards' }),
        ...todos(dlgLista, TEXTOS).map((t) => fade(t, 1, 0, { duration: 200, fill: 'forwards' }))
      );
      await fim(anims);
    }
    encerrar();
  }

  async function fechar() {
    if (!aberto || ocupado) return;
    ocupado = true;
    try {
      await (aberto.dlg === dlgLista ? fecharLista() : fecharVazio());
    } finally {
      ocupado = false;
    }
  }

  // devolve tudo ao estado original (pode ser chamada mais de uma vez sem problema)
  function encerrar() {
    todos(dlgLista, '.pend__voo').forEach((c) => c.remove());
    dlgLista.querySelector('.pend__linhas').replaceChildren();
    document.querySelectorAll(SEL_LINHAS).forEach((tr) => { tr.style.visibility = ''; });
    [dlgVazio, dlgLista].forEach((d) => d.getAnimations?.({ subtree: true }).forEach((a) => a.cancel()));
    html.classList.remove('pend-aberto');
    [dlgVazio, dlgLista].forEach((d) => { if (d.open) d.close(); });
    aberto = null;
  }

  /* ---------- eventos ---------- */
  botao.addEventListener('click', (e) => {
    e.preventDefault();
    abrir();
  });
  botao.addEventListener('keydown', (e) => {
    if (e.key === ' ') { // o link age como botão: espaço também abre
      e.preventDefault();
      abrir();
    }
  });

  for (const dlg of [dlgVazio, dlgLista]) {
    dlg.addEventListener('click', (e) => {
      if (e.target.closest('[data-fechar]')) fechar(); // botão "Fechar" ou clique fora do painel
    });
    dlg.addEventListener('cancel', (e) => { // tecla Esc: fecha com a animação
      e.preventDefault();
      fechar();
    });
    dlg.addEventListener('close', encerrar);
  }
})();