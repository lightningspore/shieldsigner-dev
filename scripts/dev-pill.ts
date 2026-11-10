import{spawn}from'node:child_process'
import{resolve}from'node:path'
// A source preview with a narrow project root; no generated JSON or private-file scan.
const child=spawn(process.execPath,[resolve('node_modules/@tscircuit/cli/cli/entrypoint.js'),'dev','PillCarrier.tsx','--port','3020'],{cwd:resolve('src'),stdio:'inherit'})
for(const signal of ['SIGINT','SIGTERM']as const)process.on(signal,()=>child.kill(signal))
child.on('exit',code=>process.exit(code??1))
