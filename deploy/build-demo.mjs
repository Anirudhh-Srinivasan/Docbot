import {mkdir, readFile, writeFile} from 'node:fs/promises';

const backend = new URL(process.env.DOCBOT_BACKEND_URL);
if (backend.protocol !== 'https:') throw new Error('Set DOCBOT_BACKEND_URL to your HTTPS backend');
const html = await readFile('static/demo.html', 'utf8');
await mkdir('dist', {recursive: true});
await writeFile('dist/index.html', html.replace('src="/static/widget.js"', `src="${backend.origin}/static/widget.js"`));
