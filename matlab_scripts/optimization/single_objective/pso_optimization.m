function [gBV, gBpos, time, reference0, position] = pso_optimization(N1, d, interM)
    clc;   % clear;
    
    % % 粒子群参数
    % N1 = 50;           % 粒子数量
    % d = 11;             % 参数维度
    % interM = 50;        % 最大迭代次数

    % 强制所有输入转为 double
    N1 = double(N1);
    d = double(d);
    interM = double(interM);
    
    c1 = 1.5; c2 = 1.5;
    omega_max = 0.9; omega_min = 0.4;
    
    lb = [1, 2.7837e+3, 0.867, 17.2799, 0.1, 1e-4, 1e-9, 10, 10, 10, 50];
    ub = [5, 1.0398e+4, 5, 100, 3, 0.1, 1e-3, 30, 50, 80, 500];
    
    % 初始种群和速度
    pop = repmat(lb, N1, 1) + rand(N1, d) .* (repmat(ub - lb, N1, 1));
    v = -0.1 * repmat(ub - lb, N1, 1) + 0.2 * rand(N1, d) .* repmat(ub - lb, N1, 1);
    
    pBV = ones(N1,1)*inf;
    gBV = inf;
    pBpos = pop;
    gBpos = zeros(1,d);
    
    % gBV_record = zeros(interM, 1);
    gBV_record = [];
    
    % % 打开并行池（如尚未打开）
    % if isempty(gcp('nocreate'))
    %     parpool('local');
    % end
    
    % % 图像初始化
    % figure;
    % hold on;
    % h = plot(NaN, NaN, 'b-o', 'LineWidth', 1.5);
    % xlabel('Iteration'); ylabel('Best Fitness Value');
    % title('PSO Iteration Progress (Parallel)');
    % grid on;
    % refresh_interval = 5;
    
    % 目标函数
    T = 0.5;
    f = @(x) fun_position(x, T);

    % 在循环之前添加数据文件初始化
    data_file = 'pso_temp_data.mat';
    if exist(data_file, 'file')
        delete(data_file);
    end
    
    % 主迭代循环
    for iter = 1:interM
        f_value = zeros(N1, 1);
    
        % 并行适应度计算
        for i = 1:N1
            val = f(pop(i,:));
            % f_value(i) = 0.3*abs(val(1)) + 0.4*abs(val(2)) + 0.3*abs(val(3));  % 可根据需要加权
           f_value(i) = f(pop(i,:));
    
        end
    
        % 更新个体极值和全局极值
        for i = 1:N1
            if f_value(i) < pBV(i)
                pBV(i) = f_value(i);
                pBpos(i,:) = pop(i,:);
            end
            if pBV(i) < gBV
                gBV = pBV(i);
                gBpos = pBpos(i,:);
            end
        end
    
        % 更新速度和位置
        for i = 1:N1
            r1 = rand(1,d); r2 = rand(1,d);
            omega = omega_max - (omega_max - omega_min) * iter / interM;
            v(i,:) = omega * v(i,:) + c1*r1.*(pBpos(i,:) - pop(i,:)) + c2*r2.*(gBpos - pop(i,:));
            v(i,:) = max(min(v(i,:), ub - lb), -abs(ub - lb));
            pop(i,:) = pop(i,:) + v(i,:);
            pop(i,:) = max(min(pop(i,:), ub), lb);
        end
    
        % gBV_record(iter) = gBV;
        gBV_record=[gBV_record;gBV];  % 保存每一代的全局最优值
    
        % if mod(iter, refresh_interval) == 0 || iter == 1 || iter == interM
        %     set(h, 'XData', 1:iter, 'YData', gBV_record(1:iter));
        %     drawnow;
        %     pause(0.01);
        % end

        % 每5次迭代或最后一次迭代时保存数据
        if mod(iter, 5) == 0 || iter == interM
            save(data_file, 'gBV_record', 'iter', 'interM');
        end
    end
    
    % fprintf('optimal_value is %.6f\\n', gBV);
    % disp('the corresponding position is:');
    % disp(gBpos);
    g = gBpos;
    % figure;
    % plot(1:interM, gBV_record, 'b-o', 'LineWidth', 1.5);
    % xlabel('Iteration');
    % ylabel('Best Fitness Value');
    % title('PSO Iteration Progress');
    % grid on;
    % 
    % save('gBV_record_data_parallelITSE.mat', 'gBV_record');
    % run Data.m
    
    PI_params.Kp_i = g(1);
    PI_params.Ki_i = g(2);
    PI_params.Kp_id = g(1);
    PI_params.Ki_id = g(2);
    PI_params.Kp_speed = g(3);
    PI_params.Ki_speed = g(4);
    PI_params.Kp_PosCtrl = g(5);
    FF.k1 = g(6);
    FF.k2 = g(7);
    jerk.k1 = g(8);% [10 500]
    jerk.k2 = g(9);% [10 500]
    jerk.k3 = g(10);%[10 500]
    jerk.k4 = g(11);
    mdlName = 'Jerk_FF_Step_2023';
    load_system(mdlName);
    cs = getActiveConfigSet(mdlName);
    model_cs = cs.copy;
    simOut = sim(mdlName, model_cs);
    time=simOut.Pos_Fb_PU.time;
    reference0 = simOut.Ref_Step_PU0.signals.values;
    reference1 = simOut.Ref_Step_PU1.signals.values;
    position = simOut.Pos_Fb_PU.signals.values;
    % figure
    % plot(time,reference0,'r')
    % hold on
    % plot(time,reference1,'b')
    % hold on
    % plot(time,position,'g')
    % % 提取红色线（reference0）和绿色线（position）对应的时间和数值
    % time = simOut.Pos_Fb_PU.time;
    % reference0 = simOut.Ref_Step_PU0.signals.values;
    % position = simOut.Pos_Fb_PU.signals.values;
    % 
    % % 保存为 .mat 文件
    % save('ref0_position_onlyITSE.mat', 'time', 'reference0', 'position');
