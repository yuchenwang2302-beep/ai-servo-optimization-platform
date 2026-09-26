function Positions = adaptive_mutation(Positions, c_current, ub, lb)
    scale = 0.1*(1 - c_current); % 随c值衰减
    for i=1:size(Positions,2)
        if rand < 0.6
            % 柯西变异增强逃逸能力
            cauchy_mut = tan(pi*(rand(size(Positions,1),1)-0.5));
            % 高斯变异精细搜索
            gauss_mut = 0.5*randn(size(Positions,1),1);
            
            Positions(:,i) = Positions(:,i) + scale*(0.6*cauchy_mut + 0.4*gauss_mut);
            Positions(:,i) = min(max(Positions(:,i), lb'), ub');
        end
    end
end