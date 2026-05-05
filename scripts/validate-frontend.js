const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.resolve(__dirname, "..");
const htmlPath = path.join(root, "index.html");
const html = fs.readFileSync(htmlPath, "utf8");

const localAssets = [];
const assetPattern = /\b(?:src|href)=["']([^"']+)["']/g;
let match;

while ((match = assetPattern.exec(html)) !== null) {
  const asset = match[1].split("?")[0];
  if (/^(https?:|#|data:|mailto:)/.test(asset)) continue;
  localAssets.push(asset);
}

const missingAssets = localAssets.filter((asset) => !fs.existsSync(path.join(root, asset)));
if (missingAssets.length) {
  console.error(`Missing frontend assets: ${missingAssets.join(", ")}`);
  process.exit(1);
}

const scripts = ["static/js/secrets.js", "static/js/api-engine.js", "static/js/app-core.js", "static/js/firebase-init.js"];
for (const script of scripts) {
  const source = fs.readFileSync(path.join(root, script), "utf8");
  const parseableSource = source.replace(/^import\s+.*?;$/gm, "");
  try {
    new vm.Script(parseableSource, { filename: script });
  } catch (error) {
    console.error(`${script}: ${error.message}`);
    process.exit(1);
  }
}

if (!html.includes('src="static/js/secrets.js') || html.indexOf("static/js/secrets.js") > html.indexOf("static/js/firebase-init.js")) {
  // Check if it's versioned: src="static/js/secrets.js?v=..."
  if (!/src="static\/js\/secrets\.js(?:\?v=[^"]+)?"/.test(html)) {
    console.error("secrets.js must load before firebase-init.js");
    process.exit(1);
  }
}

console.log("OK - Frontend assets and scripts are valid");
