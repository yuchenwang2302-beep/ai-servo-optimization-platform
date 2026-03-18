function [time, reference0, position] = MDF_MOGOA(N, ArchiveMaxSize, iterM, dim, obj_no)

clc;
% clear;
close all;

% 强制所有输入转为 double
N = double(N);
ArchiveMaxSize = double(ArchiveMaxSize);
iterM = double(iterM);
dim = double(dim);
obj_no = double(obj_no);

% hv=ones(10,1);
% dm=ones(10,1);
% deltap=ones(10,1);
% nd_solutions=ones(10,1);
% time=ones(10,1);
% for pp=1:10
% 创建 data 文件夹
% if ~exist('data1', 'dir')
%     mkdir('C:\Users\26392\Desktop\涛哥大法\MOGOA 发lrh\MOGOA\MOGOA\data1');
%     addpath('C:\Users\26392\Desktop\涛哥大法\MOGOA 发lrh\MOGOA\MOGOA\data1');
%     savepath;
% end
% rng(0)
% Change these details with respect to your problem%%%%%%%%%%%%%%
ObjectiveFunction=@fun_position_2;
% dim=11;
% obj_no=3;
lb = [1, 2.7837e+3,  0.867,  17.2799, 0.1,     1e-4,   1e-9,  10, 10,  10,  10];
ub = [5,      1.0398e+4, 5, 100,   3,       0.1,   1e-3, 300, 300, 300, 300];

if size(ub,2)==1
    ub=ones(1,dim)*ub;
    lb=ones(1,dim)*lb;
end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
flag=0;
if (rem(dim,2)~=0)
    dim = dim+1;
    ub = [ub, 1];
    lb = [lb, 0];
    flag=1;
end


% iterM=20;
% N=100;
% ArchiveMaxSize=150;

Archive_X=zeros(100,dim);
Archive_F=ones(100,obj_no)*inf;

Archive_member_no=0;

%Initialize the positions of artificial whales
GrassHopperPositions=initialization(N,dim,ub,lb);

TargetPosition=zeros(dim,1);
TargetFitness=inf*ones(1,obj_no);

cMax=1;
cMin=0.00004;
cc=ones(iterM,1);
cc_adam = ones(iterM, 1);
gg=ones(iterM, 1);
%adaptive
% 初始化一阶和二阶矩
m_c = 0;
v_c = 0;
beta1 = 0.9;   %一阶矩的衰减速率[0.85 0.99]
beta2 = 0.95; % 二阶矩的衰减速率[0.99 0.9999]
epsilon = 1e-8;
learning_rate = 1;

lambda =0.9; % 动量系数
c = 1/lambda; % 初始化 c 值



IGD_values = zeros(1, iterM);  %IGD
HV_values = zeros(1, iterM);   %HV
DM_values = zeros(1, iterM);   %DM
Deltap_values = zeros(1, iterM);
learning_rate_1=zeros(1, iterM);
elapsed_time=zeros(1, iterM);
optimum = GetOptimum(obj_no, N);  % 获取参考 Pareto 前沿点

tic %

if isempty(gcp('nocreate'))
parpool;
end

spmd
rng(labindex); % 使用worker的ID作为种子
end

% 在循环之前添加数据文件初始化
data_file = 'MDF_MOGOA_temp_data.mat';
if exist(data_file, 'file')
    delete(data_file);
end

