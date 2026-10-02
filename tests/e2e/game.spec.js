// The shipped game in a browser, start to finish. Timers are fast-forwarded
// with Playwright's clock and Math.random is seeded, so every run plays the
// same random boards in a few seconds instead of a minute.
const { test, expect } = require("@playwright/test");

const SEED = Number(process.env.RM_SEED || 20261002);

test.beforeEach(async ({ page }) => {
  page.errors = [];
  page.on("pageerror", e => page.errors.push(String(e)));
  // Any failed request is an error, except the favicon the browser asks for on its own.
  page.on("response", r => {
    if (r.status() >= 400 && !r.url().endsWith("/favicon.ico")) page.errors.push(r.status() + " " + r.url());
  });
  page.on("console", m => {
    if (m.type() === "error" && !m.text().startsWith("Failed to load resource")) page.errors.push(m.text());
  });
  await page.addInitScript(seed => {
    let s = seed >>> 0;                      // mulberry32, as in qa/adversary.js
    Math.random = () => {
      s = (s + 0x6D2B79F5) >>> 0;
      let t = Math.imul(s ^ (s >>> 15), s | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    try { localStorage.clear(); } catch (e) {}
  }, SEED);
  await page.clock.install();
  await page.goto("/index.html");
  await expect(page.locator("#stage")).toContainText("Start from the shelter");
});

test.afterEach(async ({ page }) => {
  expect(page.errors, "browser errors").toEqual([]);
});

// Advance the game's timers until a condition holds in the page.
async function runUntil(page, fn, { stepMs = 1300, maxSteps = 400 } = {}) {
  for (let i = 0; i < maxSteps; i++) {
    if (await page.evaluate(fn)) return true;
    await page.clock.runFor(stepMs);
  }
  return page.evaluate(fn);
}

test("the page loads all 42 rows from the five tables", async ({ page }) => {
  await expect(page.locator("#prov")).toContainText("42 rows across 5 DataTables");
});

test("the computer plays the six encounters and wins the fight", async ({ page }) => {
  await page.getByRole("button", { name: "Watch the computer" }).click();

  const reachedFight = await runUntil(page, () => S.mode === "fight");
  expect(reachedFight, "never reached the fight").toBe(true);
  expect(await page.evaluate(() => S.hazard)).toBe(5);

  const over = await runUntil(page, () => S.mode === "fight" && S.over);
  expect(over, "the fight never ended").toBe(true);
  expect(await page.evaluate(() => approach())).toBe(1);
  await expect(page.locator("#say")).toContainText("She sees you");

  const log = await page.evaluate(() => S.log);
  expect(log.some(l => l.startsWith("REX:")), "Rex never spoke").toBe(true);
});

test("arrow keys play the fight: a legal move is a round, a refused one is not", async ({ page }) => {
  await page.getByRole("button", { name: /Skip to the fight/ }).click();
  await expect.poll(() => page.evaluate(() => S.mode)).toBe("fight");

  // Which directions are legal from where the dog stands now, and which are not.
  const sides = () => page.evaluate(() => {
    const keys = { up: "ArrowUp", down: "ArrowDown", left: "ArrowLeft", right: "ArrowRight" };
    const ok = [], refused = [];
    for (const d of Object.keys(keys)) {
      const t = [S.dog[0] + STEP[d][0], S.dog[1] + STEP[d][1]];
      (inBounds(t) && !eq(t, S.rex) ? ok : refused).push(keys[d]);
    }
    return { ok, refused };
  });

  const round0 = await page.evaluate(() => S.round);
  await page.keyboard.press((await sides()).ok[0]);
  expect(await page.evaluate(() => S.round)).toBe(round0 + 1);
  expect(await page.evaluate(() => S.predicted)).not.toBeNull();

  // Push into the fence or into Rex, if the dog's tile now has a refused side.
  const now = await sides();
  if (now.refused.length) {
    const before = await page.evaluate(() => [S.round, S.log.length]);
    await page.keyboard.press(now.refused[0]);
    const after = await page.evaluate(() => [S.round, S.log.length]);
    expect(after[0]).toBe(before[0]);
    expect(after[1]).toBeGreaterThan(before[1]);
  }
});

// Known: the game page is laid out for desktop and is 749 px wide at a 390 px
// viewport. Logged as RM-21 on the case-study tracker. Remove fixme when fixed.
test.fixme("on a phone-sized screen the board fits without sideways scrolling", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: /Skip to the fight/ }).click();
  await expect.poll(() => page.evaluate(() => S.mode)).toBe("fight");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
});
