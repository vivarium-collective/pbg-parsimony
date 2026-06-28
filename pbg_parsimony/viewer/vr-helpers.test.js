import { test } from "node:test";
import assert from "node:assert/strict";
import { resolveGrab } from "./vr-helpers.js";
import { makeAdaptiveBudget } from "./vr-helpers.js";

test("resolveGrab: trigger pressed grabs", () => {
  assert.equal(resolveGrab({ buttons: [{ pressed: true }, { pressed: false }] }, null), true);
});

test("resolveGrab: grip pressed grabs", () => {
  assert.equal(resolveGrab({ buttons: [{ pressed: false }, { pressed: true }] }, null), true);
});

test("resolveGrab: hand pinch grabs with no gamepad", () => {
  assert.equal(resolveGrab(null, { pinching: true }), true);
});

test("resolveGrab: nothing pressed does not grab", () => {
  assert.equal(resolveGrab({ buttons: [{ pressed: false }, { pressed: false }] }, { pinching: false }), false);
});

test("resolveGrab: null inputs do not grab or throw", () => {
  assert.equal(resolveGrab(null, null), false);
});

import { makeMotionGate } from "./vr-helpers.js";

test("makeMotionGate: fires once after idle window elapses", () => {
  const g = makeMotionGate(180);
  g.noteMotion(1000);
  assert.equal(g.shouldFire(1100), false); // still within idle window
  assert.equal(g.shouldFire(1180), true);  // window elapsed → fire once
  assert.equal(g.shouldFire(1200), false);  // does not fire again until new motion
});

test("makeMotionGate: new motion re-arms the gate", () => {
  const g = makeMotionGate(180);
  g.noteMotion(0);
  assert.equal(g.shouldFire(200), true);
  g.noteMotion(500);
  assert.equal(g.shouldFire(600), false);
  assert.equal(g.shouldFire(700), true);
});

test("makeMotionGate: does not fire before any motion", () => {
  const g = makeMotionGate(180);
  assert.equal(g.shouldFire(10000), false);
});

test("makeAdaptiveBudget: shrinks on low fps and signals change", () => {
  const b = makeAdaptiveBudget(1000);
  const changed = b.update(30); // well below shrinkAt threshold
  assert.equal(changed, true);
  assert.ok(b.value < 1000, `expected value < 1000, got ${b.value}`);
});

test("makeAdaptiveBudget: grows toward max on high fps", () => {
  const b = makeAdaptiveBudget(1000);
  b.update(30); // shrink first
  const shrunk = b.value;
  const changed = b.update(80); // well above growAt threshold
  assert.equal(changed, true);
  assert.ok(b.value > shrunk, `expected value > ${shrunk}, got ${b.value}`);
});

test("makeAdaptiveBudget: clamps at min and returns false when stable", () => {
  const b = makeAdaptiveBudget(1000, { min: 500 });
  // Drive to floor
  for (let i = 0; i < 100; i++) b.update(10);
  assert.equal(b.value, 500);
  const changed = b.update(10);
  assert.equal(changed, false);
});
