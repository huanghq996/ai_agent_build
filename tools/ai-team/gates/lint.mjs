import fs from "node:fs";
import path from "node:path";

function isTextFile(path) {
  return !/\.(png|jpg|jpeg|gif|ico|jar|zip|gz|pdf)$/i.test(path);
}

function checkTrailingWhitespace(content) {
  const lines = content.split("\n");
  const violations = [];
  for (let i = 0; i < lines.length; i += 1) {
    if (/[ \t]+$/.test(lines[i])) violations.push(i + 1);
  }
  return violations;
}

function walkDir(root, rel = "", files = []) {
  const full = path.join(root, rel);
  const entries = fs.readdirSync(full, { withFileTypes: true });
  for (const ent of entries) {
    const relPath = path.join(rel, ent.name);
    if (ent.isDirectory()) {
      if (
        ent.name === ".git" ||
        ent.name === "node_modules" ||
        relPath === path.join("docs", "ops", "logs") ||
        ent.name === "target" ||
        ent.name === ".cache"
      ) {
        continue;
      }
      walkDir(root, relPath, files);
      continue;
    }
    if (ent.isFile()) files.push(relPath);
  }
  return files;
}

function main() {
  const errors = [];
  const repoRoot = process.cwd();
  const files = walkDir(repoRoot).filter((p) => p !== ".env");

  for (const file of files) {
    if (!isTextFile(file)) continue;
    const buf = fs.readFileSync(file);
    if (buf.includes(0)) continue;
    const text = buf.toString("utf-8");

    if (text.length > 0 && !text.endsWith("\n")) {
      errors.push(`${file}: missing trailing newline`);
    }

    const ws = checkTrailingWhitespace(text);
    for (const line of ws.slice(0, 20)) {
      errors.push(`${file}:${line}: trailing whitespace`);
    }
  }

  // WEB rule: forbid direct axios import outside http.js
  const webPrefix = path.join("apps", "web") + path.sep;
  for (const file of files) {
    if (!file.startsWith(webPrefix)) continue;
    if (!/\.(js|vue)$/i.test(file)) continue;
    if (file === path.join("apps", "web", "src", "api", "http.js")) continue;
    const text = fs.readFileSync(file, "utf-8");
    if (/\bfrom\s+['"]axios['"]/.test(text) || /\brequire\(\s*['"]axios['"]\s*\)/.test(text)) {
      errors.push(`WEB_AXIOS_DIRECT_IMPORT: ${file}`);
    }
  }

  if (errors.length > 0) {
    console.error("LINT_FAIL");
    for (const e of errors) console.error(` - ${e}`);
    process.exit(1);
  }

  console.log("LINT_OK");
}

main();
