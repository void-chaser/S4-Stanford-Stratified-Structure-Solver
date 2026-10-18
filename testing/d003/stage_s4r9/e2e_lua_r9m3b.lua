-- e2e_lua_r9m3b.lua -- Lua batch frontend E2E point (one solve per process).
-- usage: S4_e2e -a "<spec>" e2e_lua_r9m3b.lua      (the spec travels in S4.arg, which
-- main_lua.c sets only for -a; extra argv is treated as script files, so none is passed)
-- Options use the real method names; a missing method is a hard error (no pcall).
local spec = S4.arg
if type(spec) ~= "string" or spec == "" then
    error("e2e_lua_r9m3b: spec must be passed as -a \"<spec>\" (S4.arg)")
end
local function call(obj, name, ...)
    local f = obj[name]
    if f == nil then
        error("e2e_lua_r9m3b: method missing: " .. name)
    end
    return f(obj, ...)
end
local S = S4.NewSimulation()
call(S, "SetLattice", {1, 0}, {0, 1})
call(S, "SetNumG", 25)
call(S, "AddMaterial", "Air", {1, 0})
call(S, "AddMaterial", "Slab", {12, 0})
call(S, "AddLayer", "Top", 0, "Air")
call(S, "AddLayer", "Middle", 0.5, "Slab")
call(S, "SetLayerPatternCircle", "Middle", "Air", {0, 0}, 0.2)
call(S, "AddLayerCopy", "Bottom", 0, "Top")
call(S, "SetFrequency", 0.4)
call(S, "SetExcitationPlanewave", {0, 0}, {1, 0}, {0, 0})
if spec == "cf" then
    -- default options: ClosedForm path
elseif spec == "fft" then
    call(S, "UseDiscretizedEpsilon")
    call(S, "SetResolution", 8)
elseif spec == "kt" then
    call(S, "UseDiscretizedEpsilon")
    call(S, "SetResolution", 8)
    call(S, "UseSubpixelSmoothing")
elseif spec == "jones" then
    call(S, "UseDiscretizedEpsilon")
    call(S, "SetResolution", 8)
    call(S, "UsePolarizationDecomposition")
    call(S, "UseJonesVectorBasis")
elseif spec == "nv" then
    call(S, "UseDiscretizedEpsilon")
    call(S, "SetResolution", 8)
    call(S, "UsePolarizationDecomposition")
    call(S, "UseNormalVectorBasis")
elseif spec == "vl" then
    call(S, "UseDiscretizedEpsilon")
    call(S, "SetResolution", 8)
    call(S, "UsePolarizationDecomposition")
elseif spec == "exp" then
    call(S, "UseExperimentalFMM")
else
    error("e2e_lua_r9m3b: unknown spec " .. tostring(spec))
end
print("PHASE batch spec=" .. spec)
local p1, p2, p3, p4 = S:GetPoyntingFlux("Bottom", 0)
print(string.format("VALUES %.17g %.17g %.17g %.17g", p1, p2, p3, p4))
print("BATCH_DONE")
