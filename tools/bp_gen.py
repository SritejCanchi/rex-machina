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

# An array pin differs from a scalar one only in ContainerType, and the array
# argument of a KismetArrayLibrary call is additionally by-ref and const --
# copied exactly from a captured Array_Length node. Get these wrong and the pin
# looks right in the graph but refuses the connection.
TAIL_ARRAY = TAIL.replace('ContainerType=None', 'ContainerType=Array')
TAIL_ARRAY_REF = TAIL_ARRAY.replace('bIsReference=False,PinType.bIsConst=False',
                                    'bIsReference=True,PinType.bIsConst=True')

ARRAYLIB = "/Script/CoreUObject.Class'/Script/Engine.KismetArrayLibrary'"
# The class of this Blueprint, for the hidden self pin a variable node carries.
SELF_CLASS = ("/Script/Engine.BlueprintGeneratedClass'"
              "/Game/Blueprints/BP_FightManager.BP_FightManager_C'")

# Variable GUIDs, read off nodes captured out of the editor. A VariableReference
# carries MemberGuid as well as MemberName, and the guid is assigned when the
# variable is created, so it cannot be derived -- only copied. Blueprint's
# new_variables array is not exposed to Python, so the way to add one here is to
# drop a Get node for it in a graph, copy it, and read the line back.
VAR_GUID = {
    "Moves":   "70CB720B484A312B1673E4996E39D643",
    "DogTile": "7BA786E0451F4F2831DB34994CF90297",
    "RexTile": "28AD973B4A6BA12AB80E2FB75F751B5E",
}

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

    def pin(self, pinname, direction, typefrag, default=None, links=(), tail=None):
        self.pins.append((pinname, direction, typefrag, default, links, tail))
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
        for pinname, direction, typefrag, default, links, tail in _padded(self.pins):
            bits = ['PinId=%s' % self.pid(pinname), 'PinName="%s"' % pinname]
            if direction == "out":
                bits.append('Direction="EGPD_Output"')
            bits.append(typefrag)
            bits.append(tail or TAIL)
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


def _pin_text(owner, pinname, direction, typefrag, default, links, tail=None,
              extra=""):
    bits = ['PinId=%s' % owner.pid(pinname), 'PinName="%s"' % pinname]
    if direction == "out":
        bits.append('Direction="EGPD_Output"')
    bits.append(typefrag)
    bits.append(tail or TAIL)
    if extra:
        bits.append(extra)
    if default is not None:
        bits.append('DefaultValue="%s"' % default)
        bits.append('AutogeneratedDefaultValue="%s"' % _autogen(typefrag))
    if links:
        bits.append('LinkedTo=(%s)' % "".join("%s %s," % (n, p) for n, p in links))
    bits.append(FLAGS)
    return '   CustomProperties Pin (%s)' % ",".join(bits)


class VarGet:
    """Read a Blueprint variable. K2Node_VariableGet, captured from the editor.

    The output pin is named after the variable, so `pid("Moves")` addresses it.
    The hidden `self` pin is typed as this Blueprint's generated class; it is
    what makes bSelfContext resolve.
    """

    def __init__(self, name, var, typefrag, x, y, tail=None):
        self.name, self.var, self.typefrag = name, var, typefrag
        self.x, self.y, self.tail = x, y, tail
        self.links = []

    def pid(self, pinname):
        return guid(self.name + "::" + pinname)

    def out_pin(self):
        return self.pid(self.var)

    def render(self):
        gid = VAR_GUID.get(self.var)
        ref = 'VariableReference=(MemberName="%s"%s,bSelfContext=True)' % (
            self.var, (",MemberGuid=%s" % gid) if gid else "")
        return "\n".join([
            'Begin Object Class=/Script/BlueprintGraph.K2Node_VariableGet Name="%s"' % self.name,
            '   ' + ref,
            '   NodePosX=%d' % self.x,
            '   NodePosY=%d' % self.y,
            '   NodeGuid=%s' % guid(self.name),
            _pin_text(self, self.var, "out", self.typefrag, None, self.links, self.tail),
            _pin_text(self, "self", "in",
                      'PinType.PinCategory="object",PinType.PinSubCategory="",'
                      'PinType.PinSubCategoryObject="%s"' % SELF_CLASS,
                      None, (), None,
                      'PinFriendlyName=NSLOCTEXT("K2Node", "Target", "Target")'),
            'End Object',
        ])


