function f = fun_position(x,T)
%% Set PWM Switching frequency
PWM_frequency 	= 20e3;             %Hz     // converter s/w freq
T_pwm           = 1/PWM_frequency;  %s      // PWM switching time period

%% Set Sample Times
Ts          	= T_pwm;            %sec    // Sample time for control system
Ts_simulink     = T_pwm/2;          %sec    // Simulation time step for model simulation
Ts_motor        = T_pwm/2;          %Sec    // Simulation time step for pmsm
Ts_inverter     = T_pwm/2;          %sec    // Simulation time step for inverter
Ts_speed        = 2*Ts;             %Sec    // Sample time for speed controller and position controller

%% Set data type for controller & code-gen
% dataType = fixdt(1,32,24);        % Fixed point code-generation
dataType = 'single';                % Floating point code-generation

%% System Parameters
% Motor parameters
%pmsm = mcb_SetPMSMMotorParameters('Teknic2310P');
pmsm.model    = 'Teknic-2310P';     %           // Manufacturer Model Number
pmsm.sn       = '003';              %           // Manufacturer Model Number
pmsm.p        = 4;                  %           // Pole Pairs for the motor
pmsm.Rs       = 0.36;               %Ohm        // Stator Resistor
pmsm.Ld       = 0.2e-3;             %H          // D-axis inductance value
pmsm.Lq       = 0.2e-3;             %H          // Q-axis inductance value
pmsm.J        = 7.061551833333e-6;  %Kg-m2      // Inertia in SI units
pmsm.B        = 2.636875217824e-6;  %Kg-m2/s    // Friction Co-efficient
pmsm.Ke       = 4.64;               %Bemf Const	// Vpk_LL/krpm
pmsm.Kt       = 0.0384;             %Nm/A       // Torque constant
pmsm.I_rated  = 7.1;                %A      	// Rated current (phase-peak)
pmsm.N_max    = 6000;               %rpm        // Max speed
% pmsm.PositionOffset = 0.1712;	    %PU position// Position Offset
pmsm.QEPSlits = 1000;               %           // QEP Encoder Slits
pmsm.FluxPM   = (pmsm.Ke)/(sqrt(3)*2*pi*1000*pmsm.p/60); %PM flux computed from Ke
% pmsm.FluxPM = (pmsm.Kt)/((3/2)*pmsm.p); %PM flux computed from Kt
%pmsm.T_rated  = mcbPMSMRatedTorque(pmsm);   %Get T_rated from I_rated
pmsm.T_rated  = 0.2724;
pmsm.PositionOffset = 0;         % Per-Unit position offset
mech.J = 7e-5;
mech.B = 1.5e-3;
mech.f = 0.015;
mech.T=T;
% mech.T=0.5;
%% Target & Inverter Parameters
%target = mcb_SetProcessorDetails('F28379D',PWM_frequency);
target.model                = 'LAUNCHXL-F28379D';	% 		// Manufacturer Model Number
target.sn                   = '123456';          	% 		// Manufacturer Serial Number
target.CPU_frequency        = 200e6;    			%Hz     // Clock frequency
target.PWM_frequency        = PWM_frequency;   		%Hz     // PWM frequency
target.PWM_Counter_Period   = round(target.CPU_frequency/target.PWM_frequency/2); % //PWM timer counts for up-down counter
target.PWM_Counter_Period   = target.PWM_Counter_Period+mod(target.PWM_Counter_Period,2); % // Count value needs to be even
target.ADC_Vref             = 3;					%V		// ADC voltage reference for LAUNCHXL-F28379D
target.ADC_MaxCount         = 4095;					%		// Max count for 12 bit ADC
target.SCI_baud_rate        = 12e6;                 %Hz     // Set baud rate for serial communication
target.comport = '<Select a port...>';
% target.comport = 'COM3';       % Uncomment and update the appropriate serial port
assignin('base', 'target', target);
%inverter = mcb_SetInverterParameters('BoostXL-DRV8305'); % BOOSTXL-3PhGaNInv
inverter.model         = 'BoostXL-DRV8305'; 	% 		// Manufacturer Model Number
inverter.sn            = 'INV_XXXX';         	% 		// Manufacturer Serial Number
inverter.V_dc          = 24;       				%V      // DC Link Voltage of the Inverter
inverter.I_trip        = 10;       				%Amps   // Max current for trip
inverter.Rds_on        = 2e-3;     				%Ohms   // Rds ON for BoostXL-DRV8305
inverter.Rshunt        = 0.007;    				%Ohms   // Rshunt for BoostXL-DRV8305
inverter.CtSensAOffset = 2295;        			%Counts // ADC Offset for phase-A
inverter.CtSensBOffset = 2286;        			%Counts // ADC Offset for phase-B
inverter.CtSensCOffset = 2295;        			%Counts // ADC Offset for phase-C
inverter.ADCGain       = 1;                     %       // ADC Gain factor scaled by SPI
inverter.EnableLogic   = 1;    					% 		// Active high for DRV8305 enable pin (EN_GATE)
inverter.invertingAmp  = 1;   					% 		// Currents entering motor phases are read as positive values in this hardware
inverter.ISenseVref    = 3.3;					%V 		// Voltage ref of inverter current sense circuit
inverter.ISenseVoltPerAmp = 0.07; 				%V/Amps // Current sense voltage output per 1 A current (Rshunt * iSense op-amp gain)
inverter.ISenseMax     = inverter.ISenseVref/(2*inverter.ISenseVoltPerAmp); %Amps // Maximum Peak-Neutral current that can be measured by inverter current sense
inverter.R_board       = inverter.Rds_on + inverter.Rshunt/3;  %Ohms

