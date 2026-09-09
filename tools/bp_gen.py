"""Generate Unreal Blueprint node text, to be pasted into a graph.

UE serialises selected Blueprint nodes to the clipboard as text and rebuilds
them on paste, wires included. So a graph can be generated and version
controlled instead of hand-wired. Every template below was captured by copying
a real node out of UE 5.5, not written from memory.

Two things that are easy to get wrong and are load-bearing here:

  * Under large world coordinates a Blueprint "float" is a double, and
    serialises as PinCategory="real" with PinSubCategory="double". Emit
    "float" and the pin silently mismatches.
  * MemberParent quoting is exact:
    MemberParent="/Script/CoreUObject.Class'/Script/Engine.KismetMathLibrary'"

Usage:
    python tools/bp_gen.py manhattan > out.txt
then paste the contents into the Manhattan graph in BP_FightManager.
"""
import sys

MATH = "/Script/CoreUObject.Class'/Script/Engine.KismetMathLibrary'"
SYS = "/Script/CoreUObject.Class'/Script/Engine.KismetSystemLibrary'"
STR = "/Script/CoreUObject.Class'/Script/Engine.KismetStringLibrary'"
SELF_CTX = "SELF"   # a call on this Blueprint, e.g. an inherited Manhattan

# Pin type fragments, verbatim from captured nodes.
T_DOUBLE = 'PinType.PinCategory="real",PinType.PinSubCategory="double",PinType.PinSubCategoryObject=None'
T_INT = 'PinType.PinCategory="int",PinType.PinSubCategory="",PinType.PinSubCategoryObject=None'
T_V2D = ('PinType.PinCategory="struct",PinType.PinSubCategory="",'
         'PinType.PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector2D\'"')

T_BOOL = 'PinType.PinCategory="bool",PinType.PinSubCategory="",PinType.PinSubCategoryObject=None'
T_STR = 'PinType.PinCategory="string",PinType.PinSubCategory="",PinType.PinSubCategoryObject=None'
T_EXEC = 'PinType.PinCategory="exec",PinType.PinSubCategory="",PinType.PinSubCategoryObject=None'

TAIL = ('PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,'
        'PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,'
        'PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False')

FLAGS = ('PersistentGuid=00000000000000000000000000000000,bHidden=False,bNotConnectable=False,'
         'bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,')


