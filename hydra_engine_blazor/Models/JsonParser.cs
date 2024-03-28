using System.Runtime.InteropServices;
using System.Text.Encodings.Web;
using System.Text.Json.Serialization;

namespace hydra_engine_blazor.Models;
using System.Text.Json.Nodes;
using System.Text.Json;
public class JsonParser
{
    public static void DeserializeTree(string? json,ControlsMeta tree,List<ControlsMeta> currentNode)
    {
        var jsonNode = JsonNode.Parse(json);
        var root = jsonNode.Root;
        var keyValuePairs = root.AsObject();
        foreach (var keyValue in keyValuePairs)
        {
            var node = new ControlsMeta();
            switch (keyValue.Key)
            {
                case "elem":
                    var elements=keyValue.Value?.AsArray();
                    var list = new List<Dictionary<string, ElemInfo>>();
                    if (elements != null)
                        foreach (var elem in elements)
                        {
                            var elemNode = elem?.AsObject();
                            if (elemNode == null) continue;
                            list.AddRange(from key in elemNode where !string.IsNullOrEmpty(key.Value?.ToString()) let elemInfo = DeserializeElemInfo(key.Value?.ToString()) select new Dictionary<string, ElemInfo>() { { key.Key, elemInfo } });
                        }

                    tree.Elem = list;
                    break;
                case "description":
                    tree.Description = keyValue.Value.ToString();
                    break;
                 case "display_name":
                     tree.DisplayName = keyValue.Value.ToString();
                     break;
                case "child":
                    if (!keyValue.Value.ToString().Equals("{}"))
                    {
                        tree.Child.Add(node);
                        DeserializeTree(keyValue.Value.ToString(),node,tree.Child);
                    }
                    break;
                case "type":
                    tree.Type = keyValue.Value.ToString();
                    break;
                case "action":
                    tree.Action = keyValue.Value?.ToString();
                    break;
                case "sub_type":
                    tree.SubType = keyValue.Value?.ToString();
                    break;
                case "site_name":
                    tree.SiteName = keyValue.Value?.ToString();
                    break;
                case "condition":
                    tree.Condition = JsonSerializer.Deserialize<List<Condition>>(keyValue.Value.ToString());
                    break;
                default:
                {
                    if (string.IsNullOrEmpty(tree.Name))
                    {
                        tree.Name = keyValue.Key;
                        DeserializeTree(keyValue.Value?.ToString(),tree,tree.Child);
                    }
                    else
                    {
                        node.Name = keyValue.Key;
                        currentNode.Add(node);
                        DeserializeTree(keyValue.Value?.ToString(),node,tree.Child);
                    }
                    break;
                }
            }
        }
    }

    public static ElemInfo DeserializeElemInfo(string? json, int index = 0, bool isDisable = false)
    {
        var elemInfo = new ElemInfo();
        if (json == null) return elemInfo;
        var jsonNode = JsonNode.Parse(json);
        var root = jsonNode.Root;
        var keyValuePairs = root.AsObject();
        foreach (var keyValue in keyValuePairs)
        {
            switch (keyValue.Key)
            {
                case"value":
                    if (keyValue.Value != null) elemInfo.value = DeserializeJsonValue(keyValue.Value);
                    break;
                case "placeholder":
                    elemInfo.placeholder = keyValue.Value?.ToString();
                    break;
                case "autocomplete":
                    elemInfo.autocomplete = keyValue.Value?.ToString();
                    break;
                case "file_id":
                    elemInfo.fileId = keyValue.Value.ToString();
                    break;
                case "type":
                    elemInfo.type = keyValue.Value.ToString() switch
                    {
                        "string" => ElemType.String,
                        "string-single-quoted"=>ElemType.String,
                        "string-double-quoted"=>ElemType.String,
                        "double" => ElemType.Double,
                        "int" => ElemType.Int,
                        "datetime" => ElemType.DateTime,
                        "bool"=>ElemType.Bool,
                        "dict"=>ElemType.Dict,
                        "array"=>ElemType.Array,
                        _ => elemInfo.type
                    };
                    break;
                case "description":
                    elemInfo.description = keyValue.Value?.ToString();
                    break;
                case "sub_type":
                    elemInfo.sub_type = keyValue.Value?.ToString() switch
                    {
                        "string" => ElemType.String,
                        "double" => ElemType.Double,
                        "int" => ElemType.Int,
                        "datetime" => ElemType.DateTime,
                        "bool"=>ElemType.Bool,
                        "dict"=>ElemType.Dict,
                        "composite"=>ElemType.Composite,
                        _ => elemInfo.type
                    };
                    break;
                case "readOnly":
                    if (bool.TryParse(keyValue.Value?.ToString().ToLower(), out _))
                    {
                        elemInfo.readOnly = (bool)keyValue.Value;
                    }
                    else
                    {
                        var readonlyDict = keyValue.Value.Deserialize<Dictionary<int,bool>>();
                        if (readonlyDict != null) elemInfo.readOnly = readonlyDict.GetValueOrDefault(index + 1, false);
                    }
                    break;
                case "commented":
                    if (keyValue.Value != null) elemInfo.commented = (bool)keyValue.Value;
                    elemInfo.disable = elemInfo.commented || isDisable;
                    break;
                case "additional":
                    if (keyValue.Value != null) elemInfo.additional = bool.Parse(keyValue.Value.ToString());
                    if (elemInfo.additional && elemInfo.value == null) elemInfo.IsActive = false;
                    break;
                case "display_name":
                    elemInfo.display_name = keyValue.Value?.ToString();
                    break;
                case "control":
                    elemInfo.control = keyValue.Value.ToString() switch
                    {
                        "input_control" => Control.Text,
                        "textarea_control" => Control.Textarea,
                        "label_control"=>Control.Label,
                        "password_control"=>Control.Password,
                        "checkbox_control" => Control.Checkbox,
                        "datetime_control"=>Control.Datetime,
                        "time_control"=>Control.Time,
                        "date_control"=>Control.Date,
                        _ => elemInfo.control
                    };
                    break;
                case "constraints":
                    if (!string.IsNullOrEmpty(keyValue.Value?.ToString()))
                    {
                        elemInfo.constraints =
                            JsonSerializer.Deserialize<List<ConstraintItem>>(keyValue.Value?.ToString());
                    }
                    break;
                case "sub_type_schema":
                    if (!string.IsNullOrEmpty(keyValue.Value?.ToString()))
                    {
                        var schema = new Dictionary<string, ElemInfo>();
                        foreach (var jsonObject in keyValue.Value.AsObject())
                        {
                            schema.Add(jsonObject.Key,DeserializeElemInfo(jsonObject.Value?.ToString(),isDisable:elemInfo.type != ElemType.Array && elemInfo.disable));
                        }

                        elemInfo.sub_type_schema = schema;
                    }
                    else
                    {
                        elemInfo.sub_type_schema = null;
                    }
                    break;
                case "array_sub_type_schema":
                    if (!string.IsNullOrEmpty(keyValue.Value?.ToString()))
                    {
                        var array_schema = new List<ArrayElement>();
                        var jsonArray = keyValue.Value.AsArray();
                        foreach (var el in jsonArray)
                        {
                            var schema = new Dictionary<string, ElemInfo>();
                            if (el != null)
                                foreach (var jsonObject in el.AsObject())
                                {
                                    schema.Add(jsonObject.Key, DeserializeElemInfo(jsonObject.Value?.ToString(),jsonArray.IndexOf(el),isDisable:elemInfo.disable));
                                }
                            array_schema.Add(new ArrayElement(){Elements = schema,Expand = true});
                        }

                        elemInfo.array_sub_type_schema = array_schema;
                    }
                    else
                    {
                        elemInfo.array_sub_type_schema = null;
                    }
                    break;
                case "isValid":
                    elemInfo.isValid = bool.Parse(keyValue.Value?.ToString());
                    break;
            }
        }

        return elemInfo;
    }

