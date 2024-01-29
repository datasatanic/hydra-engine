using System.ComponentModel;
using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace hydra_engine_blazor.Models;

public class ElemInfo : ICloneable
{
    [DataMember(Name = "value", EmitDefaultValue = false)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("value")]
    public object value;
    
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
    
    [DataMember(Name = "readOnly", EmitDefaultValue = false)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("readOnly")]
    
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

    public object Clone()
    {
        return MemberwiseClone();
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