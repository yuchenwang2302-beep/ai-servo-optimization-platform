function [gBV, gBpos, time, reference0, position] = DE_optimization(NP, d, iterM, objective)
    if nargin < 4, objective = 'ITSE'; end
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
    
    [lb, ub] = servo_search_bounds('standard');
    
    f = @(x) fun_position(x, T, objective);  % 目标函数
    
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
    
            vi = min(max(vi, lb), ub);
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
        

        % 每次迭代完成后发布收敛数据
        servo_save_progress(data_file, gBV_record, iter);
    end
    
    % fprintf('\nOptimal Value = %.6f\n', gBV);
    % disp('Best Parameters:');
    % disp(gBpos);
    % 
    % % 保存数据
    % save('gBV_record_data_deITSE.mat', 'gBV_record');
    
    % 仿真并保存结果

    [~, time, reference0, position] = fun_position(gBpos, T, objective);
end
