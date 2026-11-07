import { chromium } from 'phantomwright';
import { existsSync } from 'node:fs';
process.exitCode = existsSync(chromium.executablePath()) ? 0 : 1;
