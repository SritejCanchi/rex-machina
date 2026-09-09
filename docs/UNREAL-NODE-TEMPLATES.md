# Blueprint node shapes, captured not guessed

`tools/bp_gen.py` writes Blueprint node text and UE rebuilds the graph from it
on paste. That only works if the text is exactly what UE itself would write, so
every node class in the generator was captured the same way: place one real
node in a graph, select it, Ctrl+C, and read the clipboard.

To capture a new one:

1. Open `BP_FightManager` and go to its **EventGraph** -- an event graph has no
   return node, so clearing it afterwards with Ctrl+A + Delete is safe. Doing
   that in a *function* graph deletes the return node and its output parameter.
2. Right-click, search for the node, Enter.
3. Ctrl+A, Ctrl+C.
4. `Get-Clipboard -Raw | Out-File tmpl.txt` and read it.
5. Delete the nodes, compile, save.

## What is already captured

| Node | Class | Notes |
|---|---|---|
| Call to a Kismet library | `K2Node_CallFunction` | `MemberParent` quoting is exact |
| Call on this Blueprint | `K2Node_CallFunction` | no `MemberParent`; `bSelfContext=True` |
| Event (BeginPlay) | `K2Node_Event` | `EventReference`, parent is `/Script/Engine.Actor` |
| Variable get | `K2Node_VariableGet` | output pin is named after the variable |
| Variable set | `K2Node_VariableSet` | `execute`/`then`, plus a spare `Output_Get` |
| Array length | `K2Node_CallArrayFunction` | array pin is by-ref **and const** |
| Array append | `K2Node_CallArrayFunction` | `Array_Add`: by-ref, **not** const |
| Array element | `K2Node_GetArrayItem` | index pin is called **`Dimension 1`** |
| Branch | `K2Node_IfThenElse` | `execute`, `Condition`, `then`, `else` -- nothing else |

## Captured and not yet used

These three came out of the editor in one pass and are what the round loop and
the visible half of the build still need. None is in `bp_gen.py` yet.

**Get All Actors Of Class** -- `K2Node_CallFunction` on
`/Script/Engine.GameplayStatics`, `MemberName="GetAllActorsOfClass"`. Impure.

    pin execute            in   exec
    pin then               out  exec
    pin self               in   object  -> GameplayStatics   (hidden)
    pin WorldContextObject in   object  -> Object
    pin ActorClass         in   class   -> Actor
    pin OutActors          out  object  Array -> Actor

**Set Actor Location** -- `MemberName="K2_SetActorLocation"`. Captured with
`bSelfContext=True` because it was dropped with no target; to move a *different*
actor, wire that actor into the `self` pin instead.

    pin execute          in   exec
    pin then             out  exec
    pin self             in   object -> Actor
    pin NewLocation      in   struct -> Vector
    pin bSweep           in   bool
    pin SweepHitResult   out  struct -> HitResult
    pin bTeleport        in   bool
    pin ReturnValue      out  bool

**Get Data Table Row Names** -- on
`/Script/Engine.DataTableFunctionLibrary`, `MemberName="GetDataTableRowNames"`.

    pin Table        in   object -> DataTable
    pin OutRowNames  out  name   Array

Note this is *not* the node `SpeakRead` wants. Searching "Get Data Table Row"
selected this one; the row lookup itself is `K2Node_GetDataTableRow`, a
dedicated node class with a wildcard output struct, and it still needs
capturing.

## The one thing that does not need capturing

A `VariableReference` resolves by **name alone** -- `MemberGuid` is optional.
That matters because Blueprint's `new_variables` array is not exposed to
Python (`tools/ue_dump_varguids.py` tries and reports why), so guids can only
be read off a node that already exists. `bp_gen.py` carries the three it
happens to have and omits the rest, and `RexAct` reads and writes `Charge`,
`PursuitCost`, `HoldCost`, `SolarRecovery` and `StartCharge` with no guid at
all.