class ArrayLength:
    """Array_Length on KismetArrayLibrary -- a K2Node_CallArrayFunction.

    Not a plain CallFunction: the array pin is the node's "wildcard anchor" and
    UE re-types the node from whatever is connected to it.
    """

    def __init__(self, name, x, y, elem_cat='PinType.PinCategory="string",'
                 'PinType.PinSubCategory="",PinType.PinSubCategoryObject=None'):
        self.name, self.x, self.y, self.elem = name, x, y, elem_cat
        self.array_links, self.out_links = [], []

    def pid(self, pinname):
        return guid(self.name + "::" + pinname)

    def render(self):
        return "\n".join([
            'Begin Object Class=/Script/BlueprintGraph.K2Node_CallArrayFunction Name="%s"' % self.name,
            '   bDefaultsToPureFunc=True',
            '   FunctionReference=(MemberParent="%s",MemberName="Array_Length")' % ARRAYLIB,
            '   NodePosX=%d' % self.x,
            '   NodePosY=%d' % self.y,
            '   NodeGuid=%s' % guid(self.name),
            _pin_text(self, "self", "in",
                      'PinType.PinCategory="object",PinType.PinSubCategory="",'
                      'PinType.PinSubCategoryObject="%s"' % ARRAYLIB, None, (), None,
                      'PinFriendlyName=NSLOCTEXT("K2Node", "Target", "Target")'),
            _pin_text(self, "TargetArray", "in", self.elem, None, self.array_links,
                      TAIL_ARRAY_REF),
            _pin_text(self, "ReturnValue", "out", T_INT, None, self.out_links),
            'End Object',
        ])


class ArrayGet:
    """K2Node_GetArrayItem. The index pin is called "Dimension 1", not "Index".

    Out-of-range indices are survivable -- UE returns the element default and
    logs -- but the callers here clamp anyway, because a warning per round is
    noise in a build someone else is going to run.
    """

    def __init__(self, name, x, y, elem_cat='PinType.PinCategory="string",'
                 'PinType.PinSubCategory="",PinType.PinSubCategoryObject=None'):
        self.name, self.x, self.y, self.elem = name, x, y, elem_cat
        self.array_links, self.index_links, self.out_links = [], [], []

    def pid(self, pinname):
        return guid(self.name + "::" + pinname)

    def render(self):
        return "\n".join([
            'Begin Object Class=/Script/BlueprintGraph.K2Node_GetArrayItem Name="%s"' % self.name,
            '   bReturnByRefDesired=False',
            '   NodePosX=%d' % self.x,
            '   NodePosY=%d' % self.y,
            '   NodeGuid=%s' % guid(self.name),
            _pin_text(self, "Array", "in", self.elem, None, self.array_links, TAIL_ARRAY),
            _pin_text(self, "Dimension 1", "in", T_INT, "0", self.index_links),
            _pin_text(self, "Output", "out", self.elem, None, self.out_links),
            'End Object',
        ])


def _padded(pins):
    """Yield pin tuples as 6-tuples, so 5-tuple call sites still work."""
    for t in pins:
        yield t if len(t) == 6 else (t + (None,))


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