    public static string SerializeElemInfo(ElemInfo elemInfo)
    {
        JsonObject node = new JsonObject
        {
            ["value"] = elemInfo.value.ToString(),
            ["file_id"] = elemInfo.fileId,
            ["type"] = elemInfo.type switch
            {
                ElemType.String => "string",
                ElemType.Int => "int",
                ElemType.Double=>"double",
                ElemType.DateTime=>"datetime",
                ElemType.Bool => "bool",
                ElemType.Dict => "dict",
                ElemType.Array => "array",
                _ => throw new ArgumentOutOfRangeException()
            },
            ["sub_type"] = elemInfo.sub_type switch
            {
                ElemType.String => "string",
                ElemType.Int => "int",
                ElemType.Double=>"double",
                ElemType.DateTime=>"datetime",
                ElemType.Bool => "bool",
                ElemType.Dict => "dict",
                ElemType.Composite => "composite",
                _ => null
            },
            ["description"] = elemInfo.description,
            ["readOnly"] = elemInfo.readOnly,
            ["display_name"] = elemInfo.display_name,
            ["control"] = elemInfo.control switch
            {
                Control.Text => "input_control",
                Control.Textarea => "textarea_control",
                Control.Label => "label_control",
                Control.Password => "password_control",
                Control.Date => "date_control",
                Control.Datetime => "datetime_control",
                Control.Time => "time_control",
                Control.Number => "number_control",
                Control.Checkbox => "checkbox_control",
                Control.Radio => "radio_control",
                _ => throw new ArgumentOutOfRangeException()
            },
            ["constraints"] = JsonSerializer.Serialize(elemInfo.constraints),
            ["sub_type_schema"] = JsonSerializer.Serialize(elemInfo.sub_type_schema),
            ["array_sub_type_schema"] = JsonSerializer.Serialize(elemInfo.array_sub_type_schema),
            ["isValid"] = elemInfo.isValid
        };

        return node.ToJsonString();
    }
    private static object? DeserializeJsonValue(JsonNode? jsonNode)
    {
        switch (jsonNode)
        {
            case JsonArray jsonArray:
                var list = new List<object?>();
                foreach (var item in jsonArray)
                {
                    list.Add(DeserializeJsonValue(item));
                }
                return list;

            case JsonObject jsonObject:
                var result = new Dictionary<string, object?>();
                foreach (var kvp in jsonObject)
                {
                    result[kvp.Key] = DeserializeJsonValue(kvp.Value);
                }
                return result;

            default:
                var value = jsonNode?.ToString();
                if (int.TryParse(value, out _))
                {
                    return int.Parse(value);
                }
                if (double.TryParse(value, out _))
                {
                    return double.Parse(value);
                }
                if (bool.TryParse(value, out _))
                {
                    return bool.Parse(value);
                }
                if (DateTime.TryParse(value, out _))
                {
                    return DateTime.Parse(value);
                }
                return value;
        }
    }
}