function value = servo_error_metric(time, reference, position, objective)
% Evaluate the selected tracking objective on aligned simulation samples.
time = double(time(:));
reference = double(reference(:));
position = double(position(:));
assert(numel(time) == numel(reference) && numel(time) == numel(position), ...
    'servo:InvalidTrackingData', 'Tracking signals must have equal lengths.');
error_signal = position - reference;
switch upper(char(objective))
    case 'ITSE'
        value = trapz(time, time .* error_signal.^2);
    case 'ISE'
        value = trapz(time, error_signal.^2);
    case 'IAE'
        value = trapz(time, abs(error_signal));
    case 'ITAE'
        value = trapz(time, time .* abs(error_signal));
    otherwise
        error('servo:InvalidObjective', 'Unknown tracking objective: %s', objective);
end
end
