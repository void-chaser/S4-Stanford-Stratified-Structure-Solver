-- Error-code-20 propagation through SolveInParallel (run by run_error20.py).
-- ERROR20_PARALLEL_SCENARIO selects the scenario:  one = one simulation object,
-- two = two objects.
-- One process per scenario: a failed layer solve ends a script-mode interpreter (the
-- non-interactive error policy), so the outcome is read from the exit status and stdout.
-- Prints RESULT lines only for calls that return normally.

local function build(freq)
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
	S:SetFrequency(freq)
	S:SetExcitationPlanewave({0,0}, {1,0}, {0,0})
	return S
end

local scenario = os.getenv("ERROR20_PARALLEL_SCENARIO")
local A = build(0.427)
print("RESULT parallel_start")
if scenario == "one" then
	S4.SolveInParallel('Film', A)
elseif scenario == "two" then
	local B = build(0.733)
	S4.SolveInParallel('Film', A, B)
else
	error("unknown scenario " .. tostring(scenario))
end
print("RESULT parallel_returned_normally")
local v = A:GetPoyntingFlux('AirTop', 0)
print(string.format("RESULT flux_after %.17g", v))
