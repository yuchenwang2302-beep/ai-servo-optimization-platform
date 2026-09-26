%_________________________________________________________________________________
%  Multi-objective Grasshopper Optimization Algorithm (MOGOA) source codes version 1.0
%
%  Developed in MATLAB R2016a
%
%  Author and programmer: Seyedali Mirjalili
%
%         e-Mail: ali.mirjalili@gmail.com
%                 seyedali.mirjalili@griffithuni.edu.au
%
%       Homepage: http://www.alimirjalili.com
%
%   Main paper:
%   S. Z. Mirjalili, S. Mirjalili, S. Saremi, H. Fatis, H. Aljarah, 
%   Grasshopper optimization algorithm for multi-objective optimization problems, 
%   Applied Intelligence, 2017, DOI: http://dx.doi.org/10.1007/s10489-017-1019-8
%____________________________________________________________________________________

function [Archive_X_updated, Archive_F_updated, Archive_member_no] = UpdateArchive(Archive_X, Archive_F, Particles_X, Particles_F, Archive_member_no)
% Ignore unused archive slots and invalid simulations; retain one copy of ties.
X = [Archive_X(1:Archive_member_no,:); Particles_X'];
F = [Archive_F(1:Archive_member_no,:); Particles_F];
valid = all(isfinite(F),2) & all(isfinite(X),2);
X = X(valid,:); F = F(valid,:);
[F, unique_indices] = unique(F, 'rows', 'stable');
X = X(unique_indices,:);
keep = true(size(F,1),1);
for i = 1:size(F,1)
    for j = 1:size(F,1)
        if j ~= i && dominates(F(j,:), F(i,:))
            keep(i) = false;
            break;
        end
    end
end
Archive_X_updated = X(keep,:);
Archive_F_updated = F(keep,:);
Archive_member_no = sum(keep);
end
