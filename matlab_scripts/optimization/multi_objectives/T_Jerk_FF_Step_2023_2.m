function results=T_Jerk_FF_Step_2023_2(x,T)
simOut = simulate_servo_position(x, T, 'Jerk_FF_Step_2023_2');

% 索引
reference0 = simOut.Ref_Step_PU0.signals.values;
% reference1 = simOut.Ref_Step_PU1.signals.values;
position = simOut.Pos_Fb_PU.signals.values;
time= simOut.Pos_Fb_PU.time;
results=[time reference0 position];
end