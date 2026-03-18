function [gBV, gBpos, time, reference0, position] = FA_optimization(NP, d, iterM)  
    clc; % clear;
    % vref = 3200;
    T = 0.5;
    % d = 11;
    % NP = 20;
    % iterM = 50;
    
    % 强制所有输入转为 double
    NP = double(NP);
    d = double(d);
    iterM = double(iterM); 

    gamma = 1;     % 光吸收系数
    beta0 = 2;     % 初始吸引强度
    alpha = 0.1;   % 步长
    
    % 参数边界
    lb = [1, 2.7837e+3, 0.867, 17.2799, 0.1, 1e-4, 1e-9, 10, 10, 10, 50]; 
    ub = [5, 1.0398e+4, 5, 100, 3, 0.1, 1e-3, 30, 50, 80, 500];
    
    f = @(x) fun_position(x, T);
    
    
    function val = try_fallback(x, T)
        try
            val = fun_position(x, T);
        catch
            warning('仿真失败，返回 inf');
            val = inf;
        end
    end
    
    % 初始化种群
    pop = repmat(lb, NP, 1) + rand(NP, d) .* (repmat(ub - lb, NP, 1));
    fitness = zeros(NP, 1);
    for i = 1:NP
        fitness(i) = f(pop(i,:));
    end
    
    % gBV_record = zeros(iterM, 1);
    gBV_record = [];

    % 在循环之前添加数据文件初始化
    data_file = 'FA_temp_data.mat';
    if exist(data_file, 'file')
        delete(data_file);
    end
    
    for iter = 1:iterM
        for i = 1:NP
            for j = 1:NP
                if fitness(j) < fitness(i)
                    r = norm(pop(i,:) - pop(j,:));
                    beta = beta0 * exp(-gamma * r^2);
                    step = beta * (pop(j,:) - pop(i,:)) + alpha * (rand(1,d) - 0.5);
                    pop(i,:) = pop(i,:) + step;
                    pop(i,:) = min(max(pop(i,:), lb), ub);  % 边界处理
                    fitness(i) = f(pop(i,:));
                end
            end
        end
    
        % 记录最优值
        [gBV, idx] = min(fitness);
        gBpos = pop(idx,:);
        % gBV_record(iter) = gBV;
        gBV_record = [gBV_record;gBV];
    
        % if mod(iter, 5) == 0 || iter == 1 || iter == iterM
        %     fprintf("FA Iter %d: Best = %.6f\n", iter, gBV);
        %     figure(1); clf;
        %     plot(gBV_record(1:iter), 'b-o');
        %     xlabel('Iteration'); ylabel('Fitness');
        %     title('FA Convergence Progress');
        %     grid on; drawnow;
        % end

        % 每5次迭代或最后一次迭代时保存数据
        if mod(iter, 5) == 0 || iter == iterM
            save(data_file, 'gBV_record', 'iter', 'iterM');
        end
    
        alpha = alpha * 0.97;  % 步长衰减
    end
    
    % fprintf('\n[FA] Optimal value: %.6f\n', gBV);
    % disp('[FA] Best parameters:');
    % disp(gBpos);
    % 
    % save('gBV_record_data_faITSE.mat', 'gBV_record');
    
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
    % save('ref0_position_only_faITSE.mat', 'time', 'reference0', 'position');
    % 
    % figure;
    % plot(time, reference0, 'r'); hold on;
    % plot(time, position, 'g');
    % legend('Reference', 'Position');
    % title('Position Tracking (FA)');
end
