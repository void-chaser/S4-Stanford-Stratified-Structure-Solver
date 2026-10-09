-- Error-code-20 propagation check for the Lua frontend (run by run_error20.py).
-- The environment variable S4_TEST_EIGEN_INFO, set or unset by the caller, decides
-- whether the library injects a layer-eigensystem failure on a seam build.
-- Prints one line per call:  RESULT <name> ok <value>   or   RESULT <name> error <msg>

local function build()
	local S = S4.NewSimulation()
	S:SetLattice({1,0}, {0,1})
	S:SetNumG(9)
	S:AddMaterial('Film', {4,0})
	S:AddMaterial('Air', {1,0})
	S:AddLayer('AirTop', 0, 'Air')
	S:AddLayer('Film', 0.25, 'Film')
	-- same-material circle: a non-uniform layer, so the eigensystem is really solved
	S:SetLayerPatternCircle('Film', 'Film', {0,0}, 0.2)
	S:AddLayer('AirBottom', 0, 'Air')
	S:SetFrequency(0.427)
	S:SetExcitationPlanewave({0,0}, {1,0}, {0,0})
	return S
end

local function call(name, f)
	local ok, a, b = pcall(f)
	if ok then
		print(string.format("RESULT %s ok %.17g %.17g", name, a, b or 0))
	else
		print(string.format("RESULT %s error %s", name, tostring(a)))
	end
end

local S = build()
call("GetPowerFlux_first", function() return S:GetPoyntingFlux('AirTop', 0) end)
call("GetPowerFlux_again", function() return S:GetPoyntingFlux('AirBottom', 0) end)

local T = build()
call("GetPowerFlux_fresh", function() return T:GetPoyntingFlux('AirBottom', 0) end)