def steptoward():
    """StepToward(From, Target) -> the neighbour of From that is in bounds and
    strictly closer to Target, else From itself.

    game.js iterates STEP in the order left, right, up, down and keeps the
    first candidate strictly closer than the best so far. A single orthogonal
    step changes Manhattan distance by exactly one, so nothing after the first
    strict improvement can beat it: the loop is really "the first direction in
    that order that closes the gap". That collapses to arithmetic -- no branch
    node, no Select, and so no node class this generator cannot already emit.

    "Strictly closer" along an axis is just the sign of the delta:

        wantLeft = dx < 0    wantRight = dx > 0
        wantUp   = dy < 0    wantDown  = dy > 0

    The InBounds guard cannot be dropped even though From and Target are both
    on the grid, because Predict deliberately returns an off-grid tile when the
    dog is against a fence -- Rex chasing (-1,0) from (0,3) has to go up, not
    off the board. That case is a self-test assertion.

    The winning direction becomes a +1/-1 offset through
    Conv_BoolToInt -> Conv_IntToDouble, so the whole body is one straight-line
    arithmetic chain.
    """
    nodes = []

    def n(name, member, x, y, lib=MATH):
        node = Node(name, member, x, y, lib=lib)
        nodes.append(node)
        return node

    def out(node, pinname, typefrag, links):
        """Set an output pin's link list after the consumers are known."""
        for i, t in enumerate(node.pins):
            if t[0] == pinname:
                node.pins[i] = t[:4] + (links,) + t[5:]
                return
        node.pin(pinname, "out", typefrag, None, links)

    # ---- unpack both tiles -------------------------------------------------
    bf = n("RM_StBF", "BreakVector2D", -2100, -260)
    bt = n("RM_StBT", "BreakVector2D", -2100, -80)
    bf.pin("InVec", "in", T_V2D)
    bt.pin("InVec", "in", T_V2D)

    dx = n("RM_StDX", "Subtract_DoubleDouble", -1900, -260)
    dy = n("RM_StDY", "Subtract_DoubleDouble", -1900, -140)
    dx.pin("A", "in", T_DOUBLE, "0.0", [(bt.name, bt.pid("X"))])
    dx.pin("B", "in", T_DOUBLE, "0.0", [(bf.name, bf.pid("X"))])
    dy.pin("A", "in", T_DOUBLE, "0.0", [(bt.name, bt.pid("Y"))])
    dy.pin("B", "in", T_DOUBLE, "0.0", [(bf.name, bf.pid("Y"))])
    out(bt, "X", T_DOUBLE, [(dx.name, dx.pid("A"))])
    out(bt, "Y", T_DOUBLE, [(dy.name, dy.pid("A"))])

    fx = [(dx.name, dx.pid("B"))]          # consumers of From.X
    fy = [(dy.name, dy.pid("B"))]          # consumers of From.Y
    dxc, dyc = [], []                      # consumers of dx / dy

    # ---- one candidate per direction, in game.js's order -------------------
    DIRS = [("L", "X", -1, "Less_DoubleDouble"),
            ("R", "X", +1, "Greater_DoubleDouble"),
            ("U", "Y", -1, "Less_DoubleDouble"),
            ("D", "Y", +1, "Greater_DoubleDouble")]
    ok, row = {}, -560
    for tag, axis, step, cmp_member in DIRS:
        delta, dcons = (dx, dxc) if axis == "X" else (dy, dyc)

        want = n("RM_StW" + tag, cmp_member, -1700, row)
        want.pin("A", "in", T_DOUBLE, "0.0", [(delta.name, delta.pid("ReturnValue"))])
        want.pin("B", "in", T_DOUBLE, "0.0")
        dcons.append((want.name, want.pid("A")))

        shift = n("RM_StC" + tag,
                  "Add_DoubleDouble" if step > 0 else "Subtract_DoubleDouble",
                  -1700, row + 110)
        shift.pin("A", "in", T_DOUBLE, "0.0", [(bf.name, bf.pid(axis))])
        shift.pin("B", "in", T_DOUBLE, "1.0")
        shift.pin("ReturnValue", "out", T_DOUBLE)
        (fx if axis == "X" else fy).append((shift.name, shift.pid("A")))

        cand = n("RM_StV" + tag, "MakeVector2D", -1480, row + 110)
        if axis == "X":
            cand.pin("X", "in", T_DOUBLE, "0.0", [(shift.name, shift.pid("ReturnValue"))])
            cand.pin("Y", "in", T_DOUBLE, "0.0", [(bf.name, bf.pid("Y"))])
            fy.append((cand.name, cand.pid("Y")))
        else:
            cand.pin("X", "in", T_DOUBLE, "0.0", [(bf.name, bf.pid("X"))])
            fx.append((cand.name, cand.pid("X")))
            cand.pin("Y", "in", T_DOUBLE, "0.0", [(shift.name, shift.pid("ReturnValue"))])
        out(shift, "ReturnValue", T_DOUBLE, [(cand.name, cand.pid("X" if axis == "X" else "Y"))])

        ib = n("RM_StI" + tag, "InBounds", -1260, row + 110, lib=SELF_CTX)
        ib.pin("Tile", "in", T_V2D, None, [(cand.name, cand.pid("ReturnValue"))])
        out(cand, "ReturnValue", T_V2D, [(ib.name, ib.pid("Tile"))])

        a = n("RM_StOK" + tag, "BooleanAND", -1040, row + 55)
        a.pin("A", "in", T_BOOL, "false", [(want.name, want.pid("ReturnValue"))])
        a.pin("B", "in", T_BOOL, "false", [(ib.name, ib.pid("Inside"))])
        out(want, "ReturnValue", T_BOOL, [(a.name, a.pid("A"))])
        out(ib, "Inside", T_BOOL, [(a.name, a.pid("B"))])
        ok[tag] = a
        row += 300

    # ---- first true wins ---------------------------------------------------
    # sel(L) = ok(L); sel(R) = ok(R) and not (L); sel(U) = ok(U) and not (L or R) ...
    sel = {"L": ok["L"]}
    okc = {t: [] for t in ok}              # consumers of each ok(tag)
    seen, seenc = ok["L"], okc["L"]        # "an earlier direction already won"
    for i, tag in enumerate(("R", "U", "D")):
        nt = n("RM_StN" + tag, "Not_PreBool", -860, -520 + i * 300)
        nt.pin("A", "in", T_BOOL, "false", [(seen.name, seen.pid("ReturnValue"))])
        seenc.append((nt.name, nt.pid("A")))
        s2 = n("RM_StS" + tag, "BooleanAND", -680, -520 + i * 300)
        s2.pin("A", "in", T_BOOL, "false", [(ok[tag].name, ok[tag].pid("ReturnValue"))])
        s2.pin("B", "in", T_BOOL, "false", [(nt.name, nt.pid("ReturnValue"))])
        out(nt, "ReturnValue", T_BOOL, [(s2.name, s2.pid("B"))])
        okc[tag].append((s2.name, s2.pid("A")))
        sel[tag] = s2
        if tag != "D":
            orn = n("RM_StOr" + tag, "BooleanOR", -860, -420 + i * 300)
            orn.pin("A", "in", T_BOOL, "false", [(seen.name, seen.pid("ReturnValue"))])
            orn.pin("B", "in", T_BOOL, "false", [(ok[tag].name, ok[tag].pid("ReturnValue"))])
            seenc.append((orn.name, orn.pid("A")))
            okc[tag].append((orn.name, orn.pid("B")))
            out(seen, "ReturnValue", T_BOOL, seenc)
            seen, seenc = orn, []
        else:
            out(seen, "ReturnValue", T_BOOL, seenc)

    # ---- the chosen direction becomes a +1 / -1 offset ----------------------
    offs = {}
    for i, tag in enumerate(("L", "R", "U", "D")):
        bi = n("RM_StB2I" + tag, "Conv_BoolToInt", -500, -520 + i * 160)
        bi.pin("InBool", "in", T_BOOL, "false", [(sel[tag].name, sel[tag].pid("ReturnValue"))])
        i2d = n("RM_StI2D" + tag, "Conv_IntToDouble", -340, -520 + i * 160)
        i2d.pin("InInt", "in", T_INT, "0", [(bi.name, bi.pid("ReturnValue"))])
        out(bi, "ReturnValue", T_INT, [(i2d.name, i2d.pid("InInt"))])
        if tag == "L":
            okc["L"].append((bi.name, bi.pid("InBool")))
            out(sel["L"], "ReturnValue", T_BOOL, okc["L"])
        else:
            out(sel[tag], "ReturnValue", T_BOOL, [(bi.name, bi.pid("InBool"))])
        offs[tag] = i2d
    for tag in ("R", "U", "D"):
        out(ok[tag], "ReturnValue", T_BOOL, okc[tag])

    offx = n("RM_StOffX", "Subtract_DoubleDouble", -180, -520)
    offx.pin("A", "in", T_DOUBLE, "0.0", [(offs["R"].name, offs["R"].pid("ReturnValue"))])
    offx.pin("B", "in", T_DOUBLE, "0.0", [(offs["L"].name, offs["L"].pid("ReturnValue"))])
    offy = n("RM_StOffY", "Subtract_DoubleDouble", -180, -360)
    offy.pin("A", "in", T_DOUBLE, "0.0", [(offs["D"].name, offs["D"].pid("ReturnValue"))])
    offy.pin("B", "in", T_DOUBLE, "0.0", [(offs["U"].name, offs["U"].pid("ReturnValue"))])
    for tag, node, pin in (("R", offx, "A"), ("L", offx, "B"),
                           ("D", offy, "A"), ("U", offy, "B")):
        out(offs[tag], "ReturnValue", T_DOUBLE, [(node.name, node.pid(pin))])

    nx = n("RM_StNX", "Add_DoubleDouble", -20, -520)
    nx.pin("A", "in", T_DOUBLE, "0.0", [(bf.name, bf.pid("X"))])
    nx.pin("B", "in", T_DOUBLE, "0.0", [(offx.name, offx.pid("ReturnValue"))])
    ny = n("RM_StNY", "Add_DoubleDouble", -20, -360)
    ny.pin("A", "in", T_DOUBLE, "0.0", [(bf.name, bf.pid("Y"))])
    ny.pin("B", "in", T_DOUBLE, "0.0", [(offy.name, offy.pid("ReturnValue"))])
    out(offx, "ReturnValue", T_DOUBLE, [(nx.name, nx.pid("B"))])
    out(offy, "ReturnValue", T_DOUBLE, [(ny.name, ny.pid("B"))])
    fx.append((nx.name, nx.pid("A")))
    fy.append((ny.name, ny.pid("A")))

    mk = n("RM_StMake", "MakeVector2D", 160, -440)
    mk.pin("X", "in", T_DOUBLE, "0.0", [(nx.name, nx.pid("ReturnValue"))])
    mk.pin("Y", "in", T_DOUBLE, "0.0", [(ny.name, ny.pid("ReturnValue"))])
    mk.pin("ReturnValue", "out", T_V2D)
    out(nx, "ReturnValue", T_DOUBLE, [(mk.name, mk.pid("X"))])
    out(ny, "ReturnValue", T_DOUBLE, [(mk.name, mk.pid("Y"))])

    out(bf, "X", T_DOUBLE, fx)
    out(bf, "Y", T_DOUBLE, fy)
    out(dx, "ReturnValue", T_DOUBLE, dxc)
    out(dy, "ReturnValue", T_DOUBLE, dyc)
    return nodes


