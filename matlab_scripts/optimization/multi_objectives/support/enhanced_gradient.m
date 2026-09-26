function g_t = enhanced_gradient(Front, z_star, z_nad)
    [N, obj_no] = size(Front);
    domination_matrix = zeros(N,1);
    for i=1:N
        domination_count = sum(all(repmat(Front(i,:),N,1) <= Front, 2)) - 1;
        domination_matrix(i) = exp(-domination_count/N); % 标准化支配强度
    end
    
    g_t = zeros(N,1);
    for i=1:N
        if any(isnan(Front(i,:))) || any(isinf(Front(i,:)))
            g_t(i) = 1e6; % 惩罚无效解
            continue;
        end
        ideal_dist = norm(Front(i,:)-z_star);
        nadir_dist = norm(Front(i,:)-z_nad);
        g_t(i) = domination_matrix(i)*(0.7*ideal_dist + 0.3*nadir_dist); % 加权距离
    end
end