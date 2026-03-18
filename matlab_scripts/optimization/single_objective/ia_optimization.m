function [gBV, gBpos, time, reference0, position] = ia_optimization(NP, d, iterM)  
    clc; % clear;
    % vref = 200;
    T = 0.5;
    % d = 11;          % 参数维度（包含扰动/前馈项）
    % NP = 50;        % 个体数量
    % iterM = 50;         % 最大代数

    % 强制所有输入转为 double
    NP = double(NP);
    d = double(d);
    iterM = double(iterM);

    pm = 0.7;        % 变异概率
    alfa = 1;        % 激励度系数
    belta = 1;
    detas = 0.1;     % 相似度阈值
    Ncl = 10;        % 克隆个体数
    deta0 = 0.5;     % 初始变异强度
    
    lb = [1, 2.7837e+3, 0.867, 17.2799, 0.1, 1e-4, 1e-9, 10, 10, 10, 50]; 
    ub = [5, 1.0398e+4, 5, 100, 3, 0.1, 1e-3, 30, 50, 80, 500];
    
    f = @(x) fun_position(x, T);
    
    % 初始化种群
    pop = repmat(lb', 1, NP) + rand(d, NP) .* repmat((ub - lb)', 1, NP);
    aff = zeros(1, NP);
    for i = 1:NP
        aff(i) = -f(pop(:,i)');
    end
    
    % gBV_record = zeros(iterM, 1);
    gBV_record = [];

    % 在循环之前添加数据文件初始化
    data_file = 'ia_temp_data.mat';
    if exist(data_file, 'file')
        delete(data_file);
    end


    for iter = 1:iterM
        % 浓度因子
        ND = zeros(1, NP);
        for i = 1:NP
            dist = vecnorm(pop - pop(:,i));
            ND(i) = sum(dist < detas) / NP;
        end
    
        score = alfa * aff - belta * ND;
        [~, idx] = sort(score, 'descend');
        elite = pop(:, idx(1:NP/2));
    
        % 克隆变异
        offspring = [];
        aff_new = zeros(1, NP/2);
        for i = 1:NP/2
            a = elite(:,i);
            clones = repmat(a, 1, Ncl);
            deta = deta0 / (iter + 1);
            for j = 2:Ncl
                for d = 1:d
                    if rand < pm
                        clones(d,j) = clones(d,j) + (rand-0.5) * deta;
                    end
                    % 边界控制
                    clones(d,j) = min(max(clones(d,j), lb(d)), ub(d));
                end
            end
            caff = zeros(1, Ncl);
            for j = 1:Ncl
                caff(j) = -f(clones(:,j)');
            end
            [~, bestIdx] = max(caff);
            offspring = [offspring clones(:,bestIdx)];
            aff_new(i) = caff(bestIdx);
        end
    
        % 新个体补充
        newpop = repmat(lb', 1, NP/2) + rand(d, NP/2) .* repmat((ub - lb)', 1, NP/2);
        aff_rnd = zeros(1, NP/2);
        for i = 1:NP/2
            aff_rnd(i) = -f(newpop(:,i)');
        end
    
        % 合并与选择
        pop_all = [offspring, newpop];
        aff_all = [aff_new, aff_rnd];
        ND_all = zeros(1, NP);
        for i = 1:NP
            dist2 = vecnorm(pop_all - pop_all(:,i));
            ND_all(i) = sum(dist2 < detas) / NP;
        end
        score_all = alfa * aff_all - belta * ND_all;
        [~, idx] = sort(score_all, 'descend');
        pop = pop_all(:, idx(1:NP));
        aff = aff_all(idx(1:NP));
    
        gBpos = pop(:,1);
        gBV_record =[gBV_record;-aff(1)];
        gBV = gBV_record(end);
    
        % if mod(iter, 5) == 0 || iter == 1 || iter == iterM
        %     fprintf("Gen %d, Best = %.6f\n", iter, gBV_record(iter));
        %     figure(1); clf;
        %     plot(gBV_record(1:iter), 'b-o');
        %     xlabel('Iteration'); ylabel('Best Fitness');
        %     title(['IA Progress - Gen ' num2str(iter)]);
        %     drawnow;
        % end

        % 每5次迭代或最后一次迭代时保存数据
        if mod(iter, 5) == 0 || iter == iterM
            save(data_file, 'gBV_record', 'iter', 'iterM');
        end
    end
    
    % fprintf('\nFinal Best Value: %.6f\n', gBV_record(end));
    % disp('Best Parameter Vector:');
    % disp(gBpos');
    % 
    % save('gBV_record_data_iaITSE.mat', 'gBV_record');
    
    % 仿真与结果保存
    g = gBpos';
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
    % save('ref0_position_only_iaITSE.mat', 'time', 'reference0', 'position');
    % 
    % figure;
    % plot(time, reference0, 'r'); hold on;
    % plot(time, position, 'g');
    % legend('Reference', 'Position');
    % title('Position Tracking (IA)');