def predict():
    """Predict() -> the tile the dog is about to step onto.

    game.js:

        const w = recentMoves().filter(m => STEP[m]);   // last 4, no "wait"
        if(!w.length) return S.dog.slice();
        const c = {}; for(const m of w) c[m] = (c[m]||0)+1;
        const best = Object.keys(c).sort((a,b)=>c[b]-c[a])[0];
        return [S.dog[0]+STEP[best][0], S.dog[1]+STEP[best][1]];

    Two details in that are easy to miss and both are load-bearing.

    The sort is stable and `Object.keys` is in first-insertion order, so a tie
    on count goes to whichever direction appeared *earliest* in the window. A
    four-move window ties constantly -- left,right,left,right is a tie -- so
    this is not a corner case, it is most of the time.

    And the returned tile is deliberately allowed off the grid: a dog against
    the west fence still moving left predicts x = -1. StepToward's InBounds
    guard is what copes with that, which is why that guard has its own
    assertion.

    Both fall out of scoring each direction by *which* slots it matched rather
    than how many:

        score(d) = sum of W[i] over slots i where move[i] == d
        W = [18, 14, 12, 11]      slot 0 is the oldest of the last four

    Every subset sum of W is distinct, so no two directions can tie. The gaps
    are wide enough that more matches always outscores fewer -- the smallest
    two-match sum, 12+11, beats the largest one-match, 18 -- and within an
    equal count the weights are ordered so the earliest slot dominates, which
    is exactly the stable-sort rule. So the whole thing is straight-line
    arithmetic: no branch, no loop, no map.

    The empty case needs no special path either. If nothing matched, every
    score is zero, `any` is false, every win flag is false, the offset is
    (0,0), and the function returns DogTile unchanged -- which is what game.js
    does when the window has no directional moves in it.
    """
    W = [18, 14, 12, 11]
    DIRS = ["left", "right", "up", "down"]
    nodes = []

    def n(node):
        nodes.append(node)
        return node

    def call(name, member, x, y, lib=MATH):
        return n(Node(name, member, x, y, lib=lib))

    def link(a, apin, b, bpin):
        """Wire a.apin -> b.bpin, declaring both ends."""
        for node, pinname, other, otherpin in ((a, apin, b, bpin), (b, bpin, a, apin)):
            for i, t in enumerate(node.pins):
                if t[0] == pinname:
                    node.pins[i] = (t[:4] + (list(t[4]) + [(other.name, other.pid(otherpin))],)
                                    + t[5:])
                    break

    T_STRARR_CAT = 'PinType.PinCategory="string",PinType.PinSubCategory="",PinType.PinSubCategoryObject=None'

    # ---- the move history --------------------------------------------------
    moves = n(VarGet("RM_PdMoves", "Moves", T_STRARR_CAT, -2600, -600, tail=TAIL_ARRAY))
    length = n(ArrayLength("RM_PdLen", -2400, -600))
    moves.links.append((length.name, length.pid("TargetArray")))
    length.array_links.append((moves.name, moves.out_pin()))

    # ---- the last four slots, oldest first ---------------------------------
    valid, item = [], []
    for i in range(4):
        row = -900 + i * 260
        idx = call("RM_PdIdx%d" % i, "Add_IntInt", -2200, row)
        idx.pin("A", "in", T_INT, "0", [(length.name, length.pid("ReturnValue"))])
        idx.pin("B", "in", T_INT, "%d" % (i - 4))
        idx.pin("ReturnValue", "out", T_INT)
        length.out_links.append((idx.name, idx.pid("A")))

        ok = call("RM_PdOk%d" % i, "GreaterEqual_IntInt", -2000, row - 60)
        ok.pin("A", "in", T_INT, "0", [(idx.name, idx.pid("ReturnValue"))])
        ok.pin("B", "in", T_INT, "0")
        ok.pin("ReturnValue", "out", T_INT)     # retyped below

        safe = call("RM_PdSafe%d" % i, "Max", -2000, row + 40)
        safe.pin("A", "in", T_INT, "0", [(idx.name, idx.pid("ReturnValue"))])
        safe.pin("B", "in", T_INT, "0")
        safe.pin("ReturnValue", "out", T_INT)
        link(idx, "ReturnValue", ok, "A")
        link(idx, "ReturnValue", safe, "A")
        # the two links above were added twice by construction; keep one each
        idx.pins[2] = idx.pins[2][:4] + ([(ok.name, ok.pid("A")),
                                          (safe.name, safe.pid("A"))],) + idx.pins[2][5:]
        ok.pins[0] = ok.pins[0][:4] + ([(idx.name, idx.pid("ReturnValue"))],) + ok.pins[0][5:]
        safe.pins[0] = safe.pins[0][:4] + ([(idx.name, idx.pid("ReturnValue"))],) + safe.pins[0][5:]
        ok.pins[2] = ok.pins[2][:3] + (None, [], None)   # bool output, links later

        get = n(ArrayGet("RM_PdGet%d" % i, -1800, row + 40))
        get.array_links.append((moves.name, moves.out_pin()))
        moves.links.append((get.name, get.pid("Array")))
        get.index_links.append((safe.name, safe.pid("ReturnValue")))
        safe.pins[2] = safe.pins[2][:4] + ([(get.name, get.pid("Dimension 1"))],) + safe.pins[2][5:]
        valid.append(ok)
        item.append(get)

    # GreaterEqual_IntInt returns a bool; fix the pin type now that it is built
    for ok in valid:
        ok.pins[2] = ("ReturnValue", "out", T_BOOL, None, [], None)

    # ---- score each direction ----------------------------------------------
    score = {}
    for di, d in enumerate(DIRS):
        col = -1500 + di * 40
        parts = []
        for i in range(4):
            row = -900 + i * 260 + di * 55
            eq = call("RM_PdEq%s%d" % (d[:1].upper(), i), "EqualEqual_StrStr", col, row, lib=STR)
            eq.pin("A", "in", T_STR, None, [(item[i].name, item[i].pid("Output"))])
            eq.pin("B", "in", T_STR, d)
            eq.pin("ReturnValue", "out", T_BOOL)
            item[i].out_links.append((eq.name, eq.pid("A")))

            hit = call("RM_PdHit%s%d" % (d[:1].upper(), i), "BooleanAND", col + 180, row)
            hit.pin("A", "in", T_BOOL, "false", [(eq.name, eq.pid("ReturnValue"))])
            hit.pin("B", "in", T_BOOL, "false", [(valid[i].name, valid[i].pid("ReturnValue"))])
            hit.pin("ReturnValue", "out", T_BOOL)
            eq.pins[2] = eq.pins[2][:4] + ([(hit.name, hit.pid("A"))],) + eq.pins[2][5:]
            valid[i].pins[2] = (valid[i].pins[2][:4]
                                + (list(valid[i].pins[2][4]) + [(hit.name, hit.pid("B"))],)
                                + valid[i].pins[2][5:])

            b2i = call("RM_PdB%s%d" % (d[:1].upper(), i), "Conv_BoolToInt", col + 340, row)
            b2i.pin("InBool", "in", T_BOOL, "false", [(hit.name, hit.pid("ReturnValue"))])
            b2i.pin("ReturnValue", "out", T_INT)
            hit.pins[2] = hit.pins[2][:4] + ([(b2i.name, b2i.pid("InBool"))],) + hit.pins[2][5:]

            wt = call("RM_PdW%s%d" % (d[:1].upper(), i), "Multiply_IntInt", col + 480, row)
            wt.pin("A", "in", T_INT, "0", [(b2i.name, b2i.pid("ReturnValue"))])
            wt.pin("B", "in", T_INT, "%d" % W[i])
            wt.pin("ReturnValue", "out", T_INT)
            b2i.pins[1] = b2i.pins[1][:4] + ([(wt.name, wt.pid("A"))],) + b2i.pins[1][5:]
            parts.append(wt)

        score[d] = _sum_ints(call, link, "RM_PdS%s" % d[:1].upper(), parts, col + 640, -900 + di * 55)

    # ---- pick the winner ---------------------------------------------------
    total = _sum_ints(call, link, "RM_PdTot", list(score.values()), -600, -1000)
    any_move = call("RM_PdAny", "Greater_IntInt", -420, -1000)
    any_move.pin("A", "in", T_INT, "0", [(total.name, total.pid("ReturnValue"))])
    any_move.pin("B", "in", T_INT, "0")
    any_move.pin("ReturnValue", "out", T_BOOL)
    link(total, "ReturnValue", any_move, "A")

    m1 = call("RM_PdMax1", "Max", -600, -700)
    m2 = call("RM_PdMax2", "Max", -600, -600)
    best = call("RM_PdBest", "Max", -440, -650)
    for node, (a, b) in ((m1, (score["left"], score["right"])),
                         (m2, (score["up"], score["down"]))):
        node.pin("A", "in", T_INT, "0")
        node.pin("B", "in", T_INT, "0")
        node.pin("ReturnValue", "out", T_INT)
        link(a, "ReturnValue", node, "A")
        link(b, "ReturnValue", node, "B")
    best.pin("A", "in", T_INT, "0")
    best.pin("B", "in", T_INT, "0")
    best.pin("ReturnValue", "out", T_INT)
    link(m1, "ReturnValue", best, "A")
    link(m2, "ReturnValue", best, "B")

    win = {}
    for di, d in enumerate(DIRS):
        eq = call("RM_PdIs%s" % d[:1].upper(), "EqualEqual_IntInt", -280, -800 + di * 120)
        eq.pin("A", "in", T_INT, "0")
        eq.pin("B", "in", T_INT, "0")
        eq.pin("ReturnValue", "out", T_BOOL)
        link(score[d], "ReturnValue", eq, "A")
        link(best, "ReturnValue", eq, "B")
        w = call("RM_PdWin%s" % d[:1].upper(), "BooleanAND", -120, -800 + di * 120)
        w.pin("A", "in", T_BOOL, "false")
        w.pin("B", "in", T_BOOL, "false")
        w.pin("ReturnValue", "out", T_BOOL)
        link(eq, "ReturnValue", w, "A")
        link(any_move, "ReturnValue", w, "B")
        win[d] = w

    # ---- winner -> offset --------------------------------------------------
    ints = {}
    for di, d in enumerate(DIRS):
        c = call("RM_PdC%s" % d[:1].upper(), "Conv_BoolToInt", 40, -800 + di * 120)
        c.pin("InBool", "in", T_BOOL, "false")
        c.pin("ReturnValue", "out", T_INT)
        link(win[d], "ReturnValue", c, "InBool")
        ints[d] = c

    offs = {}
    for axis, (plus, minus, row) in (("X", ("right", "left", -800)),
                                     ("Y", ("down", "up", -660))):
        sub = call("RM_PdOff%s" % axis, "Subtract_IntInt", 220, row)
        sub.pin("A", "in", T_INT, "0")
        sub.pin("B", "in", T_INT, "0")
        sub.pin("ReturnValue", "out", T_INT)
        link(ints[plus], "ReturnValue", sub, "A")
        link(ints[minus], "ReturnValue", sub, "B")
        cv = call("RM_PdD%s" % axis, "Conv_IntToDouble", 380, row)
        cv.pin("InInt", "in", T_INT, "0")
        cv.pin("ReturnValue", "out", T_DOUBLE)
        link(sub, "ReturnValue", cv, "InInt")
        offs[axis] = cv

    # ---- DogTile + offset --------------------------------------------------
    dog = n(VarGet("RM_PdDog", "DogTile", T_V2D, 380, -480))
    br = call("RM_PdBr", "BreakVector2D", 540, -480)
    br.pin("InVec", "in", T_V2D)
    br.pin("X", "out", T_DOUBLE, "0.0")
    br.pin("Y", "out", T_DOUBLE, "0.0")
    dog.links.append((br.name, br.pid("InVec")))
    br.pins[0] = br.pins[0][:4] + ([(dog.name, dog.out_pin())],) + br.pins[0][5:]

    mk = call("RM_PdMake", "MakeVector2D", 880, -560)
    for axis, pin in (("X", "X"), ("Y", "Y")):
        add = call("RM_PdAdd%s" % axis, "Add_DoubleDouble", 700,
                   -600 if axis == "X" else -480)
        add.pin("A", "in", T_DOUBLE, "0.0")
        add.pin("B", "in", T_DOUBLE, "0.0")
        add.pin("ReturnValue", "out", T_DOUBLE)
        link(br, axis, add, "A")
        link(offs[axis], "ReturnValue", add, "B")
        mk.pin(pin, "in", T_DOUBLE, "0.0")
        link(add, "ReturnValue", mk, pin)
    mk.pin("ReturnValue", "out", T_V2D)
    return nodes


