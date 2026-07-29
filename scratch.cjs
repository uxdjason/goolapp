const fs = require('fs');
const files = fs.readdirSync('src/content/apps');
let apps = [];
files.forEach(f => {
  const content = fs.readFileSync('src/content/apps/' + f, 'utf8');
  const m1 = content.match(/title:\s*(.+)/);
  const m2 = content.match(/publishedAt:\s*(.+)/);
  if (m1 && m2) {
    let t = m1[1].trim();
    if(t.startsWith('"') && t.endsWith('"')) t = t.slice(1, -1);
    if(t.startsWith("'") && t.endsWith("'")) t = t.slice(1, -1);
    apps.push({title: t, pub: m2[1].trim()});
  }
});
apps.sort((a, b) => a.title.localeCompare(b.title, 'ko-KR'));
console.log(apps.slice(0, 10));
