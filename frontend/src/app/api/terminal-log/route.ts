import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { level = 'info', message = '', route = '', details } = body;
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });

    // ANSI color codes
    const cyan = '\x1b[36m';
    const green = '\x1b[32m';
    const yellow = '\x1b[33m';
    const red = '\x1b[31m';
    const magenta = '\x1b[35m';
    const dim = '\x1b[2m';
    const bold = '\x1b[1m';
    const reset = '\x1b[0m';

    let badge = `${cyan}[INFO]${reset}`;
    const lvl = (level || '').toLowerCase();

    if (lvl === 'action') {
      badge = `${yellow}${bold}⚡ [USER ACTION]${reset}`;
    } else if (lvl === 'nav' || lvl === 'navigation') {
      badge = `${magenta}${bold}🧭 [PAGE VIEW]${reset}`;
    } else if (lvl === 'api') {
      badge = `${green}📡 [API CALL]${reset}`;
    } else if (lvl === 'auth') {
      badge = `${yellow}${bold}🔐 [AUTH]${reset}`;
    } else if (lvl === 'error') {
      badge = `${red}${bold}🚨 [CLIENT ERROR]${reset}`;
    } else if (lvl === 'warn' || lvl === 'warning') {
      badge = `${yellow}⚠️  [CLIENT WARN]${reset}`;
    }

    const routeStr = route ? ` ${cyan}(${route})${reset}` : '';
    const detailsStr = details && Object.keys(details).length > 0 ? ` ${dim}${JSON.stringify(details)}${reset}` : '';

    console.log(`${dim}${time}${reset} ${badge}${routeStr} ${message}${detailsStr}`);

    return NextResponse.json({ success: true });
  } catch {
    return NextResponse.json({ success: false }, { status: 400 });
  }
}
