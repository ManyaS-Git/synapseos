const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const OUTPUT_DIR = path.join(__dirname, '..', 'docs', 'images');

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

async function run() {
  console.log('Launching Edge for crisp 2x application captures...');
  const browser = await puppeteer.launch({
    executablePath: EDGE_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--window-size=1600,1050',
    ],
    defaultViewport: {
      width: 1600,
      height: 1050,
      deviceScaleFactor: 2,
    },
  });

  try {
    const page = await browser.newPage();

    // 1. Dashboard Overview
    console.log('Capturing Real Dashboard Overview...');
    await page.goto('http://localhost:3000/showcase?tab=Overview', { waitUntil: 'networkidle2', timeout: 30000 });
    await new Promise(r => setTimeout(r, 2000));
    const overviewPath = path.join(OUTPUT_DIR, 'real_dashboard_overview.png');
    await page.screenshot({ path: overviewPath });
    console.log('Saved:', overviewPath);

    // 2. Assistant Copilot
    console.log('Capturing Real Assistant Copilot...');
    await page.goto('http://localhost:3000/showcase?tab=Assistant', { waitUntil: 'networkidle2', timeout: 30000 });
    await new Promise(r => setTimeout(r, 2000));
    // Click on the prompt to start an active reasoning view
    try {
      await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const promptBtn = buttons.find(b => b.textContent && b.textContent.includes('What did I decide'));
        if (promptBtn) promptBtn.click();
      });
      await new Promise(r => setTimeout(r, 1500));
    } catch {}
    const assistantPath = path.join(OUTPUT_DIR, 'real_assistant_copilot.png');
    await page.screenshot({ path: assistantPath });
    console.log('Saved:', assistantPath);

    // 3. Memory Manager
    console.log('Capturing Real Memory Manager...');
    await page.goto('http://localhost:3000/showcase?tab=Memory', { waitUntil: 'networkidle2', timeout: 30000 });
    await new Promise(r => setTimeout(r, 2000));
    const memPath = path.join(OUTPUT_DIR, 'real_memory_manager.png');
    await page.screenshot({ path: memPath });
    console.log('Saved:', memPath);

    // 4. Interactive Knowledge Graph
    console.log('Capturing Real Knowledge Graph...');
    await page.goto('http://localhost:3000/showcase?tab=Graph', { waitUntil: 'networkidle2', timeout: 30000 });
    await new Promise(r => setTimeout(r, 2500));
    const graphPath = path.join(OUTPUT_DIR, 'real_knowledge_graph.png');
    await page.screenshot({ path: graphPath });
    console.log('Saved:', graphPath);

    // 5. Landing Page Hero
    console.log('Capturing Landing Page Hero...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle2', timeout: 30000 });
    await new Promise(r => setTimeout(r, 2000));
    const heroPath = path.join(OUTPUT_DIR, 'real_landing_hero.png');
    await page.screenshot({ path: heroPath, fullPage: false });
    console.log('Saved:', heroPath);

    // 6. Features section
    console.log('Capturing Features Section...');
    await page.evaluate(() => {
      const el = document.getElementById('how-it-works') || document.getElementById('features');
      if (el) el.scrollIntoView();
    });
    await new Promise(r => setTimeout(r, 1500));
    const featPath = path.join(OUTPUT_DIR, 'real_features.png');
    await page.screenshot({ path: featPath, fullPage: false });
    console.log('Saved:', featPath);

    // 7. Login Page
    console.log('Capturing Login Page...');
    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle2', timeout: 30000 });
    await new Promise(r => setTimeout(r, 1500));
    const loginPath = path.join(OUTPUT_DIR, 'real_login.png');
    await page.screenshot({ path: loginPath, fullPage: false });
    console.log('Saved:', loginPath);

    // 8. Register Page
    console.log('Capturing Register Page...');
    await page.goto('http://localhost:3000/register', { waitUntil: 'networkidle2', timeout: 30000 });
    await new Promise(r => setTimeout(r, 1500));
    const regPath = path.join(OUTPUT_DIR, 'real_register.png');
    await page.screenshot({ path: regPath, fullPage: false });
    console.log('Saved:', regPath);

    console.log('SUCCESS: All 8 real application screenshots captured!');
  } catch (err) {
    console.error('Capture error:', err);
  } finally {
    await browser.close();
  }
}

run();
