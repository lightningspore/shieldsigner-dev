import { spawn } from "node:child_process"
import { resolve } from "node:path"
// Keep the CLI scanner away from mounted KiCad apps and private OS/Telegram data.
const child = spawn(process.execPath, [resolve("node_modules/@tscircuit/cli/dist/cli/main.js"), "dev", "board.circuit.json", "--port", "3020"], {cwd: resolve("dist/tscircuit-preview"), stdio: "inherit"})
for (const signal of ["SIGINT", "SIGTERM"] as const) process.on(signal, () => child.kill(signal))
child.on("exit", code => process.exit(code ?? 1))
