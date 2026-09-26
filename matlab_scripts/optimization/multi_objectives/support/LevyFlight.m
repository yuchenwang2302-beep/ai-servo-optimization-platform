% Levy Flight函数
function step = LevyFlight(dim)
    beta = 1.5;
    sigma_u = (gamma(1+beta)*sin(pi*beta/2) / ...
              (gamma((1+beta)/2)*beta*2^((beta-1)/2)))^(1/beta);
    sigma_v = 1;
    
    u = normrnd(0, sigma_u, 1, dim);
    v = normrnd(0, sigma_v, 1, dim);
    
    S = u ./ (abs(v).^(1/beta));
    step = 0.01 * S; % 缩放因子f=0.01
end