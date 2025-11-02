const fs = require("fs");
const path = require("path");

const ROUTES_DIR = path.join(__dirname, "src/routes"); // adjust if needed

function checkFile(filePath) {
  const content = fs.readFileSync(filePath, "utf-8");
  const lines = content.split("\n");

  lines.forEach((line, index) => {
    const routerRegex = /router\.(get|post|put|delete|patch)\(([^)]+)\)/;
    const match = line.match(routerRegex);
    if (match) {
      const routePath = match[2].trim();
      // Remove quotes
      const cleaned = routePath.replace(/^['"`]/, "").replace(/['"`]$/, "");
      // Check for invalid patterns
      if (/https?:\/\//.test(cleaned) || cleaned.includes("://") || /[^\/:a-zA-Z0-9_\-{}]/.test(cleaned)) {
        console.log(`❌ Invalid route in ${filePath}:${index + 1} -> ${cleaned}`);
      }
    }
  });
}

function walkDir(dir) {
  const files = fs.readdirSync(dir);
  files.forEach((file) => {
    const fullPath = path.join(dir, file);
    if (fs.statSync(fullPath).isDirectory()) {
      walkDir(fullPath);
    } else if (fullPath.endsWith(".js")) {
      checkFile(fullPath);
    }
  });
}

walkDir(ROUTES_DIR);
