clc;
clear;
%---------code to generate CSV file and putting .png into class folders for
%RGB dataset using mylabes text files.
clc;
clear;
path_sub='/home/shubham/Egocentric/dataset/GTea/png/';
subjects=dir(path_sub);
path_label='/home/shubham/Egocentric/dataset/GTea/gtea_labels_mylabels/';
labels=dir(path_label);
subjects=subjects(3:end);
labels=labels(3:end);
[total_sub,~]=size(subjects);
count=1;
cell_temp_sub_path={};
cell_label={};
%struct_CSV = struct('Name',{},'Path',{},'Label',{});
for i=1:total_sub-7
    i
    label_txt=strcat(labels(i).folder,'/',labels(i).name)
    subject_path=strcat(subjects(i).folder,'/',subjects(i).name,'/')
    fid = fopen(label_txt);
    tline=fgetl(fid);
    count
    while ischar(tline)
        temp=tline;
        line=strsplit(temp);
        [~,yolo]=size(line);
        if yolo>3
            action=string(line{1,1});
            if action==string('x')
                action=string('bg');
            end
            if action==string('open')
                action=string('close');
            end
            from=str2double(line(end-2));
            to=str2double(line(end-1));
            for j=from:to
                %image_path=strcat(subject_path,num2str(j,'%.10d'),'.png');
                img_source=strcat(subjects(i).name,'/',num2str(j,'%.10d'),'.png');
                %temp_image=imread(strcat('/home/shubham/Egocentric/dataset/GTea/png/',img_source));
                cell_temp_sub_path{count}=img_source;
                cell_label{count}=char(action);
                count=count+1
            end
        end    
        tline = fgetl(fid);
    end
    fclose(fid);
end
[~,NoS]=size(cell_temp_sub_path);
indexing=rand()

struct_CSV(1).Path=cell_temp_sub_path';
struct_CSV(1).Label=cell_label';
struct2csv(struct_CSV, 'train_label_Gtea.CSV');

%%%%%%%%%%%%%%-------for validation------%%%%%%%%%%%%
%%%%%%%%%%%%%%---------------------------%%%%%%%%%%%%
count=1;
cell_temp_sub_path={};
cell_label={};
%struct_CSV = struct('Name',{},'Path',{},'Label',{});
for i=22:total_sub
    i
    label_txt=strcat(labels(i).folder,'/',labels(i).name)
    subject_path=strcat(subjects(i).folder,'/',subjects(i).name,'/')
    fid   = fopen(label_txt);
    tline = fgetl(fid);
    while ischar(tline)
        temp=tline;
        line=strsplit(temp);
        [~,yolo]=size(line);
        if yolo>3
            action=string(line{1,1});
            if action==string('x')
                action=string('bg');
            end
            if action==string('open')
                action=string('close');
            end
            from=str2double(line(end-2));
            to=str2double(line(end-1));             
            for j=from:to
                img_source=strcat(subjects(i).name,'/',num2str(j,'%.10d'),'.png');
                cell_temp_sub_path{count}=img_source;
                cell_label{count}=char(action);
                count=count+1;
               
            end
        end    
        tline = fgetl(fid);
    end
    fclose(fid);
end
% 
struct_CSV(1).Path=cell_temp_sub_path';
struct_CSV(1).Label=cell_label';
struct2csv(struct_CSV, 'test_label_Gtea.CSV');
