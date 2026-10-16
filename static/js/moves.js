// =====================================================================
// MovesLocation · interacciones comunes a todas las páginas
// =====================================================================
(() => {
  const $ = (sel, raiz = document) => raiz.querySelector(sel);
  const $$ = (sel, raiz = document) => [...raiz.querySelectorAll(sel)];
  const movimientoReducido = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------- Tema claro / oscuro (se recuerda entre visitas) ----------
  $$('[data-cambiar-tema]').forEach((boton) => {
    boton.addEventListener('click', () => {
      const oscuro = document.documentElement.dataset.tema !== 'oscuro';
      if (oscuro) document.documentElement.dataset.tema = 'oscuro';
      else delete document.documentElement.dataset.tema;
      try { localStorage.setItem('moves-tema', oscuro ? 'oscuro' : 'claro'); } catch (e) {}
    });
  });

  // ---------- Cabecera: se vuelve sólida al bajar ----------
  const cabecera = $('[data-cabecera]');
  if (cabecera) {
    const actualizar = () => cabecera.classList.toggle('cabecera--solida', scrollY > 40);
    actualizar();
    addEventListener('scroll', actualizar, { passive: true });
  }

  // ---------- Menú en móvil ----------
  const botonMenu = $('[data-menu]');
  const nav = $('#nav-principal');
  if (botonMenu && nav) {
    botonMenu.addEventListener('click', () => {
      const abierto = nav.classList.toggle('abierto');
      botonMenu.setAttribute('aria-expanded', abierto);
    });
    $$('a', nav).forEach((a) => a.addEventListener('click', () => nav.classList.remove('abierto')));
  }

  // ---------- Parallax ----------
  // Cada elemento con data-velocidad se desplaza a esa fracción del scroll.
  // data-eje="x" lo mueve en horizontal (cintas de destinos).
  const capas = $$('[data-velocidad]');
  if (capas.length && !movimientoReducido) {
    let pendiente = false;
    const mover = () => {
      pendiente = false;
      const alto = innerHeight;
      for (const capa of capas) {
        const caja = (capa.closest('[data-parallax]') || capa.parentElement).getBoundingClientRect();
        if (caja.bottom < -200 || caja.top > alto + 200) continue; // fuera de la pantalla
        const progreso = (alto - caja.top) - (alto + caja.height) / 2; // 0 cuando la sección está centrada
        const d = progreso * parseFloat(capa.dataset.velocidad);
        capa.style.transform = capa.dataset.eje === 'x' ? `translate3d(${d}px,0,0)` : `translate3d(0,${d}px,0)`;
      }
    };
    const pedir = () => { if (!pendiente) { pendiente = true; requestAnimationFrame(mover); } };
    addEventListener('scroll', pedir, { passive: true });
    addEventListener('resize', pedir);
    mover();
  }

  // Inclinación suave del hero siguiendo al ratón
  const hero = $('[data-inclinar]');
  if (hero && !movimientoReducido && matchMedia('(pointer: fine)').matches) {
    const objetivos = $$('[data-profundidad]', hero);
    hero.addEventListener('pointermove', (e) => {
      const x = e.clientX / innerWidth - 0.5;
      const y = e.clientY / innerHeight - 0.5;
      objetivos.forEach((el) => {
        const p = parseFloat(el.dataset.profundidad);
        el.style.translate = `${x * p}px ${y * p}px`;
      });
    });
  }

  // ---------- Aparición al hacer scroll y contadores ----------
  const animarContador = (el) => {
    const final = parseFloat(el.dataset.contador);
    const sufijo = el.dataset.sufijo || '';
    const decimales = (el.dataset.contador.split('.')[1] || '').length;
    if (movimientoReducido) { el.textContent = final.toLocaleString('es-ES') + sufijo; return; }
    const inicio = performance.now();
    const paso = (t) => {
      const k = Math.min((t - inicio) / 1600, 1);
      const suave = 1 - Math.pow(1 - k, 3);
      el.textContent = (final * suave).toLocaleString('es-ES', { minimumFractionDigits: decimales, maximumFractionDigits: decimales }) + sufijo;
      if (k < 1) requestAnimationFrame(paso);
    };
    requestAnimationFrame(paso);
  };

  const observador = new IntersectionObserver((entradas) => {
    for (const entrada of entradas) {
      if (!entrada.isIntersecting) continue;
      const el = entrada.target;
      el.classList.add('visible');
      if (el.dataset.contador) animarContador(el);
      $$('[data-contador]', el).forEach(animarContador);
      $$('[data-ancho]', el).forEach((barra) => (barra.style.width = barra.dataset.ancho));
      observador.unobserve(el);
    }
  }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
  $$('[data-aparecer], [data-observar]').forEach((el) => observador.observe(el));

  // ---------- Pestañas de los paneles (con #hash para enlazarlas) ----------
  const enlacesPestana = $$('[data-pestana]');
  if (enlacesPestana.length) {
    const mostrar = (id, enfocar) => {
      const destino = document.getElementById(id);
      if (!destino || !destino.classList.contains('panel__seccion')) return;
      $$('.panel__seccion').forEach((s) => s.classList.toggle('oculto', s !== destino));
      enlacesPestana.forEach((a) => a.classList.toggle('activo', a.dataset.pestana === id));
      const titulo = $('[data-titulo-panel]');
      const enlace = enlacesPestana.find((a) => a.dataset.pestana === id);
      if (titulo && enlace) titulo.textContent = enlace.dataset.titulo || enlace.textContent.trim();
      $('.panel__lateral')?.classList.remove('abierto');
      $$('[data-observar]', destino).forEach((el) => observador.observe(el));
      if (enfocar) scrollTo({ top: 0, behavior: 'smooth' });
    };
    $$('[data-ir-a]').forEach((el) => el.addEventListener('click', (e) => {
      e.preventDefault();
      history.replaceState(null, '', '#' + el.dataset.irA);
      mostrar(el.dataset.irA, true);
    }));
    enlacesPestana.forEach((a) => a.addEventListener('click', (e) => {
      e.preventDefault();
      history.replaceState(null, '', '#' + a.dataset.pestana);
      mostrar(a.dataset.pestana, true);
    }));
    const inicial = location.hash.slice(1);
    if (inicial) mostrar(inicial, false);
  }
  $('[data-abrir-lateral]')?.addEventListener('click', () => $('.panel__lateral')?.classList.toggle('abierto'));

  // ---------- Buscador de las tablas de administración ----------
  $$('[data-buscar]').forEach((input) => {
    input.addEventListener('input', () => {
      const termino = input.value.trim().toLowerCase();
      $$('[data-filtrable] tbody tr, [data-filtrable] details').forEach((fila) => {
        fila.style.display = fila.textContent.toLowerCase().includes(termino) ? '' : 'none';
      });
    });
  });

  // ---------- Medidor de fuerza de la contraseña ----------
  const clave = $('[data-fuerza]');
  if (clave) {
    const barra = $('.fuerza i');
    const texto = $('[data-fuerza-texto]');
    clave.addEventListener('input', () => {
      const v = clave.value;
      const puntos = [v.length >= 8, /[a-z]/.test(v), /[A-Z]/.test(v), /\d/.test(v), /[^A-Za-z0-9]/.test(v)].filter(Boolean).length;
      const niveles = [['0%', 'transparent', ''], ['25%', '#d8343f', 'Muy débil'], ['45%', '#d8343f', 'Débil'], ['65%', '#f6b81a', 'Aceptable'], ['85%', '#12a37b', 'Fuerte'], ['100%', '#12a37b', 'Muy fuerte']];
      const [ancho, color, etiqueta] = niveles[v ? puntos : 0];
      barra.style.width = ancho;
      barra.style.backgroundColor = color;
      if (texto) texto.textContent = etiqueta;
    });
  }

  // Comprueba que las dos contraseñas coinciden antes de enviar
  const confirmar = $('[data-confirmar]');
  if (confirmar && clave) {
    const validar = () => confirmar.setCustomValidity(confirmar.value && confirmar.value !== clave.value ? 'Las contraseñas no coinciden' : '');
    confirmar.addEventListener('input', validar);
    clave.addEventListener('input', validar);
  }

  // ---------- Cuentas de la demo: rellenan el formulario de acceso ----------
  $$('[data-cuenta]').forEach((boton) => {
    boton.addEventListener('click', () => {
      $('#email').value = boton.dataset.cuenta;
      $('#password').value = 'Demo1234!';
      $('#password').focus();
    });
  });

  // ---------- Nombre del archivo elegido ----------
  $$('.selector-archivo input').forEach((input) => {
    input.addEventListener('change', () => {
      const etiqueta = input.parentElement.querySelector('span');
      if (etiqueta && input.files[0]) etiqueta.textContent = input.files[0].name;
    });
  });

  // ---------- Botones que envían: evitan el doble clic ----------
  $$('form').forEach((form) => form.addEventListener('submit', () => {
    const boton = form.querySelector('button[type=submit]');
    if (boton && form.checkValidity()) setTimeout(() => (boton.disabled = true), 0);
  }));

  // ---------- Chat: baja al último mensaje ----------
  $$('.chat').forEach((chat) => (chat.scrollTop = chat.scrollHeight));
})();
