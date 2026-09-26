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

function o=dominates(x,y)
    
    o=all(x<=y) && any(x<y);

end