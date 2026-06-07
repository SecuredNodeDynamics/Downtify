const fs = require('fs');
const path = require('path');

const root = __dirname;

function read(file) {
  return fs.readFileSync(path.join(root, file), 'utf8');
}

function write(file, content) {
  fs.writeFileSync(path.join(root, file), content, 'utf8');
}

function currentVersion() {
  const text = read('downtify/__init__.py');
  const match = text.match(/__version__\s*=\s*['"]([^'"]+)['"]/);
  if (!match) throw new Error('Could not find __version__ in downtify/__init__.py');
  return match[1];
}

function bump(version, part) {
  const m = version.match(/^(\d+)\.(\d+)\.(\d+)$/);
  if (!m) throw new Error(`Invalid semver: ${version}`);
  let major = Number(m[1]);
  let minor = Number(m[2]);
  let patch = Number(m[3]);

  if (part === 'patch') patch += 1;
  else if (part === 'minor') { minor += 1; patch = 0; }
  else if (part === 'major') { major += 1; minor = 0; patch = 0; }
  else if (/^\d+\.\d+\.\d+$/.test(part)) return part;
  else throw new Error(`Invalid bump part: ${part}`);

  return `${major}.${minor}.${patch}`;
}

const arg = process.argv[2] || 'patch';
const oldVersion = currentVersion();
const newVersion = bump(oldVersion, arg);

if (oldVersion === newVersion) {
  console.log(`Already at version ${newVersion}`);
  process.exit(0);
}

console.log(`Bumping ${oldVersion} -> ${newVersion}`);

const replacements = [
  ['downtify/__init__.py', /__version__\s*=\s*['"][^'"]+['"]/, `__version__ = '${newVersion}'`],
  ['pyproject.toml', /version\s*=\s*["'][^"']+["']/, `version = "${newVersion}"`],
  ['frontend/package.json', /"version"\s*:\s*"[^"]+"/, `"version": "${newVersion}"`],
  ['Makefile', /DOWNTIFY_VERSION := .*/, `DOWNTIFY_VERSION := ${newVersion}`],
  ['frontend/src/components/Hero.vue', /\|\|\s*'[^']+'/, `|| '${newVersion}'`],
];

for (const [file, pattern, replacement] of replacements) {
  const filePath = path.join(root, file);
  if (!fs.existsSync(filePath)) continue;
  const original = fs.readFileSync(filePath, 'utf8');
  const updated = original.replace(pattern, replacement);
  if (updated !== original) {
    fs.writeFileSync(filePath, updated, 'utf8');
    console.log(`updated ${file}`);
  }
}

const dockerfile = path.join(root, 'Dockerfile');
if (fs.existsSync(dockerfile)) {
  let text = fs.readFileSync(dockerfile, 'utf8');
  const oldText = text;
  text = text
    .replace(/LABEL version="[^"]+"/, `LABEL version="${newVersion}"`)
    .replace(/org\.opencontainers\.image\.version="[^"]+"/, `org.opencontainers.image.version="${newVersion}"`);
  if (text !== oldText) {
    fs.writeFileSync(dockerfile, text, 'utf8');
    console.log('updated Dockerfile');
  }
}

console.log(newVersion);