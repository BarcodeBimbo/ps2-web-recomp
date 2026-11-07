# Phone access

Run **Setup.cmd** on the host PC. The desktop library opens at http://127.0.0.1:8620/ . Expand **Phone access** to find the mobile link, or copy it from the console.

The service automatically selects the PC's private LAN IPv4 address, generates its HTTPS certificates and binds a free OS-assigned port. It serves the installed game list and ready players. Desktop Store, downloads, builds, deletion and private keys remain inaccessible through this listener. Closing the host revokes the session link. Use the same Wi-Fi/LAN; Windows may prompt to allow Python through the firewall on Private networks.

You do not supply PEM files or type host/port arguments. Browser-native WebGPU and threaded WebAssembly require a trusted secure context: ordinary HTTP on a 192.168.x.x address cannot satisfy that requirement. On the phone, trust the host's local CA once. The **Download phone trust certificate** link in the desktop page provides only the public certificate; transfer it to the phone. iOS requires installing the profile and enabling trust under Settings → General → About → Certificate Trust Settings; Android's certificate settings vary by device/browser. Local CA support also varies by browser. The host cannot silently modify the phone's trust settings.

Keep tools/mobile private. The CA remains stable between restarts; the server certificate is renewed with the current IP automatically. A VPN or multiple LAN adapters can affect which private address the PC selects. If the console reports no LAN interface, connect Wi-Fi/Ethernet and restart Setup.cmd. If a link stops working after the PC changes IP, restart and copy the new link.

Mobile HTTPS and authentication tests pass with a synthetic disc. Physical Android/iOS performance, browser trust and WebGPU compatibility still require testing on the device.