inverter.CtSensOffsetMax = 2500; % Maximum permitted ADC counts for current sense offset
inverter.CtSensOffsetMin = 1500; % Minimum permitted ADC counts for current sense offset

% Enable automatic calibration of ADC offset for current measurement
inverter.ADCOffsetCalibEnable = 1; % Enable: 1, Disable:0

% If automatic ADC offset calibration is disabled, uncomment and update the
% offset values below manually
inverter.CtSensAOffset = 2295;      % ADC Offset for phase current A
inverter.CtSensBOffset = 2286;      % ADC Offset for phase current B

% Update inverter.ISenseMax based for the chosen motor and target
inverter = mcb_updateInverterParameters(pmsm,inverter,target);

% Max and min ADC counts for current sense offsets
inverter.CtSensOffsetMax = 2500; % Maximum permitted ADC counts for current sense offset
inverter.CtSensOffsetMin = 1500; % Minimum permitted ADC counts for current sense offset

%% Derive Characteristics
%pmsm.N_base = mcb_getBaseSpeed(pmsm,inverter); %rpm // Base speed of motor at given Vdc
pmsm.N_base = 4107;

% mcb_getCharacteristics(pmsm,inverter);

%% PU System details // Set base values for pu conversion

%PU_System = mcb_SetPUSystem(pmsm,inverter);
PU_System.V_base = 13.8564;
PU_System.I_base = 21.4286;
PU_System.N_base = 4107;
PU_System.P_base = 445.3845;
PU_System.T_base = 0.8223;
PU_System.AngleBase = 360;

%% Controller design // Get ballpark values!

%PI_params = mcb_SetControllerParameters(pmsm,inverter,PU_System,T_pwm,Ts,Ts_speed);
PI_params.delay_IIR = 0.02;
PI_params.Ti_i = 5.4895e-4;
% PI_params.Kp_i = 3.0929;
% PI_params.Ki_i = 5.6343e+3;
% PI_params.Kp_id = 3.0929;
% PI_params.Ki_id = 5.6343e+3;
PI_params.Ti_speed = 0.0321;
% PI_params.Kp_speed = 1.0838;
% PI_params.Ki_speed = 33.7498;
PI_params.Ti_fwc = 5.4895e-4;
PI_params.Kp_fwc = 0.0137;
PI_params.Ki_fwc = 24.9377;
% PI_params.Kp_PosCtrl = 1;

%Updating delays for simulation
PI_params.delay_Currents    = int32(Ts/Ts_simulink);
PI_params.delay_Position    = int32(Ts/Ts_simulink);
PI_params.delay_Speed       = int32(Ts_speed/Ts_simulink);
PI_params.delay_Speed1      = (PI_params.delay_IIR + 0.5*Ts)/Ts_speed;
%Low-Pass Filter Parameters

% LPF.freq = 25; %频率越大越抖

% mcb_getControlAnalysis(pmsm,inverter,PU_System,PI_params,Ts,Ts_speed);

%% Set position and speed limits
PosCtrlSpeedLimit = 0.3;	%PU speed
PosCtrlPosLimit = 5; 		%PU Angle in positive direction // e.g. max position input in either direction is 5*360 degrees.
assignin('base', 'PosCtrlSpeedLimit', PosCtrlSpeedLimit);
assignin('base', 'PosCtrlPosLimit', PosCtrlPosLimit);
OpenLoop.SpeedRef = 0.01*pmsm.N_base;    % RPM
OpenLoop.RampTime = 0.15;                   % seconds
OpenLoop.MagUpperLimit = 0.95;           % Per-Unit //Voltage Amplitude upper limit
OpenLoop.MagLowerLimit = 0.15;           % Per-Unit //Voltage Amplitude lower limit

