// vr-helpers.js — pure, dependency-free logic for the WebXR path.
// No `three` import: this module is unit-tested under `node --test`.

// Grab is active when grip (button[1]) OR trigger (button[0]) is pressed,
// OR the hand-tracking source reports a pinch. Tolerant of null inputs so a
// controllers-off / binding-quirk session can still grab.
export function resolveGrab(gamepad, hand) {
  if (gamepad && gamepad.buttons) {
    const trig = gamepad.buttons[0] && gamepad.buttons[0].pressed;
    const grip = gamepad.buttons[1] && gamepad.buttons[1].pressed;
    if (trig || grip) return true;
  }
  if (hand && hand.pinching) return true;
  return false;
}

// Fires once after VR navigation has been idle for `idleMs`. Used to defer the
// (expensive) LOD reassess until motion settles, so detail upgrades without the
// per-frame walk that caused stutter.
export function makeMotionGate(idleMs) {
  let lastMotion = -Infinity;
  let armed = false; // becomes true on motion, false after firing
  return {
    noteMotion(now) { lastMotion = now; armed = true; },
    shouldFire(now) {
      if (armed && now - lastMotion >= idleMs) { armed = false; return true; }
      return false;
    },
  };
}
