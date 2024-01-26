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

    public static ElemInfo DeserializeElemInfo(string? json, int index = 0)
    {
        var elemInfo = new ElemInfo();
        var jsonNode = JsonNode.Parse(json);
        var root = jsonNode.Root;
        var keyValuePairs = root.AsObject();
        foreach (var keyValue in keyValuePairs)
        {
            switch (keyValue.Key)
            {
                case"value":
                    elemInfo.value = keyValue.Value?.ToString() ?? "";
                    break;
                case "file_id":
                    elemInfo.fileId = keyValue.Value.ToString();
                    break;
                case "type":
                    elemInfo.type = keyValue.Value.ToString() switch
                    {
                        "string" => ElemType.String,
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
                        "radio_control" => Control.Radio,
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
                        elemInfo.sub_type_schema =
                            JsonSerializer.Deserialize<Dictionary<string, object>>(keyValue.Value?.ToString());
                    }
                    else
                    {
                        elemInfo.sub_type_schema = null;
                    }
                    break;
                case "array_sub_type_schema":
                    if (!string.IsNullOrEmpty(keyValue.Value?.ToString()))
                    {
                        elemInfo.array_sub_type_schema =
                            JsonSerializer.Deserialize<List<Dictionary<string, object>>>(keyValue.Value?.ToString());
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
}