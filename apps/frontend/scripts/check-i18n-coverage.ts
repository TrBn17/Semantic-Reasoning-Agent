import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(process.cwd(), "src");
const TARGET_EXTENSIONS = new Set([".tsx", ".ts"]);
const JSX_TEXT_REGEX = />\s*([A-Za-z][^<{]{2,})\s*</g;
const PROP_REGEX =
  /\b(?:placeholder|title|aria-label|label)\s*=\s*(?:"([^"]*[A-Za-z][^"]*)"|'([^']*[A-Za-z][^']*)')/g;
const STRING_CALL_REGEX =
  /\b(?:toast\.(?:error|success|warning)|new Error)\(\s*(?:"([^"]*[A-Za-z][^"]*)"|'([^']*[A-Za-z][^']*)')/g;

function walk(dir: string, out: string[]) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "i18n") continue;
      walk(full, out);
      continue;
    }
    if (TARGET_EXTENSIONS.has(path.extname(entry.name))) {
      out.push(full);
    }
  }
}

function isIgnorable(text: string): boolean {
  return (
    !text ||
    text.includes("className") ||
    text.includes("http") ||
    text.startsWith("/") ||
    text === "all"
  );
}

const files: string[] = [];
walk(ROOT, files);

let issues = 0;
for (const file of files) {
  const content = fs.readFileSync(file, "utf8");
  const matches = [
    ...content.matchAll(JSX_TEXT_REGEX),
    ...content.matchAll(PROP_REGEX),
    ...content.matchAll(STRING_CALL_REGEX),
  ].filter((match) => {
    const text = (match[1] ?? match[2] ?? "").trim();
    return !isIgnorable(text);
  });

  if (matches.length > 0) {
    issues += matches.length;
    console.log(`${path.relative(process.cwd(), file)}: ${matches.length} potential literal(s)`);
  }
}

if (issues > 0) {
  console.warn(`Found ${issues} potential literal UI strings.`);
  if (process.env.I18N_STRICT === "1") {
    process.exitCode = 1;
  }
} else {
  console.log("No literal UI strings detected.");
}
