# Prato à Lupa — contexto para o Claude

Ficheiro lido automaticamente pelo Claude Code em cada sessão (local ou claude.ai/code).
Mantém-no atualizado quando algo importante mudar. Estado descrito: 2026-10-09.

## Quem é o utilizador e como trabalhar
- Filipe, estudante de Engenharia Informática (ISEC). Escreve em **português europeu**, informal.
- Respostas **concisas, diretas e técnicas**. Explica o porquê quando introduzires ferramentas ou conceitos novos (ele pergunta muito "porquê?" — explica o mecanismo por baixo, com exemplos concretos).
- **Não começar fases novas sem ele confirmar.** Dizer sempre o que não foi possível testar.
- Uso pessoal, **custo zero** é requisito.
- Ele tem ficheiros de apontamentos locais `NOTAS.txt` e `FLUXOS.txt` (no `.gitignore`, não estão no repo). Estilo: título `== Área: o que afeta ==` + 1–2 linhas (até ~4 quando é preciso o porquê), linguagem natural dele, sem diagramas. Ele acha "overkill" texto longo.
- Ele diz que o código é "vibe coded": não quer refatorar/organizar por agora.
- Atualiza a app fazendo push para `main` (GitHub Pages publica sozinho em ~1 min).

## O que é a app
PWA para telemóvel que estima calorias e macros (proteína, hidratos, gordura, fibra) de um prato a partir de um vídeo curto (~8 s a rodar à volta do prato). Extrai 8 fotogramas nítidos, manda-os a um modelo de visão, e mostra um rótulo nutricional com intervalo de kcal, componentes e gramas editáveis. Regista refeições por dia, com calendário.

- URL: https://filipegomes-code.github.io/CaloriesCounter-App/ (caminho sensível a maiúsculas)
- Repo público: github.com/filipegomes-code/CaloriesCounter-App (conta `filipegomes-code`)
- Aparelhos dele: Samsung Galaxy S24 Ultra (Chrome Android; login e sync testados lá) e Mac (Safari).

## Ficheiros
- `index.html` — tudo inline (HTML, CSS, JS num IIFE), ~1170 linhas, sem build. Secções marcadas com `// ---------- nome ----------`: definições, util, nitidez e captura, câmara ao vivo, ficheiros, análise, tabelas nutricionais, resultado, escolher o alimento na tabela, dias, cópia de segurança, sincronização, ligações.
- `sw.js` — service worker, rede primeiro, cache como fallback. **Sempre que mudares ficheiros, aumenta `CACHE` (`prato-a-lupa-vN`)** — atualmente v14.
- `manifest.webmanifest`, `icon.svg`, `icon-180/192/512.png`.
- `data/insa.json` (1376 alimentos, ~83 KB) e `data/usda.json` (7448, ~670 KB): `{fonte, versao, alimentos:[[id, nome, kcal, proteina, hidratos, gordura, fibra], ...]}`, valores por 100 g. Hidratos = disponíveis (sem fibra); no USDA a fibra foi subtraída ao "carbohydrate by difference".
- `tools/build_tables.py` — gera os dois JSON (INSA a partir do Excel do PortFIR, precisa de openpyxl; USDA a partir do CSV SR Legacy 2018-04). Instruções no topo do ficheiro.
- `firestore.rules` — regras do Firestore (cada utilizador só acede a `users/{uid}/**`). Têm de ser coladas na consola do Firebase quando mudarem.
- `README.md` — inclui os créditos das tabelas.
- `.gitignore` — `NOTAS.txt`, `FLUXOS.txt`, `.DS_Store`.

## Fluxo de análise
1. Entrada: câmara ao vivo (`getUserMedia`, só HTTPS/localhost), vídeo/fotos da galeria, ou gravar com a app da câmara. Fotogramas escolhidos por nitidez (variância do Laplaciano), lado maior 1024 px, JPEG.
2. IA escolhida nas definições: **Gemini** (por omissão, nível grátis) ou **Claude** (pago). Chaves coladas pelo utilizador, guardadas só em localStorage, enviadas diretamente do browser (Claude usa `anthropic-dangerous-direct-browser-access`).
   - Gemini: `gemini-3.8-flash` (omissão), `gemini-3.7-flash`, `gemini-3.5-flash-lite`. Em 503/500/404 repete uma vez e passa ao seguinte.
   - Claude: `claude-sonnet-5-5`, `claude-haiku-4-5-20251001`.
