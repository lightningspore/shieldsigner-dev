import { ShieldSignerPlus } from "./ShieldSignerPlus"
import data from "./generated/pill-board.json"

/** 0.0.12-dev eight-pin pill carrier; native KiCad remains authoritative. */
export default function PillCarrier() {
  return <ShieldSignerPlus data={data} />
}
