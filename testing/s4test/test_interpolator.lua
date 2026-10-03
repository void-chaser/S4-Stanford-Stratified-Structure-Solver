local s = S4.NewSimulation()
local table = {
    {0.0, {0.0}},
    {0.5, {0.25}},
    {1.0, {1.0}}
}
local interp = S4.NewInterpolator('cubic spline', table)
local y = interp:Get(0.75)
if math.abs(y - 0.578125) > 1e-6 then
    error('cubic spline natural boundary failed: ' .. y)
end
print('Cubic spline natural Lua OK')

local table2 = {
    {0.0, {0.0}},
    {0.0, {1.0}}
}
local success, err = pcall(function() S4.NewInterpolator('linear', table2) end)
if success then
    error('Failed to block duplicate x')
else
    print('Blocked duplicate x OK: ' .. err)
end