for iter=1:iterM
    learning_rate_1(iter)=learning_rate;
    parfor i = 1:N
        % 确保草蜢的位置在边界内
        Flag4ub = GrassHopperPositions(:, i) > ub';
        Flag4lb = GrassHopperPositions(:, i) < lb';
        GrassHopperPositions(:, i) = (GrassHopperPositions(:, i) .* (~(Flag4ub + Flag4lb))) + ub' .* Flag4ub + lb' .* Flag4lb;

        % 并行计算目标函数值
        T=0.2724*rand;
        % T=0;
        GrassHopperFitness(i, :) = ObjectiveFunction(GrassHopperPositions(:, i)',0);
    end

    % 在并行外部更新 TargetFitness 和 TargetPosition
    for i = 1:N
        if dominates(GrassHopperFitness(i, :), TargetFitness)
            TargetFitness = GrassHopperFitness(i, :);  % 更新目标适应度
            TargetPosition = GrassHopperPositions(:, i);  % 更新目标位置
        end
    end
    [Archive_X, Archive_F, Archive_member_no]=UpdateArchive(Archive_X, Archive_F, GrassHopperPositions, GrassHopperFitness, Archive_member_no);

    if Archive_member_no>ArchiveMaxSize
        Archive_mem_ranks=RankingProcess(Archive_F, ArchiveMaxSize, obj_no);
        [Archive_X, Archive_F, Archive_mem_ranks, Archive_member_no]=HandleFullArchive(Archive_X, Archive_F, Archive_member_no, Archive_mem_ranks, ArchiveMaxSize);
    else
        Archive_mem_ranks=RankingProcess(Archive_F, ArchiveMaxSize, obj_no);
    end

    Archive_mem_ranks=RankingProcess(Archive_F, ArchiveMaxSize, obj_no);
    index=RouletteWheelSelection(1./Archive_mem_ranks);
    if index==-1
        index=1;
    end
    TargetFitness=Archive_F(index,:);
    TargetPosition=Archive_X(index,:)';
    % % 将 inf 替换为 NaN
    % validFitness = GrassHopperFitness;
    % validFitness(isinf(validFitness)) = NaN;
    %
    % % 计算当前种群的理想点和反理想点
    % z_star = min(validFitness, [], 1, 'omitnan'); % 理想点
    % z_nad = max(validFitness, [], 1, 'omitnan'); % 反理想点
    %
    % % 使用默认值替换 NaN
    % z_star(isnan(z_star)) = 0;
    % z_nad(isnan(z_nad)) = 1;
    % 计算每个个体到理想点和反理想点的距离之和

    % g_t = zeros(N, 1);
    % for i = 1:N
    %     if any(isnan(GrassHopperFitness(i, :))) || any(isinf(GrassHopperFitness(i, :)))
    %         continue; % 跳过不合格的个体
    %     end
    %
    %     distance_to_ideal = sqrt(sum((GrassHopperFitness(i, :) - z_star).^2));
    %     distance_to_nadir = sqrt(sum((GrassHopperFitness(i, :) - z_nad).^2));
    %     g_t(i) = distance_to_ideal +distance_to_nadir;
    % end
    % 修改为：
    valid_indices = ~any(isnan(GrassHopperFitness), 2) & ~any(isinf(GrassHopperFitness), 2);
    valid_Front = GrassHopperFitness(valid_indices, :);

    % 计算理想点和反理想点时需要排除无效解
    z_star = min(valid_Front, [], 1);
    z_nad = max(valid_Front, [], 1);

    % 调用新梯度函数
    g_t = enhanced_gradient(valid_Front, z_star, z_nad);
    % k_neighbors=15;
    % g_t = neighborhood_gradient(valid_Front, z_star, z_nad, k_neighbors);


    % 处理无效解（保持原惩罚机制）
    temp_g = ones(N,1)*1e6;
    temp_g(valid_indices) = g_t;
    g_t = temp_g;
    gg(iter)=mean(g_t);
    % 为 g_t 设置上下限
    g_t(g_t > 1e6) = 1e6;
    g_t(g_t < 1e-6) = 1e-6;



    % 更新一阶和二阶矩
    m_c = beta1 * m_c + (1 - beta1) * g_t;
    v_c = beta2 * v_c + (1 - beta2) * (g_t.^2);

    % 偏差校正
    m_hat_c = m_c / (1 - beta1^iter);
    v_hat_c = v_c / (1 - beta2^iter);

    % % 自适应更新权重 c
    % % % 计算自适应更新部分的 c 值
    c_adam = cMax - ((cMax - cMin) / (sqrt(v_hat_c) + epsilon)) * learning_rate *m_hat_c;
    % % c = hybrid_decay(c,c_adam, iter, max_iter,lambda);
    %
    % % 结合上一轮的 c 值，进行带动量的更新
    c = lambda * c + (1 - lambda) * c_adam;
    c = max(min(c, 1), 0);

    cc_adam(iter)=c_adam;

    cc(iter)=c;
    % c=cMax-iter*((cMax-cMin)/max_iter); % Eq. (3.8) in the paper

    for i=1:N
        temp= GrassHopperPositions;
        for k=1:2:dim
            S_i=zeros(2,1);
            for j=1:N
                if i~=j
                    Dist=distance(temp(k:k+1,j), temp(k:k+1,i));
                    r_ij_vec=(temp(k:k+1,j)-temp(k:k+1,i))/(Dist+eps);
                    xj_xi=2+rem(Dist,2);

                    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% % Eq. (3.2) in the paper
                    s_ij=((ub(k:k+1)' - lb(k:k+1)') .*c/2)*S_func(xj_xi).*r_ij_vec;
                    S_i=S_i+s_ij;
                    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                end
            end
            S_i_total(k:k+1, :) = S_i;

        end

        X_new=c*S_i_total'+(TargetPosition)'; % Eq. (3.7) in the paper
        GrassHopperPositions_temp(i,:)=X_new';
    end
    % GrassHopperPositions
    GrassHopperPositions=GrassHopperPositions_temp';

    GrassHopperPositions = adaptive_mutation(GrassHopperPositions, c, ub, lb);
  
    % 在位置更新后添加
    % [~, elite_idx] = min(Archive_F(:,1) + Archive_F(:,2));
    % elite_solution = Archive_X(elite_idx,:);
    % 
    % for i=1:N
    %     if rand < 0.3
    %         GrassHopperPositions(:,i) = 0.8*GrassHopperPositions(:,i) + ...
    %             0.2*elite_solution';
    %     end
    % end
    % 计算 IGD 和 HV
    toc
    elapsed_time(iter) = toc;
    IGD_values(iter) = myIGD(Archive_F, optimum);  % 使用 PlatEMO 的 IGD 计算方法
    HV_values(iter) = myHV(Archive_F, optimum);    % 使用 PlatEMO 的 HV 计算方法
    DM_values(iter) = myDM(Archive_F, optimum);    % 使用 PlatEMO 的 HV 计算方法
    Deltap_values(iter) = myDeltaP(Archive_F,optimum);

   
    % 每5次迭代或最后一次迭代时保存数据
    gBV_record = HV_values;
    if mod(iter, 5) == 0 || iter == iterM
        save(data_file, 'gBV_record', 'iter');
    end



    % save(['C:\Users\26392\Desktop\test\MOGOA_lrh\MOGOA\MOGOA\data1\Archive_X_', num2str(iter)], 'Archive_X');  % 保存位置数据
    % save(['C:\Users\26392\Desktop\test\MOGOA_lrh\MOGOA\MOGOA\data1\Archive_F_', num2str(iter)], 'Archive_F');  % 保存位置数据
    % disp(['At the iteration ', num2str(iter), ' there are ', num2str(Archive_member_no), ' non-dominated solutions in the archive']);
    % disp(['Elapsed time: ', num2str(elapsed_time), ' seconds']);
    % disp(['IGD: ', num2str(IGD_values(iter)), ' HV: ', num2str(HV_values(iter)), ' DM: ', num2str(DM_values(iter)), ' Deltap: ', num2str(Deltap_values(iter))]);
end


if (flag==1)
    TargetPosition = TargetPosition(1:dim-1);
end

%%选择TOPSIS
f_matrix=Archive_F;
original_indices = (1:size(f_matrix, 1))';
% 找到包含 inf 的行
inf_rows = any(isinf(f_matrix), 2);
% 去除包含 inf 的行，并保留有效行的索引
filtered_f_matrix = f_matrix(~inf_rows, :);
filtered_indices = original_indices(~inf_rows);
% 标准化决策矩阵 (基于最小值)
min_values = min(filtered_f_matrix);
max_values = max(filtered_f_matrix);
f_matrix_norm = (max_values - filtered_f_matrix) ./ (max_values - min_values);
% 定义权重向量 (根据实际优先级调整)
% weights = [10, 10, 0.1, 1, 0.2, 0.2];
weights = [0.5,0.4,0.1];
%稳态误差 超调 上升时间 调整时间 振荡次数 RMSE
% 构建加权标准化矩阵
weighted_matrix = f_matrix_norm .* weights;
% 确定理想解 (最优情况) 和反理想解 (最差情况)
ideal_solution = max(weighted_matrix); % 理想解是所有列的最小值
negative_ideal_solution = min(weighted_matrix); % 反理想解是所有列的最大值
% 计算到理想解和反理想解的欧几里得距离
distance_to_ideal = sqrt(sum((weighted_matrix - ideal_solution).^2, 2));
distance_to_negative_ideal = sqrt(sum((weighted_matrix - negative_ideal_solution).^2, 2));
% 计算相对接近度
relative_closeness = distance_to_negative_ideal ./ (distance_to_ideal + distance_to_negative_ideal);
% 找到相对接近度最大的解
[~, best_solution_index] = max(relative_closeness);
% 找到最佳解在原始矩阵中的索引
best_solution_original_index = filtered_indices(best_solution_index);
% 输出最佳解的原始索引和相对接近度
% disp(['最佳解在原始矩阵中的索引为: ', num2str(best_solution_original_index)]);
% disp(['最佳解的相对接近度为: ', num2str(relative_closeness(best_solution_index))]);
% 如果需要，可以进一步查看这个解的具体指标
best_solution = f_matrix(best_solution_original_index, :);
% disp(['最佳解的指标值为: ', num2str(best_solution)]);
g=Archive_X(best_solution_original_index,:);




results=T_Jerk_FF_Step_2023_2(g,0);

% 从 results 中提取三个变量
time = results(:,1);         % 时间序列
reference0 = results(:,2);   % 参考信号
position = results(:,3);     % 位置响应

% % 调试输出 - 检查数据点数
% disp(['MATLAB端数据点数: ', num2str(length(results))]);
















% %     time(pp)=elapsed_time(end);
% %     hv(pp)=HV_values(end);
% %     dm(pp)=DM_values(end);
% %     nd_solutions(pp)=Archive_member_no;
% %     deltap(pp)=Deltap_values(end);
% % end
% % hv_mean=mean(hv);
% % dm_mean=mean(dm);
% % nd_solutions_mean=mean(nd_solutions);
% % Deltap_values_mean=mean(deltap);
% % time_mean=mean(time);
% % 
% % aa=[hv dm deltap time nd_solutions];
% % aaa=[hv_mean dm_mean Deltap_values_mean time_mean nd_solutions_mean];
% % figure
% % 
% % Draw_DTLZ5_3();
% % 
% % hold on
% % plot3(Archive_F(:,1),Archive_F(:,2),Archive_F(:,3),'ro','MarkerSize',8,'markerfacecolor','k');
% % 
% % legend('True PF','Obtained PF');
% % title('AMOGOA');
% % 
% % set(gcf, 'pos', [403   466   230   200])
% figure
% plot(cc)
% %% 绘制 IGD 和 HV 变化曲线
% figure;
% subplot(1,3,1);
% plot(1:iterM, IGD_values, '-o');
% title('IGD over iterations');
% xlabel('Iteration');
% ylabel('IGD');
% 
% subplot(1,3,2);
% plot(1:iterM, HV_values, '-o');
% title('HV over iterations');
% xlabel('Iteration');
% ylabel('HV');
% 
% subplot(1,3,3);
% plot(1:iterM, DM_values, '-o');
% title('DM over iterations');
% xlabel('Iteration');
% ylabel('DM');
% 
% 
% %% 决策
% % 去除包含inf的行
% % 假设 f_matrix 已经被定义，包含了所有解的指标值
% % 记录原始的索引
% f_matrix=abs(Archive_F);
% original_indices = (1:size(f_matrix, 1))';
% 
% % 找到包含 inf 的行
% inf_rows = any(isinf(f_matrix), 2);
% 
% % 去除包含 inf 的行，并保留有效行的索引
% filtered_f_matrix = f_matrix(~inf_rows, :);
% filtered_indices = original_indices(~inf_rows);
% 
% % 标准化决策矩阵 (基于最小值)
% min_values = min(filtered_f_matrix);
% max_values = max(filtered_f_matrix);
% 
% f_matrix_norm = (max_values - filtered_f_matrix) ./ (max_values - min_values);
% 
% % 定义权重向量 (根据实际优先级调整)
% weights = [0.1 0 1];
% %稳态误差 超调 上升时间 调整时间 振荡次数 RMSE
% 
% % 构建加权标准化矩阵
% weighted_matrix = f_matrix_norm .* weights;
% 
% % 确定理想解 (最优情况) 和反理想解 (最差情况)
% ideal_solution = max(weighted_matrix);  % 理想解是所有列的最小值
% negative_ideal_solution = min(weighted_matrix);  % 反理想解是所有列的最大值
% 
% % 计算到理想解和反理想解的欧几里得距离
% distance_to_ideal = sqrt(sum((weighted_matrix - ideal_solution).^2, 2));
% distance_to_negative_ideal = sqrt(sum((weighted_matrix - negative_ideal_solution).^2, 2));
% 
% % 计算相对接近度
% relative_closeness = distance_to_negative_ideal ./ (distance_to_ideal + distance_to_negative_ideal);
% 
% % 找到相对接近度最大的解
% [~, best_solution_index] = max(relative_closeness);
% best_solution_index=74;
% % 找到最佳解在原始矩阵中的索引
% best_solution_original_index = filtered_indices(best_solution_index);
% 
% % 输出最佳解的原始索引和相对接近度
% disp(['最佳解在原始矩阵中的索引为: ', num2str(best_solution_original_index)]);
% disp(['最佳解的相对接近度为: ', num2str(relative_closeness(best_solution_index))]);
% 
% % 如果需要，可以进一步查看这个解的具体指标
% best_solution = f_matrix(best_solution_original_index, :);
% disp(['最佳解的指标值为: ', num2str(best_solution)]);
% 
% g=Archive_X(best_solution_original_index,:);
% 
% PI_params.Kp_i = g(1);
% PI_params.Ki_i = g(2);
% PI_params.Kp_id = g(1);
% PI_params.Ki_id = g(2);
% PI_params.Kp_speed = g(3);
% PI_params.Ki_speed = g(4);
% PI_params.Kp_PosCtrl = g(5);
% FF.k1 = g(6);
% FF.k2 = g(7);
% jerk.k1 = g(8);% [10 500]
% jerk.k2 = g(9);% [10 500]
% jerk.k3 = g(10);%[10 500]
% jerk.k4 = g(11);%[10 500]
% mdlName = 'Jerk_FF_Step_2023';
% load_system(mdlName);
% cs = getActiveConfigSet(mdlName);
% model_cs = cs.copy;
% simOut = sim(mdlName, model_cs);
% time=simOut.Pos_Fb_PU.time;
% reference0 = simOut.Ref_Step_PU0.signals.values;
% reference1 = simOut.Ref_Step_PU1.signals.values;
% position = simOut.Pos_Fb_PU.signals.values;
% figure
% plot(time,reference0,'r')
% hold on
% plot(time,reference1,'b')
% hold on
% plot(time,position,'g')