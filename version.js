const fs = require('fs');
const path = require('path');

const root = __dirname;

function read(file) {
  return fs.readFileSync(path.join(root, file), 'utf8');
}

function write(file, content) {
  fs.writeFileSync(path.join(root, file), content, 'utf8');
}

function writeJson(file, updater) {
  const filePath = path.join(root, file);
  if (!fs.existsSync(filePath)) return false;
  const json = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  const original = JSON.stringify(json);
  updater(json);
  if (JSON.stringify(json) === original) return false;
  fs.writeFileSync(filePath, `${JSON.stringify(json, null, 2)}\n`, 'utf8');
  console.log(`updated ${file}`);
  return true;
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

function semverToVersionCode(version) {
  const m = version.match(/^(\d+)\.(\d+)\.(\d+)$/);
  if (!m) throw new Error(`Invalid semver: ${version}`);
  const major = Number(m[1]);
  const minor = Number(m[2]);
  const patch = Number(m[3]);
  if (minor > 999 || patch > 999) {
    throw new Error(
      `Android versionCode supports minor/patch <= 999: ${version}`
    );
  }
  return major * 1000000 + minor * 1000 + patch;
}

function syncAndroidGradle(version) {
  const gradlePath = path.join(root, 'frontend/android/app/build.gradle');
  if (!fs.existsSync(gradlePath)) {
    console.error('skip android gradle sync (project not present)');
    return false;
  }
  const versionCode = semverToVersionCode(version);
  const text = fs.readFileSync(gradlePath, 'utf8');
  const updated = text
    .replace(/versionCode\s+\d+/, `versionCode ${versionCode}`)
    .replace(/versionName\s+"[^"]+"/, `versionName "${version}"`);
  if (updated === text) {
    console.error('android build.gradle already up to date');
    return false;
  }
  fs.writeFileSync(gradlePath, updated, 'utf8');
  console.error(
    `updated frontend/android/app/build.gradle (${version}, code ${versionCode})`
  );
  return true;
}

const arg = process.argv[2] || 'patch';
const oldVersion = currentVersion();

if (arg === '--current') {
  console.log(oldVersion);
  process.exit(0);
}

if (arg === '--sync-android') {
  syncAndroidGradle(oldVersion);
  console.log(oldVersion);
  process.exit(0);
}

const newVersion = bump(oldVersion, arg);

if (oldVersion === newVersion) {
  console.log(`Syncing version ${newVersion}`);
} else {
  console.log(`Bumping ${oldVersion} -> ${newVersion}`);
}

const replacements = [
  ['downtify/__init__.py', /__version__\s*=\s*['"][^'"]+['"]/, `__version__ = '${newVersion}'`],
  ['pyproject.toml', /version\s*=\s*["'][^"']+["']/, `version = "${newVersion}"`],
  ['Makefile', /DOWNTIFY_VERSION := .*/, `DOWNTIFY_VERSION := ${newVersion}`],
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

writeJson('frontend/package.json', (json) => {
  json.version = newVersion;
});

writeJson('frontend/package-lock.json', (json) => {
  json.version = newVersion;
  if (json.packages && json.packages['']) {
    json.packages[''].version = newVersion;
  }
});

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

syncAndroidGradle(newVersion);

console.log(newVersion);
