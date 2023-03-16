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

    public ControlsMeta(string name,List<ControlsMeta> child, List<Dictionary<string,ElemInfo>> elem, string description,string displayName)
    {
        Name = name;
        Child = child;
        Description = description;
        DisplayName = displayName;
        Elem = elem;
    }

    public ControlsMeta()
    {
        Child = new List<ControlsMeta>();
        Elem = new List<Dictionary<string,ElemInfo>>();
    }
}