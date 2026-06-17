function value = beamGetField(s, names, defaultValue)
%BEAMGETFIELD 从结构体中读取字段，若不存在则返回默认值。
%
% names 可以是字符串、字符向量或字符串数组。例如 ["M", "M0"] 表示
% 先尝试读取 M 字段，若不存在再尝试读取 M0 字段。这个工具函数用于
% 提高输入结构体的兼容性。

if ischar(names)
    names = string(names);
end

for k = 1:numel(names)
    name = char(names(k));
    if isfield(s, name)
        value = s.(name);
        return;
    end
end

value = defaultValue;
end
