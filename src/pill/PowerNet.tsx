/** Explicit supply labels keep return paths local and the schematic readable. */
export function PowerNet({pin,net}:{pin:string,net:string}) {
  return <trace from={pin} to={net} schDisplayLabel={net.slice(4)}/>
}
