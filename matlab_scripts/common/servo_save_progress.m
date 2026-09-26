function servo_save_progress(data_file, gBV_record, iter)
% Publish every completed iteration without exposing a partly written MAT file.
% A run has one writer and its own directory. Readers only open data_file.
temporary_file = [data_file '.next.mat'];
save(temporary_file, 'gBV_record', 'iter', '-v7');
for attempt = 1:5
    [ok, message] = movefile(temporary_file, data_file, 'f');
    if ok
        return;
    end
    pause(0.02);
end
error('Servo:ProgressWrite', 'Could not publish progress: %s', message);
end
