classdef JSON
    %JSON  Serialize a matlab variable to json format
    %
    %  [ X ] = JSON.load( S )
    %  [ S ] = JSON.dump( X )
    %
    %  [ X ] = JSON.read( filepath )
    %  JSON.write( filepath, X )
    %
    % JSON.load takes JSON string S and returns matlab variable X.
    % JSON.dump takes matlab variable X and converts to JSON string S.
    % JSON.read and JSON.write are convenient methods to load and dump
    % JSON string directly from a file.
    % 
    % Examples:
    % To serialize matlab object
    % 
    %   >> X = struct('matrix', magic(2), 'char', 'hello');
    %   >> S = JSON.dump(X);
    %   >> disp(S);
    %   {"char":"hello","matrix":[[1,3],[4,2]]}
    % 
    % To decode json string
    % 
    %   >> X = JSON.load(S);
    %   >> disp(X);
    %      char: 'hello'
    %    matrix: [2x2 double]
    %
    % To save matlab object in a JSON file
    %
    %   >> JSON.write('/path/to/my.JSON',X);
    %
    % To read matlab object from a JSON file
    %
    %   >> X = JSON.read('/path/to/my.JSON');
    %
    % See also xmlread xmlwrite
    
    properties (Constant, Access = private)
        JARFILE = JSON.jarfile % Java class path to JSON library
    end
    
    methods (Static)        
        function X = load( S )
            %LOAD load matlab object from json string
            javaaddpath(JSON.JARFILE);
            S = strtrim(S);
            if isempty(S)
                error('JSON:load:invalidString','Invalid JSON string');
            end
            if S(1)=='['
                obj = org.json.JSONArray(java.lang.String(S));
            elseif S(1)=='{'
                obj = org.json.JSONObject(java.lang.String(S));
            else
                error('JSON:load:invalidString','Invalid JSON string');
            end
            
            % Convert to matlab object
            X = JSON.load_data(obj);
        end
        
        function S = dump( X )
            %DUMP serialize matlab object into json string
            javaaddpath(JSON.JARFILE);
            obj = JSON.dump_data(X);
            
            % Dump into json string
            S = char(obj.toString());
        end
        
        function X = read( filepath )
            %READ read and decode json data from file
            fid = fopen(filepath,'r');
            S = fscanf(fid,'%c',inf);
            fclose(fid);
            X = JSON.load( S );
        end
        
        function write( filepath, X )
            %WRITE serialize and write json data to file
            S = JSON.dump( X );
            fid = fopen(filepath,'w');
            fprintf(fid,'%s',S);
            fclose(fid);
        end
    end
    
    methods (Static, Access=private)
        function [ S ] = jarfile()
            %JARFILE path to the SnakeYAML jar file
            S = fileparts(mfilename('fullpath'));
            S = fullfile(S,'java','json.jar');
        end
        
        function result = load_data( r )
            %LOAD_DATA recursively convert java objects
            if isa(r, 'char')
                result = char(r);
            elseif isa(r, 'double')
                result = double(r);
            elseif isa(r, 'org.json.JSONArray')
                result = cell(1,r.length());
                for i = 1:r.length()
                    result{i} = JSON.load_data(r.get(i-1));
                end
                result = JSON.merge_cell(result);
            elseif isa(r, 'org.json.JSONObject')
                result = struct;
                itr = r.keys();
                while itr.hasNext()
                    key = itr.next();
                    result.(char(key)) = JSON.load_data(...
                        r.get(java.lang.String(key)));
                end
            else
                error('JSON:load_data:typeError',...
                    ['Unknown data type: ' class(r)]);
            end
        end
        
        function result = merge_cell( r )
            %MERGE_CELL convert cell array to native matrix
            
            % Check eligibility
            merge = false;
            if all(cellfun(@isnumeric,r))
                merge = true;
            elseif all(cellfun(@isstruct,r))
                f = cellfun(@fieldnames,r,'UniformOutput',false);
                if isempty(f) || all(cellfun(@(x) all(strcmp(f{1},x)),f))
                    merge = true;
                end
            end
            
            % Merge if scalar or row vector
            result = r;
            if merge
                if all(cellfun(@isscalar,r))
                    result = [r{:}];
                elseif all(cellfun(@isrow,r)) &&...
                        length(unique(cellfun(@length,r)))==1
                    result = cat(1,r{:});
                end
            end
        end
        
        function result = dump_data( r )
            %DUMP_DATA convert 
            if ischar(r)
                result = java.lang.String(r);
            elseif ~isscalar(r)
                result = org.json.JSONArray();
                if size(r,1)==1
                    for i = 1:numel(r)
                        if iscell(r)
                            result.put(JSON.dump_data(r{i}));
                        else
                            result.put(JSON.dump_data(r(i)));
                        end
                    end
                else
                    for i = 1:size(r,1)
                        result.put(JSON.dump_data(r(i,:)));
                    end
                end
            elseif isnumeric(r)
                result = java.lang.Double(r);
            elseif isstruct(r)
                result = org.json.JSONObject();
                keys = fields(r);
                for i = 1:length(keys)
                    result.put(keys{i},JSON.dump_data(r.(keys{i})));
                end
            elseif iscell(r)
                result = org.json.JSONArray();
                result.put(JSON.dump_data(r{1}));
            else
                error('JSON:load_data:typeError',...
                    ['Unsupported data type: ' class(r)]);
            end
        end
        
    end
    
end