%%

PI_params.Kp_i = x(1);
PI_params.Ki_i = x(2);
PI_params.Kp_id = x(1);
PI_params.Ki_id = x(2);
PI_params.Kp_speed = x(3);
PI_params.Ki_speed = x(4);
PI_params.Kp_PosCtrl = x(5);
FF.k1 = x(6);
FF.k2 = x(7);
jerk.k1 = x(8);% [10 500]
jerk.k2 = x(9);% [10 500]
jerk.k3 = x(10);%[10 500]
jerk.k4 = x(11);


% 将结构体写入工作区
assignin('base', 'PWM_frequency', PWM_frequency);
assignin('base', 'T_pwm', T_pwm);
assignin('base', 'Ts', Ts);
assignin('base', 'Ts_simulink', Ts_simulink);
assignin('base', 'Ts_motor', Ts_motor);
assignin('base', 'Ts_inverter', Ts_inverter);
assignin('base', 'Ts_speed', Ts_speed);
assignin('base', 'dataType', dataType);
assignin('base', 'inverter', inverter);
assignin('base', 'pmsm', pmsm);
assignin('base', 'PU_System', PU_System);
assignin('base', 'PI_params', PI_params);
% assignin('base', 'LPF', LPF);
assignin('base', 'OpenLoop', OpenLoop);
assignin('base', 'dataType', 'single');  % 确保dataType存在
assignin('base', 'PI_params', PI_params);
assignin('base', 'FF', FF);
assignin('base', 'jerk', jerk);
assignin('base', 'mech', mech);

mdlName = 'Jerk_FF_Step_2023';
load_system(mdlName);
cs = getActiveConfigSet(mdlName);
model_cs = cs.copy;
simOut = sim(mdlName, model_cs);

% 索引
reference0 = simOut.Ref_Step_PU0.signals.values;
reference1 = simOut.Ref_Step_PU1.signals.values;
position = simOut.Pos_Fb_PU.signals.values;
time= simOut.Pos_Fb_PU.time;

time_step_idx = find(time ==0.5,1);

% 设定稳态时间窗口 (例如最后0.15秒)
steady_state_window = time(end) - 0.15;  % 假设最后2秒是稳态

% 找到时间窗口的索引
steady_state_indices = find(time >= steady_state_window);

% 计算在稳态时间段内的平均值
% steady_state_value = mean(position(steady_state_indices));

% 计算稳态误差
% desired_value = 0.5;  % 单位阶跃输入
% steady_state_error = abs(desired_value - steady_state_value);
% 
% % 计算超调量 (Overshoot)
% peak_value = max(position);
% overshoot = (peak_value - reference0(time_step_idx)) / reference0(time_step_idx) * 100;

% % 计算峰值时间 (Peak Time)
% [~, peak_index] = max(position);
% peak_time = time(peak_index)-0.5;

% 计算调整时间 (Settling Time)

% upper = desired_value+0.005;
% lower = desired_value-0.005;
% tolerance = upper-lower;
% if steady_state_error <= tolerance
%     settling_time_index = find(position>upper | position < lower, 1,'last');
%     settling_time = time(settling_time_index)-0.5;
% else
%     settling_time = 0.5;
% end

% % 计算振荡次数 (Number of Oscillations)
% zero_crossings = sum(diff(sign(position - desired_value)) ~= 0);
% num_oscillations = fix(zero_crossings / 2);


% if steady_state_error < 0 || steady_state_error >= 0.05 * reference1(end) || overshoot >= 20
%     f(1)=inf;
%     f(2)=inf;
%     f(3)=inf;
%     % f(4)=inf;
%     % f(5)=inf;
%     % f(6)=inf;
% else
%     f(1)=steady_state_error;
%     f(2)=overshoot;
%     % f(3)=peak_time;
%     f(3)=settling_time;
%     % f(5)=num_oscillations;
%     % f(6)=rmse;
% end
% 计算时间乘绝对误差 (ITAE)
%2
% ITAE = trapz(time, time .* abs(position - reference0));
% f=ITAE;
%计算RMSE
% rmse = sqrt(mean((position- reference1).^2));
%3
% IAE = trapz(time, abs(position - reference0));
% f=IAE;
%4
% ISE = trapz(time, (position - reference0).^2);
% f=ISE;
%5
ITSE = trapz(time, time .* (position - reference0).^2);
f=ITSE;
end
