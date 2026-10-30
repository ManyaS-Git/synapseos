const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const EDGE_PATH =
  process.env.EDGE_PATH ||
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const BASE_URL = process.env.CAPTURE_BASE_URL || 'http://localhost:3000';
const OUTPUT_DIR = path.join(__dirname, '..', 'docs', 'images');
const VIEWPORT = { width: 1600, height: 1050 };

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function settle(page) {
  await page.evaluate(async () => {
    await document.fonts.ready;
    const images = Array.from(document.images).filter((img) => !img.complete);
    if (images.length > 0) {
      await new Promise((resolve) => {
        let remaining = images.length;
        const done = () => {
          remaining -= 1;
          if (remaining <= 0) resolve();
        };
        images.forEach((img) => {
          img.addEventListener('load', done, { once: true });
          img.addEventListener('error', done, { once: true });
        });
        setTimeout(resolve, 3000);
      });
    }
  });
  await sleep(1200);
}

async function freezeAnimations(page) {
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-duration: 0.001ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.001ms !important;
        caret-color: transparent !important;
      }
      html { scroll-behavior: auto !important; }
    `,
  });
}

async function prepareForFullPage(page) {
  const height = await page.evaluate(() =>
    Math.max(
      document.documentElement.scrollHeight,
      document.body.scrollHeight,
      window.innerHeight
    )
  );

  // Fixed sidebars only cover the first viewport in a full-page capture.
  // Extend them to the document height so the complete page is represented.
  await page.addStyleTag({
    content: `
      aside.fixed {
        position: absolute !important;
        top: 0 !important;
        bottom: auto !important;
        height: ${height}px !important;
      }
      body { overflow: visible !important; }
    `,
  });
  await sleep(400);
  return height;
}

async function capture(page, name, route, options = {}) {
  const scale = options.scale || 2;

  await page.setViewport({
    width: VIEWPORT.width,
    height: VIEWPORT.height,
    deviceScaleFactor: scale,
  });

  console.log(`Capturing ${name} from ${route} ...`);
  await page.goto(`${BASE_URL}${route}`, {
    waitUntil: 'networkidle2',
    timeout: 60000,
  });
  await freezeAnimations(page);
  await settle(page);

  if (options.after) {
    await options.after(page);
    await settle(page);
  }

  await page.evaluate(() => window.scrollTo(0, 0));
  const height = await prepareForFullPage(page);
  const outputPath = path.join(OUTPUT_DIR, name);
  await page.screenshot({
    path: outputPath,
    type: 'jpeg',
    quality: 92,
    fullPage: true,
    captureBeyondViewport: true,
  });
  console.log(
    `Saved ${name}: ${VIEWPORT.width}x${Math.round(height)} CSS px at ${scale}x`
  );
}

async function openApprovalGate(page) {
  const input = 'textarea[aria-label="Message the assistant"]';
  await page.waitForSelector(input, { timeout: 10000 });
  await page.click(input);
  await page.type(
    input,
    'Create a guardrails rollout project and configure workspace policies',
    { delay: 8 }
  );
  const clicked = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const send = buttons.find((button) => button.textContent?.trim() === 'Send');
    if (!send) return false;
    send.click();
    return true;
  });
  if (!clicked) {
    throw new Error('Assistant send button was not found');
  }
  await sleep(1800);
}

async function run() {
  console.log('Launching Edge for full-page application captures...');
  const browser = await puppeteer.launch({
    executablePath: EDGE_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--force-color-profile=srgb',
    ],
    defaultViewport: {
      width: VIEWPORT.width,
      height: VIEWPORT.height,
      deviceScaleFactor: 2,
    },
  });

  try {
    const page = await browser.newPage();

    // Public entry points
    await capture(page, 'screenshot_landing.jpg', '/', { scale: 1 });
    await capture(page, 'screenshot_login.jpg', '/login');
    await capture(page, 'screenshot_register.jpg', '/register');

    // Complete showcase application pages
    await capture(page, 'screenshot_overview.jpg', '/showcase?tab=Overview');
    await capture(page, 'screenshot_assistant.jpg', '/showcase?tab=Assistant', {
      after: openApprovalGate,
    });
    await capture(page, 'screenshot_memory.jpg', '/showcase?tab=Memory');
    await capture(page, 'screenshot_graph.jpg', '/showcase?tab=Graph');
    await capture(page, 'screenshot_documents.jpg', '/showcase?tab=Documents');
    await capture(page, 'screenshot_agents.jpg', '/showcase?tab=Agents');
    await capture(page, 'screenshot_activity.jpg', '/showcase?tab=Activity');

    console.log('SUCCESS: Full-page application screenshots captured.');
  } finally {
    await browser.close();
  }
}

run().catch((error) => {
  console.error('Capture error:', error);
  process.exitCode = 1;
});
