namespace hydra_engine_blazor.Models;
using System.Text.Json.Serialization;
public class ControlsMeta
{
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public string Name { get; set; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("child")] 
    public List<ControlsMeta> Child { get; set; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("elem")] 
    public List<Dictionary<string,ElemInfo>> Elem { get; set; }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("description")]
    public string Description { get; set; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("type")]
    public string Type { get; set; } = "form";
    
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("display_name")]
    public string DisplayName { get; set; }
    
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("condition")]
    public List<Condition> Condition{ get; set; }
    
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("action")]
    public string? Action { get; set; }
    
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    [JsonPropertyName("sub_type")]
    public string? SubType { get; set; }

    public ControlsMeta(string name,List<ControlsMeta> child, List<Dictionary<string,ElemInfo>> elem, string description,string displayName,List<Condition> condition)
    {
        Name = name;
        Child = child;
        Description = description;
        DisplayName = displayName;
        Elem = elem;
        Condition = condition;
    }

    public ControlsMeta()
    {
        Child = new List<ControlsMeta>();
        Elem = new List<Dictionary<string,ElemInfo>>();
    }
}