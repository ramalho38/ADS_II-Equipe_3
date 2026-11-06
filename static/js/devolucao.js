(() => {
    const btn    = document.getElementById('btn-devolucao');
    const modal  = document.getElementById('modal-devolucao');
    const dica   = document.getElementById('emp-dica');
    if (!btn || !modal) return;

    // true  = só os empréstimos em atraso tremem e podem ser escolhidos
    // false = todos os empréstimos do painel (permite devolver livro que ainda está no prazo)
    const SO_ATRASADOS = false;

    const VALOR_POR_DIA = 2.50;   // multa em reais por dia de atraso
    const reais = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

    // Lê "Venceu há 11 dia(s)" da linha e devolve 11. Se não estiver vencido, devolve 0.
    function diasDeAtraso(linha) {
        const texto = linha.querySelector('.prazo')?.textContent || '';
        const m = texto.match(/Venceu há (\d+)/i);
        return m ? parseInt(m[1], 10) : 0;
    }

    const campoLivro = document.getElementById('devolucao-livro');
    const campoMulta = document.getElementById('devolucao-multa');
    const confirmar  = document.getElementById('devolucao-confirmar');
    const link       = btn.querySelector('.link');
    const textoLink  = link ? link.textContent : '';

    let modoAtivo = false;
    let timerAviso = null;

    const linhas = () =>
        [...document.querySelectorAll('.emp-linha')]
            .filter(l => !SO_ATRASADOS || l.dataset.atraso === '1');

    /* ---------- Modo "escolher livro" ---------- */
    function entrarModo() {
        const alvo = linhas();

        if (alvo.length === 0) {
            dica.textContent = SO_ATRASADOS
                ? 'Você não tem empréstimos em atraso.'
                : 'Você não tem livros para devolver.';
            dica.hidden = false;
            clearTimeout(timerAviso);
            timerAviso = setTimeout(() => { dica.hidden = true; }, 3500);
            return;
        }

        modoAtivo = true;
        document.body.classList.add('modo-devolucao');
        btn.classList.add('ativo');
        btn.setAttribute('aria-pressed', 'true');
        if (link) link.textContent = 'Cancelar devolução ✕';

        dica.textContent = 'Escolha o livro que você quer devolver.';
        dica.hidden = false;

        alvo.forEach(l => {
            l.classList.add('devolvivel');
            l.tabIndex = 0;
            l.setAttribute('role', 'button');
        });

        // Leva o leitor até o painel para ele ver as linhas tremendo
        document.getElementById('emp-titulo')
            .scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function sairModo() {
        modoAtivo = false;
        document.body.classList.remove('modo-devolucao');
        btn.classList.remove('ativo');
        btn.setAttribute('aria-pressed', 'false');
        if (link) link.textContent = textoLink;
        dica.hidden = true;

        document.querySelectorAll('.emp-linha.devolvivel').forEach(l => {
            l.classList.remove('devolvivel');
            l.removeAttribute('tabindex');
            l.removeAttribute('role');
        });
    }

    btn.addEventListener('click', e => {
        e.preventDefault();
        modoAtivo ? sairModo() : entrarModo();
    });

    /* ---------- Popup ---------- */
    function abrirPopup(linha) {
        // Escolheu um livro: as linhas param de tremer
        sairModo();
        idEmprestimo.value = linha.querySelector('#emprestimoID').value
        campoLivro.value = linha.dataset.titulo || '';
        campoMulta.value = reais.format(diasDeAtraso(linha) * VALOR_POR_DIA);
        modal.classList.add('aberto');
        confirmar.focus();
    }

    function fecharPopup() {
        modal.classList.remove('aberto');
    }

    // Clique (ou Enter/Espaço) em uma linha que está tremendo
    document.addEventListener('click', e => {
        const linha = e.target.closest('.emp-linha.devolvivel');
        if (linha) abrirPopup(linha);
    });

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            if (modal.classList.contains('aberto')) fecharPopup();
            else if (modoAtivo) sairModo();
            return;
        }
        if ((e.key === 'Enter' || e.key === ' ') && e.target.matches('.emp-linha.devolvivel')) {
            e.preventDefault();
            abrirPopup(e.target);
        }
    });

    modal.querySelectorAll('[data-fechar-devolucao]')
        .forEach(el => el.addEventListener('click', fecharPopup));
})();