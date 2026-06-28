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
