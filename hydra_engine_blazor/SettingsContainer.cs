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
	public string Plan { get; set; }
    private Dictionary<string,string> dictOutputUrl = new();
    private bool expand;
    private DateTime modifyTime;

    public DateTime ModifyTime
    {
        get => modifyTime;
        set
        {
            modifyTime = value;
            NotifyStateChanged();
        }
    }

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

    public Dictionary<string, string> DictOutputUrl
    {
        get => dictOutputUrl;
        set
        {
            dictOutputUrl = value;
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

    public async Task<DateTime> GetModifiedTime()
    {
        return await _client.GetFromJsonAsync<DateTime>("api/hydra/modify");
    }

    public async Task<HttpResponseMessage> CheckModifyTime(DateTime time)
    {
        var formattedTime = time.ToString("o");
        var apiUrl = "api/hydra/check/modify";
        var queryString = $"modify_time={Uri.EscapeDataString(formattedTime)}";
        var apiUrlWithQuery = $"{apiUrl}?{queryString}";
        const string json = "";
        HttpContent content = new StringContent(json, Encoding.UTF8, "application/json");
        return await _client.PostAsync(apiUrlWithQuery,content);
    }
    /// <summary>
    /// Set new value to element in file
    /// </summary>
    /// <param name="Key"></param>
    /// <param name="Value"></param>
    /// <param name="FilePath"></param>
    public async Task<HttpResponseMessage> SetValues(List<KeyValuePair<string,ElemInfo>> changeElements,string formurl)
    {
        var saveElements = changeElements.Select(element => new ParameterSaveInfo(){File_id = element.Value.fileId,Input_url = element.Key,Value = element.Value.value}).ToList();
        var json = JsonSerializer.Serialize(saveElements);
        HttpContent content = new StringContent(json, Encoding.UTF8, "application/json");
        return await _client.PostAsync($"api/hydra/elements/values?name={formurl}",content);
    }

    public async Task<HttpResponseMessage> ResetInfrastructure()
    {
        HttpContent content = new StringContent("", Encoding.UTF8, "application/json");
        return await _client.PostAsync("api/hydra/configuration", content);
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