3. **Tabela nutricional** (definição `pal-table`: `ambas` por omissão / `insa` / `usda` / `ia`):
   - INSA: a lista `código|nome` (~45k caracteres, ~15k tokens) vai **no pedido, antes das imagens**; a IA devolve `"insa":"<código>"`. No Claude esse bloco leva `cache_control`. A app confirma que o código existe.
   - USDA: não cabe no pedido; a IA devolve `"usda":"<descrição inglesa estilo SR Legacy>"` e a app faz procura por palavras (`search()`, aceita se cobrir ≥60% das palavras; bónus por match exato).
   - Ordem: INSA → USDA → estimativa da IA (marcada "Estimativa da IA").
   - A app multiplica gramas × valores/100 g. A IA continua a devolver as suas estimativas (guardadas em `it.ia`) para poder voltar a elas.
   - Cada componente mostra a fonte (ex. "INSA: Arroz cozido simples · 125 kcal/100 g") com "Mudar" → diálogo de procura (separadores INSA/USDA, "Usar a estimativa da IA").
   - O intervalo kcal_min/max da IA é escalado pelo total final ÷ total original da IA.
4. O INSA exige crédito visível da fonte: está no rodapé da app ("Fonte: Base de Dados da Composição de Alimentos. INSA. v 7.1 - 2026") e no README.

## Dias e calendário
- localStorage `pal-days-v1`: `{open, metaUpd, days:[{id, date:"AAAA-MM-DD", start, end|null, upd, meals:[{id, nome, ts, hora, itens:[{nome, gramas, kcal, proteina, hidratos, gordura, fibra, per:{...por grama}|null, fonte?:{tab,id,nome}}]}]}]}`.
- "Começar o dia"/"Terminar o dia" com confirmação, não depende da hora. O dia fica na data em que começou. Se já existe um dia nessa data, reabre-o em vez de criar outro. Só pode haver um dia aberto.
- "Guardar refeição": se não houver dia aberto, pergunta se começa um.
- Refeições guardadas: expandir, editar gramas (recalcula via `per`), remover alimento, apagar refeição. Calendário mensal com kcal por dia, reabrir dia, média mensal (só dias terminados). Aviso se o dia estiver aberto há mais de 20 h.
- Migra o formato antigo (`pal-AAAA-MM-DD`, só totais; ficam sem gramas editáveis).
- Exportar/Importar JSON nas definições (sem as chaves; importar substitui tudo, também na conta se houver login).

## Sincronização (Firebase, opcional)
- Sem login: tudo só no aparelho. Com login Google: dias, refeições, dia aberto e tabela escolhida sincronizam. **A chave da IA nunca sincroniza** (decisão do Filipe: como dono do projeto veria as chaves de outros utilizadores).
- Projeto Firebase: `caloriescounter-app` (nº 222605303356), plano Spark grátis. Config em `FIREBASE_CONFIG` no index.html (não é secreta). Analytics ativado na consola mas a app não o carrega.
- SDK via `https://www.gstatic.com/firebasejs/13.0.0/` com `import()` dinâmico, só carregado ao entrar (ou se `pal-sync-on` estiver ativo). Firestore com `persistentLocalCache`.
- Modelo: `users/{uid}` = `{open, table, upd}`; `users/{uid}/days/{id}` = o dia. Cada alteração marca `upd`; ao juntar ganha o `upd` mais recente. No 1.º login, dias da mesma data criados em aparelhos diferentes são fundidos. `push()` envia só os dias cujo conteúdo mudou; `onSnapshot` aplica alterações de outros aparelhos (ignora `hasPendingWrites`).
- **Login**: botão oficial da Google (Google Identity Services, `accounts.google.com/gsi/client`) → ID token → `signInWithCredential`. Porquê: o `signInWithPopup` do Firebase passa pelo `firebaseapp.com` por um iframe, e o **Safari bloqueia** (armazenamento particionado/anti-rastreio), por isso o login nunca chegava à app. O popup antigo só é usado se `GOOGLE_CLIENT_ID` for null.
  - `GOOGLE_CLIENT_ID` = `566345685137-lvmkf8hfss94avlsrkfv1f5schmev27c.apps.googleusercontent.com`. **Está noutro projeto Google Cloud (nº 566345685137)**, não no do Firebase — por isso foi adicionado no Firebase em Authentication → Google → "lista de permissões de IDs de cliente de projetos externos". Origem autorizada: `https://filipegomes-code.github.io`.
  - O ecrã de consentimento está **Externo + modo de teste**: só entram os emails em "Utilizadores de teste". Publicar abriria a qualquer conta Google (os dados ficariam no Firebase dele).
  - Botão sempre tema `filled_black`, `pill`, largura medida ao abrir as definições (máx. 400 px); `#gisBtn iframe{color-scheme:light}` evita o fundo branco no modo escuro.
