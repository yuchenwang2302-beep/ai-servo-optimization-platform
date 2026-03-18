function [gBV, gBpos, time, reference0, position] = DE_optimization(NP, d, iterM)  
    clc; % clear;
    % vref = 100;
    T = 0.5;
    % d = 11;           % 参数维度
    % NP = 50;         % 种群规模
    % G = 50;          % 最大迭代次数

    % 强制所有输入转为 double
    NP = double(NP);
    d = double(d);
    iterM = double(iterM);
    
    lb = [1, 2.7837e+3, 0.867, 17.2799, 0.1, 1e-4, 1e-9, 10, 10, 10, 50]; 
    ub = [5, 1.0398e+4, 5, 100, 3, 0.1, 1e-3, 30, 50, 80, 500];
    
    f = @(x) fun_position(x, T);  % 目标函数
    
    F_ind = 0.5 + 0.3 * rand(NP, 1);
    CR_ind = 0.9 * ones(NP, 1);
    pop = repmat(lb, NP, 1) + rand(NP, d) .* (repmat(ub - lb, NP, 1));
    
    fitness = zeros(NP, 1);
    for i = 1:NP
        fitness(i) = f(pop(i,:));
    end
    
    % gBV_record = zeros(iterM, 1);
    gBV_record = [];

    % figure; hold on;
    % h = plot(NaN, NaN, 'b-o', 'LineWidth', 1.5);
    % xlabel('Iteration'); ylabel('Best Fitness Value');
    % title('DE Iteration Progress');
    % grid on;
    % refresh_interval = 5;

    % 在循环之前添加数据文件初始化
    data_file = 'DE_temp_data.mat';
    if exist(data_file, 'file')
        delete(data_file);
    end
    
    for iter = 1:iterM
        for i = 1:NP
            % jDE 参数更新
            if rand < 0.1
                F_ind(i) = min(max(0.5 + 0.3 * randn, 0.1), 1.0);
            end
            if rand < 0.1
                CR_ind(i) = min(max(0.5 + 0.1 * randn, 0.0), 1.0);
            end
    
            % 变异与交叉
            idx = randperm(NP, 3);
            while any(idx == i)
                idx = randperm(NP, 3);
            end
            vi = pop(idx(1), :) + F_ind(i) * (pop(idx(2), :) - pop(idx(3), :));
    
            for j = 1:d
                if vi(j) < lb(j)
                    vi(j) = lb(j) + rand * (lb(j) - vi(j));
                elseif vi(j) > ub(j)
                    vi(j) = ub(j) - rand * (vi(j) - ub(j));
                end
            end
    
            jrand = randi(d);
            ui = pop(i,:);
            for j = 1:d
                if rand < CR_ind(i) || j == jrand
                    ui(j) = vi(j);
                end
            end
    
            % 后期微扰机制
            if iter > iterM * 0.6
                ui = ui + 0.01 * randn(1, d);
                ui = min(max(ui, lb), ub);
            end
    
            fit_ui = f(ui);
            if fit_ui < fitness(i)
                pop(i,:) = ui;
                fitness(i) = fit_ui;
            end
        end
    
        [gBV, best_idx] = min(fitness);
        gBpos = pop(best_idx, :);
        % gBV_record(iter) = gBV;
        gBV_record = [gBV_record;gBV];
    
        % if mod(gen, refresh_interval) == 0 || gen == 1 || gen == G
        %     set(h, 'XData', 1:gen, 'YData', gBV_record(1:gen));
        %     drawnow; pause(0.01);
        % end
        % 
        % fprintf('Generation %d, Best Fitness = %.6f\n', gen, gBV);
        

        % 每5次迭代或最后一次迭代时保存数据
        if mod(iter, 5) == 0 || iter == iterM
            save(data_file, 'gBV_record', 'iter', 'iterM');
        end
    end
    
    % fprintf('\nOptimal Value = %.6f\n', gBV);
    % disp('Best Parameters:');
    % disp(gBpos);
    % 
    % % 保存数据
    % save('gBV_record_data_deITSE.mat', 'gBV_record');
    
    % 仿真并保存结果
    run Data.m
    PI_params.Kp_i = gBpos(1); PI_params.Ki_i = gBpos(2);
    PI_params.Kp_id = gBpos(1); PI_params.Ki_id = gBpos(2);
    PI_params.Kp_speed = gBpos(3); PI_params.Ki_speed = gBpos(4);
    PI_params.Kp_PosCtrl = gBpos(5);
    FF.k1 = gBpos(6); FF.k2 = gBpos(7);
    jerk.k1 = gBpos(8); jerk.k2 = gBpos(9); jerk.k3 = gBpos(10); jerk.k4 = gBpos(11);
    
    mdlName = 'Jerk_FF_Step_2023';
    load_system(mdlName);
    cs = getActiveConfigSet(mdlName); model_cs = cs.copy;
    simOut = sim(mdlName, model_cs);
    
    time = simOut.Pos_Fb_PU.time;
    reference0 = simOut.Ref_Step_PU0.signals.values;
    position = simOut.Pos_Fb_PU.signals.values;
    % save('ref0_position_only_deITSE.mat', 'time', 'reference0', 'position');
    
    % figure;
    % plot(time, reference0, 'r'); hold on;
    % plot(time, position, 'g');
    % legend('Reference', 'Position');
    % title('Position Tracking (DE)');