def _sum_ints(call, link, prefix, parts, x, y):
    """Add a list of int-producing nodes pairwise; return the final node."""
    level, tier = list(parts), 0
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            if i + 1 == len(level):
                nxt.append(level[i])
                continue
            a = call("%s_%d_%d" % (prefix, tier, i), "Add_IntInt", x + tier * 140, y + i * 60)
            a.pin("A", "in", T_INT, "0")
            a.pin("B", "in", T_INT, "0")
            a.pin("ReturnValue", "out", T_INT)
            link(level[i], "ReturnValue", a, "A")
            link(level[i + 1], "ReturnValue", a, "B")
            nxt.append(a)
        level, tier = nxt, tier + 1
    return level[0]


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
            for i, t in enumerate(prev_print.pins):
                if t[0] == "then":
                    prev_print.pins[i] = (t[:4] + ([(pr.name, pr.pid("execute"))],)
                                          + t[5:])
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
        # The output is "Inside", not "IsInBounds": UE 5.5 refuses that exact
        # name on this Blueprint (the parameter rename silently reverts, while
        # "IsInBound" and "Inside" are both accepted). Whatever holds the name,
        # the pin name here has to match the one on the function or the pasted
        # call nodes orphan their output pin.
        ib.pin("Inside", "out", T_BOOL, None, [(cb.name, cb.pid("InBool"))])
        cb.pin("InBool", "in", T_BOOL, "false", [(ib.name, ib.pid("Inside"))])
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

    def approach_case(tag, ax, ay, bx, by, expect):
        """Approach is the One Wow's read of "is the dog closing in".

        It is worth asserting even though nothing else calls it yet: GDD 3
        exploit 4 was an approach value that only ever ratcheted upward, and the
        fix was to make it positional -- recomputed from the two tiles on every
        call, storing nothing. A test that feeds it the same pair twice and a
        receding pair is the only thing that keeps that property honest.
        """
        va = Node("RM_APA" + tag, "MakeVector2D", -900, y_of(), lib=MATH)
        vb = Node("RM_APB" + tag, "MakeVector2D", -900, y_of() + 90, lib=MATH)
        ap = Node("RM_AP" + tag, "Approach", -650, y_of(), lib=SELF_CTX)
        cv = Node("RM_APC" + tag, "Conv_DoubleToString", -420, y_of(), lib=STR)
        for v, (px, py) in ((va, (ax, ay)), (vb, (bx, by))):
            v.pin("X", "in", T_DOUBLE, "%.1f" % px)
            v.pin("Y", "in", T_DOUBLE, "%.1f" % py)
            v.pin("ReturnValue", "out", T_V2D, None,
                  [(ap.name, ap.pid("Dog" if v is va else "Kid"))])
        ap.pin("Dog", "in", T_V2D, None, [(va.name, va.pid("ReturnValue"))])
        ap.pin("Kid", "in", T_V2D, None, [(vb.name, vb.pid("ReturnValue"))])
        ap.pin("Approach", "out", T_DOUBLE, None, [(cv.name, cv.pid("InDouble"))])
        cv.pin("InDouble", "in", T_DOUBLE, "0.0", [(ap.name, ap.pid("Approach"))])
        cv.pin("ReturnValue", "out", T_STR, None)
        nodes.extend([va, vb, ap, cv])
        print_line(tag, "Approach (%g,%g)->(%g,%g) expect %s got "
                   % (ax, ay, bx, by, expect), cv, "ReturnValue")

    def steptoward_case(tag, fx, fy, tx, ty, expect):
        """StepToward returns a tile, so the assertion prints "x,y".

        The out-of-bounds case is the one that matters. Predict deliberately
        returns an off-grid tile when the dog is against a fence, so Rex is
        routinely asked to walk toward somewhere that does not exist. game.js
        skips a candidate that fails inBounds and falls through to the next
        direction; if the guard were dropped here Rex would step off the board
        and every later InBounds would read false.
        """
        va = Node("RM_SVA" + tag, "MakeVector2D", -1150, y_of(), lib=MATH)
        vb = Node("RM_SVB" + tag, "MakeVector2D", -1150, y_of() + 90, lib=MATH)
        st = Node("RM_ST" + tag, "StepToward", -900, y_of(), lib=SELF_CTX)
        br = Node("RM_SBR" + tag, "BreakVector2D", -700, y_of(), lib=MATH)
        cx = Node("RM_SCX" + tag, "Conv_DoubleToString", -540, y_of(), lib=STR)
        cy = Node("RM_SCY" + tag, "Conv_DoubleToString", -540, y_of() + 60, lib=STR)
        j1 = Node("RM_SJ1" + tag, "Concat_StrStr", -380, y_of(), lib=STR)
        j2 = Node("RM_SJ2" + tag, "Concat_StrStr", -280, y_of(), lib=STR)
        for v, (px, py), pin in ((va, (fx, fy), "From"), (vb, (tx, ty), "Target")):
            v.pin("X", "in", T_DOUBLE, "%.1f" % px)
            v.pin("Y", "in", T_DOUBLE, "%.1f" % py)
            v.pin("ReturnValue", "out", T_V2D, None, [(st.name, st.pid(pin))])
        st.pin("From", "in", T_V2D, None, [(va.name, va.pid("ReturnValue"))])
        st.pin("Target", "in", T_V2D, None, [(vb.name, vb.pid("ReturnValue"))])
        st.pin("Step", "out", T_V2D, None, [(br.name, br.pid("InVec"))])
        br.pin("InVec", "in", T_V2D, None, [(st.name, st.pid("Step"))])
        br.pin("X", "out", T_DOUBLE, "0.0", [(cx.name, cx.pid("InDouble"))])
        br.pin("Y", "out", T_DOUBLE, "0.0", [(cy.name, cy.pid("InDouble"))])
        cx.pin("InDouble", "in", T_DOUBLE, "0.0", [(br.name, br.pid("X"))])
        cx.pin("ReturnValue", "out", T_STR, None, [(j1.name, j1.pid("A"))])
        cy.pin("InDouble", "in", T_DOUBLE, "0.0", [(br.name, br.pid("Y"))])
        cy.pin("ReturnValue", "out", T_STR, None, [(j2.name, j2.pid("B"))])
        j1.pin("A", "in", T_STR, None, [(cx.name, cx.pid("ReturnValue"))])
        j1.pin("B", "in", T_STR, ",")
        j1.pin("ReturnValue", "out", T_STR, None, [(j2.name, j2.pid("A"))])
        j2.pin("A", "in", T_STR, None, [(j1.name, j1.pid("ReturnValue"))])
        j2.pin("B", "in", T_STR, None, [(cy.name, cy.pid("ReturnValue"))])
        j2.pin("ReturnValue", "out", T_STR, None)
        nodes.extend([va, vb, st, br, cx, cy, j1, j2])
        print_line(tag, "StepToward (%g,%g)->(%g,%g) expect %s got "
                   % (fx, fy, tx, ty, expect), j2, "ReturnValue")

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
    # Approach: 1 - Manhattan/11, clamped 0..1. The dog spawns exactly 11 tiles
    # from the kid, which is why the divisor is 11 and why spawn reads 0.
    approach_case("F", 0, 0, 7, 4, "0")          # spawn
    approach_case("G", 7, 4, 7, 4, "1")          # standing on the kid
    approach_case("H", 6, 4, 7, 4, "0.909091")   # one tile out
    approach_case("I", 9, 9, 0, 0, "0 (clamped)")  # 18 tiles: 1-18/11 is negative
    # StepToward: game.js tries left, right, up, down and keeps the first that
    # closes the gap, so X is preferred over Y whenever both differ.
    steptoward_case("J", 5, 5, 5, 5, "5.0,5.0")    # already there, do not move
    steptoward_case("K", 5, 5, 7, 4, "6.0,5.0")    # both differ: X wins
    steptoward_case("L", 5, 5, 5, 2, "5.0,4.0")    # dx is 0, so Y moves
    steptoward_case("M", 0, 3, -1, 0, "0.0,2.0")   # left is off-grid: falls to up
    steptoward_case("N", 9, 9, 9, 0, "9.0,8.0")    # against the far fence
    return nodes


GRAPHS = {"manhattan": manhattan, "band": band, "inbounds": inbounds,
          "approach": approach, "tiletoworld": tiletoworld,
          "steptoward": steptoward, "predict": predict,
          "selftest": selftest}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "manhattan"
    if which not in GRAPHS:
        raise SystemExit("unknown graph %r; have: %s" % (which, ", ".join(sorted(GRAPHS))))
    sys.stdout.write("\n".join(n.render() for n in GRAPHS[which]()) + "\n")
