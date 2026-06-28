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

// Adapts the per-frame VR triangle budget in response to measured frame rate.
// Shrinks the budget when fps falls below `shrinkAt` (Quest GPU under pressure),
// restores it when there is headroom (`fps >= growAt`). Both directions are
// rate-limited (shrinkBy / growBy multipliers per measurement) so the response
// is smooth. Returns true from update() when the budget changed, so the caller
// can fire scheduleReassess() to pick up the new geometry cap immediately.
// Pure / dependency-free — safe to unit-test under `node --test`.
export function makeAdaptiveBudget(initial, {
  min = Math.round(initial * 0.25),
  max = initial,
  shrinkAt = 60,    // fps below this → reduce budget (Quest 2 target is 72 fps)
  growAt = 68,      // fps at/above this → restore budget (margin below 72)
  shrinkBy = 0.85,  // multiply budget by this on each low-fps measurement
  growBy = 1.05,    // multiply budget by this on each high-fps measurement
} = {}) {
  let _value = initial;
  return {
    get value() { return _value; },
    update(fps) {
      const prev = _value;
      if (fps < shrinkAt) {
        _value = Math.max(min, Math.round(_value * shrinkBy));
      } else if (fps >= growAt) {
        _value = Math.min(max, Math.round(_value * growBy));
      }
      return _value !== prev;
    },
  };
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
