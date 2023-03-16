using System.Text.Json.Serialization;

namespace hydra_engine_blazor.Models;

public class SearchEntity
{
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("description")]
    public string Description { get; set; }
    
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("display_name")]
    public string DisplayName { get; set; }
    
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("entity")]
    public Entity Entity { get; set; }
    
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("input_url")]
    public string Input_Url { get; set; }
    
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("output_url")]
    public string Output_Url { get; set; }
    
}

public enum Entity
{
    Form,
    Group,
    Field
}