using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace hydra_engine_blazor.Models;

public class ParameterSaveInfo
{
    [DataMember(Name = "input_url", EmitDefaultValue = false)]
    [JsonPropertyName("input_url")]
    public string Input_url { get; set; }
    [DataMember(Name = "value", EmitDefaultValue = false)]
    [JsonPropertyName("value")]
    public object Value { get; set; }
    [DataMember(Name = "file_id", EmitDefaultValue = false)]
    [JsonPropertyName("file_id")]
    public string File_id { get; set; }
}