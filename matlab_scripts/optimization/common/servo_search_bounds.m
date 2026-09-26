function [lb, ub] = servo_search_bounds(variant)
% Original search bounds; MDF intentionally retains its separate jerk range.
if nargin < 1, variant = 'standard'; end
lb = [1, 2.7837e+3, 0.867, 17.2799, 0.1, 1e-4, 1e-9, 10, 10, 10, 50];
ub = [5, 1.0398e+4, 5, 100, 3, 0.1, 1e-3, 30, 50, 80, 500];
switch variant
    case 'standard'
    case 'mdf'
        lb(11) = 10;
        ub(8:11) = 300;
    otherwise
        error('servo:UnknownBounds', 'Unknown search-bound variant: %s', variant);
end
end
