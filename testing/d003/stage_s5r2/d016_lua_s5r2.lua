-- d016_lua_s5r2.lua -- D016 points on the Lua public API, F4 build at $EV/trees/F4.
-- Streamed to the Lua REPL (stdin, mode chosen with -a main|ref -> S4.arg). Each line is one
-- complete chunk and stays under main_lua.c's 256-byte REPL buffer (char buff[256]).
-- In REPL mode S4L_error prints and returns instead of exiting, which is what allows the
-- same-process retry and the same-process recovery object. API names verified against
-- S4/main_lua.c: SetLattice, SetNumG, UsePolarizationDecomposition, UseJonesVectorBasis,
-- UseNormalVectorBasis, AddMaterial, AddLayer, SetLayerPatternCircle, SetExcitationPlanewave,
-- SetFrequency, GetPowerFlux (alias of GetPoyntingFlux; the error text names GetPoyntingFlux).
-- Each "if M/R then ... end" fragment is one fresh object per point; options are set at
-- construction time only (no option change after a solve).
M=(S4.arg=="main"); R=(S4.arg=="ref")
function pf(t) a,b,c,d=S:GetPowerFlux("Air_above",0); if a==nil then print("POINT "..t.." FAIL_VISIBLE") else print("POINT "..t.." VALUES",a,b,c,d) end end
if M then S=S4.NewSimulation(); S:SetLattice({1,0},{0,1}); S:SetNumG(1) end
if M then S:UsePolarizationDecomposition(); S:AddMaterial("Air",{1,0}); S:AddMaterial("Glass",{4,0}) end
if M then S:AddLayer("Air_above",0,"Air"); S:AddLayer("Slab",0.5,"Air") end
if M then S:SetLayerPatternCircle("Slab","Glass",{0,0},0.25); S:AddLayer("Air_below",0,"Air") end
if M then S:SetExcitationPlanewave({0,0},{1,0},{0,0}); S:SetFrequency(0.427) end
if M then pf("VL_NB1") end
if M then pf("VL_NB1_RETRY") end
if M then S=S4.NewSimulation(); S:SetLattice({1,0},{0,1}); S:SetNumG(2) end
if M then S:UsePolarizationDecomposition(); S:AddMaterial("Air",{1,0}); S:AddMaterial("Glass",{4,0}) end
if M then S:AddLayer("Air_above",0,"Air"); S:AddLayer("Slab",0.5,"Air") end
if M then S:SetLayerPatternCircle("Slab","Glass",{0,0},0.25); S:AddLayer("Air_below",0,"Air") end
if M then S:SetExcitationPlanewave({0,0},{1,0},{0,0}); S:SetFrequency(0.427) end
if M then pf("VL_NB2") end
if M then pf("VL_NB2_RETRY") end
if M then S=S4.NewSimulation(); S:SetLattice({1,0},{0,1}); S:SetNumG(3) end
if M then S:UsePolarizationDecomposition(); S:AddMaterial("Air",{1,0}); S:AddMaterial("Glass",{4,0}) end
if M then S:AddLayer("Air_above",0,"Air"); S:AddLayer("Slab",0.5,"Air") end
if M then S:SetLayerPatternCircle("Slab","Glass",{0,0},0.25); S:AddLayer("Air_below",0,"Air") end
if M then S:SetExcitationPlanewave({0,0},{1,0},{0,0}); S:SetFrequency(0.427) end
if M then pf("VL_NB3") end
if M then pf("VL_NB3_RETRY") end
if M then S=S4.NewSimulation(); S:SetLattice({1,0},{0,1}); S:SetNumG(4) end
if M then S:UsePolarizationDecomposition(); S:AddMaterial("Air",{1,0}); S:AddMaterial("Glass",{4,0}) end
if M then S:AddLayer("Air_above",0,"Air"); S:AddLayer("Slab",0.5,"Air") end
if M then S:SetLayerPatternCircle("Slab","Glass",{0,0},0.25); S:AddLayer("Air_below",0,"Air") end
if M then S:SetExcitationPlanewave({0,0},{1,0},{0,0}); S:SetFrequency(0.427) end
if M then pf("VL_NB4") end
if M then pf("VL_NB4_RETRY") end
if M then S=S4.NewSimulation(); S:SetLattice({1,0},{0,1}); S:SetNumG(5) end
if M then S:UsePolarizationDecomposition(); S:AddMaterial("Air",{1,0}); S:AddMaterial("Glass",{4,0}) end
if M then S:AddLayer("Air_above",0,"Air"); S:AddLayer("Slab",0.5,"Air") end
if M then S:SetLayerPatternCircle("Slab","Glass",{0,0},0.25); S:AddLayer("Air_below",0,"Air") end
if M then S:SetExcitationPlanewave({0,0},{1,0},{0,0}); S:SetFrequency(0.427) end
if M then pf("VL_NB5") end
if M then S=S4.NewSimulation(); S:SetLattice({1,0},{0,1}); S:SetNumG(9) end
if M then S:UsePolarizationDecomposition(); S:AddMaterial("Air",{1,0}); S:AddMaterial("Glass",{4,0}) end
if M then S:AddLayer("Air_above",0,"Air"); S:AddLayer("Slab",0.5,"Air") end
if M then S:SetLayerPatternCircle("Slab","Glass",{0,0},0.25); S:AddLayer("Air_below",0,"Air") end
if M then S:SetExcitationPlanewave({0,0},{1,0},{0,0}); S:SetFrequency(0.427) end
if M then pf("VL_NB9") end
if M then S=S4.NewSimulation(); S:SetLattice({1,0},{0,1}); S:SetNumG(9) end
if M then S:UsePolarizationDecomposition(); S:AddMaterial("Air",{1,0}); S:AddMaterial("Glass",{4,0}) end
if M then S:AddLayer("Air_above",0,"Air"); S:AddLayer("Slab",0.5,"Air") end
if M then S:SetLayerPatternCircle("Slab","Glass",{0,0},0.25); S:AddLayer("Air_below",0,"Air") end
if M then S:SetExcitationPlanewave({0,0},{1,0},{0,0}); S:SetFrequency(0.427) end
if M then pf("VL_NB9_RECOVER") end
if M then S=S4.NewSimulation(); S:SetLattice({1,0},{0,1}); S:SetNumG(1) end
if M then S:UsePolarizationDecomposition(); S:UseJonesVectorBasis(); S:AddMaterial("Air",{1,0}); S:AddMaterial("Glass",{4,0}) end
if M then S:AddLayer("Air_above",0,"Air"); S:AddLayer("Slab",0.5,"Air") end
if M then S:SetLayerPatternCircle("Slab","Glass",{0,0},0.25); S:AddLayer("Air_below",0,"Air") end
if M then S:SetExcitationPlanewave({0,0},{1,0},{0,0}); S:SetFrequency(0.427) end
if M then pf("Jones_NB1") end
if M then S=S4.NewSimulation(); S:SetLattice({1,0},{0,1}); S:SetNumG(1) end
if M then S:UsePolarizationDecomposition(); S:UseNormalVectorBasis(); S:AddMaterial("Air",{1,0}); S:AddMaterial("Glass",{4,0}) end
if M then S:AddLayer("Air_above",0,"Air"); S:AddLayer("Slab",0.5,"Air") end
if M then S:SetLayerPatternCircle("Slab","Glass",{0,0},0.25); S:AddLayer("Air_below",0,"Air") end
if M then S:SetExcitationPlanewave({0,0},{1,0},{0,0}); S:SetFrequency(0.427) end
if M then pf("NV_NB1") end
if M then print("LUA_MAIN_DONE") end
if R then S=S4.NewSimulation(); S:SetLattice({1,0},{0,1}); S:SetNumG(9) end
if R then S:UsePolarizationDecomposition(); S:AddMaterial("Air",{1,0}); S:AddMaterial("Glass",{4,0}) end
if R then S:AddLayer("Air_above",0,"Air"); S:AddLayer("Slab",0.5,"Air") end
if R then S:SetLayerPatternCircle("Slab","Glass",{0,0},0.25); S:AddLayer("Air_below",0,"Air") end
if R then S:SetExcitationPlanewave({0,0},{1,0},{0,0}); S:SetFrequency(0.427) end
if R then pf("VL_NB9_REF") end
if R then print("LUA_REF_DONE") end
print("LUA_SCRIPT_END")
