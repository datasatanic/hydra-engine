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
    private bool initializing;

    public bool Initializing
    {
        get => initializing;
        set
        {
            initializing = value;
            NotifyStateChanged();
        }
    }
    private string _currentOutputUrl;

    public string CurrentOutputUrl
    {
        get => _currentOutputUrl;
        set
        {
            _currentOutputUrl = value;
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

    private List<Dictionary<string,ElemInfo>> formElements = new();

    public List<Dictionary<string,ElemInfo>> FormElements
    {
        get => formElements;
        set
        {
            formElements = value;
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

    public async Task<HttpResponseMessage> InitArch(string archName)
    {
        HttpContent content = new StringContent("", Encoding.UTF8, "application/json");
        return await _client.PostAsync($"api/wizard/init_arch?name={archName}",content);
    }

    public async Task<HttpResponseMessage> DeploySite(string siteName)
    {
        HttpContent content = new StringContent("", Encoding.UTF8, "application/json");
        return await _client.PostAsync($"api/wizard/deploy?name={siteName}",content);
    }

    public async Task<string> CheckDeploy()
    {
        return await _client.GetStringAsync("/api/wizard/check-deploy");
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
}
