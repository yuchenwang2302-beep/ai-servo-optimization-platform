function simOut = simulate_servo_position(x, T, mdlName)
% Shared original motor/controller initialization and model execution.
% mdlName remains explicit: the single/multi models are not interchangeable.
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
dataType = 'single';                % Floating point code-generation

%% System Parameters
% Motor parameters
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
pmsm.QEPSlits = 1000;               %           // QEP Encoder Slits
pmsm.FluxPM   = (pmsm.Ke)/(sqrt(3)*2*pi*1000*pmsm.p/60); %PM flux computed from Ke
pmsm.T_rated  = 0.2724;
pmsm.PositionOffset = 0;         % Per-Unit position offset
mech.J = 7e-5;
mech.B = 1.5e-3;
mech.f = 0.015;
mech.T=T;
%% Target & Inverter Parameters
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
assignin('base', 'target', target);
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
pmsm.N_base = 4107;

% mcb_getCharacteristics(pmsm,inverter);

%% PU System details // Set base values for pu conversion

PU_System.V_base = 13.8564;
PU_System.I_base = 21.4286;
PU_System.N_base = 4107;
PU_System.P_base = 445.3845;
PU_System.T_base = 0.8223;
PU_System.AngleBase = 360;

%% Controller design // Get ballpark values!

PI_params.delay_IIR = 0.02;
PI_params.Ti_i = 5.4895e-4;
PI_params.Ti_speed = 0.0321;
PI_params.Ti_fwc = 5.4895e-4;
PI_params.Kp_fwc = 0.0137;
PI_params.Ki_fwc = 24.9377;

%Updating delays for simulation
PI_params.delay_Currents    = int32(Ts/Ts_simulink);
PI_params.delay_Position    = int32(Ts/Ts_simulink);
PI_params.delay_Speed       = int32(Ts_speed/Ts_simulink);
PI_params.delay_Speed1      = (PI_params.delay_IIR + 0.5*Ts)/Ts_speed;
%Low-Pass Filter Parameters


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
assignin('base', 'OpenLoop', OpenLoop);
assignin('base', 'dataType', 'single');  % 确保dataType存在
assignin('base', 'PI_params', PI_params);
assignin('base', 'FF', FF);
assignin('base', 'jerk', jerk);
assignin('base', 'mech', mech);

load_system(mdlName);
cs = getActiveConfigSet(mdlName);
model_cs = cs.copy;
config_cleanup = onCleanup(@() delete(model_cs));
simOut = sim(mdlName, model_cs);

end
