// Correct the six integer/pointer arguments of mapSensorExpToHal before
// decompiling its callers. Verified against the ARM call setup, not float VFP args.
// @category ShieldSigner
import ghidra.app.script.GhidraScript;
import ghidra.program.model.data.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.SourceType;
public class FixAecMapAbi extends GhidraScript {
 public void run() throws Exception {
  Function f=getFunctionAt(toAddr(0xbe558));
  if(f==null||!f.getName().equals("mapSensorExpToHal"))throw new Exception("Pinned function missing");
  DataType fp=new PointerDataType(FloatDataType.dataType,4);
  f.setReturnType(IntegerDataType.dataType,SourceType.USER_DEFINED);
  f.replaceParameters(Function.FunctionUpdateType.DYNAMIC_STORAGE_ALL_PARAMS,true,SourceType.USER_DEFINED,
    new ParameterImpl("context",new PointerDataType(VoidDataType.dataType,4),currentProgram),
    new ParameterImpl("gainCode",UnsignedIntegerDataType.dataType,currentProgram),
    new ParameterImpl("timeCode",UnsignedIntegerDataType.dataType,currentProgram),
    new ParameterImpl("dcg",IntegerDataType.dataType,currentProgram),
    new ParameterImpl("gainOut",fp,currentProgram),
    new ParameterImpl("timeOut",fp,currentProgram));
  println(f.getSignature().toString());
 }
}
