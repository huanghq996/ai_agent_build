import fs from "node:fs";

function mustExist(path) {
  if (!fs.existsSync(path)) throw new Error(`MISSING: ${path}`);
}

function main() {
  try {
    mustExist(".nvmrc");
    mustExist("pnpm-workspace.yaml");
    mustExist("package.json");
    mustExist("apps/web/package.json");
    mustExist("apps/server/pom.xml");
    mustExist("packages/api-contract/openapi.yaml");
    mustExist("packages/api-contract/error-codes.json");
    console.log("BUILD_OK");
  } catch (e) {
    console.error("BUILD_FAIL");
    console.error(String(e && e.message ? e.message : e));
    process.exit(1);
  }
}

main();

