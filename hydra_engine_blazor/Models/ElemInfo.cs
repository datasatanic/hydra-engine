using System.ComponentModel;
using System.Runtime.Serialization;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Components;

namespace hydra_engine_blazor.Models;

public class ElemInfo
{
    [DataMember(Name = "value", EmitDefaultValue = false)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("value")]
    public object value;
    
    [DataMember(Name = "placeholder", EmitDefaultValue = false)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("placeholder")]
    public object? placeholder;
    
    [DataMember(Name = "autocomplete", EmitDefaultValue = false)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("autocomplete")]
    public object? autocomplete;
    
    [DataMember(Name = "file_id", EmitDefaultValue = false)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("file_id")]
    public string fileId;
    
    [DataMember(Name = "type", EmitDefaultValue = false)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("type")] 
    public ElemType type { get; set; }
    
    [DataMember(Name = "description", EmitDefaultValue = false)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("description")] 
    public string? description { get; set; }

    [DataMember(Name = "sub_type", EmitDefaultValue = true)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("sub_type")]
    public ElemType sub_type { get; set; }
    
    [DataMember(Name = "readOnly", EmitDefaultValue = false)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("readOnly")] 
    public bool readOnly { get; set; }
    
    [DataMember(Name = "additional", EmitDefaultValue = false)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("additional")] 
    public bool additional { get; set; }
    
    [DataMember(Name = "display_name", EmitDefaultValue = false)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("display_name")]
    
    public string? display_name { get; set; }
    [DataMember(Name = "control", EmitDefaultValue = false)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("control")] 
    public Control control { get; set; }

    [DataMember(Name = "constraints", EmitDefaultValue = false)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("constraints")]
    public List<ConstraintItem> constraints { get; set; }
    
    [DataMember(Name = "sub_type_schema", EmitDefaultValue = false)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("sub_type_schema")]
    public Dictionary<string,ElemInfo>? sub_type_schema { get; set; }
    [DataMember(Name = "array_sub_type_schema", EmitDefaultValue = false)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("array_sub_type_schema")]
    public List<Dictionary<string,ElemInfo>>? array_sub_type_schema { get; set; }

    [JsonIgnore(Condition = JsonIgnoreCondition.Always)]
    public bool isValid { get; set; } = true;

    [JsonIgnore(Condition = JsonIgnoreCondition.Always)]
    public bool Expand { get; set; }

    [JsonIgnore(Condition = JsonIgnoreCondition.Always)]
    public bool IsActive { get; set; } = true;

    public ElemInfo DeepCopy()
    {
        var clonedElemInfo = new ElemInfo
        {
            value = DeepCopyValue(value),
            placeholder = placeholder,
            fileId = fileId,
            type = type,
            sub_type = sub_type,
            description = description,
            display_name = display_name,
            constraints = new List<ConstraintItem>(constraints).Select(item => new ConstraintItem()
                { value = item.value, message = item.message, type = item.type }).ToList(),
            control = control,
            readOnly = readOnly,
            additional = additional,
            isValid = isValid,
            IsActive = IsActive,
            sub_type_schema = sub_type_schema?.ToDictionary(
                kvp => kvp.Key,
                kvp => kvp.Value.DeepCopy()
            ),
            array_sub_type_schema = array_sub_type_schema?.Select(item =>
                item.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.DeepCopy())).ToList()
        };

        return clonedElemInfo;
    }
    private object DeepCopyValue(object originalValue)
    {
        switch (originalValue)
        {
            case null:
                return null;
            case Dictionary<string, object> originalDictionary:
            {
                var clonedDictionary = new Dictionary<string, object>();
                foreach (var kvp in originalDictionary)
                {
                    clonedDictionary.Add(kvp.Key, DeepCopyValue(kvp.Value));
                }
                return clonedDictionary;
            }
            case List<object> originalList:
            {
                var clonedList = new List<object>();
                foreach (var item in originalList)
                {
                    clonedList.Add(DeepCopyValue(item));
                }
                return clonedList;
            }
            default:
                return originalValue;
        }
    }


}
[Flags]
public enum ElemType
{
    [EnumMember(Value = "string")]
    String,
    [EnumMember(Value = "int")]
    Int,
    [EnumMember(Value = "double")]
    Double,
    [EnumMember(Value = "bool")]
    Bool,
    [EnumMember(Value = "datetime")]
    DateTime,
    [EnumMember(Value = "range")]
    Range,
    [EnumMember(Value = "array")]
    Array,
    [EnumMember(Value = "composite")]
    Composite,
    [EnumMember(Value = "dict")]
    Dict
}
[Flags]
public enum Control
{
    [EnumMember(Value = "input_control")]
    Text,
    [EnumMember(Value = "textarea_control")]
    Textarea,
    [EnumMember(Value = "label_control")]
    Label,
    [EnumMember(Value = "password_control")]
    Password,
    [EnumMember(Value = "date_control")]
    Date,
    [EnumMember(Value = "datetime_control")]
    Datetime,
    [EnumMember(Value = "time_control")]
    Time,
    [EnumMember(Value = "number_control")]
    Number,
    [EnumMember(Value = "checkbox_control")]
    Checkbox,
    [EnumMember(Value = "radio_control")]
    Radio
}

public class ConstraintItem
{
    public string value { get; set; }
    public string type { get; set; }
    public string? message { get; set; }

}