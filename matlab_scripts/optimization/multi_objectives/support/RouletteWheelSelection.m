% Please note that these codes have been taken from:
%http://playmedusa.com/blog/roulette-wheel-selection-algorithm-in-matlab-2/

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


% ---------------------------------------------------------
% Roulette Wheel Selection Algorithm. A set of weights
% represents the probability of selection of each
% individual in a group of choices. It returns the index
% of the chosen individual.
% Usage example:
% fortune_wheel ([1 5 3 15 8 1])
%    most probable result is 4 (weights 15)
% ---------------------------------------------------------

function choice = RouletteWheelSelection(weights)
  weights = weights(:)';
  if isempty(weights), choice = -1; return; end
  if any(isinf(weights) & weights > 0)
      weights = double(isinf(weights) & weights > 0);
  else
      weights(~isfinite(weights) | weights < 0) = 0;
  end
  if sum(weights) <= 0, weights(:) = 1; end
  accumulation = cumsum(weights / sum(weights));
  choice = find(accumulation > rand(), 1);
  if isempty(choice), choice = numel(weights); end
end
