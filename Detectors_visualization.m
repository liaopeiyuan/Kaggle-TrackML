%uiopen('/Users/alexanderliao/Documents/GitHub/Kaggle-TrackML/portable-dataset/detectors.csv',1)
position = table2array(detectors(:,1:3));
coordinates = table2array(detectors(:,4:6));

i=1;

if 0 %layer:[2,4,6,8,10,12,14]
    while i<=max(size(position))
       if all([position(i,2)~=6, position(i,2)~=4, position(i,2)~=2])
           position(i,:)=[];
       else
           i=i+1;
       end
    end
end

if 0 %volume:[7,8,9,12,13,14,16,17,18]
    while i<=max(size(position))
       if all([position(i,1)~=7, position(i,1)~=8])
           position(i,:)=[];
       else
           i=i+1;
       end
    end
end

if 0 %module
    while i<=max(size(position))
       if position(i,3)<1000
           position(i,:)=[];
       else
           i=i+1;
       end
    end
end


layers=position(:,2);
layers=unique(layers);

volumes=position(:,1);
volumes=unique(volumes);

modules=position(:,3);
modules=unique(modules);

color = zeros(size(position));
for i=1:3
    color(:,i)=position(:,i)./max(position(:,i));
end

n=max(size(position))
scatter3(coordinates(1:n,1),coordinates(1:n,2),coordinates(1:n,3),30,[zeros(n,1),color(1:n,2),zeros(n,1)],'filled');
hold on
