import { test } from "node:test";
import assert from "node:assert/strict";
import { resolveGrab } from "./vr-helpers.js";

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
