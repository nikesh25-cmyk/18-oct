import { createHash } from 'node:crypto';
import { readFile, writeFile, rename, unlink } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const args = process.argv.slice(2);
const value = (flag) => args[args.indexOf(flag) + 1];
if (!args.includes('--source') || !args.includes('--output')) {
  process.stderr.write('usage: node export_world_atlas.mjs --source map.js --output atlas.json [--expected-count 23]\n');
  process.exit(2);
}
const source = resolve(value('--source'));
const output = resolve(value('--output'));
const expected = args.includes('--expected-count') ? Number(value('--expected-count')) : null;

const rectsOverlap = (a, b) => a.x < b.x + b.width && b.x < a.x + a.width &&
  a.y < b.y + b.height && b.y < a.y + a.height;

try {
  const raw = await readFile(source);
  const { MAP_COLUMNS, MAP_ROWS, MAP_LAYOUT } = await import(pathToFileURL(source).href);
  if (MAP_COLUMNS !== 288 || MAP_ROWS !== 208 || !Array.isArray(MAP_LAYOUT) ||
      MAP_LAYOUT.length === 0 || (expected !== null && MAP_LAYOUT.length !== expected))
    throw new Error('atlas dimensions or region count mismatch');
  const seen = new Set();
  for (const region of MAP_LAYOUT) {
    const { world, x, y, width, height } = region;
    if (typeof world !== 'string' || !world || seen.has(world) ||
        ![x, y, width, height].every(Number.isSafeInteger) ||
        x < 0 || y < 0 || width < 1 || height < 1 ||
        x + width > MAP_COLUMNS || y + height > MAP_ROWS)
      throw new Error(`invalid, duplicate or out-of-bounds region: ${world}`);
    seen.add(world);
  }
  for (let i = 0; i < MAP_LAYOUT.length; i++)
    for (let j = i + 1; j < MAP_LAYOUT.length; j++)
      if (rectsOverlap(MAP_LAYOUT[i], MAP_LAYOUT[j]))
        throw new Error(`overlapping regions: ${MAP_LAYOUT[i].world}, ${MAP_LAYOUT[j].world}`);
  const packageData = {
    format: 'nemoworld-unity-atlas-v1',
    bounds: [MAP_COLUMNS, MAP_ROWS],
    source_sha256: createHash('sha256').update(raw).digest('hex'),
    regions: MAP_LAYOUT.map(({ world, x, y, width, height }) => ({ world, x, y, width, height })),
  };
  const temporary = output + '.tmp';
  try {
    await writeFile(temporary, JSON.stringify(packageData, null, 2) + '\n');
    await rename(temporary, output);
  } finally { await unlink(temporary).catch(() => {}); }
  process.stdout.write(`Exported ${MAP_LAYOUT.length} regions\n`);
} catch (error) {
  process.stderr.write(`atlas export failed: ${error.message}\n`);
  process.exitCode = 1;
}
