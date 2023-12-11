using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace hydra_engine_blazor.Models;

public class Condition
{
    [DataMember(Name = "key", EmitDefaultValue = false)]
    [JsonPropertyName("key")]
    public string Key { get; set; }
    
    [DataMember(Name = "allow", EmitDefaultValue = false)]
    [JsonPropertyName("allow")]
    public Dictionary<string,List<object>> Allow { get; set; }
}