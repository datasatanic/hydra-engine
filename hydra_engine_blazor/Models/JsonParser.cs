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
                            list.AddRange(from key in elemNode
                                let elemInfo = DeserializeElemInfo(key.Value?.ToString())
                                select new Dictionary<string, ElemInfo>() { { key.Key, elemInfo } });
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
                default:
                {
                    if (string.IsNullOrEmpty(tree.Name))
                    {
                        tree.Name = keyValue.Key;
                        DeserializeTree(keyValue.Value.ToString(),tree,tree.Child);
                    }
                    else
                    {
                        node.Name = keyValue.Key;
                        currentNode.Add(node);
                        DeserializeTree(keyValue.Value.ToString(),node,tree.Child);
                    }
                    break;
                }
            }
        }
    }

    public static ElemInfo DeserializeElemInfo(string? json)
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
                    elemInfo.value = keyValue.Value.ToString();
                    break;
                case "file_id":
                    elemInfo.fileId = keyValue.Value.ToString();
                    break;
                case "type":
                    elemInfo.type = keyValue.Value.ToString() switch
                    {
                        "string" => ElemType.String,
                        "double" => ElemType.Double,
                        "integer" => ElemType.Int,
                        "datetime" => ElemType.DateTime,
                        "bool"=>ElemType.Bool,
                        "range"=>ElemType.Range,
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
                        "integer" => ElemType.Int,
                        "datetime" => ElemType.DateTime,
                        "bool"=>ElemType.Bool,
                        "range"=>ElemType.Range,
                        _ => elemInfo.type
                    };
                    break;
                case "readOnly":
                    elemInfo.readOnly = (bool)keyValue.Value;
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
                        "list_control" => Control.Fieldset,
                        "range_control"=>Control.Range,
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
            }
        }

        return elemInfo;
    }
}