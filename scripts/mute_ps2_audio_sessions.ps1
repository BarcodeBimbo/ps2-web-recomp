# Mute Windows audio sessions for ps2run / browser hosts without killing processes.
# God AUDIO_TO_ZERO runtime helper.
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Collections.Generic;

[Guid("87CE5498-68D6-44E5-9215-6DA47EF883D8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface ISimpleAudioVolume {
  int SetMasterVolume(float fLevel, ref Guid EventContext);
  int GetMasterVolume(out float pfLevel);
  int SetMute([MarshalAs(UnmanagedType.Bool)] bool bMute, ref Guid EventContext);
  int GetMute(out bool pbMute);
}
[Guid("BFB7FF88-7239-4FC9-8FA2-07C950BE9C6D"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionControl2 {
  int NotImpl0(); int NotImpl1(); int NotImpl2(); int NotImpl3(); int NotImpl4();
  int NotImpl5(); int NotImpl6(); int NotImpl7(); int NotImpl8();
  int GetSessionIdentifier([MarshalAs(UnmanagedType.LPWStr)] out string pRetVal);
  int GetSessionInstanceIdentifier([MarshalAs(UnmanagedType.LPWStr)] out string pRetVal);
  int GetProcessId(out uint pRetVal);
  int IsSystemSoundsSession();
  int SetDuckingPreference(bool optOut);
}
[Guid("E2F5BB11-0570-40CA-ACDD-3AA01277DEE8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionEnumerator {
  int GetCount(out int SessionCount);
  int GetSession(int SessionCount, out IAudioSessionControl2 Session);
}
[Guid("77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionManager2 {
  int NotImpl0(); int NotImpl1();
  int GetSessionEnumerator(out IAudioSessionEnumerator SessionEnum);
}
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {
  int Activate(ref Guid iid, int dwClsCtx, IntPtr pActivationParams, [MarshalAs(UnmanagedType.IUnknown)] out object ppInterface);
}
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {
  int EnumAudioEndpoints(int dataFlow, int dwStateMask, out object ppDevices);
  int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice ppDevice);
}
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
class MMDeviceEnumeratorComObject {}

public static class AudioMuteUtil {
  public static List<string> MutePids(int[] pids) {
    var notes = new List<string>();
    var set = new HashSet<uint>();
    foreach (var p in pids) set.Add((uint)p);
    var enumerator = (IMMDeviceEnumerator)(object)new MMDeviceEnumeratorComObject();
    IMMDevice device;
    enumerator.GetDefaultAudioEndpoint(0, 0, out device);
    Guid iid = typeof(IAudioSessionManager2).GUID;
    object o;
    device.Activate(ref iid, 23, IntPtr.Zero, out o);
    var mgr = (IAudioSessionManager2)o;
    IAudioSessionEnumerator sessions;
    mgr.GetSessionEnumerator(out sessions);
    int count;
    sessions.GetCount(out count);
    Guid ctx = Guid.Empty;
    int matched = 0;
    for (int i = 0; i < count; i++) {
      IAudioSessionControl2 ctl;
      sessions.GetSession(i, out ctl);
      uint pid;
      ctl.GetProcessId(out pid);
      if (!set.Contains(pid)) continue;
      matched++;
      var vol = ctl as ISimpleAudioVolume;
      if (vol == null) { notes.Add("pid=" + pid + " no_ISimpleAudioVolume"); continue; }
      float level; bool muted;
      vol.SetMasterVolume(0f, ref ctx);
      vol.SetMute(true, ref ctx);
      vol.GetMasterVolume(out level);
      vol.GetMute(out muted);
      notes.Add("pid=" + pid + " level=" + level + " muted=" + muted);
    }
    notes.Insert(0, "sessions_scanned=" + count + " matched=" + matched);
    return notes;
  }
}
'@

$names = @('ps2run','chrome','msedge','firefox','msedgewebview2')
$pids = @(Get-Process -Name $names -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id -Unique)
if (-not $pids) {
  Write-Output 'no_target_processes'
  exit 0
}
Write-Output ("target_pids=" + ($pids -join ','))
[AudioMuteUtil]::MutePids($pids) | ForEach-Object { $_ }
