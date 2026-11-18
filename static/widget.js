// Load once per script tag. Keep the host site's CSS outside the chat panel.
(() => {
  const script = document.currentScript;
  const site = script.dataset.site;
  if (!/^[a-z0-9][a-z0-9-]{0,47}$/.test(site || '')) return;
  const url = new URL('/', script.src);
  url.searchParams.set('site', site);
  function mount() {
    const host = document.createElement('div');
    const root = host.attachShadow({mode: 'open'});
    root.innerHTML = `<style>
      :host{all:initial;position:fixed;right:max(14px,env(safe-area-inset-right));bottom:max(14px,env(safe-area-inset-bottom));z-index:2147483000}
      section{display:flex;flex-direction:column;align-items:flex-end;gap:8px}
      button{font:600 15px/1.2 system-ui,sans-serif;color:#fff;background:#454bc5;border:0;border-radius:28px;padding:15px 20px;cursor:pointer;box-shadow:0 3px 16px #10153636}
      iframe{width:min(400px,calc(100vw - 28px));height:min(570px,calc(100dvh - 90px));border:1px solid #ccd2e1;border-radius:16px;background:white;box-shadow:0 10px 40px #10153638}
      [hidden]{display:none}
    </style><section><iframe id="panel" title="Documentation support" hidden></iframe><button type="button" aria-controls="panel" aria-expanded="false">Ask support</button></section>`;
    const button = root.querySelector('button');
    const panel = root.querySelector('iframe');
    button.addEventListener('click', () => {
      panel.hidden = !panel.hidden;
      if (!panel.hidden && !panel.hasAttribute('src')) panel.src = url.href;
      button.textContent = panel.hidden ? 'Ask support' : 'Close chat';
      button.setAttribute('aria-expanded', String(!panel.hidden));
      if (!panel.hidden) panel.focus();
    });
    document.body.append(host);
  }
  if (document.body) mount();
  else document.addEventListener('DOMContentLoaded', mount, {once: true});
})();