def guid(seed):
    """Deterministic 32-hex GUID, so regenerating gives a byte-identical file."""
    h = 0xcbf29ce484222325
    for ch in seed.encode():
        h = ((h ^ ch) * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return ("%016X" % h) + ("%016X" % (h ^ 0xA5A5A5A5A5A5A5A5))


def _autogen(typefrag):
    """The zero value UE itself would put on a pin of this type."""
    if 'PinCategory="bool"' in typefrag:
        return "false"
    if 'PinCategory="int"' in typefrag:
        return "0"
    if 'PinCategory="string"' in typefrag:
        return ""
    return "0.0"


class Node:
    def __init__(self, name, member, x, y, lib=None, guid=None):
        """lib: MATH / SYS / STR, or SELF_CTX for a call on this Blueprint.

        A self-context call carries no MemberParent at all -- it is
        bSelfContext=True plus the function's MemberGuid. Captured from a real
        node; guessing this shape does not work.
        """
        self.name, self.member, self.x, self.y = name, member, x, y
        self.lib = lib or MATH
        self.member_guid = guid
        self.pins = []   # (pinname, direction, typefrag, default, links)

    def pin(self, pinname, direction, typefrag, default=None, links=()):
        self.pins.append((pinname, direction, typefrag, default, links))
        return self

    def pid(self, pinname):
        return guid(self.name + "::" + pinname)

    def render(self):
        if self.lib == SELF_CTX:
            ref = 'FunctionReference=(MemberName="%s"%s,bSelfContext=True)' % (
                self.member, (",MemberGuid=%s" % self.member_guid) if self.member_guid else "")
        else:
            ref = 'FunctionReference=(MemberParent="%s",MemberName="%s")' % (self.lib, self.member)
        out = [
            'Begin Object Class=/Script/BlueprintGraph.K2Node_CallFunction Name="%s"' % self.name,
            '   bDefaultsToPureFunc=True',
            '   ' + ref,
            '   NodePosX=%d' % self.x,
            '   NodePosY=%d' % self.y,
            '   NodeGuid=%s' % guid(self.name),
        ]
        if self.lib != SELF_CTX:
            # the hidden static-library target pin every Kismet* call carries
            default_obj = "/Script/Engine.Default__" + self.lib.rsplit(".", 1)[1].rstrip("'")
            out.append(
                '   CustomProperties Pin (PinId=%s,PinName="self",'
                'PinFriendlyName=NSLOCTEXT("K2Node", "Target", "Target"),PinType.PinCategory="object",'
                'PinType.PinSubCategory="",PinType.PinSubCategoryObject="%s",%s,'
                'DefaultObject="%s",'
                'PersistentGuid=00000000000000000000000000000000,bHidden=True,bNotConnectable=False,'
                'bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,'
                'bOrphanedPin=False,)' % (self.pid("self"), self.lib, TAIL, default_obj))
        for pinname, direction, typefrag, default, links in self.pins:
            bits = ['PinId=%s' % self.pid(pinname), 'PinName="%s"' % pinname]
            if direction == "out":
                bits.append('Direction="EGPD_Output"')
            bits.append(typefrag)
            bits.append(TAIL)
            if default is not None:
                # AutogeneratedDefaultValue must stay the function's OWN default,
                # not the literal we want. If the two match, UE decides the pin was
                # never edited and rewrites it from the function signature on paste
                # -- so a literal silently reverts to 0.0 or "". They must differ.
                bits.append('DefaultValue="%s"' % default)
                bits.append('AutogeneratedDefaultValue="%s"' % _autogen(typefrag))
            if links:
                bits.append('LinkedTo=(%s)' % "".join("%s %s," % (n, p) for n, p in links))
            bits.append(FLAGS)
            out.append('   CustomProperties Pin (%s)' % ",".join(bits))
        out.append('End Object')
        return "\n".join(out)


class EventNode:
    """An overridden Actor event, e.g. BeginPlay.

    Captured from a real node. Two details matter: the reference field is
    EventReference, not FunctionReference, and MemberParent is the base
    /Script/Engine.Actor rather than the Blueprint's own class. The captured
    sample also carried EnabledState=Disabled because it was one of the greyed
    default stubs -- emitting that would produce an event that never fires.
    """

    def __init__(self, name, member, x, y):
        self.name, self.member, self.x, self.y = name, member, x, y
        self.pins = []

    def pin(self, pinname, direction, typefrag, default=None, links=()):
        self.pins.append((pinname, direction, typefrag, default, links))
        return self

    def pid(self, pinname):
        return guid(self.name + "::" + pinname)

    def render(self):
        out = [
            'Begin Object Class=/Script/BlueprintGraph.K2Node_Event Name="%s"' % self.name,
            '   EventReference=(MemberParent="/Script/CoreUObject.Class\'/Script/Engine.Actor\'",'
            'MemberName="%s")' % self.member,
            '   bOverrideFunction=True',
            '   NodePosX=%d' % self.x,
            '   NodePosY=%d' % self.y,
            '   NodeGuid=%s' % guid(self.name),
            '   CustomProperties Pin (PinId=%s,PinName="OutputDelegate",Direction="EGPD_Output",'
            'PinType.PinCategory="delegate",PinType.PinSubCategory="",'
            'PinType.PinSubCategoryObject=None,%s,%s)' % (self.pid("OutputDelegate"), TAIL, FLAGS),
        ]
        for pinname, direction, typefrag, default, links in self.pins:
            bits = ['PinId=%s' % self.pid(pinname), 'PinName="%s"' % pinname]
            if direction == "out":
                bits.append('Direction="EGPD_Output"')
            bits.append(typefrag)
            bits.append(TAIL)
            if links:
                bits.append('LinkedTo=(%s)' % "".join("%s %s," % (n, q) for n, q in links))
            bits.append(FLAGS)
            out.append('   CustomProperties Pin (%s)' % ",".join(bits))
        out.append('End Object')
        return "\n".join(out)


def manhattan():
    """abs(A.X - B.X) + abs(A.Y - B.Y), truncated to int.

    Boundary wires to the function entry and result nodes use the ids UE
    already assigned them in this graph, so the paste stitches itself into
    the existing entry/result rather than duplicating them.
    """
    ENTRY = "K2Node_FunctionEntry_0"
    ENTRY_A = "105817254C69A61E175EC5AD33102068"
    ENTRY_B = "4BFC60F34FF725D2F06C3EA92DB3D9E2"
    RESULT = "K2Node_FunctionResult_0"
    RESULT_D = "6F6EBA714496EB34749F14A344FCA281"

    ba = Node("RM_BreakA", "BreakVector2D", -700, -300)
    bb = Node("RM_BreakB", "BreakVector2D", -700, -80)
    sx = Node("RM_SubX", "Subtract_DoubleDouble", -450, -300)
    sy = Node("RM_SubY", "Subtract_DoubleDouble", -450, -100)
    ax = Node("RM_AbsX", "Abs", -250, -300)
    ay = Node("RM_AbsY", "Abs", -250, -100)
    ad = Node("RM_Add", "Add_DoubleDouble", -60, -200)
    tr = Node("RM_Trunc", "FTrunc", 140, -200)

    ba.pin("InVec", "in", T_V2D, links=[(ENTRY, ENTRY_A)])
    ba.pin("X", "out", T_DOUBLE, "0.0", [(sx.name, sx.pid("A"))])
    ba.pin("Y", "out", T_DOUBLE, "0.0", [(sy.name, sy.pid("A"))])

    bb.pin("InVec", "in", T_V2D, links=[(ENTRY, ENTRY_B)])
    bb.pin("X", "out", T_DOUBLE, "0.0", [(sx.name, sx.pid("B"))])
    bb.pin("Y", "out", T_DOUBLE, "0.0", [(sy.name, sy.pid("B"))])

    sx.pin("A", "in", T_DOUBLE, "0.0", [(ba.name, ba.pid("X"))])
    sx.pin("B", "in", T_DOUBLE, "0.0", [(bb.name, bb.pid("X"))])
    sx.pin("ReturnValue", "out", T_DOUBLE, "0.0", [(ax.name, ax.pid("A"))])

    sy.pin("A", "in", T_DOUBLE, "0.0", [(ba.name, ba.pid("Y"))])
    sy.pin("B", "in", T_DOUBLE, "0.0", [(bb.name, bb.pid("Y"))])
    sy.pin("ReturnValue", "out", T_DOUBLE, "0.0", [(ay.name, ay.pid("A"))])

    ax.pin("A", "in", T_DOUBLE, "0.0", [(sx.name, sx.pid("ReturnValue"))])
    ax.pin("ReturnValue", "out", T_DOUBLE, "0.0", [(ad.name, ad.pid("A"))])

    ay.pin("A", "in", T_DOUBLE, "0.0", [(sy.name, sy.pid("ReturnValue"))])
    ay.pin("ReturnValue", "out", T_DOUBLE, "0.0", [(ad.name, ad.pid("B"))])

    ad.pin("A", "in", T_DOUBLE, "0.0", [(ax.name, ax.pid("ReturnValue"))])
    ad.pin("B", "in", T_DOUBLE, "0.0", [(ay.name, ay.pid("ReturnValue"))])
    ad.pin("ReturnValue", "out", T_DOUBLE, "0.0", [(tr.name, tr.pid("A"))])

    tr.pin("A", "in", T_DOUBLE, "0.0", [(ad.name, ad.pid("ReturnValue"))])
    tr.pin("ReturnValue", "out", T_INT, "0", [(RESULT, RESULT_D)])

    return [ba, bb, sx, sy, ax, ay, ad, tr]


def band():
    """Charge > 60 -> clinical; >= 30 -> confident; else strained.

    Kept pure by selecting rather than branching, so it can be called from
    BP_SelfTest without any exec wiring. Thresholds are literals on unconnected
    pins, so no constant nodes are needed.

    Takes Charge as a parameter rather than reading the member variable. The
    spec writes it as Band(), but an explicit input is what makes it testable in
    isolation -- the caller passes Charge.

    Boundary wires to add by hand: entry Charge -> RM_GT60.A and RM_GE30.A,
    and RM_SelOuter.ReturnValue -> the result node.
    """
    gt = Node("RM_GT60", "Greater_DoubleDouble", -600, -200)
    ge = Node("RM_GE30", "GreaterEqual_DoubleDouble", -600, 0)
    inner = Node("RM_SelInner", "SelectString", -300, 0)
    outer = Node("RM_SelOuter", "SelectString", -60, -160)

    gt.pin("A", "in", T_DOUBLE, "0.0")
    gt.pin("B", "in", T_DOUBLE, "60.0")
    gt.pin("ReturnValue", "out", T_BOOL, "false", [(outer.name, outer.pid("bPickA"))])

    ge.pin("A", "in", T_DOUBLE, "0.0")
    ge.pin("B", "in", T_DOUBLE, "30.0")
    ge.pin("ReturnValue", "out", T_BOOL, "false", [(inner.name, inner.pid("bPickA"))])

    inner.pin("A", "in", T_STR, "confident")
    inner.pin("B", "in", T_STR, "strained")
    inner.pin("bPickA", "in", T_BOOL, "false", [(ge.name, ge.pid("ReturnValue"))])
    inner.pin("ReturnValue", "out", T_STR, None, [(outer.name, outer.pid("B"))])

    outer.pin("A", "in", T_STR, "clinical")
    outer.pin("B", "in", T_STR, None, [(inner.name, inner.pid("ReturnValue"))])
    outer.pin("bPickA", "in", T_BOOL, "false", [(gt.name, gt.pid("ReturnValue"))])
    outer.pin("ReturnValue", "out", T_STR, None)

    return [gt, ge, inner, outer]


def inbounds():
    """0 <= X < 10 and 0 <= Y < 10.

    GridSpan is "10x10" in all three DT_ArenaPhases rows, so the bounds are
    literals rather than a parsed string. Keep the column; the pipeline still
    authors it.

    Boundary wires to add by hand: entry Tile -> RM_BreakT.InVec, and
    RM_And3.ReturnValue -> the result node.
    """
    br = Node("RM_BreakT", "BreakVector2D", -900, -100)
    xlo = Node("RM_XLo", "GreaterEqual_DoubleDouble", -650, -260)
    xhi = Node("RM_XHi", "Less_DoubleDouble", -650, -100)
    ylo = Node("RM_YLo", "GreaterEqual_DoubleDouble", -650, 60)
    yhi = Node("RM_YHi", "Less_DoubleDouble", -650, 220)
    a1 = Node("RM_And1", "BooleanAND", -380, -180)
    a2 = Node("RM_And2", "BooleanAND", -380, 140)
    a3 = Node("RM_And3", "BooleanAND", -150, -20)

    br.pin("InVec", "in", T_V2D)
    br.pin("X", "out", T_DOUBLE, "0.0", [(xlo.name, xlo.pid("A")), (xhi.name, xhi.pid("A"))])
    br.pin("Y", "out", T_DOUBLE, "0.0", [(ylo.name, ylo.pid("A")), (yhi.name, yhi.pid("A"))])

    for n, lit, tgt, slot in ((xlo, "0.0", a1, "A"), (xhi, "10.0", a1, "B"),
                              (ylo, "0.0", a2, "A"), (yhi, "10.0", a2, "B")):
        n.pin("A", "in", T_DOUBLE, "0.0")
        n.pin("B", "in", T_DOUBLE, lit)
        n.pin("ReturnValue", "out", T_BOOL, "false", [(tgt.name, tgt.pid(slot))])

    a1.pin("A", "in", T_BOOL, "false", [(xlo.name, xlo.pid("ReturnValue"))])
    a1.pin("B", "in", T_BOOL, "false", [(xhi.name, xhi.pid("ReturnValue"))])
    a1.pin("ReturnValue", "out", T_BOOL, "false", [(a3.name, a3.pid("A"))])

    a2.pin("A", "in", T_BOOL, "false", [(ylo.name, ylo.pid("ReturnValue"))])
    a2.pin("B", "in", T_BOOL, "false", [(yhi.name, yhi.pid("ReturnValue"))])
    a2.pin("ReturnValue", "out", T_BOOL, "false", [(a3.name, a3.pid("B"))])

    a3.pin("A", "in", T_BOOL, "false", [(a1.name, a1.pid("ReturnValue"))])
    a3.pin("B", "in", T_BOOL, "false", [(a2.name, a2.pid("ReturnValue"))])
    a3.pin("ReturnValue", "out", T_BOOL, "false")

    return [br, xlo, xhi, ylo, yhi, a1, a2, a3]


def approach():
    """1 - Manhattan(Dog, Kid) / 11, clamped to 0..1.

    Positional, never accumulated. GDD 3 exploit 4 was the ratchet -- an
    approach value that only ever went up -- and recomputing it from the current
    tile every time is the fix. There is deliberately no stored previous value
    here for that reason.

    11 is Manhattan((0,0),(7,4)), the spawn-to-kid distance, so Approach is 0 at
    spawn and 1 on arrival. BP_SelfTest checks both ends.

    Takes Dog and Kid as parameters rather than reading the member variables, so
    it can be tested in isolation.

    Boundary wires by hand: entry Dog -> RM_ApMan.A, entry Kid -> RM_ApMan.B,
    and RM_ApClamp.ReturnValue -> the result node.
    """
    man = Node("RM_ApMan", "Manhattan", -800, -100, lib=SELF_CTX, guid=MANHATTAN_GUID)
    tof = Node("RM_ApToF", "Conv_IntToDouble", -560, -100, lib=MATH)
    div = Node("RM_ApDiv", "Divide_DoubleDouble", -360, -100, lib=MATH)
    sub = Node("RM_ApSub", "Subtract_DoubleDouble", -160, -100, lib=MATH)
    clp = Node("RM_ApClamp", "FClamp", 60, -100, lib=MATH)

    man.pin("A", "in", T_V2D)
    man.pin("B", "in", T_V2D)
    man.pin("Distance", "out", T_INT, "0", [(tof.name, tof.pid("InInt"))])

    tof.pin("InInt", "in", T_INT, "0", [(man.name, man.pid("Distance"))])
    tof.pin("ReturnValue", "out", T_DOUBLE, None, [(div.name, div.pid("A"))])

    div.pin("A", "in", T_DOUBLE, "0.0", [(tof.name, tof.pid("ReturnValue"))])
    div.pin("B", "in", T_DOUBLE, "11.0")
    div.pin("ReturnValue", "out", T_DOUBLE, None, [(sub.name, sub.pid("B"))])

    sub.pin("A", "in", T_DOUBLE, "1.0")
    sub.pin("B", "in", T_DOUBLE, "0.0", [(div.name, div.pid("ReturnValue"))])
    sub.pin("ReturnValue", "out", T_DOUBLE, None, [(clp.name, clp.pid("Value"))])

    clp.pin("Value", "in", T_DOUBLE, "0.0", [(sub.name, sub.pid("ReturnValue"))])
    clp.pin("Min", "in", T_DOUBLE, "0.0")
    clp.pin("Max", "in", T_DOUBLE, "1.0")
    clp.pin("ReturnValue", "out", T_DOUBLE, None)

    return [man, tof, div, sub, clp]


T_VEC = ('PinType.PinCategory="struct",PinType.PinSubCategory="",'
         'PinType.PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector\'"')

TILE_SIZE = 200.0


def tiletoworld():
    """(Tile.X * TileSize, Tile.Y * TileSize, 0).

    TileSize is emitted as the literal 200.0 rather than read from the member
    variable, because a variable getter is a K2Node_VariableGet and no template
    for one has been captured yet. That is a real duplication -- 200 also
    appears in tools/ue_build_arena.py -- so BP_SelfTest pins it: if either copy
    changes without the other, TileToWorld(7,4) stops being (1400, 800, 0) and
    the assertion says so.

    Swap the literal for a TileSize get as soon as a variable-get template
    exists, and delete this note.

    Boundary wires by hand: entry Tile -> RM_TwBreak.InVec, and
    RM_TwMake.ReturnValue -> the result node.
    """
    br = Node("RM_TwBreak", "BreakVector2D", -700, -100)
    mx = Node("RM_TwMulX", "Multiply_DoubleDouble", -450, -180)
    my = Node("RM_TwMulY", "Multiply_DoubleDouble", -450, 20)
    mk = Node("RM_TwMake", "MakeVector", -200, -100)

    br.pin("InVec", "in", T_V2D)
    br.pin("X", "out", T_DOUBLE, "0.0", [(mx.name, mx.pid("A"))])
    br.pin("Y", "out", T_DOUBLE, "0.0", [(my.name, my.pid("A"))])

    mx.pin("A", "in", T_DOUBLE, "0.0", [(br.name, br.pid("X"))])
    mx.pin("B", "in", T_DOUBLE, "%.1f" % TILE_SIZE)
    mx.pin("ReturnValue", "out", T_DOUBLE, None, [(mk.name, mk.pid("X"))])

    my.pin("A", "in", T_DOUBLE, "0.0", [(br.name, br.pid("Y"))])
    my.pin("B", "in", T_DOUBLE, "%.1f" % TILE_SIZE)
    my.pin("ReturnValue", "out", T_DOUBLE, None, [(mk.name, mk.pid("Y"))])

    mk.pin("X", "in", T_DOUBLE, "0.0", [(mx.name, mx.pid("ReturnValue"))])
    mk.pin("Y", "in", T_DOUBLE, "0.0", [(my.name, my.pid("ReturnValue"))])
    mk.pin("Z", "in", T_DOUBLE, "0.0")
    mk.pin("ReturnValue", "out", T_VEC, None)

    return [br, mx, my, mk]


MANHATTAN_GUID = "ED02AD0F4DA7F45E772004BAD7F4BC10"


def selftest():
    """BP_SelfTest's EventGraph: run the maths and print what it actually got.

    A Blueprint graph cannot be read back and checked, so this checks behaviour
    instead. It deliberately prints the computed value next to the expected one
    rather than asserting internally -- a PASS/FAIL boolean would hide *what*
    was wrong, and the values are what caught the Band literals reverting to
    zero.

    Boundary cases matter more than the middle of each range: Band(60) and
    Band(30) sit exactly on the spec's thresholds, where a > that should be >=
    would slip through unnoticed.

    One boundary wire to add by hand: Event BeginPlay -> RM_P0.execute.
    """
    begin = EventNode("RM_BeginPlay", "ReceiveBeginPlay", -1150, -700)
    nodes, prev_print, y = [begin], None, -600

    def y_of():
        return y

    def print_line(tag, label, value_node, value_pin):
        """label + value -> Print String, chained onto the previous print."""
        nonlocal prev_print, y
        cat = Node("RM_Cat" + tag, "Concat_StrStr", -200, y, lib=STR)
        pr = Node("RM_P" + tag, "PrintString", 120, y, lib=SYS)
        cat.pin("A", "in", T_STR, label)
        cat.pin("B", "in", T_STR, None, [(value_node.name, value_node.pid(value_pin))])
        cat.pin("ReturnValue", "out", T_STR, None, [(pr.name, pr.pid("InString"))])
        head = prev_print if prev_print is not None else begin
        pr.pin("execute", "in", T_EXEC, None, [(head.name, head.pid("then"))])
        pr.pin("then", "out", T_EXEC)
        pr.pin("InString", "in", T_STR, None, [(cat.name, cat.pid("ReturnValue"))])
        # exec links are two-way, so name this end on the upstream node too
        if prev_print is None:
            begin.pin("then", "out", T_EXEC, None, [(pr.name, pr.pid("execute"))])
        else:
            for i, (pn, d, tf, dv, lk) in enumerate(prev_print.pins):
                if pn == "then":
                    prev_print.pins[i] = (pn, d, tf, dv, [(pr.name, pr.pid("execute"))])
        nodes.extend([cat, pr])
        prev_print = pr
        y += 200

    def manhattan_case(tag, ax, ay, bx, by, expect):
        va = Node("RM_VA" + tag, "MakeVector2D", -900, y, lib=MATH)
        vb = Node("RM_VB" + tag, "MakeVector2D", -900, y + 90, lib=MATH)
        mn = Node("RM_MN" + tag, "Manhattan", -650, y, lib=SELF_CTX, guid=MANHATTAN_GUID)
        cv = Node("RM_CV" + tag, "Conv_IntToString", -420, y, lib=STR)
        for v, (px, py) in ((va, (ax, ay)), (vb, (bx, by))):
            v.pin("X", "in", T_DOUBLE, "%.1f" % px)
            v.pin("Y", "in", T_DOUBLE, "%.1f" % py)
            v.pin("ReturnValue", "out", T_V2D, None,
                  [(mn.name, mn.pid("A" if v is va else "B"))])
        mn.pin("A", "in", T_V2D, None, [(va.name, va.pid("ReturnValue"))])
        mn.pin("B", "in", T_V2D, None, [(vb.name, vb.pid("ReturnValue"))])
        mn.pin("Distance", "out", T_INT, "0", [(cv.name, cv.pid("InInt"))])
        cv.pin("InInt", "in", T_INT, "0", [(mn.name, mn.pid("Distance"))])
        cv.pin("ReturnValue", "out", T_STR, None)
        nodes.extend([va, vb, mn, cv])
        print_line(tag, "Manhattan (%g,%g)->(%g,%g) expect %s got " % (ax, ay, bx, by, expect),
                   cv, "ReturnValue")

    def inbounds_case(tag, x, y, expect):
        v = Node("RM_IBV" + tag, "MakeVector2D", -900, y_of(), lib=MATH)
        ib = Node("RM_IB" + tag, "InBounds", -650, y_of(), lib=SELF_CTX)
        cb = Node("RM_IBC" + tag, "Conv_BoolToString", -420, y_of(), lib=STR)
        v.pin("X", "in", T_DOUBLE, "%.1f" % x)
        v.pin("Y", "in", T_DOUBLE, "%.1f" % y)
        v.pin("ReturnValue", "out", T_V2D, None, [(ib.name, ib.pid("Tile"))])
        ib.pin("Tile", "in", T_V2D, None, [(v.name, v.pid("ReturnValue"))])
        ib.pin("IsInBounds", "out", T_BOOL, None, [(cb.name, cb.pid("InBool"))])
        cb.pin("InBool", "in", T_BOOL, "false", [(ib.name, ib.pid("IsInBounds"))])
        cb.pin("ReturnValue", "out", T_STR, None)
        nodes.extend([v, ib, cb])
        print_line(tag, "InBounds(%g,%g) expect %s got " % (x, y, expect), cb, "ReturnValue")

    def tiletoworld_case(tag, x, y, expect):
        v = Node("RM_TWV" + tag, "MakeVector2D", -900, y_of(), lib=MATH)
        tw = Node("RM_TW" + tag, "TileToWorld", -650, y_of(), lib=SELF_CTX)
        cv = Node("RM_TWC" + tag, "Conv_VectorToString", -420, y_of(), lib=STR)
        v.pin("X", "in", T_DOUBLE, "%.1f" % x)
        v.pin("Y", "in", T_DOUBLE, "%.1f" % y)
        v.pin("ReturnValue", "out", T_V2D, None, [(tw.name, tw.pid("Tile"))])
        tw.pin("Tile", "in", T_V2D, None, [(v.name, v.pid("ReturnValue"))])
        tw.pin("World", "out", T_VEC, None, [(cv.name, cv.pid("InVec"))])
        cv.pin("InVec", "in", T_VEC, None, [(tw.name, tw.pid("World"))])
        cv.pin("ReturnValue", "out", T_STR, None)
        nodes.extend([v, tw, cv])
        print_line(tag, "TileToWorld(%g,%g) expect %s got " % (x, y, expect), cv, "ReturnValue")

    def band_case(tag, charge, expect):
        bd = Node("RM_BD" + tag, "Band", -650, y, lib=SELF_CTX)
        bd.pin("Charge", "in", T_DOUBLE, "%.1f" % charge)
        bd.pin("BandName", "out", T_STR, None)
        nodes.append(bd)
        print_line(tag, "Band(%g) expect %s got " % (charge, expect), bd, "BandName")

    manhattan_case("0", 0, 0, 7, 4, "11")
    manhattan_case("1", 9, 9, 0, 0, "18")
    band_case("2", 100, "clinical")
    band_case("3", 60, "confident")    # boundary: > 60 is clinical, so 60 is not
    band_case("4", 45, "confident")
    band_case("5", 30, "confident")    # boundary: >= 30
    band_case("6", 29, "strained")
    band_case("7", 10, "strained")
    # InBounds: the grid is 10x10, so 0..9 is inside and anything else is not
    inbounds_case("8", 0, 0, "true")
    inbounds_case("9", 9, 9, "true")
    inbounds_case("A", 10, 0, "false")
    inbounds_case("B", 0, 10, "false")
    inbounds_case("C", -1, 5, "false")
    # TileToWorld: pins the 200 that is duplicated in ue_build_arena.py
    tiletoworld_case("D", 0, 0, "X=0 Y=0 Z=0")
    tiletoworld_case("E", 7, 4, "X=1400 Y=800 Z=0")
    return nodes


GRAPHS = {"manhattan": manhattan, "band": band, "inbounds": inbounds,
          "approach": approach, "tiletoworld": tiletoworld, "selftest": selftest}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "manhattan"
    if which not in GRAPHS:
        raise SystemExit("unknown graph %r; have: %s" % (which, ", ".join(sorted(GRAPHS))))
    sys.stdout.write("\n".join(n.render() for n in GRAPHS[which]()) + "\n")
