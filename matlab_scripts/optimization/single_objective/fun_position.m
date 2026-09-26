function [f, time, reference0, position] = fun_position(x,T,objective)
if nargin < 3, objective = 'ITSE'; end
simOut = simulate_servo_position(x, T, 'Jerk_FF_Step_2023');
reference0 = simOut.Ref_Step_PU0.signals.values;
position = simOut.Pos_Fb_PU.signals.values;
time = simOut.Pos_Fb_PU.time;
f = servo_error_metric(time, reference0, position, objective);
end
