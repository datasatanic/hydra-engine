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

    [JsonPropertyName("site_name")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public string? SiteName;

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

public class WizardState
{
    public event Action? OnChange;
    private void NotifyStateChanged() => OnChange?.Invoke();
    private string currentStep;
    private Arch arch;
    private List<Site> _sites;

    [JsonPropertyName("current_step")]
    public string CurrentStep
    {
        get => currentStep;
        set
        {
            currentStep = value;
            NotifyStateChanged();
        }
    }

    [JsonPropertyName("arch")]
    public Arch Arch
    {
        get => arch;
        set
        {
            arch = value;
            arch.OnChange += NotifyStateChanged;
            NotifyStateChanged();
        }
    }

    [JsonPropertyName("sites")]
    public List<Site> Sites
    {
        get => _sites;
        set
        {
            _sites = value;
            NotifyStateChanged();
        }
    }

    public void AddSite(Site site)
    {
        site.OnChange += NotifyStateChanged;
        _sites.Add(site);
        NotifyStateChanged();
    }
}
public class Arch
{
    public event Action? OnChange;
    private void NotifyStateChanged() => OnChange?.Invoke();
    private string archName;
    private string status = "not completed";
    private ArchStatus statusEnum = ArchStatus.NotCompleted;

    [JsonPropertyName("arch_name")]
    public string ArchName
    {
        get => archName;
        set
        {
            archName = value;
            NotifyStateChanged();
        }
    }

    [JsonPropertyName("status")]
    public string Status
    {
        get => status;
        set
        {
            status = value;
            NotifyStateChanged();
        }
    }
    // Дополнительное свойство, хранящее значение перечисления для статуса
    [JsonIgnore]
    public ArchStatus StatusEnum
    {
        get => statusEnum;
        set
        {
            statusEnum = value;
            NotifyStateChanged();
        }
    }
}

public class Site
{
    public event Action? OnChange;
    private void NotifyStateChanged() => OnChange?.Invoke();
    private string siteName;
    private int stepNumber;
    private string status = "not completed";
    private ArchStatus statusEnum = ArchStatus.NotCompleted;
    [JsonPropertyName("site_name")]
    public string SiteName
    {
        get => siteName;
        set
        {
            siteName = value;
            NotifyStateChanged();
        }
    }
    [JsonPropertyName("status")]
    public string Status
    {
        get => status;
        set
        {
            status = value;
            NotifyStateChanged();
        }
    }

    [JsonPropertyName("step_number")]
    public int StepNumber
    {
        get => stepNumber;
        set
        {
            stepNumber = value;
            NotifyStateChanged();
        }
    }
    [JsonIgnore]
    public ArchStatus StatusEnum
    {
        get => statusEnum;
        set
        {
            statusEnum = value;
            NotifyStateChanged();
        }
    }
}
public enum ArchStatus
{
    Completed,
    NotCompleted,
    InProgress,
    Failed
}
