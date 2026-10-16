import { readFileSync, writeFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
const root = fileURLToPath(new URL('../', import.meta.url));
const source = readFileSync(resolve(root, 'src/app.ts'), 'utf8');
const js = '// Generated from src/app.ts. Run npm run build.\n' + stripTypeScriptTypes(source, { mode: 'strip' });
const tokens = JSON.parse(readFileSync(resolve(root, 'tokens.json'), 'utf8'));
const css = '/* Generated from tokens.json. Run npm run build. */\n:root {\n' + Object.entries(tokens).map(([key, value]) => `  --${key}: ${value};`).join('\n') + '\n}\n';
const styles = readFileSync(resolve(root, 'styles.css'), 'utf8');
const template = readFileSync(resolve(root, 'src/catalog.html'), 'utf8');
const html = template.replace('<link rel="stylesheet" href="tokens.css">', '<style>\n' + css + '\n</style>')
  .replace('<link rel="stylesheet" href="styles.css">', '<style>\n' + styles + '\n</style>')
  .replace('<script src="app.js" defer></script>', '')
  .replace('</body>', '<script>\n' + js.replaceAll('</script', '<\\/script') + '\n</script></body>');
for (const [name, data] of [['app.js', js], ['tokens.css', css], ['index.html', html]]) {
  if (process.argv.includes('--check')) {
    if (readFileSync(resolve(root, name), 'utf8') !== data) throw new Error(`${name} is stale: npm run build`);
  } else writeFileSync(resolve(root, name), data);
}
console.log(process.argv.includes('--check') ? 'Generated files match their sources.' : 'Built self-contained index.html, app.js and tokens.css; no runtime dependencies.');
