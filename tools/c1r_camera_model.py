"""C1-R: pure-Python model of the original ordinary camera follow (`$5832` / `$58E1` / `$4CB0` / `$4CF7`) and the Y-lead writers.

Source: BYTE-VERIFIED disassembly (docs/c1r-gameplay-fidelity-audit.md section 3).  No ROM access; the model is validated frame by frame against
data/c1r/camera-look-trace.json (tests/test_c1r_audit.py).

Registers (original names):  D174/D176 committed camera X/Y;  D284/D286 working camera;  D28A X lead, D288 X lead target (`$58E1`);  D28D Y lead,
D289 Y lead TARGET (written by the player callbacks);  zones: X lead-8..lead+8, Y lead-16..lead+16.
The follow works on the LOW BYTE of (player - camera), exactly like the original; it is exact only while |player - camera| < 256.
"""

# Y-lead target ($D289) written by the player callbacks.  Value per state (None = the callback does not write it, the previous value persists).
Y_LEAD_STAND = 0x60       # state 0/1 ($36C6), 5 walk ($3783), 0F ($39E6), 10 ($3A23), 15 ($396D), 19 ($3BC6), 1A ($39B6), loop helper $3EFD, jump launch $462D, walk request $45E7
Y_LEAD_LOOK_UP = 0xB8     # state 3 ($3713) only when the platform-owner byte D3C0 == 0
Y_LEAD_CRAWL = 0x30       # state 4 ($3759) only when D3C0 == 0 (look down / crouch)
Y_LEAD_INIT = 0x78        # level header loader $5074/$507B (D28D initial); first stand callback retargets to $60
X_LEAD_RIGHT, X_LEAD_LEFT, X_LEAD_PAN = 0x68, 0x88, 0x78
STEP_MAX = 7


def _s8(v):
    return v - 256 if v >= 128 else v


def x_lead_target(facing_left, pan_mode):
    """`$58E1`: B = $78; if (D15F & 3) == 0: B = $68, and $88 when +$04 bit 4 (facing left) is set."""
    if pan_mode:
        return X_LEAD_PAN
    return X_LEAD_LEFT if facing_left else X_LEAD_RIGHT


def slew(lead, target):
    """One update of the working lead toward its target (1 px/update)."""
    if lead == target:
        return lead
    return lead + 1 if target > lead else lead - 1


def _axis(player, cam, lead, half, up_bit, down_bit):
    """Common `$5832` axis body.  Returns signed step (None = early RET before SET: no flag, no change)."""
    d = (player - cam) & 0xFFFF
    if d == 0:
        return None
    low = d & 0xFF
    if low >= lead:
        upper = (lead + half) & 0xFF
        if low < upper:
            return None
        a = (low - upper) & 0xFF
        return a if a < 8 else STEP_MAX
    lower = (lead - half) & 0xFF
    if low >= lower:
        return None
    a = (low - lower) & 0xFF
    return _s8(a) if a >= 0xF8 else -7


def follow_axis(player, cam, lead, half, lo, hi):
    """Apply one follow step with the `$4CB0/$4CF7` limit check: lo inclusive, hi exclusive; a crossing step is DROPPED (the camera keeps its position)."""
    step = _axis(player, cam, lead, half, 0, 1)
    if step is None:
        return cam
    new = (cam + step) & 0xFFFF
    if step < 0 and (new >= 0xFF00 or new < lo):
        return cam
    if step >= 0 and hi is not None and new >= hi:
        return cam
    return new


class Camera:
    """State of the follow camera between updates."""

    def __init__(self, cam_x, cam_y, lead_x=0x78, lead_y=Y_LEAD_INIT, limits=(0, 0xFFFF, 0, 0xFFFF)):
        self.cam_x, self.cam_y, self.lead_x, self.lead_y = cam_x, cam_y, lead_x, lead_y
        self.left, self.right, self.top, self.bottom = limits

    def update(self, player_x, player_y, facing_left, y_target, pan_mode=False):
        """One call of `$5832` (after the player update of the same game update)."""
        if pan_mode:                  # `$583A BIT 0,(IX+1) / JP NZ,$5956`: the pan routine replaces the whole follow, including the lead slew
            return
        self.lead_x = slew(self.lead_x, x_lead_target(facing_left, False))
        self.lead_y = slew(self.lead_y, y_target)
        self.cam_x = follow_axis(player_x, self.cam_x, self.lead_x, 8, self.left, self.right)
        self.cam_y = follow_axis(player_y, self.cam_y, self.lead_y, 16, self.top, self.bottom)


def look_displacement(start_screen_y, target, hold_updates, lead_start=Y_LEAD_STAND):
    """Closed form helper for the contract: camera displacement after holding a look direction.
    Returns (first_move_update, final_screen_y)."""
    lead = lead_start
    L = start_screen_y
    cam_dy = 0
    first = None
    for n in range(1, hold_updates + 1):
        lead = slew(lead, target)
        step = _axis(L, 0, lead, 16, 0, 1)
        if step:
            L -= step
            cam_dy += step
            if first is None:
                first = n
    return first, L