- Domínio autorizado no Firebase Auth: `filipegomes-code.github.io`.

## Outras definições
- Tema: `pal-theme` = `auto` (segue o sistema) / `dark` / `light`, aplicado via `data-theme` no `<html>` (script no `<head>` para não piscar). Não sincroniza.
- Chaves localStorage: `pal-provider`, `pal-gem-key`, `pal-gem-model`, `pal-cld-key`, `pal-cld-model`, `pal-table`, `pal-theme`, `pal-days-v1`, `pal-sync-on`, `pal-emu` (só testes).

## Como testar
- Servidor local: `python3 -m http.server 8765` na pasta (câmara ao vivo precisa de HTTPS ou localhost, não `file://`).
- Testes feitos com Playwright (Chromium e WebKit = motor do Safari), com respostas da IA simuladas por `page.route`. Instalar num diretório temporário (`npm i playwright`), não no repo.
- Sync: Firebase Emulator (`npx firebase emulators:start --project demo-pal --only auth,firestore`, precisa de Java; firebase-tools recente). Na app, com `localStorage.pal-emu="1"` em localhost liga aos emuladores e expõe `window.palEmuSignIn(sub, email)`. Nos testes substitui-se `FIREBASE_CONFIG` por `{apiKey:"fake-key",authDomain:"demo-pal.firebaseapp.com",projectId:"demo-pal",appId:"1:1:web:1"}`. Teste de dois "aparelhos" = dois browser contexts.
- O botão GIS só se desenha em origens autorizadas (no localhost aparece vazio).
- GitHub Pages: `cache-control: max-age=600`; no Safari recarregar com Cmd+Option+R. Ver deploy: `gh api repos/filipegomes-code/CaloriesCounter-App/pages/builds/latest`.

## Decisões e porquês
- GitHub Pages + Gemini grátis, sem servidor intermédio (custo zero). No nível grátis a Google pode usar os pedidos para treino; limites mudam (Flash ~20/dia não confirmado, Flash-Lite ~500/dia).
- Nunca pôr chaves de IA no repo (é público).
- A precisão depende sobretudo das **gramas** (volume) — maior fonte de erro. A tabela elimina o erro dos valores por 100 g.
- INSA no prompt (a IA percebe significados, ex. "bitoque" ↔ "Vaca, bife à café") vs procura por palavras no cliente (falha com sinónimos). Se ficar lento ou bater limites: pré-filtrar candidatos no cliente e mandar só esses (dois pedidos).

## Fase 3 (adiada): ARCore / profundidade
- Ideia: APK (Capacitor + plugin Kotlin ARCore Depth API, build no GitHub Actions) para medir o volume; a IA identifica, o volume dá as gramas.
- Testes de 2026-10-08 no S24: XR Blocks (WebXR) não funciona em telemóvel; Depth Lab (APK antigo via APKMirror, a Play Store esconde-a) mostra tudo vermelho a 40–60 cm — inconclusivo (escala de cores em metros). O S24 Ultra não tem ToF; a profundidade é por movimento (mais precisa a 0,5–5 m). Rodar no sítio não dá profundidade (precisa de translação).
- Se retomar: começar por um APK mínimo que mostre a distância em cm num ponto tocado. Só vale a pena se os testes de precisão mostrarem erro grande nas gramas.

## Pendentes
- Testes do Filipe: sync telemóvel↔PC no uso real; login com o botão novo no telemóvel/PWA instalada; Gemini real com a tabela (escolha dos códigos INSA, latência, limites); 4–5 pratos com rótulo para medir o erro (ele não tem balança).
- Ideia oferecida, não feita: aviso no topo do resultado com nº de alimentos sem tabela.
- Possível limpeza: clientes OAuth criados por engano na Google Cloud.
