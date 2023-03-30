using System.Net.Http.Json;
using System.Security.Cryptography;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Serialization;
using hydra_engine_blazor.Models;

namespace hydra_engine_blazor;

public class SettingsContainer
{
    public Dictionary<string,string> ListOutputUrl = new();
    private bool expand;

    public bool Expand
    {
        get => expand;
        set
        {
            expand = value;
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

    private string _currentDisplayNamePath;

    public string CurrentDisplayNamePath
    {
        get => _currentDisplayNamePath;
        set
        {
            _currentDisplayNamePath = value;
            NotifyStateChanged();
        }
    }
    public event Action? OnChange;
    private void NotifyStateChanged() => OnChange?.Invoke();
    private readonly HttpClient _client;
    private JsonSerializerOptions options = new()
    {
        Converters =
        {
            new JsonStringEnumConverter()
        },
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
    };
    public SettingsContainer(IHttpClientFactory ClientFactory)
    {
        _client = ClientFactory.CreateClient("WebApi");
    }
    /// <summary>
    /// Get structure of tree to form a menu
    /// </summary>
    public async Task<object?> GetTree()
    {
        return await _client.GetFromJsonAsync<object>($"api/hydra/tree");
    }
    /// <summary>
    /// Get all info about current form
    /// </summary>
    /// <param name="url"></param>
    /// <returns></returns>
    public async Task<object?> GetFormInfo(string url)
    {
        return await _client.GetFromJsonAsync<object>($"api/hydra/tree/{url}");
    }

    public async Task<object?> GetElementValue(string FilePath,string Key)
    {
        return await _client.GetFromJsonAsync<object>($"api/hydra/element/value/{FilePath}/{Key}", options);
    }

    public async Task<object?> GetElementInfo(string Key,string FilePath)
    {
        return await _client.GetFromJsonAsync<object>($"api/hydra/elements/info/{Key}?file_path={FilePath}",options);
    }
    /// <summary>
    /// Set new value to element in file
    /// </summary>
    /// <param name="Key"></param>
    /// <param name="Value"></param>
    /// <param name="FilePath"></param>
    public async Task<HttpResponseMessage> SetValues(List<KeyValuePair<string,ElemInfo>> changeElements)
    {
        var saveElements = changeElements.Select(element => new KeyValuePair<string, KeyValuePair<string, object>>(element.Value.fileId, new KeyValuePair<string, object>(element.Key, element.Value.value))).ToList();
        var json = JsonSerializer.Serialize(saveElements, options);
        HttpContent content = new StringContent(json, Encoding.UTF8, "application/json");
        return await _client.PostAsync($"api/hydra/elements/values",content);
    }

    public async Task<object?> UpdateData()
    {
        return await _client.GetFromJsonAsync<object>("update/data",options);
    }

    public async Task<string?> ResetInfrastructure()
    {
        return await _client.GetFromJsonAsync<string?>("api/hydra/reset/configuration", options);
    }
    
    /// <summary>
    /// Search elements,forms,groups
    /// </summary>
    /// <param name="value"></param>
    /// <returns></returns>
    public async Task<List<SearchEntity>?> SearchRequest(string value)
    {
        return await _client.GetFromJsonAsync<List<SearchEntity>>($"api/hydra/search?q={value}&pagelen=6", options);
    }
    /// <summary>
    /// Generating a hash code for anchor scrolling to an element
    /// </summary>
    /// <param name="input"></param>
    /// <returns></returns>
    public string GetHash(string input)
    {
        var sha256 = SHA256.Create();
        var hash = sha256.ComputeHash(Encoding.UTF8.GetBytes(input));
        return Convert.ToBase64String(hash);
    }

}