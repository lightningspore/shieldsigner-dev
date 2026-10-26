// Export original-symbol inventory and selected pseudocode for a reproducible RE session.
// @category ShieldSigner
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import com.google.gson.*;
import java.nio.file.*;
import java.util.*;

public class ExportRkaiq extends GhidraScript {
 public void run() throws Exception {
  Path output=Paths.get(getScriptArgs()[0]); Files.createDirectories(output);
  Gson gson=new GsonBuilder().setPrettyPrinting().create();
  ArrayList<Map<String,Object>> functions=new ArrayList<>();
  DecompInterface decompiler=new DecompInterface();
  decompiler.openProgram(currentProgram);
  int recovered=0;
  for(Function function:currentProgram.getFunctionManager().getFunctions(true)) {
   if(monitor.isCancelled())break;
   String name=function.getName();
   Map<String,Object> entry=new LinkedHashMap<>();
   entry.put("name",name); entry.put("entry",function.getEntryPoint().toString());
   entry.put("bodyBytes",function.getBody().getNumAddresses());
   entry.put("external",function.isExternal());
   entry.put("signature",function.getSignature().toString());
   functions.add(entry);
   boolean select=currentProgram.getName().contains("3A_server") || name.contains("interpolation") || name.contains("Interpolate") || name.contains("InterpLut") || name.contains("AdpccInterpolation") || name.contains("gain_fix_transfer") || name.contains("gain_float_lim2_int") || name.contains("gain_select_params_by_ISO") || name.contains("convertAiqAwbGainToIsp32Params") || name.contains("convertAiqExpIspDgainToIsp32Params") || name.contains("get_v4l2_pixelformat") || name.contains("get_sensor_desc") || name.contains("get_sensor_fps") || name.contains("get_nr_switch") || name.contains("get_dcg_ratio") || name.contains("SensorHw9get_blank") || name.contains("SensorHw9get_pixel") || name.contains("get_exposure_range") || name.equals("AeReal2RegConv") || name.equals("mapSensorExpToHal") || name.contains("setLinearSensorExposureEP17") || name.equals("ClmExecute") || name.contains("ClmCalcHistTriangle") || name.equals("AecRun") || name.contains("AecClmExecute") || name.contains("AecDynamicDamp") || name.contains("AecClmExpChkForEnv") || name.contains("calcAec") || name.contains("getBindedSnsEntNmByVd") || (name.contains("RkAiqResourceTranslatorV32") && (name.contains("translateAecStats") || name.contains("translateAwbStats"))) || name.equals("rk_aiq_uapi2_getVersionInfo") || name.contains("wbgainConvert2");
   if(getScriptArgs().length > 1) select=name.matches(getScriptArgs()[1]);
   if(select&&!function.isExternal()&&!function.isThunk()) {
    DecompileResults result=decompiler.decompileFunction(function,45,monitor);
    entry.put("decompileCompleted",result.decompileCompleted());
    entry.put("error",result.getErrorMessage());
    if(result.decompileCompleted()) {
     String file=function.getEntryPoint()+"-"+name.replaceAll("[^a-zA-Z0-9_.-]","_")+".c";
     Files.writeString(output.resolve(file),"/* Original binary symbol: "+name+"; entry: "+function.getEntryPoint()+".\n * Ghidra pseudocode; inferred types require verification. */\n"+result.getDecompiledFunction().getC());
     entry.put("pseudocode",file); recovered++;
    }
   }
  }
  Files.writeString(output.resolve("functions.json"),gson.toJson(functions)+"\n");
  decompiler.dispose();println("RKAIQ EXPORT "+currentProgram.getName()+": "+functions.size()+" functions; "+recovered+" selected decompiled");
 }
}
