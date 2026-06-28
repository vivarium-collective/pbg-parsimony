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
