using System.Net.Http.Json;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Serialization;
using hydra_engine_blazor.Models;

namespace hydra_engine_blazor;

public class WizardContainer
{  
    public event Action? OnChange;
    private void NotifyStateChanged() => OnChange?.Invoke();
    private WizardState _wizardState = new(){CurrentStep = string.Empty,Arch = new Arch(){ArchName = string.Empty,Status = "not completed",StatusEnum = ArchStatus.NotCompleted},Sites = new List<Site>()};

    public WizardState WizardState
    {
        get => _wizardState;
        set
        {
            _wizardState = value;
            _wizardState.OnChange += NotifyStateChanged;
            NotifyStateChanged();
        }
    }

    private ControlsMeta wizardTree = new();

    public ControlsMeta WizardTree
    {
        get => wizardTree;
        set
        {
            wizardTree = value;
            NotifyStateChanged();
        }
    }
    private string currentElemKey;

    public string CurrentElemKey
    {
        get => currentElemKey;
        set
        {
            currentElemKey = value;
            NotifyStateChanged();
        }
    }

    private List<CommentItem> commentItems = new();

    public List<CommentItem> CommentItems
    {
        get => commentItems;
        set
        {
            commentItems = value;
            NotifyStateChanged();
        }
    }
    private readonly HttpClient _client;
    private JsonSerializerOptions options = new()
    {
        Converters =
        {
            new JsonStringEnumConverter()
        },
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
    };
    public WizardContainer(IHttpClientFactory ClientFactory)
    {
        _client = ClientFactory.CreateClient("WebApi");
    }
    public async Task<HttpResponseMessage> GetFormInfo(string url, List<Condition> conditions)
    {
        var json = JsonSerializer.Serialize(conditions, options);
        HttpContent content = new StringContent(json, Encoding.UTF8, "application/json");
        return await _client.PostAsync($"api/wizard/tree/{url}",content);
    }
    public async Task<HttpResponseMessage?> SetValues(List<KeyValuePair<string,ElemInfo>> changeElements,string formurl)
    {
        if (changeElements.Count <= 0) return null;
        var saveElements = changeElements.Select(element => new ParameterSaveInfo(){File_id = element.Value.fileId,Input_url = element.Key,Value = element.Value.value}).ToList();
        var json = JsonSerializer.Serialize(saveElements);
        HttpContent content = new StringContent(json, Encoding.UTF8, "application/json");
        return await _client.PostAsync($"api/wizard/elements/values?name={formurl}",content);

    }

    public async Task<HttpResponseMessage> SetCommentsOut()
    {
        var json = JsonSerializer.Serialize(commentItems);
        HttpContent content = new StringContent(json, Encoding.UTF8, "application/json");
        var response = await _client.PostAsync($"api/wizard/comment-out",content);
        if (response.IsSuccessStatusCode)
        {
            commentItems.Clear();
        }
        return response;
    }
    public async Task<HttpResponseMessage> InitArch(string archName)
    {
        HttpContent content = new StringContent("", Encoding.UTF8, "application/json");
        return await _client.PostAsync($"api/wizard/init_arch?name={archName}",content);
    }

    public async Task<HttpResponseMessage> DeploySite(string siteName, int stepNumber)
    {
        HttpContent content = new StringContent("", Encoding.UTF8, "application/json");
        return await _client.PostAsync($"api/wizard/deploy?name={siteName}&step_number={stepNumber}",content);
    }

    public async Task<List<Site>> CheckDeploy()
    {
        var sites = await _client.GetFromJsonAsync<List<Site>>("/api/wizard/check-deploy");
        foreach (var site in sites)
        {
            site.StatusEnum = site.Status switch
            {
                "not completed"=>ArchStatus.NotCompleted,
                "in progress"=>ArchStatus.InProgress,
                "completed"=>ArchStatus.Completed,
                "failed"=>ArchStatus.Failed
            };
        }
        return sites;
    }

    public async Task<ControlsMeta> UpdateLayoutTree()
    {
        var tree = new ControlsMeta();
        var query = await _client.GetFromJsonAsync<object>($"api/wizard/tree");
        tree.Name = "tree";
        if (query != null)
        {
            JsonParser.DeserializeTree(query.ToString(),tree,tree.Child);
        }

        return tree;
    }

    public async Task<WizardState> GetWizardState()
    {
        var wizardState = await _client.GetFromJsonAsync<WizardState>("api/wizard/wizard-state");
        if (wizardState != null)
        {
            wizardState.Arch.StatusEnum = wizardState.Arch.Status switch
            {
                "not completed" => ArchStatus.NotCompleted,
                "in progress" => ArchStatus.InProgress,
                "completed" => ArchStatus.Completed,
                _ => wizardState.Arch.StatusEnum
            };
            foreach (var wizardStateSite in wizardState.Sites)
            {
                wizardStateSite.StatusEnum = wizardStateSite.Status switch
                {
                    "not completed"=>ArchStatus.NotCompleted,
                    "in progress"=>ArchStatus.InProgress,
                    "completed"=>ArchStatus.Completed,
                    "failed"=>ArchStatus.Failed
                };
            }
        }
        return wizardState;
    }
}
