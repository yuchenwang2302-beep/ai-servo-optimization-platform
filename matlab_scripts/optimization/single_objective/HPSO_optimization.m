function [gBV, gBpos, time, reference0, position] = HPSO_optimization(NP, d, iterM)
    clc; % clear;
    % vref = 200;
    T = 0.5;
    % d = 11;              % 参数维度
    % NP = 50;             % 粒子数
    % iterM = 50;
    
    % 强制所有输入转为 double
    NP = double(NP);
    d = double(d);
    iterM = double(iterM);

    % 参数边界（统一）
    lb = [1, 2.7837e+3, 0.867, 17.2799, 0.1, 1e-4, 1e-9, 10, 10, 10, 50]; 
    ub = [5, 1.0398e+4, 5, 100, 3, 0.1, 1e-3, 30, 50, 80, 500];
    
    % 目标函数封装
    f = @(x) fun_position(x, T);
    
    % 初始化位置与速度
    pop = repmat(lb, NP, 1) + rand(NP, d) .* (repmat(ub - lb, NP, 1));
    v = -0.1 * repmat(ub - lb, NP, 1) + 0.2 * rand(NP, d) .* repmat(ub - lb, NP, 1);
    
    pBV = ones(NP, 1) * inf;
    pBpos = pop;
    gBV = inf;
    gBpos = zeros(1, d);
    
    % gBV_record = zeros(iterM, 1);
    gBV_record = [];

    
    wmax = 0.9; wmin = 0.4;
    c1 = 1.5; c2 = 1.5;
    K = 3;
    neib = @(i) mod(i-1 + (0:K-1), NP) + 1;

    % 在循环之前添加数据文件初始化
    data_file = 'HPSO_temp_data.mat';
    if exist(data_file, 'file')
        delete(data_file);
    end
    
    % 主循环
    for iter = 1:iterM
        f_value = zeros(NP, 1);
        for i = 1:NP
            f_value(i) = f(pop(i, :));
        end
    
        for i = 1:NP
            if f_value(i) < pBV(i)
                pBV(i) = f_value(i);
                pBpos(i,:) = pop(i,:);
            end
            if pBV(i) < gBV
                gBV = pBV(i);
                gBpos = pBpos(i,:);
            end
        end
    
        for i = 1:NP
            omega = wmax - (wmax - wmin) * iter / iterM;
            q = rand;
            r1 = rand(1,d); r2 = rand(1,d); r3 = rand(1,d);
    
            local_ind = neib(i);
            [~, idx] = min(pBV(local_ind));
            pLocal = pBpos(local_ind(idx), :);
    
            v(i,:) = omega * v(i,:) + ...
                     c1 * r1 .* (pBpos(i,:) - pop(i,:)) + ...
                     c2 * (q * r2 .* (gBpos - pop(i,:)) + (1 - q) * r3 .* (pLocal - pop(i,:)));
    
            pop(i,:) = pop(i,:) + v(i,:);
            pop(i,:) = max(min(pop(i,:), ub), lb);  % 边界控制
            v(i,:)   = max(min(v(i,:), ub - lb), -abs(ub - lb));
        end
    
        % gBV_record(iter) = gBV;
        gBV_record = [gBV_record;gBV];


        % if mod(iter, 5) == 0 || iter == 1 || iter == iterM
        %     fprintf("Iteration %d: Best = %.6f\n", iter, gBV);
        %     figure(1); clf;
        %     plot(gBV_record(1:iter), 'b-o');
        %     xlabel('Iteration'); ylabel('Fitness');
        %     title('HPSO Convergence Progress');
        %     grid on; drawnow;
        % end

        % 每5次迭代或最后一次迭代时保存数据
        if mod(iter, 5) == 0 || iter == iterM
            save(data_file, 'gBV_record', 'iter', 'iterM');
        end


    end
    
    % fprintf('\n[HPSO] Optimal value: %.6f\n', gBV);
    % disp('[HPSO] Best parameters:');
    % disp(gBpos);
    % 
    % save('gBV_record_data_hpsoITSE.mat', 'gBV_record');
    
    % 仿真阶段
    g = gBpos;
    run Data.m
    PI_params.Kp_i = g(1); PI_params.Ki_i = g(2);
    PI_params.Kp_id = g(1); PI_params.Ki_id = g(2);
    PI_params.Kp_speed = g(3); PI_params.Ki_speed = g(4);
    PI_params.Kp_PosCtrl = g(5);
    FF.k1 = g(6); FF.k2 = g(7);
    jerk.k1 = g(8); jerk.k2 = g(9); jerk.k3 = g(10); jerk.k4 = g(11);
    
    mdlName = 'Jerk_FF_Step_2023';
    load_system(mdlName);
    cs = getActiveConfigSet(mdlName); model_cs = cs.copy;
    simOut = sim(mdlName, model_cs);
    
    time = simOut.Pos_Fb_PU.time;
    reference0 = simOut.Ref_Step_PU0.signals.values;
    position = simOut.Pos_Fb_PU.signals.values;
    
    % save('ref0_position_only_hpsoITSE.mat', 'time', 'reference0', 'position');
    % 
    % figure;
    % plot(time, reference0, 'r'); hold on;
    % plot(time, position, 'g');
    % legend('Reference', 'Position');
    % title('Position Tracking (HPSO)');
