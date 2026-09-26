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


function ranks=RankingProcess(Archive_F, ArchiveMaxSize, obj_no)

global my_min;
global my_max;

%if all(my_min>min(Archive_F))
if size(Archive_F,1) == 1
    my_min = Archive_F;
    my_max = Archive_F;
else
    my_min=min(Archive_F);
    %end

    %if all(my_max<max(Archive_F))
    my_max=max(Archive_F);
    %end
end

r=max((my_max-my_min)/(20), eps);
ranks=zeros(1,size(Archive_F,1));

for i=1:size(Archive_F,1)
    ranks(i)=0;
    for j=1:size(Archive_F,1)
        flag=0; % a flag to see if the point is in the neoghbourhood in all dimensions.
        for k=1:obj_no
            if (abs(Archive_F(j,k)-Archive_F(i,k))<r(k))
            %if ((sum(Archive_F(j,k).^obj_no-Archive_F(i,k).^obj_no))^(1/obj_no)<r(k))
                %ranks(i)=ranks(i)+sqrt(sum((Archive_F(i,:)-Archive_F(j,:)).^2));
                flag=flag+1;
            end
        end
        if flag==obj_no
            ranks(i)=ranks(i)+1;
        end
    end
end
end